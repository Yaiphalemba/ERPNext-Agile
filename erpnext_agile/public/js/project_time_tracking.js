// erpnext_agile/public/js/project_time_tracking.js

frappe.ui.form.on('Project', {
    enable_agile: function(frm) {
        if (frm.doc.enable_agile) {
            show_time_tracking_section(frm);
        } else {
            hide_time_tracking_section(frm);
        }
    },

    refresh: function(frm) {
        if (frm.doc.enable_agile) {
            add_time_tracking_buttons(frm);
            load_and_display_time_summary(frm);
        }
    }
});

frappe.ui.form.on('Project User', {
    form_render: function(frm, cdt, cdn) {
        // Refresh time display when Project User row is rendered
        if (frm.doc.enable_agile) {
            update_project_user_display(frm, cdn);
        }
    }
});

function add_time_tracking_buttons(frm) {
    // Button: View Time Summary
    frm.add_custom_button(__('Time Summary'), function() {
        show_project_time_summary(frm);
    }, __('Time Tracking'));

    // Button: User Time Details
    frm.add_custom_button(__('User Details'), function() {
        show_user_time_details_dialog(frm);
    }, __('Time Tracking'));

    // Button: Recalculate Times (for data cleanup)
    if (frappe.session.user === frm.doc.owner || frappe.session.user_roles.includes('Project Manager')) {
        frm.add_custom_button(__('Recalculate Times'), function() {
            frappe.confirm(
                __('Recalculate all time metrics for this project? This may take a moment.'),
                function() {
                    frappe.call({
                        method: 'erpnext_agile.project_time_tracking.force_recalculate_project_times',
                        args: { project_name: frm.doc.name },
                        callback: function(r) {
                            if (r.message && r.message.success) {
                                frappe.show_alert({
                                    message: __('Times recalculated'),
                                    indicator: 'green'
                                });
                                frm.reload_doc();
                            }
                        }
                    });
                }
            );
        }, __('Time Tracking'));
    }
}

function show_time_tracking_section(frm) {
    frm.toggle_display('custom_time_allocated', true);
    frm.toggle_display('custom_time_utilized', true);
    frm.toggle_display('custom_designated_task_status', true);
}

function hide_time_tracking_section(frm) {
    frm.toggle_display('custom_time_allocated', false);
    frm.toggle_display('custom_time_utilized', false);
    frm.toggle_display('custom_designated_task_status', false);
}

function load_and_display_time_summary(frm) {
    // Load summary and update the child table display
    if (!frm.doc.name || frm.doc.is_new()) return;

    frappe.call({
        method: 'erpnext_agile.project_time_tracking.get_project_user_time_summary',
        args: { project_name: frm.doc.name },
        callback: function(r) {
            if (r.message && r.message.length > 0) {
                // Create dashboard indicators or update display
                display_time_summary_dashboard(frm, r.message);
            }
        },
        error: function() {
            console.log('Error loading time summary');
        }
    });
}

function display_time_summary_dashboard(frm, summaries) {
    // Calculate aggregate stats
    let total_allocated = 0;
    let total_utilized = 0;
    let team_members_working = 0;

    summaries.forEach(summary => {
        if (summary.total_time_spent) {
            // Parse formatted time back to seconds for calculation
            total_utilized += parse_time_to_seconds(summary.total_time_spent);
        }
        if (summary.status === 'Working') {
            team_members_working++;
        }
    });

    // Show as dashboard
    let dashboard_html = `
        <div style="padding: 15px; background: #f8f9fa; border-radius: 4px; margin-bottom: 15px;">
            <h6 style="margin-bottom: 10px;">📊 Team Time Overview</h6>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px;">
                <div style="background: white; padding: 10px; border-radius: 4px; border-left: 4px solid #007bff;">
                    <div style="font-size: 0.8em; color: #666; margin-bottom: 5px;">Team Members</div>
                    <div style="font-size: 1.5em; font-weight: bold;">${summaries.length}</div>
                </div>
                <div style="background: white; padding: 10px; border-radius: 4px; border-left: 4px solid #28a745;">
                    <div style="font-size: 0.8em; color: #666; margin-bottom: 5px;">Working Now</div>
                    <div style="font-size: 1.5em; font-weight: bold;">${team_members_working}</div>
                </div>
                <div style="background: white; padding: 10px; border-radius: 4px; border-left: 4px solid #6610f2;">
                    <div style="font-size: 0.8em; color: #666; margin-bottom: 5px;">Total Time Logged</div>
                    <div style="font-size: 1.5em; font-weight: bold;">${format_seconds_readable(total_utilized)}</div>
                </div>
            </div>
        </div>
    `;

    // Find or create container in form
    let container = document.querySelector('[data-fieldname="users"]').closest('.frappe-control');
    let dashboard = container.querySelector('.time-tracking-dashboard');

    if (!dashboard) {
        dashboard = document.createElement('div');
        dashboard.className = 'time-tracking-dashboard';
        container.insertBefore(dashboard, container.firstChild);
    }

    dashboard.innerHTML = dashboard_html;
}

