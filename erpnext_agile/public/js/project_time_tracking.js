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
    if (frappe.session.user === frm.doc.owner || frappe.user.has_role('Project Manager')) {
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
    if (!frm.doc.name || frm.is_new()) return;

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
    // 1. Calculate aggregate stats cleanly
    let total_utilized = 0;
    let team_members_working = 0;

    summaries.forEach(summary => {
        if (summary.total_time_spent) {
            total_utilized += parse_time_to_seconds(summary.total_time_spent);
        }
        if (summary.status === 'Working') {
            team_members_working++;
        }
    });

    // 2. Modern, clean dashboard HTML
    const dashboard_html = `
        <div class="time-tracking-dashboard-inner" style="background: #f4f5f7; border-radius: 8px; padding: 16px; margin-bottom: 20px; border: 1px solid #dfe1e6;">
            <div style="font-size: 13px; font-weight: 600; color: #5e6c84; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.5px;">
                Team Time Overview
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px;">
                <div style="background: white; padding: 12px 16px; border-radius: 6px; border-left: 3px solid #0052cc; box-shadow: 0 1px 1px rgba(9,30,66,0.05);">
                    <div style="font-size: 0.85em; color: #6b778c; margin-bottom: 4px;">Team Members</div>
                    <div style="font-size: 1.4em; font-weight: 600; color: #172b4d;">${summaries.length}</div>
                </div>
                <div style="background: white; padding: 12px 16px; border-radius: 6px; border-left: 3px solid #36b37e; box-shadow: 0 1px 1px rgba(9,30,66,0.05);">
                    <div style="font-size: 0.85em; color: #6b778c; margin-bottom: 4px;">Working Now</div>
                    <div style="font-size: 1.4em; font-weight: 600; color: #172b4d;">${team_members_working}</div>
                </div>
                <div style="background: white; padding: 12px 16px; border-radius: 6px; border-left: 3px solid #6554c0; box-shadow: 0 1px 1px rgba(9,30,66,0.05);">
                    <div style="font-size: 0.85em; color: #6b778c; margin-bottom: 4px;">Total Time Logged</div>
                    <div style="font-size: 1.4em; font-weight: 600; color: #172b4d;">${format_seconds_readable(total_utilized)}</div>
                </div>
            </div>
        </div>
    `;

    // 3. The Frappe-safe way to inject HTML
    // Safely get the wrapper for the 'users' child table
    const field_wrapper = frm.fields_dict['users'] ? frm.fields_dict['users'].$wrapper : null;
    
    if (!field_wrapper) {
        console.warn("Could not find the 'users' field wrapper to attach the time dashboard.");
        return;
    }

    // Find existing dashboard or create a new one to avoid duplicating on every refresh
    let $dashboard = field_wrapper.find('.time-tracking-dashboard-container');
    
    if ($dashboard.length === 0) {
        // Create the container and prepend it BEFORE the child table
        $dashboard = $('<div class="time-tracking-dashboard-container"></div>').prependTo(field_wrapper);
    }

    // Update the inner HTML safely
    $dashboard.html(dashboard_html);
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
    const tasks = data.tasks || [];

    if (!tasks.length) {
        container.html('<p class="text-muted text-center py-4">No tasks assigned to this user.</p>');
        return;
    }

    // 1. Calculate totals cleanly using reduce
    const totals = tasks.reduce((acc, task) => {
        acc.time += parse_time_to_seconds(task.time_spent);
        acc.est += parse_time_to_seconds(task.estimated);
        acc.rem += parse_time_to_seconds(task.remaining);
        return acc;
    }, { time: 0, est: 0, rem: 0 });

    // 2. Build the UI using clean template literals
    const html = `
        <div class="user-breakdown">
            <div class="summary-cards" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 24px;">
                <div class="card-metric" style="background: #eef5ff; padding: 16px; border-radius: 6px;">
                    <div style="font-size: 0.85em; color: #5a6b85; margin-bottom: 4px;">Time Logged</div>
                    <div style="font-size: 1.4em; font-weight: 600; color: #1a2b4c;">${format_seconds_readable(totals.time)}</div>
                </div>
                <div class="card-metric" style="background: #fff8e6; padding: 16px; border-radius: 6px;">
                    <div style="font-size: 0.85em; color: #7a6331; margin-bottom: 4px;">Estimated</div>
                    <div style="font-size: 1.4em; font-weight: 600; color: #3d3118;">${format_seconds_readable(totals.est)}</div>
                </div>
                <div class="card-metric" style="background: #f4f5f7; padding: 16px; border-radius: 6px;">
                    <div style="font-size: 0.85em; color: #505f79; margin-bottom: 4px;">Remaining</div>
                    <div style="font-size: 1.4em; font-weight: 600; color: #172b4d;">${format_seconds_readable(totals.rem)}</div>
                </div>
            </div>

            <div class="table-responsive">
                <table class="table table-borderless table-hover" style="border-collapse: separate; border-spacing: 0 8px;">
                    <thead style="color: #6b778c; font-size: 0.85em; border-bottom: 1px solid #dfe1e6;">
                        <tr>
                            <th class="font-weight-bold pb-2">Issue</th>
                            <th class="font-weight-bold pb-2">Task</th>
                            <th class="font-weight-bold pb-2">Status</th>
                            <th class="font-weight-bold pb-2">Time Logged</th>
                            <th class="font-weight-bold pb-2">Estimated</th>
                            <th class="font-weight-bold pb-2">Remaining</th>
                            <th class="font-weight-bold pb-2">Sprint</th>
                        </tr>
                    </thead>
                    <tbody style="font-size: 0.9em; color: #172b4d;">
                        ${tasks.map(task => `
                            <tr style="border-bottom: 1px solid #f4f5f7;">
                                <td class="align-middle"><strong>${task.issue_key}</strong></td>
                                <td class="align-middle" style="max-width: 250px;">
                                    <a href="/app/task/${task.task_name}" 
                                       style="display: block; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: #344563; text-decoration: none;"
                                       title="${task.subject}">
                                        ${task.subject}
                                    </a>
                                </td>
                                <td class="align-middle">
                                    <span class="badge badge-pill badge-secondary" style="background-color: #dfe1e6; color: #42526e; padding: 4px 8px; border-radius: 12px; font-weight: 600;">
                                        ${task.status}
                                    </span>
                                </td>
                                <td class="align-middle">${task.time_spent}</td>
                                <td class="align-middle">${task.estimated}</td>
                                <td class="align-middle">${task.remaining}</td>
                                <td class="align-middle" style="color: #6b778c; font-size: 0.85em;">
                                    ${task.sprint ? task.sprint : '-'}
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    `;

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
    // 1. Dig into the grid API to find the exact row object
    const grid = frm.fields_dict['users'].grid;
    const grid_row = grid.grid_rows.find(row => row.doc.name === cdn);
    
    // Bail if the DOM hasn't caught up yet
    if (!grid_row || !grid_row.wrapper) return;
    
    const status = grid_row.doc.custom_designated_task_status || 'Open';
    
    // 2. Map your Atlassian-style subtle colors
    const row_colors = {
        'Working': '#ebecf0',    // Subtle blue-grey
        'Completed': '#e3fcef',  // Mint green
        'Cancelled': '#fafbfc',  // Very light grey
        'Open': '#fffae6'        // Warm yellow
    };
    
    const bg_color = row_colors[status] || 'transparent';
    
    // 3. Apply the style directly to the row's outer wrapper
    $(grid_row.wrapper)
        .css('background-color', bg_color)
        .css('transition', 'background-color 0.3s ease'); // Smooth fade just to be fancy
}