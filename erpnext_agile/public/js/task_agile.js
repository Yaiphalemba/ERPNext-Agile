// erpnext_agile/public/js/task_agile.js
frappe.ui.form.on('Task', {
    refresh: function(frm) {
        if (frm.doc.is_agile) {
            // Add Version Control buttons
            frm.add_custom_button(__('Version History'), function() {
                show_version_history(frm);
            }, __('Version Control'));
            
            frm.add_custom_button(__('Create Version'), function() {
                create_version_snapshot(frm);
            }, __('Version Control'));
            
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
        
        // Show agile status indicator if available
        if (frm.doc.issue_status && (!frm.doc.custom_timer_status || frm.doc.custom_timer_status === 0)) {
            frm.page.set_indicator(frm.doc.issue_status,
                get_agile_status_color(frm.doc.issue_status)
            );
        }
        
        // Show timer indicator if timer is running
        if (frm.doc.custom_timer_status === 1) {
            show_timer_indicator(frm);
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

// Helper to color-code agile statuses
function get_agile_status_color(status) {
    let colors = {
        "Open": "red",
        "In Progress": "orange",
        "In Review": "blue",
        "Testing": "blue",
        "Resolved": "green",
        "Closed": "green",
        "Done": "green",
        "Reopened": "red",
        "Blocked": "grey",
        "To Do": "orange"
    };
    return colors[status] || "blue";
}

function add_agile_buttons(frm) {
    // View Activity button
    frm.add_custom_button(__('View Activity'), function() {
        show_activity_dialog(frm);
    });
    
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
            frm.add_custom_button(__('Sync to GitHub'), function() {
                sync_to_github(frm);
            }, __('GitHub'));
        }
    }
    
    // Time Tracking
    frm.add_custom_button(__('Start Timer'), function() {
        start_work_timer(frm);
    }, __('Time'));
}

function show_activity_dialog(frm) {
    let d = new frappe.ui.Dialog({
        title: __('Issue Activity - {0}', [frm.doc.issue_key || frm.doc.name]),
        size: 'large',
        fields: [
            {
                fieldname: 'activity_html',
                fieldtype: 'HTML'
            }
        ]
    });
    
    // Show loading
    d.fields_dict.activity_html.$wrapper.html(`
        <div class="text-center" style="padding: 40px;">
            <div class="spinner-border text-primary" role="status"></div>
            <p class="text-muted mt-3">Loading activity...</p>
        </div>
    `);
    
    d.show();
    
    // Load activity data
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Agile Issue Activity',
            filters: {
                issue: frm.doc.name
            },
            fields: ['name', 'activity_type', 'user', 'timestamp', 'data', 'comment'],
            order_by: 'timestamp desc',
            limit: 50
        },
        callback: function(r) {
            if (r.message) {
                render_activity_timeline(d.fields_dict.activity_html.$wrapper, r.message);
            }
        }
    });
}