function show_project_time_summary(frm) {
    let d = new frappe.ui.Dialog({
        title: __('Project Time Summary - {0}', [frm.doc.project_name]),
        size: 'large',
        fields: [
            {
                fieldname: 'summary_html',
                fieldtype: 'HTML'
            }
        ]
    });

    d.fields_dict.summary_html.$wrapper.html(`
        <div class="text-center" style="padding: 40px;">
            <div class="spinner-border text-primary" role="status"></div>
            <p class="text-muted mt-3">Loading time summary...</p>
        </div>
    `);

    d.show();

    // Store project name globally so button can access it
    window.current_project_name = frm.doc.name;

    // Load summary data
    frappe.call({
        method: 'erpnext_agile.project_time_tracking.get_project_user_time_summary',
        args: { project_name: frm.doc.name },
        callback: function(r) {
            if (r.message) {
                render_time_summary_table(d.fields_dict.summary_html.$wrapper, r.message);
            }
        }
    });
}

function render_time_summary_table(container, summaries) {
    if (!summaries || summaries.length === 0) {
        container.html(`
            <div class="text-center text-muted" style="padding: 40px;">
                <p>No time data available</p>
            </div>
        `);
        return;
    }

    let html = `
        <div class="table-responsive" style="max-height: 400px; overflow-y: auto;">
            <table class="table table-bordered table-hover" style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr>
                        <th style="min-width: 200px;">User</th>
                        <th style="width: 100px;">Status</th>
                        <th style="width: 110px;">Time Logged</th>
                        <th style="width: 110px;">Estimated</th>
                        <th style="width: 110px;">Remaining</th>
                        <th style="width: 100px;">Utilization</th>
                        <th style="width: 90px;">Tasks</th>
                        <th style="width: 120px;">Actions</th>
                    </tr>
                </thead>
                <tbody>
    `;

    const userMap = Object.fromEntries(cur_frm.doc.users.map(u => [u.user, u.full_name]));

    summaries.forEach(summary => {
        let status_badge = get_status_badge(summary.status);
        let utilization_color = summary.utilization_percentage > 100 ? 'danger' : 
                               summary.utilization_percentage > 80 ? 'warning' : 'success';
        let fullname = userMap[summary.user] || summary.user;

        html += `
            <tr>
                <td><strong>${fullname}</strong></td>
                <td>${status_badge}</td>
                <td>${summary.total_time_spent}</td>
                <td>${summary.total_estimated}</td>
                <td>${summary.total_remaining}</td>
                <td>
                    <span class="badge badge-${utilization_color}">
                        ${summary.utilization_percentage}%
                    </span>
                </td>
                <td>
                    <span class="badge badge-info">
                        ${summary.task_summary.completed}/${summary.task_summary.total}
                    </span>
                </td>
                <td>
                    <button class="btn btn-xs btn-default view-user-details-btn" 
                            data-user="${summary.user}"
                            data-project="${window.current_project_name}">
                        <i class="fa fa-eye"></i> Details
                    </button>
                </td>
            </tr>
        `;
    });

    html += `
            </tbody>
            </table>
        </div>
    `;
    container.html(html);

    // Attach click handler using event delegation
    container.off('click', '.view-user-details-btn').on('click', '.view-user-details-btn', function(e) {
        e.preventDefault();
        let user = $(this).data('user');
        let project = $(this).data('project');
        show_user_time_breakdown(user, project);
    });
}

function get_status_badge(status) {
    const badges = {
        'Working': '<span class="badge badge-success">🔄 Working</span>',
        'Completed': '<span class="badge badge-info">✓ Completed</span>',
        'Cancelled': '<span class="badge badge-secondary">✗ Cancelled</span>',
        'Open': '<span class="badge badge-warning">⏳ Open</span>'
    };
    return badges[status] || badges['Open'];
}

function show_user_time_details_dialog(frm) {
    let users = frm.doc.users.map(u => u.user).join('\n');

    let d = new frappe.ui.Dialog({
        title: __('Select User for Detailed View'),
        fields: [
            {
                fieldname: 'user',
                fieldtype: 'Link',
                options: 'User',
                label: __('User'),
                reqd: 1
            }
        ],
        primary_action_label: __('View Details'),
        primary_action: function(values) {
            show_user_time_breakdown(values.user, frm.doc.name);
            d.hide();
        }
    });

    d.show();
}

