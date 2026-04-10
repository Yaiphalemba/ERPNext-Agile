// erpnext_agile/public/js/project_agile.js
frappe.ui.form.on('Project', {
    refresh: function(frm) {
        if (frm.doc.enable_agile) {
            add_agile_project_buttons(frm);
        }
    },
    
    enable_agile: function(frm) {
        if (frm.doc.enable_agile && !frm.doc.project_key && frm.doc.project_name) {
            frm.set_value('project_key', generate_project_key(frm.doc.project_name));
        }
    },

    project_name: function(frm) {
        if (frm.doc.__islocal && frm.doc.project_name && frm.doc.enable_agile) {
            frm.set_value('project_key', generate_project_key(frm.doc.project_name));
        }
    }
});

function generate_project_key(project_name) {
    if (!project_name) return '';
    let words = project_name.trim().toUpperCase().split(/\s+/); // Better regex split
    if (words.length >= 3) {
        return words[0][0] + words[1][0] + words[2][0];
    } else if (words.length === 2) {
        return words[0][0] + (words[1].length > 1 ? words[1].substring(0, 2) : words[1][0]);
    } else {
        return words[0].substring(0, 3);
    }
}

function add_agile_project_buttons(frm) {
    // View Board - Opens a dialog showing the board
    frm.add_custom_button(__('View Board'), function() {
        show_agile_board(frm);
    }, __('Agile'));
    
    // View Backlog - Opens backlog dialog
    frm.add_custom_button(__('View Backlog'), function() {
        show_backlog(frm);
    }, __('Agile'));
    
    // Sprint Planning - Opens sprint planning dialog
    frm.add_custom_button(__('Sprint Planning'), function() {
        show_sprint_planning(frm);
    }, __('Agile'));
    
    // Reports - Shows report menu
    frm.add_custom_button(__('Reports'), function() {
        show_agile_reports_menu(frm);
    }, __('Agile'));
    
    
    // Bulk Sync GitHub
    let github_enabled = 0;
    frappe.db.get_value('GitHub Settings', 'GitHub Settings', 'enabled', (r)=>{
        if(r && r.enabled == 1){
            github_enabled = 1;
        }
        if (github_enabled === 1 && frm.doc.repository) {
            frm.add_custom_button(__('Bulk Sync GitHub'), function() {
                bulk_sync_github(frm);
            }, __('GitHub'));
        }
    });
}

function show_agile_board(frm) {
    // 1. Create the dialog only if it doesn't exist yet
    if (!frm.agile_board_dialog) {
        frm.agile_board_dialog = new frappe.ui.Dialog({
            title: __('Agile Board - {0}', [frm.doc.project_name]),
            size: 'extra-large',
            fields: [
                { fieldname: 'board_html', fieldtype: 'HTML' }
            ]
        });
    }

    let d = frm.agile_board_dialog;

    // 2. Update the title (just in case they edited the project name before clicking)
    d.set_title(__('Agile Board - {0}', [frm.doc.project_name]));

    // 3. Reset the container to the loading state
    d.fields_dict.board_html.$wrapper.html(`
        <div class="text-center" style="padding: 60px 20px;">
            <div class="spinner-border text-primary" role="status">
                <span class="sr-only">Loading...</span>
            </div>
            <p class="text-muted mt-3" style="font-size: 14px;">Fetching board data...</p>
        </div>
    `);

    // 4. Show the dialog
    d.show();

    // 5. Fire off the API call to populate the board
    load_board(frm, frm.doc.name, null, d.fields_dict.board_html.$wrapper);
}

function load_board(frm, project, sprint, container) {
    frappe.call({
        method: 'erpnext_agile.api.get_board_data',
        args: {
            project: project,
            sprint: sprint || null,
            view_type: 'sprint'
        },
        callback: function(r) {
            if (r.message) {
                render_board(container, r.message, frm, project, sprint);
            }
        }
    });
}

