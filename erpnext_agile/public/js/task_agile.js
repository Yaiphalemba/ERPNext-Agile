// erpnext_agile/public/js/task_agile.js
frappe.ui.form.on('Task', {
    refresh: function(frm) {
        if (frm.doc.is_agile) {
            // Add Version History button
            frm.add_custom_button(__('Version History'), function() {
                show_version_history(frm);
            }, __('Version Control'));
            
            // Add Create Version button
            frm.add_custom_button(__('Create Version'), function() {
                create_version_snapshot(frm);
            }, __('Version Control'));
            
            // Add Restore button
            frm.add_custom_button(__('Restore Version'), function() {
                show_restore_dialog(frm);
            }, __('Version Control'));
            // Add custom buttons for agile features
            add_agile_buttons(frm);
            
            // Show agile fields
            show_agile_fields(frm);
            
            // Add custom indicators
            add_agile_indicators(frm);
        }
        if (frm.doc.issue_status && (frm.doc.custom_timer_status === 0 || frm.doc.custom_timer_status === undefined)) {
            // Replace the header status display
            frm.page.set_indicator(frm.doc.issue_status,
                get_agile_status_color(frm.doc.issue_status)
            );
        }
        if (frm.doc.custom_timer_status === 1) {
            show_timer_indicator(frm, frm.doc.custom_timer_status);
        }
    },
    
    is_agile: function(frm) {
        if (frm.doc.is_agile) {
            show_agile_fields(frm);
        } else {
            hide_agile_fields(frm);
        }
    },
    
    project: function(frm) {
        if (frm.doc.project && frm.doc.is_agile) {
            // Load project-specific agile configuration
            load_project_agile_config(frm);
        }
    }
});

// helper to color-code agile statuses
function get_agile_status_color(status) {
    let colors = {
        "Open": "red",
        "In Progress": "orange",
        "In Review": "blue",
        "Testing": "blue",
        "Resolved": "green",
        "Closed": "green",
        "Reopened": "red",
        "Blocked": "grey",
        "To Do": "orange"
    };
    return colors[status] || "blue";
}

function add_agile_buttons(frm) {
    // Quick Actions
    frm.add_custom_button(__('Quick Actions'), function() {
        show_quick_actions_dialog(frm);
    }, __('Agile'));
    
    // Log Work
    frm.add_custom_button(__('Log Work'), function() {
        show_log_work_dialog(frm);
    }, __('Agile'));
    
    // Transition Issue
    frm.add_custom_button(__('Transition'), function() {
        show_transition_dialog(frm);
    }, __('Agile'));
    
    // Link to Sprint
    if (!frm.doc.current_sprint) {
        frm.add_custom_button(__('Add to Sprint'), function() {
            show_add_to_sprint_dialog(frm);
        }, __('Agile'));
    } else {
        frm.add_custom_button(__('Remove from Sprint'), function() {
            remove_from_sprint(frm);
        }, __('Agile'));
    }
    
    // GitHub Integration
    if (frm.doc.github_repo) {
        if (frm.doc.github_issue_number) {
            frm.add_custom_button(__('View on GitHub'), function() {
                window.open(get_github_issue_url(frm), '_blank');
            }, __('GitHub'));
        } else {
            frappe.msgprint(__('This Task is linked to a GitHub Repo but does not have an Issue Number set. You can create a GitHub issue for this task.'), __('GitHub'));
        }
    }
    
    // Time Tracking
    frm.add_custom_button(__('Start Timer'), function() {
        start_work_timer(frm);
    }, __('Time'));
    
    // View Activity
    frm.add_custom_button(__('View Activity'), function() {
        show_activity_dialog(frm);
    });
}

function show_quick_actions_dialog(frm) {
    let d = new frappe.ui.Dialog({
        title: __('Quick Actions'),
        fields: [
            {
                label: __('Action'),
                fieldname: 'action',
                fieldtype: 'Select',
                options: [
                    'Assign to Me',
                    'Watch This Issue',
                    'Clone Issue',
                    'Split Story',
                    'Link to Epic'
                ]
            }
        ],
        primary_action_label: __('Execute'),
        primary_action: function(values) {
            execute_quick_action(frm, values.action);
            d.hide();
        }
    });
    d.show();
}

