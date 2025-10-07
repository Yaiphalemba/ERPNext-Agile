frappe.ui.form.on('Project', {
    refresh: function(frm) {
        if (frm.doc.enable_agile) {
            add_agile_project_buttons(frm);
        }
    },
    
    enable_agile: function(frm) {
        if (frm.doc.enable_agile && !frm.doc.project_key) {
            // Auto-generate project key suggestion
            let suggested_key = generate_project_key(frm.doc.project_name);
            frm.set_value('project_key', suggested_key);
        }
    }
});

function add_agile_project_buttons(frm) {
    // View Board
    frm.add_custom_button(__('View Board'), function() {
        show_agile_board(frm);
    }, __('Agile'));
    
    // View Backlog
    frm.add_custom_button(__('View Backlog'), function() {
        show_backlog(frm);
    }, __('Agile'));
    
    // Sprint Planning
    frm.add_custom_button(__('Sprint Planning'), function() {
        show_sprint_planning(frm);
    }, __('Agile'));
    
    // Reports
    frm.add_custom_button(__('Reports'), function() {
        show_agile_reports_menu(frm);
    }, __('Agile'));
    
    // Bulk Sync GitHub
    if (frm.doc.github_repository) {
        frm.add_custom_button(__('Bulk Sync GitHub'), function() {
            bulk_sync_github(frm);
        }, __('GitHub'));
    }
}

function show_agile_board(frm) {
    frappe.route_options = {
        project: frm.doc.name
    };
    frappe.set_route('agile-board', frm.doc.name);
}

function show_backlog(frm) {
    frappe.route_options = {
        project: frm.doc.name
    };
    frappe.set_route('agile-backlog', frm.doc.name);
}

function show_sprint_planning(frm) {
    frappe.route_options = {
        project: frm.doc.name
    };
    frappe.set_route('sprint-planning', frm.doc.name);
}

function show_agile_reports_menu(frm) {
    let d = new frappe.ui.Dialog({
        title: __('Agile Reports'),
        fields: [
            {
                label: __('Report Type'),
                fieldname: 'report_type',
                fieldtype: 'Select',
                options: [
                    'Sprint Report',
                    'Burndown Chart',
                    'Velocity Chart',
                    'Cumulative Flow',
                    'Team Time Report',
                    'Epic Progress'
                ]
            }
        ],
        primary_action_label: __('View Report'),
        primary_action: function(values) {
            open_agile_report(frm, values.report_type);
            d.hide();
        }
    });
    d.show();
}

function bulk_sync_github(frm) {
    frappe.confirm(
        __('Sync all GitHub issues for this project?'),
        function() {
            frappe.call({
                method: 'erpnext_agile.api.bulk_sync_project_issues',
                args: {
                    project_name: frm.doc.name
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.msgprint(__('Synced {0} issues ({1} created, {2} updated)',
                            [r.message.synced, r.message.created, r.message.updated]));
                    }
                }
            });
        }
    );
}

function generate_project_key(project_name) {
    // Generate project key from project name
    // Example: "My Awesome Project" -> "MAP"
    let words = project_name.toUpperCase().split(' ');
    if (words.length >= 3) {
        return words[0][0] + words[1][0] + words[2][0];
    } else if (words.length === 2) {
        return words[0][0] + words[1].substring(0, 2);
    } else {
        return words[0].substring(0, 3);
    }
}

function open_agile_report(frm, report_type) {
    // Open specific agile report
    frappe.set_route('query-report', report_type, {
        project: frm.doc.name
    });
}