function render_board(container, board_data, frm, current_project, current_sprint) {
    let html = '';

    // Project + Sprint Filters UI
    html += `
        <div style="margin-bottom: 15px; display:flex; gap:10px;">
            <select id="project_filter" class="form-control"></select>
            <select id="sprint_filter" class="form-control"></select>
        </div>
    `;

    // Active Sprint Header
    html += `<div class="board-header" style="margin-bottom: 20px;">`;
    if (board_data.active_sprint) {
        html += `<div class="alert alert-info">
            <strong>Active Sprint:</strong> ${board_data.active_sprint.sprint_name}
            <span class="text-muted ml-3">
                ${frappe.datetime.str_to_user(board_data.active_sprint.start_date)} - 
                ${frappe.datetime.str_to_user(board_data.active_sprint.end_date)}
            </span>
        </div>`;
    } else {
        html += '<div class="alert alert-warning">No active sprint</div>';
    }
    html += '</div>';

    // Board Columns
    html += '<div class="board-columns" style="display: flex; gap: 15px; overflow-x: auto;">';
    for (let status in board_data.columns) {
        html += render_board_column(status, board_data.columns[status]);
    }
    html += '</div>';

    container.html(html);

    // Wait for DOM to be ready before populating filters
    setTimeout(() => {
        populate_project_and_sprint_filters(board_data, frm, current_project, current_sprint, container);
    }, 100);

    make_columns_sortable(frm, board_data);

    container.find('.issue-card').on('click', function() {
        frappe.set_route('Form', 'Task', $(this).data('issue-name'));
    });
}

function populate_project_and_sprint_filters(board_data, frm, current_project, current_sprint, container) {
    const $projectFilter = container.find('#project_filter');
    const $sprintFilter = container.find('#sprint_filter');

    if ($projectFilter.length === 0 || $sprintFilter.length === 0) {
        console.warn('Filter elements not found in container');
        return;
    }

    // 1. Eager Load (Prevents UI flickering while API calls happen)
    $projectFilter.empty().append(`<option value="${current_project}">${board_data.project_name || current_project}</option>`);
    
    $sprintFilter.empty().append('<option value="">All Sprints</option>');
    if (current_sprint) {
        let eager_sprint_name = board_data.active_sprint ? board_data.active_sprint.sprint_name : current_sprint;
        $sprintFilter.append(`<option value="${current_sprint}" selected>${eager_sprint_name}</option>`);
    }

    // 2. Fetch and populate ALL Projects
    frappe.call({
        method: "frappe.client.get_list",
        args: { 
            doctype: "Project", 
            fields: ["name", "project_name"], 
            limit_page_length: 100 
        },
        callback: function(r) {
            if (r.message) {
                $projectFilter.empty(); // Clear eager load
                r.message.forEach(proj => {
                    $projectFilter.append(`<option value="${proj.name}">${proj.project_name || proj.name}</option>`);
                });
                
                // Set the active value
                $projectFilter.val(current_project);

                // Set up project filter change event
                $projectFilter.off('change').on('change', function() {
                    let selected_project = $(this).val();
                    // CRITICAL FIX: Force sprint to null when switching projects!
                    load_board(frm, selected_project, null, container);
                });
            }
        }
    });

    // 3. Fetch and populate ALL Sprints for this specific project
    if (current_project) {
        frappe.call({
            method: "frappe.client.get_list",
            args: { 
                doctype: "Agile Sprint", 
                filters: { project: current_project }, 
                fields: ["name", "sprint_name"], 
                limit_page_length: 100 
            },
            callback: function(r) {
                if (r.message) {
                    $sprintFilter.empty(); // Clear eager load
                    $sprintFilter.append('<option value="">All Sprints</option>'); // Always available
                    
                    r.message.forEach(s => {
                        $sprintFilter.append(`<option value="${s.name}">${s.sprint_name}</option>`);
                    });

                    // Safely set the active sprint
                    if (current_sprint) {
                        $sprintFilter.val(current_sprint);
                    }

                    // Set up sprint filter change event
                    $sprintFilter.off('change').on('change', function() {
                        let selected_project = $projectFilter.val();
                        let selected_sprint = $(this).val() || null;
                        load_board(frm, selected_project, selected_sprint, container);
                    });
                }
            }
        });
    }
}

