// Copyright (c) 2025, Yanky and contributors
// For license information, please see license.txt

frappe.ui.form.on('Test Case', {
    refresh(frm) {
        // Set test_case_id as title field
        frm.set_df_property('test_case_id', 'bold', 1);
        
        if (!frm.is_new()) {
            // Add custom buttons
            frm.add_custom_button(__('Execute Test'), () => {
                create_test_execution(frm);
            }).addClass('btn-primary');
            
            frm.add_custom_button(__('Clone Test Case'), () => {
                frappe.call({
                    method: 'clone_test_case',
                    doc: frm.doc,
                    callback: (r) => {
                        if (r.message) {
                            frappe.set_route('Form', 'Test Case', r.message);
                        }
                    }
                });
            });
            
            // Show metrics
            show_test_metrics(frm);
        }
    },
    
    project(frm) {
        // Filter linked items based on project
        if (frm.doc.project) {
            frm.fields_dict['linked_items'].grid.get_field('link_name').get_query = function(doc, cdt, cdn) {
                let row = locals[cdt][cdn];
                if (row.link_doctype === 'Task') {
                    return {
                        filters: {
                            'project': frm.doc.project,
                            'is_group': 0
                        }
                    };
                }
            };
        }
    }
});

frappe.ui.form.on('Test Step', {
    test_steps_add(frm, cdt, cdn) {
        // Auto-set step number
        let row = locals[cdt][cdn];
        row.step_number = frm.doc.test_steps.length;
        frm.refresh_field('test_steps');
    }
});

frappe.ui.form.on('Test Case Link', {
    link_doctype(frm, cdt, cdn) {
        // Clear link_name when doctype changes
        let row = locals[cdt][cdn];
        row.link_name = '';
        frm.refresh_field('linked_items');
    }
});

function create_test_execution(frm) {
    let d = new frappe.ui.Dialog({
        title: __('Create Test Execution'),
        fields: [
            {
                fieldtype: 'Link',
                label: __('Test Cycle'),
                fieldname: 'test_cycle',
                options: 'Test Cycle',
                reqd: 1,
                get_query: () => ({
                    filters: { 'status': ['in', ['Not Started', 'In Progress']] }
                }),
                onchange: function() {
                    const test_cycle = d.get_value('test_cycle');
                    if (test_cycle) {
                        frappe.db.get_doc('Test Cycle', test_cycle)
                            .then(doc => {
                                if (doc.release_version) {
                                    d.set_value('build_version', doc.release_version);
                                }
                            })
                            .catch(() => {
                                frappe.msgprint(__('Unable to fetch Test Cycle details'));
                            });
                    }
                }
            },
            {
                fieldtype: 'Link',
                label: __('Assigned To'),
                fieldname: 'assigned_to',
                options: 'User',
                default: frappe.session.user
            },
            {
                fieldtype: 'Select',
                label: __('Environment'),
                fieldname: 'environment',
                options: 'Development\nStaging\nProduction',
                default: 'Development'
            },
            {
                fieldtype: 'Link',
                label: __('Build Version'),
                fieldname: 'build_version',
                options: 'Agile Release Version'
            }
        ],
        primary_action_label: __('Create'),
        primary_action(values) {
            frappe.call({
                method: 'erpnext_agile.test_management.api.create_test_execution',
                args: {
                    test_case: frm.doc.name,
                    test_cycle: values.test_cycle,
                    assigned_to: values.assigned_to,
                    environment: values.environment,
                    build_version: values.build_version
                },
                callback: (r) => {
                    if (r.message) {
                        frappe.show_alert({
                            message: __('Test Execution {0} created', [r.message]),
                            indicator: 'green'
                        });
                        d.hide();
                        frappe.set_route('Form', 'Test Execution', r.message);
                    }
                }
            });
        }
    });

    d.show();
}

function show_test_metrics(frm) {
    // Show execution metrics in sidebar
    frappe.call({
        method: 'get_execution_count',
        doc: frm.doc,
        callback: (r) => {
            if (r.message !== undefined) {
                frm.dashboard.add_indicator(__('Total Executions: {0}', [r.message]), 'blue');
            }
        }
    });
    
    frappe.call({
        method: 'get_pass_rate',
        doc: frm.doc,
        callback: (r) => {
            if (r.message !== undefined) {
                let color = r.message >= 80 ? 'green' : r.message >= 50 ? 'orange' : 'red';
                frm.dashboard.add_indicator(__('Pass Rate: {0}%', [r.message.toFixed(2)]), color);
            }
        }
    });
}