function show_log_work_dialog(frm) {
    let d = new frappe.ui.Dialog({
        title: __('Log Work'),
        fields: [
            {
                label: __('Time Spent'),
                fieldname: 'time_spent',
                fieldtype: 'Data',
                reqd: 1,
                description: 'e.g., "2h 30m", "1.5h", or "90m"'
            },
            {
                label: __('Work Description'),
                fieldname: 'work_description',
                fieldtype: 'Small Text',
                reqd: 1
            },
            {
                label: __('Work Date'),
                fieldname: 'work_date',
                fieldtype: 'Date',
                default: frappe.datetime.get_today()
            }
        ],
        primary_action_label: __('Log Work'),
        primary_action: function(values) {
            frappe.call({
                method: 'erpnext_agile.api.log_work',
                args: {
                    task_name: frm.doc.name,
                    time_spent: values.time_spent,
                    work_description: values.work_description,
                    work_date: values.work_date
                },
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: __('Work logged: {0}', [r.message.time_logged]),
                            indicator: 'green'
                        });
                        frm.reload_doc();
                    }
                }
            });
            d.hide();
        }
    });
    d.show();
}

function show_transition_dialog(frm) {
    // Get available transitions
    frappe.call({
        method: 'erpnext_agile.api.get_available_transitions',
        args: {
            task_name: frm.doc.name,
            from_status: frm.doc.issue_status
        },
        callback: function(r) {
            if (r.message) {
                let transitions = r.message;
                let d = new frappe.ui.Dialog({
                    title: __('Transition Issue'),
                    fields: [
                        {
                            label: __('To Status'),
                            fieldname: 'to_status',
                            fieldtype: 'Select',
                            options: transitions.map(t => t.to_status).join('\n'),
                            reqd: 1
                        },
                        {
                            label: __('Comment'),
                            fieldname: 'comment',
                            fieldtype: 'Small Text'
                        }
                    ],
                    primary_action_label: __('Transition'),
                    primary_action: function(values) {
                        frappe.call({
                            method: 'erpnext_agile.api.transition_issue',
                            args: {
                                task_name: frm.doc.name,
                                from_status: frm.doc.issue_status,
                                to_status: values.to_status,
                                comment: values.comment
                            },
                            callback: function(r) {
                                if (r.message) {
                                    frappe.show_alert({
                                        message: __('Issue transitioned successfully'),
                                        indicator: 'green'
                                    });
                                    frm.reload_doc();
                                }
                            }
                        });
                        d.hide();
                    }
                });
                d.show();
            }
        }
    });
}

function show_add_to_sprint_dialog(frm) {
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Agile Sprint',
            filters: {
                project: frm.doc.project,
                sprint_state: ['in', ['Future', 'Active']]
            },
            fields: ['name', 'sprint_name', 'sprint_state']
        },
        callback: function(r) {
            if (r.message) {
                let sprints = r.message;
                let d = new frappe.ui.Dialog({
                    title: __('Add to Sprint'),
                    fields: [
                        {
                            label: __('Sprint'),
                            fieldname: 'sprint',
                            fieldtype: 'Select',
                            options: sprints.map(s => s.name + ' - ' + s.sprint_name).join('\n'),
                            reqd: 1
                        }
                    ],
                    primary_action_label: __('Add'),
                    primary_action: function(values) {
                        let sprint_name = values.sprint.split(' - ')[0];
                        frappe.call({
                            method: 'erpnext_agile.api.add_issues_to_sprint',
                            args: {
                                sprint_name: sprint_name,
                                issue_keys: [frm.doc.issue_key]
                            },
                            callback: function(r) {
                                if (r.message && r.message.added > 0) {
                                    frappe.show_alert({
                                        message: __('Added to sprint'),
                                        indicator: 'green'
                                    });
                                    frm.reload_doc();
                                }
                            }
                        });
                        d.hide();
                    }
                });
                d.show();
            }
        }
    });
}