function render_board_column(status, column) {
    const border_color = column.status.color || '#dfe1e6';
    
    let html = `
        <div class="board-column" data-status="${status}" style="min-width: 320px; max-width: 320px; background: #f4f5f7; border-radius: 8px; padding: 12px; display: flex; flex-direction: column; max-height: 70vh;">
            <div class="column-header" style="font-weight: 600; font-size: 14px; color: #5e6c84; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 3px solid ${border_color}; display: flex; justify-content: space-between; align-items: center;">
                <span class="text-uppercase" style="letter-spacing: 0.5px;">${status}</span>
                <div>
                    ${column.total_points > 0 ? `<span class="badge badge-light ml-1" style="font-size: 11px;">${column.total_points} pts</span>` : ''}
                    <span class="badge badge-secondary ml-1" style="border-radius: 12px;">${column.issues.length}</span>
                </div>
            </div>
            <div class="column-issues" data-status="${status}" style="flex-grow: 1; overflow-y: auto; padding-right: 4px; min-height: 100px;">`;

    if (column.issues && column.issues.length > 0) {
        column.issues.forEach(issue => {
            html += `
                <div class="issue-card" data-issue-name="${issue.name}" style="background: white; border-radius: 6px; padding: 12px; margin-bottom: 10px; cursor: grab; box-shadow: 0 1px 2px rgba(9,30,66,0.15); transition: background-color 0.2s ease;">
                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 6px;">
                        <span style="font-size: 12px; color: #6b778c; font-weight: 500;">${issue.issue_key}</span>
                        ${issue.story_points ? `<span class="badge badge-info" style="border-radius: 10px; font-size: 11px;">${issue.story_points}</span>` : ''}
                    </div>
                    <div style="font-size: 14px; color: #172b4d; font-weight: 500; line-height: 1.4; margin-bottom: 12px;">
                        ${issue.subject}
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span class="badge" style="background: #ebecf0; color: #42526e;">${issue.issue_type || 'Task'}</span>
                        ${issue.issue_priority ? `<span class="badge badge-${get_priority_badge_class(issue.issue_priority)}">${issue.issue_priority}</span>` : ''}
                    </div>
                </div>`;
        });
    } else {
        // Empty state block so SortableJS has a drop target
        html += '<div class="empty-column-dropzone" style="height: 100%; border: 2px dashed #dfe1e6; border-radius: 6px; display: flex; align-items: center; justify-content: center; color: #a5adba; font-size: 12px;">Drop issues here</div>';
    }

    html += `</div></div>`;
    return html;
}

function get_priority_badge_class(priority) {
    const classes = { 'Critical': 'danger', 'High': 'warning', 'Medium': 'info', 'Low': 'secondary' };
    return classes[priority] || 'secondary';
}

function make_columns_sortable(frm, board_data) {
    $(".board-column .column-issues").each(function() {
        Sortable.create(this, {
            group: 'issues',
            animation: 150,
            onEnd: function(evt) {
                let task_name = $(evt.item).data("issue-name");
                
                // The item might drop into an empty column or a populated one. 
                // We get the status from the .column-issues wrapper we dropped it into.
                let from_status = $(evt.from).data("status");
                let to_status = $(evt.to).data("status");

                if (from_status === to_status) return; // Didn't actually change columns

                // Remove the empty state dashed box if it exists
                $(evt.to).find('.empty-column-dropzone').remove();

                frappe.call({
                    method: "erpnext_agile.api.move_issue",
                    args: { task_name, from_status, to_status },
                    callback: function(r) {
                        if (!r.exc) {
                            frappe.show_alert({ message: __('Moved to ' + to_status), indicator: 'green' });
                        }
                    }
                });
            }
        });
    });
}

function show_backlog(frm) {
    // 1. Create the dialog only if it doesn't exist yet
    if (!frm.agile_backlog_dialog) {
        frm.agile_backlog_dialog = new frappe.ui.Dialog({
            title: __('Product Backlog - {0}', [frm.doc.project_name]),
            size: 'extra-large',
            fields: [
                {
                    fieldname: 'filters_section',
                    fieldtype: 'Section Break',
                    label: 'Filters'
                },
                {
                    fieldname: 'type_filter',
                    fieldtype: 'Link',
                    label: 'Issue Type',
                    options: 'Agile Issue Type',
                    onchange: function() {
                        // Let Frappe finish updating its internal state first
                        setTimeout(() => {
                            load_backlog_data(frm.agile_backlog_dialog, frm);
                        }, 50);
                    }
                },
                {
                    fieldname: 'backlog_html',
                    fieldtype: 'HTML'
                }
            ],
            primary_action_label: __('Create Issue'),
            primary_action: function() {
                // Open new issue form
                frappe.new_doc('Task', {
                    project: frm.doc.name,
                    is_agile: 1
                });
            }
        });
    }

    let d = frm.agile_backlog_dialog;

    // 2. Update the title dynamically
    d.set_title(__('Product Backlog - {0}', [frm.doc.project_name]));
    
    // Note: We deliberately DO NOT clear the filters here. 
    // This provides a great UX: if they close the backlog and reopen it, 
    // their previous filters remain intact!

    // 3. Show the dialog
    d.show();
    
    // 4. Load the data (which will show its own spinner inside load_backlog_data)
    load_backlog_data(d, frm);
}