function show_user_time_breakdown(user, project_name) {
    let d = new frappe.ui.Dialog({
        title: __('Time Breakdown - {0}', [frappe.user_info(user).fullname]),
        size: 'large',
        fields: [
            {
                fieldname: 'breakdown_html',
                fieldtype: 'HTML'
            }
        ]
    });

    d.fields_dict.breakdown_html.$wrapper.html(`
        <div class="text-center" style="padding: 40px;">
            <div class="spinner-border text-primary" role="status"></div>
        </div>
    `);

    d.show();

    // Load details
    frappe.call({
        method: 'erpnext_agile.project_time_tracking.get_user_time_details',
        args: { project_name: project_name, user: user },
        callback: function(r) {
            if (r.message) {
                render_user_time_breakdown(d.fields_dict.breakdown_html.$wrapper, r.message);
            }
        }
    });
}

function render_user_time_breakdown(container, data) {
    let tasks = data.tasks || [];

    if (tasks.length === 0) {
        container.html('<p class="text-muted text-center">No tasks assigned to this user</p>');
        return;
    }

    let html = '<div class="user-breakdown">';

    // Summary cards
    html += `
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; margin-bottom: 20px;">
    `;

    // Calculate totals
    let total_time = 0;
    let total_est = 0;
    let total_remaining = 0;

    tasks.forEach(task => {
        total_time += parse_time_to_seconds(task.time_spent);
        total_est += parse_time_to_seconds(task.estimated);
        total_remaining += parse_time_to_seconds(task.remaining);
    });

    html += `
            <div style="background: #e7f3ff; padding: 10px; border-radius: 4px;">
                <div style="font-size: 0.8em; color: #666;">Time Logged</div>
                <div style="font-size: 1.3em; font-weight: bold;">${format_seconds_readable(total_time)}</div>
            </div>
            <div style="background: #fff7e6; padding: 10px; border-radius: 4px;">
                <div style="font-size: 0.8em; color: #666;">Estimated</div>
                <div style="font-size: 1.3em; font-weight: bold;">${format_seconds_readable(total_est)}</div>
            </div>
            <div style="background: #f0f0f0; padding: 10px; border-radius: 4px;">
                <div style="font-size: 0.8em; color: #666;">Remaining</div>
                <div style="font-size: 1.3em; font-weight: bold;">${format_seconds_readable(total_remaining)}</div>
            </div>
        </div>
    `;

    // Tasks table
    html += `
        <table class="table table-sm">
            <thead>
                <tr>
                    <th>Issue</th>
                    <th>Task</th>
                    <th>Status</th>
                    <th>Time Logged</th>
                    <th>Estimated</th>
                    <th>Remaining</th>
                    <th>Sprint</th>
                </tr>
            </thead>
            <tbody>
    `;

    tasks.forEach(task => {
        html += `
            <tr>
                <td><strong>${task.issue_key}</strong></td>
                <td>
                    <a href="/app/task/${task.task_name}">
                        ${task.subject.substring(0, 30)}...
                    </a>
                </td>
                <td><span class="badge badge-secondary">${task.status}</span></td>
                <td>${task.time_spent}</td>
                <td>${task.estimated}</td>
                <td>${task.remaining}</td>
                <td>${task.sprint ? `<small>${task.sprint}</small>` : '-'}</td>
            </tr>
        `;
    });

    html += '</tbody></table></div>';

    container.html(html);
}

// ============================================
// UTILITY FUNCTIONS
// ============================================

function format_seconds_readable(seconds) {
    if (!seconds) return '0m';
    
    seconds = parseInt(seconds);
    let hours = Math.floor(seconds / 3600);
    let minutes = Math.floor((seconds % 3600) / 60);
    
    if (hours > 0 && minutes > 0) {
        return `${hours}h ${minutes}m`;
    } else if (hours > 0) {
        return `${hours}h`;
    } else {
        return `${minutes}m`;
    }
}

function parse_time_to_seconds(time_str) {
    if (!time_str) return 0;
    if (typeof time_str === 'number') return time_str;
    
    let total = 0;
    let match_h = time_str.match(/(\d+)h/);
    let match_m = time_str.match(/(\d+)m/);
    
    if (match_h) total += parseInt(match_h[1]) * 3600;
    if (match_m) total += parseInt(match_m[1]) * 60;
    
    return total;
}

function update_project_user_display(frm, cdn) {
    // Update visual indicators for Project User rows
    let row = frm.get_row(cdn);
    if (!row) return;
    
    let status = row.custom_designated_task_status || 'Open';
    let time_util = row.custom_time_utilized || 0;
    
    // Add styling based on status
    let row_color = {
        'Working': '#e7f3ff',
        'Completed': '#e6f9e6',
        'Cancelled': '#f0f0f0',
        'Open': '#fffbf0'
    };
    
    // This would require accessing the DOM directly, which is complex in Frappe
    // Better to rely on field formatters in customizations
}