function remove_from_sprint(frm) {
    frappe.confirm(
        __('Remove this issue from sprint {0}?', [frm.doc.current_sprint]),
        function() {
            frappe.call({
                method: 'erpnext_agile.api.remove_issues_from_sprint',
                args: {
                    sprint_name: frm.doc.current_sprint,
                    issue_keys: [frm.doc.issue_key]
                },
                callback: function(r) {
                    if (r.message && r.message.removed > 0) {
                        frappe.show_alert({
                            message: __('Removed from sprint'),
                            indicator: 'green'
                        });
                        frm.reload_doc();
                    }
                }
            });
        }
    );
}

function start_work_timer(frm) {
    frappe.call({
        method: 'erpnext_agile.api.start_timer',
        args: {
            task_name: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.show_alert({
                    message: __('Timer started'),
                    indicator: 'green'
                });
                frm.set_value('custom_timer_status', 1);
                frm.save();
                show_timer_indicator(frm);
            }
        }
    });
}

function stop_timer(frm) {
    frappe.db.get_value(
        'Agile Work Timer',
        { 'user': frappe.session.user, 'status': 'Running', 'task': frm.doc.name },
        'name'
    ).then(res => {
        if (res && res.message && res.message.name) {
            frappe.call({
                method: 'erpnext_agile.api.stop_timer',
                args: {
                    timer_name: res.message.name
                },
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: __('Timer stopped'),
                            indicator: 'green'
                        });
                    }
                }
            });
        } else {
            frappe.msgprint(__('No running timer found for this task.'));
        }
    });
}

function show_timer_indicator(frm) {
    // Set the red "Timer Running" indicator in the form header
    frm.page.set_indicator(__('Timer Running'), 'red');

    // Remove any existing Stop Timer button (avoid duplicates on refresh)
    frm.page.clear_inner_toolbar();

    // Add a Stop Timer button in the header toolbar
    frm.page.add_inner_button(__('Stop Timer'), function() {
        stop_timer(frm);
    });
}

function show_agile_fields(frm) {
    frm.toggle_display('agile_details_section', true);
    frm.toggle_display('agile_planning_section', true);
    frm.toggle_display('time_tracking_section', true);
}

function hide_agile_fields(frm) {
    frm.toggle_display('agile_details_section', false);
    frm.toggle_display('agile_planning_section', false);
    frm.toggle_display('time_tracking_section', false);
}

function add_agile_indicators(frm) {
    // Add priority indicator
    if (frm.doc.issue_priority) {
        let color = get_priority_color(frm.doc.issue_priority);
        frm.page.set_indicator(frm.doc.issue_priority, color);
    }
}

function get_priority_color(priority) {
    const colors = {
        'Critical': 'red',
        'High': 'orange',
        'Medium': 'yellow',
        'Low': 'blue'
    };
    return colors[priority] || 'gray';
}

function get_github_issue_url(frm) {
    return `https://github.com/${frm.doc.github_repo}/issues/${frm.doc.github_issue_number}`;
}

function load_project_agile_config(frm) {
    // Load project-specific configurations
    frappe.call({
        method: 'frappe.client.get',
        args: {
            doctype: 'Project',
            name: frm.doc.project
        },
        callback: function(r) {
            if (r.message) {
                // Set default values based on project config
                if (!frm.doc.issue_type && r.message.default_issue_type) {
                    frm.set_value('issue_type', r.message.default_issue_type);
                }
            }
        }
    });
}

function show_version_history(frm) {
    frappe.call({
        method: 'erpnext_agile.version_control.get_version_history',
        args: { task_name: frm.doc.name },
        callback: function(r) {
            let history = r.message;
            
            let d = new frappe.ui.Dialog({
                title: __('Version History'),
                fields: [
                    {
                        fieldtype: 'HTML',
                        fieldname: 'version_list'
                    }
                ]
            });
            
            let html = '<table class="table table-bordered">';
            html += '<tr><th>Version</th><th>Created By</th><th>Date</th><th>Description</th><th>Actions</th></tr>';
            
            history.forEach(function(v) {
                html += `<tr>
                    <td>v${v.version_number}</td>
                    <td>${v.created_by}</td>
                    <td>${v.created_at}</td>
                    <td>${v.change_description}</td>
                    <td>
                        <button class="btn btn-xs btn-primary" onclick="restore_version('${frm.doc.name}', ${v.version_number})">
                            Restore
                        </button>
                        <button class="btn btn-xs btn-default" onclick="compare_version('${frm.doc.name}', ${v.version_number})">
                            Compare
                        </button>
                    </td>
                </tr>`;
            });
            
            html += '</table>';
            d.fields_dict.version_list.$wrapper.html(html);
            d.show();
        }
    });
}