function load_backlog_data(dialog, frm) {
    dialog.fields_dict.backlog_html.$wrapper.html(`
        <div class="text-center" style="padding: 40px;">
            <div class="spinner-border text-primary" role="status"></div>
            <p class="text-muted mt-3">Loading backlog...</p>
        </div>
    `);
    
    let filters = {};
    let selected_type = dialog.get_value('type_filter');
    
    if (selected_type) {
        // Double-check that your database field is actually 'issue_type' 
        // and not 'custom_issue_type'
        filters.issue_type = selected_type; 
    }
    
    frappe.call({
        method: 'erpnext_agile.api.get_backlog',
        args: {
            project: frm.doc.name,
            // Force it into a clean JSON string so Python receives it correctly
            filters: Object.keys(filters).length > 0 ? JSON.stringify(filters) : null
        },
        callback: function(r) {
            if (r.message) {
                render_backlog(dialog.fields_dict.backlog_html.$wrapper, r.message, frm);
            }
        }
    });
}

function render_backlog(container, backlog_items, frm) {
    if (!backlog_items || backlog_items.length === 0) {
        container.html(`
            <div class="text-center text-muted" style="padding: 40px;">
                <p>No items in backlog</p>
                <button class="btn btn-primary btn-sm" onclick="frappe.new_doc('Task', {project: '${frm.doc.name}', is_agile: 1})">
                    Create First Issue
                </button>
            </div>
        `);
        return;
    }
    
    let html = '<div class="backlog-items" style="max-height: 500px; overflow-y: auto;">';
    html += '<table class="table table-hover">';
    html += `
        <thead>
            <tr>
                <th>Key</th>
                <th>Summary</th>
                <th>Type</th>
                <th>Priority</th>
                <th>Story Points</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
    `;
    
    backlog_items.forEach(item => {
        html += `
            <tr class="backlog-item" data-issue="${item.name}" style="cursor: pointer;">
                <td><strong>${item.issue_key}</strong></td>
                <td>${item.subject}</td>
                <td><span class="badge badge-light">${item.issue_type || '-'}</span></td>
                <td>${item.issue_priority ? `<span class="badge badge-${get_priority_badge_class(item.issue_priority)}">${item.issue_priority}</span>` : '-'}</td>
                <td>${item.story_points || '-'}</td>
                <td>
                    <button class="btn btn-xs btn-default open-issue" data-issue="${item.name}">
                        <i class="fa fa-external-link"></i>
                    </button>
                </td>
            </tr>
        `;
    });
    
    html += '</tbody></table></div>';
    
    container.html(html);
    
    // Add click handlers
    container.find('.backlog-item').on('click', function(e) {
        if (!$(e.target).hasClass('btn')) {
            let issue_name = $(this).data('issue');
            frappe.set_route('Form', 'Task', issue_name);
        }
    });
    
    container.find('.open-issue').on('click', function(e) {
        e.stopPropagation();
        let issue_name = $(this).data('issue');
        frappe.set_route('Form', 'Task', issue_name);
    });
}

function show_sprint_planning(frm) {
    let d = new frappe.ui.Dialog({
        title: __('Sprint Planning - {0}', [frm.doc.project_name]),
        size: 'extra-large',
        fields: [
            {
                fieldname: 'sprint_section',
                fieldtype: 'Section Break',
                label: 'Sprint Selection'
            },
            {
                fieldname: 'sprint',
                fieldtype: 'Link',
                label: 'Sprint',
                options: 'Agile Sprint',
                get_query: function() {
                    return {
                        filters: {
                            project: frm.doc.name,
                            sprint_state: ['in', ['Future', 'Active']]
                        }
                    };
                },
                reqd: 1,
                onchange: function() {
                    load_sprint_planning_data(d, frm);
                }
            },
            {
                fieldname: 'create_sprint_btn',
                fieldtype: 'Button',
                label: 'Create New Sprint',
                click: function() {
                    show_create_sprint_dialog(frm, function(new_sprint) {
                        d.set_value('sprint', new_sprint.name);
                    });
                }
            },
            {
                fieldname: 'planning_section',
                fieldtype: 'Section Break'
            },
            {
                fieldname: 'planning_html',
                fieldtype: 'HTML'
            }
        ]
    });
    
    d.show();
    
    // Load active sprint if exists
    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Agile Sprint',
            filters: {
                project: frm.doc.name,
                sprint_state: 'Active'
            },
            fieldname: 'name'
        },
        callback: function(r) {
            if (r.message && r.message.name) {
                d.set_value('sprint', r.message.name);
            }
        }
    });
}

