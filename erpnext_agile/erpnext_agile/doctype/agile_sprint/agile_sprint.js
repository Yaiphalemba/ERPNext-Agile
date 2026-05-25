frappe.ui.form.on('Agile Sprint', {
    validate: function(frm) {
        return new Promise((resolve, reject) => {
            frappe.call({
                method: 'erpnext_agile.erpnext_agile.doctype.agile_sprint.agile_sprint.check_active_sprint',
                args: {
                    project: frm.doc.project,
                    name: frm.doc.name
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.confirm(
                            `Another sprint '${r.message}' is already active. Continue anyway?`,
                            () => resolve(),   // user clicked YES
                            () => reject()     // user clicked NO → stops save
                        );
                    } else {
                        resolve();
                    }
                }
            });
        });
    },

    refresh(frm) {
        if (frm.doc.sprint_state === "Future") {
            frm.add_custom_button(__('Start Sprint'), () => {
                frappe.call({
                    method: "erpnext_agile.api.start_sprint",
                    args: {
                        sprint_name: frm.doc.name
                    },
                    callback: function(r) {
                        if (!r.exc) {
                            frm.reload_doc();
                        }
                    }
                });
            }).addClass('btn-primary');
        }
        if (frm.doc.sprint_state === "Active") {
            frm.add_custom_button(__('Complete Sprint'), () => {
                show_complete_sprint_dialog(frm);
            }).addClass('btn-danger');
        }
    }
});

function show_complete_sprint_dialog(frm) {
    // First, fetch the sprint report to get the list of issues
    frappe.call({
        method: 'erpnext_agile.api.get_sprint_report',
        args: { sprint_name: frm.doc.name },
        callback: function(r) {
            if (r.message && r.message.issues) {
                // Filter out issues that are already completed
                // Note: Adjust the status array below based on your actual completion statuses
                let completion_statuses = ['Done', 'Completed', 'Closed'];
                let incomplete_issues = r.message.issues.filter(
                    issue => !completion_statuses.includes(issue.issue_status)
                );
                
                render_complete_dialog(frm, incomplete_issues);
            } else {
                // Fallback if no issues found
                render_complete_dialog(frm, []);
            }
        }
    });
}