function render_activity_timeline(container, activities) {
    if (!activities || activities.length === 0) {
        container.html(`
            <div class="text-center text-muted" style="padding: 40px;">
                <p>No activity recorded yet</p>
            </div>
        `);
        return;
    }
    
    let html = '<div class="activity-timeline" style="max-height: 500px; overflow-y: auto;">';
    
    activities.forEach((activity, index) => {
        let data = {};
        try {
            data = activity.data ? JSON.parse(activity.data) : {};
        } catch(e) {
            data = {};
        }
        
        let icon = get_activity_icon(activity.activity_type);
        let description = get_activity_description(activity.activity_type, data, activity.comment);
        let color = get_activity_color(activity.activity_type);
        
        html += `
            <div class="activity-item" style="
                display: flex;
                gap: 15px;
                padding: 15px;
                border-left: 2px solid ${color};
                margin-left: 20px;
                position: relative;
                ${index < activities.length - 1 ? 'margin-bottom: 10px;' : ''}
            ">
                <div style="
                    position: absolute;
                    left: -11px;
                    top: 15px;
                    width: 20px;
                    height: 20px;
                    border-radius: 50%;
                    background: ${color};
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-size: 10px;
                ">
                    ${icon}
                </div>
                
                <div style="flex: 1; margin-left: 15px;">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div>
                            <strong>${frappe.user_info(activity.user).fullname}</strong>
                            <span class="text-muted"> ${description}</span>
                        </div>
                        <small class="text-muted">${frappe.datetime.prettyDate(activity.timestamp)}</small>
                    </div>
                    ${activity.comment ? `<div class="text-muted mt-2" style="font-style: italic;">"${activity.comment}"</div>` : ''}
                    ${render_activity_details(activity.activity_type, data)}
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.html(html);
}

function get_activity_icon(activity_type) {
    const icons = {
        'created': '✓',
        'transitioned': '→',
        'status_changed': '→',
        'assigned': '👤',
        'unassigned': '✗',
        'commented': '💬',
        'work_logged': '⏱',
        'estimation_changed': '📊',
        'sprint_added': '🏃',
        'sprint_removed': '🏁',
        'epic_linked': '🎯',
        'github_synced': '🔗',
        'version_restored': '↺'
    };
    return icons[activity_type] || '•';
}

function get_activity_color(activity_type) {
    const colors = {
        'created': '#28a745',
        'transitioned': '#007bff',
        'status_changed': '#007bff',
        'assigned': '#17a2b8',
        'work_logged': '#6610f2',
        'estimation_changed': '#fd7e14',
        'sprint_added': '#20c997',
        'github_synced': '#6c757d',
        'version_restored': '#e83e8c'
    };
    return colors[activity_type] || '#6c757d';
}

function get_activity_description(activity_type, data, comment) {
    const descriptions = {
        'created': 'created this issue',
        'transitioned': `changed status from <strong>${data.from_status || 'Unknown'}</strong> to <strong>${data.to_status || 'Unknown'}</strong>`,
        'status_changed': `changed status from <strong>${data.from_status || 'Unknown'}</strong> to <strong>${data.to_status || 'Unknown'}</strong>`,
        'assigned': `assigned to ${data.assignees ? data.assignees.join(', ') : 'someone'}`,
        'unassigned': 'unassigned',
        'commented': 'added a comment',
        'work_logged': `logged <strong>${data.time_spent || '0m'}</strong> of work`,
        'estimation_changed': `updated estimate from ${data.old_value || '0m'} to ${data.new_value || '0m'}`,
        'sprint_added': `added to sprint <strong>${data.sprint || 'Unknown'}</strong>`,
        'sprint_removed': 'removed from sprint',
        'epic_linked': `linked to epic <strong>${data.epic || 'Unknown'}</strong>`,
        'github_synced': 'synced with GitHub',
        'version_restored': `restored to version ${data.version_number || '?'}`
    };
    return descriptions[activity_type] || activity_type.replace(/_/g, ' ');
}

function render_activity_details(activity_type, data) {
    if (activity_type === 'work_logged' && data.description) {
        return `<div class="mt-2 p-2" style="background: #f8f9fa; border-radius: 4px; font-size: 0.9em;">${data.description}</div>`;
    }
    return '';
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
        method: 'erpnext_agile.utils.get_available_transitions_api',
        args: {
            task_name: frm.doc.name,
            from_status: frm.doc.issue_status
        },
        callback: function(r) {
            if (r.message && r.message.length > 0) {
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
            } else {
                frappe.msgprint(__('No valid transitions available from current status'));
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
            fields: ['name', 'sprint_name', 'sprint_state', 'start_date', 'end_date']
        },
        callback: function(r) {
            if (r.message && r.message.length > 0) {
                let sprints = r.message;
                let options = sprints.map(s => 
                    `${s.name} - ${s.sprint_name} (${s.sprint_state})`
                ).join('\n');
                
                let d = new frappe.ui.Dialog({
                    title: __('Add to Sprint'),
                    fields: [
                        {
                            label: __('Sprint'),
                            fieldname: 'sprint',
                            fieldtype: 'Select',
                            options: options,
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
            } else {
                frappe.msgprint(__('No active or future sprints available. Create a sprint first.'));
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
            }
        },
        error: function(r) {
            frappe.msgprint({
                title: __('Timer Error'),
                message: r.message || __('Could not start timer'),
                indicator: 'red'
            });
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
            // Ask for work description
            let d = new frappe.ui.Dialog({
                title: __('Stop Timer'),
                fields: [
                    {
                        label: __('Work Description'),
                        fieldname: 'work_description',
                        fieldtype: 'Small Text',
                        reqd: 1
                    }
                ],
                primary_action_label: __('Stop & Log'),
                primary_action: function(values) {
                    frappe.call({
                        method: 'erpnext_agile.api.stop_timer',
                        args: {
                            timer_name: res.message.name,
                            work_description: values.work_description
                        },
                        callback: function(r) {
                            if (r.message && r.message.success) {
                                frappe.show_alert({
                                    message: __('Timer stopped. Logged: {0}', [r.message.time_spent]),
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

function sync_to_github(frm) {
    frappe.confirm(
        __('Create GitHub issue for {0}?', [frm.doc.issue_key]),
        function() {
            frappe.call({
                method: 'erpnext_agile.api.sync_agile_issue_to_github',
                args: {
                    task_name: frm.doc.name
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.show_alert({
                            message: __('GitHub issue created successfully'),
                            indicator: 'green'
                        });
                        frm.reload_doc();
                    }
                },
                error: function(r) {
                    frappe.msgprint({
                        title: __('GitHub Sync Failed'),
                        message: r.message || __('Could not sync to GitHub'),
                        indicator: 'red'
                    });
                }
            });
        }
    );
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

// ============================================
// VERSION CONTROL FUNCTIONS
// ============================================

function show_version_history(frm) {
    frappe.call({
        method: 'erpnext_agile.version_control.get_version_history',
        args: { task_name: frm.doc.name },
        callback: function(r) {
            if (!r.message || r.message.length === 0) {
                frappe.msgprint(__('No version history available'));
                return;
            }
            
            let history = r.message;
            
            let d = new frappe.ui.Dialog({
                title: __('Version History'),
                size: 'large',
                fields: [
                    {
                        fieldtype: 'HTML',
                        fieldname: 'version_list'
                    }
                ]
            });
            
            let html = '<table class="table table-bordered table-hover">';
            html += '<thead><tr><th>Version</th><th>Created By</th><th>Date</th><th>Description</th><th>Actions</th></tr></thead>';
            html += '<tbody>';
            
            history.forEach(function(v) {
                html += `<tr>
                    <td><strong>v${v.version_number}</strong></td>
                    <td>${frappe.user_info(v.created_by).fullname}</td>
                    <td>${frappe.datetime.str_to_user(v.created_at)}</td>
                    <td>${v.change_description || 'No description'}</td>
                    <td>
                        <button class="btn btn-xs btn-primary restore-version-btn" data-version="${v.version_number}">
                            <i class="fa fa-undo"></i> Restore
                        </button>
                        <button class="btn btn-xs btn-default compare-version-btn" data-version="${v.version_number}">
                            <i class="fa fa-exchange"></i> Compare
                        </button>
                    </td>
                </tr>`;
            });
            
            html += '</tbody></table>';
            d.fields_dict.version_list.$wrapper.html(html);
            
            // Add click handlers
            d.$wrapper.find('.restore-version-btn').on('click', function() {
                let version_num = $(this).data('version');
                restore_version_from_dialog(frm, version_num, d);
            });
            
            d.$wrapper.find('.compare-version-btn').on('click', function() {
                let version_num = $(this).data('version');
                compare_version(frm.doc.name, version_num);
            });
            
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
                    if (r.message) {
                        frappe.show_alert({
                            message: __('Version snapshot created'),
                            indicator: 'green'
                        });
                        d.hide();
                    }
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
            if (!r.message || r.message.length === 0) {
                frappe.msgprint(__('No versions available to restore'));
                return;
            }
            
            let versions = r.message;
            
            let d = new frappe.ui.Dialog({
                title: __('Restore Version'),
                fields: [
                    {
                        label: __('Select Version'),
                        fieldname: 'version_number',
                        fieldtype: 'Select',
                        options: versions.map(v => `${v.version_number} - ${v.change_description || 'No description'}`).join('\n'),
                        reqd: 1
                    },
                    {
                        fieldtype: 'HTML',
                        fieldname: 'warning',
                        options: '<div class="alert alert-warning"><i class="fa fa-exclamation-triangle"></i> <strong>Warning:</strong> Current state will be backed up before restore.</div>'
                    }
                ],
                primary_action_label: __('Restore'),
                primary_action: function(values) {
                    let version_num = parseInt(values.version_number.split(' - ')[0]);
                    
                    frappe.confirm(
                        __('Are you sure you want to restore to version {0}? This will create a backup of the current state.', [version_num]),
                        function() {
                            frappe.call({
                                method: 'erpnext_agile.version_control.restore_issue_version',
                                args: {
                                    task_name: frm.doc.name,
                                    version_number: version_num
                                },
                                callback: function(r) {
                                    if (r.message) {
                                        frappe.show_alert({
                                            message: __('Issue restored to version {0}', [version_num]),
                                            indicator: 'green'
                                        });
                                        frm.reload_doc();
                                        d.hide();
                                    }
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

function restore_version_from_dialog(frm, version_number, parent_dialog) {
    frappe.confirm(
        __('Are you sure you want to restore to version {0}? This will create a backup of the current state.', [version_number]),
        function() {
            frappe.call({
                method: 'erpnext_agile.version_control.restore_issue_version',
                args: {
                    task_name: frm.doc.name,
                    version_number: version_number
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.show_alert({
                            message: __('Issue restored to version {0}', [version_number]),
                            indicator: 'green'
                        });
                        frm.reload_doc();
                        if (parent_dialog) parent_dialog.hide();
                    }
                }
            });
        }
    );
}

function compare_version(task_name, version_number) {
    frappe.call({
        method: 'erpnext_agile.version_control.compare_with_current',
        args: {
            task_name: task_name,
            version_number: version_number
        },
        callback: function(r) {
            if (!r.message) {
                frappe.msgprint(__('No differences found'));
                return;
            }
            
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
            html += '<thead><tr><th>Field</th><th>Change Type</th><th>Old Value</th><th>New Value</th></tr></thead>';
            html += '<tbody>';
            
            if (diff.length === 0) {
                html += '<tr><td colspan="4" class="text-center text-muted">No changes detected between this version and current state.</td></tr>';
            } else {
                diff.forEach(function(change) {
                    let badge_class = change.change_type === 'added' ? 'success' : 
                                     change.change_type === 'removed' ? 'danger' : 'warning';
                    
                    let row_class = change.change_type === 'added' ? 'table-success' : 
                                   change.change_type === 'removed' ? 'table-danger' : 'table-warning';
                    
                    html += `<tr class="${row_class}">
                        <td><strong>${change.field}</strong></td>
                        <td><span class="badge badge-${badge_class}">${change.change_type}</span></td>
                        <td><code>${change.old_value}</code></td>
                        <td><code>${change.new_value}</code></td>
                    </tr>`;
                });
            }
            
            html += '</tbody></table>';
            
            d.fields_dict.diff_view.$wrapper.html(html);
            d.show();
        }
    });
}