function load_sprint_planning_data(dialog, frm) {
    let sprint = dialog.get_value('sprint');
    if (!sprint) {
        dialog.fields_dict.planning_html.$wrapper.html('<p class="text-muted">Select a sprint to begin planning</p>');
        return;
    }
    
    dialog.fields_dict.planning_html.$wrapper.html(`
        <div class="text-center" style="padding: 40px;">
            <div class="spinner-border text-primary" role="status"></div>
        </div>
    `);
    
    frappe.call({
        method: 'erpnext_agile.api.get_sprint_report',
        args: { sprint_name: sprint },
        callback: function(r) {
            if (r.message) {
                render_sprint_planning(dialog.fields_dict.planning_html.$wrapper, r.message, frm, dialog);
            }
        }
    });
}

function render_sprint_planning(container, report, frm, dialog) {
    let sprint = report.sprint;
    let metrics = report.metrics;
    
    let html = '<div class="sprint-planning">';
    
    // Sprint info
    html += `
        <div class="alert alert-info">
            <h5>${sprint.sprint_name}</h5>
            <p><strong>Goal:</strong> ${sprint.sprint_goal || 'No goal set'}</p>
            <p><strong>Duration:</strong> ${frappe.datetime.str_to_user(sprint.start_date)} - ${frappe.datetime.str_to_user(sprint.end_date)}</p>
            <p><strong>State:</strong> <span class="badge badge-${sprint.sprint_state === 'Active' ? 'success' : 'secondary'}">${sprint.sprint_state}</span></p>
        </div>
    `;
    
    // Metrics
    html += `
        <div class="row" style="margin-bottom: 20px;">
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h3>${metrics.total_points || 0}</h3>
                        <p class="text-muted">Total Points</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h3>${metrics.completed_points || 0}</h3>
                        <p class="text-muted">Completed</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h3>${Math.round(metrics.progress_percentage || 0)}%</h3>
                        <p class="text-muted">Progress</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h3>${report.issue_stats.total}</h3>
                        <p class="text-muted">Issues</p>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Sprint actions
    html += '<div class="sprint-actions" style="margin-bottom: 20px;">';
    if (sprint.sprint_state === 'Future') {
        html += '<button class="btn btn-primary btn-sm start-sprint-btn">Start Sprint</button> ';
    }
    if (sprint.sprint_state === 'Active') {
        html += '<button class="btn btn-warning btn-sm complete-sprint-btn">Complete Sprint</button> ';
    }
    html += '<button class="btn btn-default btn-sm add-issues-btn">Add Issues to Sprint</button>';
    html += '</div>';
    
    // Issues in sprint
    html += '<h6>Issues in Sprint</h6>';
    if (report.issues && report.issues.length > 0) {
        html += '<table class="table table-sm table-hover">';
        html += '<thead><tr><th>Key</th><th>Summary</th><th>Type</th><th>Status</th><th>Points</th><th>Actions</th></tr></thead><tbody>';
        
        report.issues.forEach(issue => {
            html += `
                <tr>
                    <td><strong>${issue.issue_key}</strong></td>
                    <td>${issue.subject}</td>
                    <td><span class="badge badge-light">${issue.issue_type || '-'}</span></td>
                    <td><span class="badge badge-secondary">${issue.issue_status || '-'}</span></td>
                    <td>${issue.story_points || '-'}</td>
                    <td>
                        <button class="btn btn-xs btn-danger remove-from-sprint" data-issue-key="${issue.issue_key}">
                            <i class="fa fa-times"></i>
                        </button>
                    </td>
                </tr>
            `;
        });
        
        html += '</tbody></table>';
    } else {
        html += '<p class="text-muted">No issues in this sprint</p>';
    }
    
    html += '</div>';
    
    container.html(html);
    
    // Add event handlers
    container.find('.start-sprint-btn').on('click', function() {
        frappe.confirm(__('Start this sprint?'), function() {
            frappe.call({
                method: 'erpnext_agile.api.start_sprint',
                args: { sprint_name: sprint.name },
                callback: function(r) {
                    if (r.message) {
                        frappe.show_alert({message: __('Sprint started!'), indicator: 'green'});
                        load_sprint_planning_data(dialog, frm);
                    }
                }
            });
        });
    });
    
    container.find('.complete-sprint-btn').on('click', function() {
        frappe.confirm(__('Complete this sprint? Incomplete issues will be moved to backlog.'), function() {
            frappe.call({
                method: 'erpnext_agile.api.complete_sprint',
                args: { sprint_name: sprint.name },
                callback: function(r) {
                    if (r.message) {
                        frappe.show_alert({message: __('Sprint completed!'), indicator: 'green'});
                        load_sprint_planning_data(dialog, frm);
                    }
                }
            });
        });
    });
    
    container.find('.add-issues-btn').on('click', function() {
        show_add_issues_to_sprint_dialog(sprint.name, frm, function() {
            load_sprint_planning_data(dialog, frm);
        });
    });
    
    container.find('.remove-from-sprint').on('click', function() {
        let issue_key = $(this).data('issue-key');
        frappe.call({
            method: 'erpnext_agile.api.remove_issues_from_sprint',
            args: {
                sprint_name: sprint.name,
                issue_keys: [issue_key]
            },
            callback: function(r) {
                if (r.message) {
                    frappe.show_alert({message: __('Issue removed from sprint'), indicator: 'green'});
                    load_sprint_planning_data(dialog, frm);
                }
            }
        });
    });
}

function show_create_sprint_dialog(frm, callback) {
    let d = new frappe.ui.Dialog({
        title: __('Create New Sprint'),
        fields: [
            {
                fieldname: 'sprint_name',
                fieldtype: 'Data',
                label: 'Sprint Name',
                reqd: 1
            },
            {
                fieldname: 'start_date',
                fieldtype: 'Date',
                label: 'Start Date',
                reqd: 1,
                default: frappe.datetime.get_today()
            },
            {
                fieldname: 'end_date',
                fieldtype: 'Date',
                label: 'End Date',
                reqd: 1,
                default: frappe.datetime.add_days(frappe.datetime.get_today(), 14)
            },
            {
                fieldname: 'sprint_goal',
                fieldtype: 'Text',
                label: 'Sprint Goal'
            }
        ],
        primary_action_label: __('Create'),
        primary_action: function(values) {
            frappe.call({
                method: 'erpnext_agile.api.create_sprint',
                args: {
                    sprint_data: {
                        project: frm.doc.name,
                        sprint_name: values.sprint_name,
                        start_date: values.start_date,
                        end_date: values.end_date,
                        sprint_goal: values.sprint_goal
                    }
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.show_alert({message: __('Sprint created!'), indicator: 'green'});
                        d.hide();
                        if (callback) callback(r.message);
                    }
                }
            });
        }
    });
    
    d.show();
}

function show_add_issues_to_sprint_dialog(sprint_name, frm, callback) {
    let d = new frappe.ui.Dialog({
        title: __('Add Issues to Sprint'),
        fields: [
            {
                fieldname: 'search',
                fieldtype: 'Data',
                label: 'Search Issues',
                onchange: function() {
                    search_backlog_issues(d, frm);
                }
            },
            {
                fieldname: 'results_html',
                fieldtype: 'HTML'
            }
        ],
        primary_action_label: __('Add Selected'),
        primary_action: function() {
            let selected = [];
            d.$wrapper.find('input.issue-checkbox:checked').each(function() {
                selected.push($(this).data('issue-key'));
            });
            
            if (selected.length === 0) {
                frappe.msgprint(__('No issues selected'));
                return;
            }
            
            frappe.call({
                method: 'erpnext_agile.api.add_issues_to_sprint',
                args: {
                    sprint_name: sprint_name,
                    issue_keys: selected
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.show_alert({
                            message: __('Added {0} issues to sprint', [r.message.added]),
                            indicator: 'green'
                        });
                        d.hide();
                        if (callback) callback();
                    }
                }
            });
        }
    });
    
    d.show();
    search_backlog_issues(d, frm);
}

function search_backlog_issues(dialog, frm) {
    let search = dialog.get_value('search') || '';
    
    frappe.call({
        method: 'erpnext_agile.api.get_backlog',
        args: {
            project: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                let items = r.message;
                
                // Filter by search
                if (search) {
                    items = items.filter(item => 
                        item.subject.toLowerCase().includes(search.toLowerCase()) ||
                        item.issue_key.toLowerCase().includes(search.toLowerCase())
                    );
                }
                
                let html = '<div style="max-height: 400px; overflow-y: auto;">';
                if (items.length > 0) {
                    items.forEach(item => {
                        html += `
                            <div class="checkbox" style="padding: 8px; border-bottom: 1px solid #eee;">
                                <label>
                                    <input type="checkbox" class="issue-checkbox" data-issue-key="${item.issue_key}">
                                    <strong>${item.issue_key}</strong>: ${item.subject}
                                    ${item.story_points ? `<span class="badge badge-info ml-2">${item.story_points} pts</span>` : ''}
                                </label>
                            </div>
                        `;
                    });
                } else {
                    html += '<p class="text-muted text-center" style="padding: 20px;">No backlog items found</p>';
                }
                html += '</div>';
                
                dialog.fields_dict.results_html.$wrapper.html(html);
            }
        }
    });
}

function show_agile_reports_menu(frm) {
    let d = new frappe.ui.Dialog({
        title: __('Agile Reports'),
        fields: [
            {
                label: __('Select Report'),
                fieldname: 'report_type',
                fieldtype: 'Select',
                options: [
                    'Sprint Velocity',
                    'Team Time Report',
                    'Backlog Health'
                ],
                reqd: 1
            },
            {
                fieldname: 'sprint',
                fieldtype: 'Link',
                label: 'Sprint (for Sprint Reports)',
                options: 'Agile Sprint',
                depends_on: 'eval:["Sprint Velocity"].includes(doc.report_type)',
                get_query: function() {
                    return {
                        filters: { project: frm.doc.name }
                    };
                }
            }
        ],
        primary_action_label: __('Generate Report'),
        primary_action: function(values) {
            generate_agile_report(frm, values.report_type, values.sprint);
            d.hide();
        }
    });
    d.show();
}

function generate_agile_report(frm, report_type, sprint) {
    if (report_type === 'Team Time Report') {
        frappe.call({
            method: 'erpnext_agile.api.get_team_time_report',
            args: { project: frm.doc.name },
            callback: function(r) {
                if (r.message) {
                    show_time_report(r.message);
                }
            }
        });
    } else if (report_type === 'Backlog Health') {
        frappe.call({
            method: 'erpnext_agile.api.get_backlog_metrics',
            args: { project: frm.doc.name },
            callback: function(r) {
                if (r.message) {
                    show_backlog_health_report(r.message);
                }
            }
        });
    } else if (report_type === 'Sprint Velocity' && sprint) {
        frappe.call({
            method: 'erpnext_agile.api.get_sprint_report',
            args: { sprint_name: sprint },
            callback: function(r) {
                if (r.message) {
                    show_sprint_report(r.message);
                }
            }
        });
    } else {
        frappe.msgprint(__('Report generation for {0} is under development', [report_type]));
    }
}

function show_time_report(data) {
    let d = new frappe.ui.Dialog({
        title: __('Team Time Report'),
        size: 'large',
        fields: [{fieldname: 'report_html', fieldtype: 'HTML'}]
    });
    
    let html = `
        <div class="time-report">
            <div class="alert alert-info">
                <strong>Period:</strong> ${frappe.datetime.str_to_user(data.start_date)} - ${frappe.datetime.str_to_user(data.end_date)}<br>
                <strong>Team Total:</strong> ${data.team_total}<br>
                <strong>Total Logs:</strong> ${data.total_logs}
            </div>
            <table class="table table-bordered">
                <thead>
                    <tr>
                        <th>Team Member</th>
                        <th>Time Logged</th>
                        <th>Total Logs</th>
                        <th>Issues Worked On</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    data.team_members.forEach(member => {
        html += `
            <tr>
                <td>${member.user_fullname}</td>
                <td><strong>${member.total_time}</strong></td>
                <td>${member.total_logs}</td>
                <td>${member.issues_count}</td>
            </tr>
        `;
    });
    
    html += '</tbody></table></div>';
    
    d.fields_dict.report_html.$wrapper.html(html);
    d.show();
}