function create_version_snapshot(frm) {
    let d = new frappe.ui.Dialog({
        title: __('Create Version Snapshot'),
        fields: [
            {
                label: __('Description'),
                fieldname: 'description',
                fieldtype: 'Text',
                reqd: 1,
                description: 'Describe what this version represents'
            }
        ],
        primary_action_label: __('Create'),
        primary_action: function(values) {
            frappe.call({
                method: 'erpnext_agile.version_control.create_issue_version',
                args: {
                    task_name: frm.doc.name,
                    change_description: values.description
                },
                callback: function(r) {
                    frappe.show_alert({
                        message: __('Version snapshot created'),
                        indicator: 'green'
                    });
                    d.hide();
                }
            });
        }
    });
    d.show();
}

function show_restore_dialog(frm) {
    frappe.call({
        method: 'erpnext_agile.version_control.get_version_history',
        args: { task_name: frm.doc.name },
        callback: function(r) {
            let versions = r.message;
            
            let d = new frappe.ui.Dialog({
                title: __('Restore Version'),
                fields: [
                    {
                        label: __('Select Version'),
                        fieldname: 'version_number',
                        fieldtype: 'Select',
                        options: versions.map(v => `${v.version_number} - ${v.change_description}`).join('\n'),
                        reqd: 1
                    },
                    {
                        fieldtype: 'HTML',
                        fieldname: 'warning',
                        options: '<div class="alert alert-warning">Warning: Current state will be backed up before restore.</div>'
                    }
                ],
                primary_action_label: __('Restore'),
                primary_action: function(values) {
                    let version_num = parseInt(values.version_number.split(' - ')[0]);
                    
                    frappe.confirm(
                        __('Are you sure you want to restore to version {0}?', [version_num]),
                        function() {
                            frappe.call({
                                method: 'erpnext_agile.version_control.restore_issue_version',
                                args: {
                                    task_name: frm.doc.name,
                                    version_number: version_num
                                },
                                callback: function(r) {
                                    frappe.show_alert({
                                        message: __('Issue restored to version {0}', [version_num]),
                                        indicator: 'green'
                                    });
                                    frm.reload_doc();
                                    d.hide();
                                }
                            });
                        }
                    );
                }
            });
            d.show();
        }
    });
}

function compare_version(task_name, version_number) {
    frappe.call({
        method: 'erpnext_agile.version_control.compare_with_current',
        args: {
            task_name: task_name,
            version_number: version_number
        },
        callback: function(r) {
            let diff = r.message;
            
            let d = new frappe.ui.Dialog({
                title: __('Version Comparison (v{0} vs Current)', [version_number]),
                size: 'large',
                fields: [
                    {
                        fieldtype: 'HTML',
                        fieldname: 'diff_view'
                    }
                ]
            });
            
            let html = '<table class="table table-bordered">';
            html += '<tr><th>Field</th><th>Change Type</th><th>Old Value</th><th>New Value</th></tr>';
            
            diff.forEach(function(change) {
                let color_class = change.change_type === 'added' ? 'success' : 
                                 change.change_type === 'removed' ? 'danger' : 'warning';
                
                html += `<tr class="${color_class}">
                    <td><strong>${change.field}</strong></td>
                    <td><span class="label label-${color_class}">${change.change_type}</span></td>
                    <td>${change.old_value}</td>
                    <td>${change.new_value}</td>
                </tr>`;
            });
            
            html += '</table>';
            
            if (diff.length === 0) {
                html = '<div class="alert alert-info">No changes detected between this version and current state.</div>';
            }
            
            d.fields_dict.diff_view.$wrapper.html(html);
            d.show();
        }
    });
}

// Add to window scope for onclick handlers
window.restore_version = function(task_name, version_number) {
    show_restore_dialog({doc: {name: task_name}});
};

window.compare_version = compare_version;