function render_complete_dialog(frm, issues) {
    let d = new frappe.ui.Dialog({
        title: __('Complete Sprint'),
        size: 'large',
        fields: [
            {
                fieldname: 'target_sprint',
                fieldtype: 'Link',
                label: __('Move Selected Issues To (Sprint)'),
                options: 'Agile Sprint',
                description: __('Select a future sprint to move issues into.'),
                get_query: function() {
                    return {
                        filters: {
                            project: frm.doc.project,
                            sprint_state: ["in", ['Future', "Active"]]
                        }
                    };
                }
            },
            {
                fieldname: 'create_sprint_btn',
                fieldtype: 'Button',
                label: __('Create New Sprint'),
                click: function() {
                    if (typeof show_create_sprint_dialog === 'function') {
                        show_create_sprint_dialog(frm, function(new_sprint) {
                            d.set_value('target_sprint', new_sprint.name);
                        });
                    }
                }
            },
            { fieldtype: 'Section Break' },
            {
                fieldname: 'issues_html',
                fieldtype: 'HTML',
                label: __('Incomplete Issues')
            }
        ],
        primary_action_label: __('Complete Sprint'),
        primary_action_classes: 'btn-danger',
        primary_action: function(values) {
            let selected_issues = [];
            d.$wrapper.find('.issue-checkbox:checked').each(function() {
                selected_issues.push($(this).data('issue-name'));
            });

            frappe.call({
                method: "erpnext_agile.api.complete_sprint",
                args: {
                    sprint_name: frm.doc.name,
                    // target_sprint: values.target_sprint || null,
                    // issues_to_move: selected_issues 
                },
                freeze: true,
                freeze_message: __('Completing Sprint...'),
                callback: function(r) {
                    if (!r.exc) {
                        frappe.show_alert({message: __('Sprint completed successfully!'), indicator: 'green'});
                        d.hide();
                        frm.reload_doc();
                    }
                }
            });
        },
        // --- CORRECTED: Use Frappe's native secondary action for Dialogs ---
        secondary_action_label: __('Move Tasks Selected Sprint'),
        secondary_action: function() {
            let target_sprint = d.get_value('target_sprint');
            let selected_issues = [];
            
            d.$wrapper.find('.issue-checkbox:checked').each(function() {
                selected_issues.push($(this).data('issue-name'));
            });

            if (!target_sprint) {
                frappe.msgprint(__('Please select a Target Sprint first before moving tasks.'));
                return;
            }
            console.log(selected_issues);
            
            if (selected_issues.length === 0) {
                frappe.msgprint(__('Please select at least one issue to move.'));
                return;
            }

            frappe.call({
                method: "erpnext_agile.api.move_tasks_to_sprint", 
                args: {
                    current_sprint: frm.doc.name,
                    target_sprint: target_sprint,
                    issues_to_move: selected_issues
                },
                freeze: true,
                freeze_message: __('Moving Tasks...'),
                callback: function(r) {
                    if (!r.exc) {
                        frappe.show_alert({message: __(`${r.message.moved_count} Tasks moved to ${target_sprint}`), indicator: 'green'});
                        
                        // Remove the moved rows from the HTML table
                        d.$wrapper.find('.issue-checkbox:checked').closest('tr').remove();
                        
                        // Check if the table body is now empty
                        if (d.$wrapper.find('.issue-checkbox').length === 0) {
                            d.fields_dict.issues_html.$wrapper.html(`
                                <div class="text-center text-muted" style="padding: 30px;">
                                    <i class="fa fa-check-circle" style="font-size: 24px; margin-bottom: 10px;"></i>
                                    <p>${__('All issues moved successfully. Ready to close the sprint!')}</p>
                                </div>
                            `);
                        }
                    }
                }
            });
        }
    });

    // Render HTML for incomplete issues table
    let html = '';
    if (issues.length > 0) {
        html = `
            <div style="margin-top: 15px;">
                <p class="" style="color: blue">${__('Select the issues you want to move. Click "Move Tasks Only" to move them to above selected sprint.')}</p>
                <p class="" style="color: blue">${__('Click "Complete Sprint" to move the incomplete tasks to backlog and close the sprint.')}</p>
                <div style="margin-bottom: 10px;">
                    <strong>
                        ${__('Selected Tasks')}:
                        <span id="selected-count">${issues.length}</span>
                    </strong>
                </div>
                <div class="row" style="margin-bottom: 15px;">
                    <div class="col-md-6">
                        <input 
                            type="text" 
                            id="filter-issue-id" 
                            class="form-control"
                            placeholder="${__('Filter by Task ID')}"
                        >
                    </div>
                    <div class="col-md-6">
                        <input 
                            type="text" 
                            id="filter-issue-subject" 
                            class="form-control"
                            placeholder="${__('Filter by Subject')}"
                        >
                    </div>
                </div>
                <div class="table-responsive">
                    <table class="table table-bordered table-hover table-sm">
                        <thead class="bg-light">
                            <tr>
                                <th style="width: 40px; text-align: center;">
                                    <input type="checkbox" id="select-all-issues" checked>
                                </th>
                                <th>${__('Name')}</th>
                                <th>${__('Summary')}</th>
                                <th>${__('Status')}</th>
                                <th>${__('Points')}</th>
                                <th style="width: 40px; text-align: center;">${__('Actions')}</th>
                            </tr>
                        </thead>
                        <tbody id="incomplete-issues-body">
        `;
        
        issues.forEach(issue => {
            html += `
                            <tr>
                                <td style="text-align: center;">
                                    <input type="checkbox" class="issue-checkbox" data-issue-name="${issue.name}" checked>
                                </td>
                                <td><strong>${issue.name}</strong></td>
                                <td>${issue.subject}</td>
                                <td><span class="badge badge-secondary">${issue.issue_status}</span></td>
                                <td>${issue.story_points || '-'}</td>
                                <td style="text-align: center;">
                                    <button class="btn btn-xs btn-default open-issue" data-issue-name="${issue.name}">
                                        <i class="fa fa-duotone fa-link"></i>
                                    </button>
                                </td>
                            </tr>
            `;
        });
        
        html += `
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    } else {
        html = `
            <div class="text-center text-muted" style="padding: 30px;">
                <i class="fa fa-check-circle" style="font-size: 24px; margin-bottom: 10px;"></i>
                <p>${__('All issues in this sprint are completed. Ready to close!')}</p>
            </div>
        `;
    }

    d.fields_dict.issues_html.$wrapper.html(html);

    // Bind "Select All" checkbox toggle functionality
    d.$wrapper.on('change', '#select-all-issues', function() {
        let is_checked = $(this).is(':checked');
        d.$wrapper.find('.issue-checkbox').prop('checked', is_checked);
        update_selected_count();
    });
    
    d.$wrapper.on('change', '.issue-checkbox', function() {

        let total = d.$wrapper.find('.issue-checkbox').length;
        let checked = d.$wrapper.find('.issue-checkbox:checked').length;

        $('#select-all-issues').prop('checked', total === checked);

        update_selected_count();
    });

    d.$wrapper.on('keyup','#filter-issue-id, #filter-issue-subject',
        function() {
            filter_issues_table();
        }
    );
    
    d.$wrapper.on('click', '.open-issue', function() {
        let issue_name = $(this).data('issue-name');
        frappe.set_route('Form', 'Task', issue_name);
    });

    d.show();

    function update_selected_count() {
        let selected_count = d.$wrapper.find('.issue-checkbox:checked').length;
        d.$wrapper.find('#selected-count').text(selected_count);
    }

    function filter_issues_table() {

        let id_filter = d.$wrapper
            .find('#filter-issue-id')
            .val()
            .toLowerCase();

        let subject_filter = d.$wrapper
            .find('#filter-issue-subject')
            .val()
            .toLowerCase();

        d.$wrapper.find('#incomplete-issues-body tr').each(function() {
            let row = $(this);
            let issue_id = row.find('td:nth-child(2)').text().toLowerCase();
            let subject = row.find('td:nth-child(3)').text().toLowerCase();
            
            let matches_id =
                !id_filter || issue_id.includes(id_filter);
            let matches_subject =
                !subject_filter || subject.includes(subject_filter);

            row.toggle(matches_id && matches_subject);
        });
    }
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
                        project: frm.doc.project,
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