function show_backlog_health_report(data) {
    let d = new frappe.ui.Dialog({
        title: __('Backlog Health Metrics'),
        size: 'large',
        fields: [{fieldname: 'report_html', fieldtype: 'HTML'}]
    });
    
    let html = `
        <div class="backlog-health">
            <div class="row">
                <div class="col-md-4">
                    <div class="card text-center">
                        <div class="card-body">
                            <h3>${data.total_items}</h3>
                            <p class="text-muted">Total Items</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card text-center">
                        <div class="card-body">
                            <h3>${data.total_points}</h3>
                            <p class="text-muted">Total Points</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card text-center">
                        <div class="card-body">
                            <h3>${Math.round(data.estimation_percentage)}%</h3>
                            <p class="text-muted">Estimated</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mt-3">
                <div class="col-md-6">
                    <h6>By Priority</h6>
                    <table class="table table-sm">
                        <tbody>
    `;
    
    for (let priority in data.by_priority) {
        html += `
            <tr>
                <td>${priority}</td>
                <td class="text-right"><strong>${data.by_priority[priority]}</strong></td>
            </tr>
        `;
    }
    
    html += `
                        </tbody>
                    </table>
                </div>
                <div class="col-md-6">
                    <h6>By Type</h6>
                    <table class="table table-sm">
                        <tbody>
    `;
    
    for (let type in data.by_type) {
        html += `
            <tr>
                <td>${type}</td>
                <td class="text-right"><strong>${data.by_type[type]}</strong></td>
            </tr>
        `;
    }
    
    html += `
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div class="alert alert-${data.readiness_percentage > 70 ? 'success' : data.readiness_percentage > 40 ? 'warning' : 'danger'} mt-3">
                <strong>Readiness:</strong> ${Math.round(data.readiness_percentage)}% of backlog items are ready for sprint (estimated with acceptance criteria)
            </div>
        </div>
    `;
    
    d.fields_dict.report_html.$wrapper.html(html);
    d.show();
}

function show_sprint_report(data) {
    let d = new frappe.ui.Dialog({
        title: __('Sprint Report - {0}', [data.sprint.sprint_name]),
        size: 'large',
        fields: [{fieldname: 'report_html', fieldtype: 'HTML'}]
    });
    
    let html = `
        <div class="sprint-report">
            <div class="row">
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h4>${data.metrics.total_points}</h4>
                            <p class="text-muted">Committed</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h4>${data.metrics.completed_points}</h4>
                            <p class="text-muted">Completed</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h4>${Math.round(data.metrics.progress_percentage)}%</h4>
                            <p class="text-muted">Progress</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h4>${data.metrics.velocity.toFixed(1)}</h4>
                            <p class="text-muted">Velocity</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="mt-3">
                <h6>Issue Statistics</h6>
                <div class="row">
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-body text-center">
                                <h5 class="text-success">${data.issue_stats.completed}</h5>
                                <p class="text-muted">Completed</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-body text-center">
                                <h5 class="text-primary">${data.issue_stats.in_progress}</h5>
                                <p class="text-muted">In Progress</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-body text-center">
                                <h5 class="text-warning">${data.issue_stats.todo}</h5>
                                <p class="text-muted">To Do</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            ${data.team_velocity ? `
                <div class="alert alert-info mt-3">
                    <strong>Team Velocity:</strong> ${data.team_velocity.average} pts/sprint (${data.team_velocity.trend})
                </div>
            ` : ''}
        </div>
    `;
    
    d.fields_dict.report_html.$wrapper.html(html);
    d.show();
}

function bulk_sync_github(frm) {
    frappe.confirm(
        __('Sync all GitHub issues for this project?'),
        function() {
            frappe.show_alert({
                message: __('Starting bulk sync...'),
                indicator: 'blue'
            });
            
            frappe.call({
                method: 'erpnext_agile.api.bulk_sync_project_issues',
                args: {
                    project_name: frm.doc.name
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.msgprint({
                            title: __('GitHub Sync Complete'),
                            message: __('Synced {0} issues ({1} created, {2} updated)',
                                [r.message.synced, r.message.created, r.message.updated]),
                            indicator: 'green'
                        });
                    }
                }
            });
        }
    );
}