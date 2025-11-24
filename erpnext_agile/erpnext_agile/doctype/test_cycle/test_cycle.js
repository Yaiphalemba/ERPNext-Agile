// Copyright (c) 2025, Yanky and contributors
// For license information, please see license.txt

frappe.ui.form.on('Test Cycle', {
    refresh(frm) {
        // Set cycle_id as title
        frm.set_df_property('cycle_id', 'bold', 1);
        
        if (!frm.is_new()) {
            // Status-based actions
            if (frm.doc.status === "Not Started") {
                frm.add_custom_button(__('Start Cycle'), () => {
                    frappe.call({
                        method: 'start_cycle',
                        doc: frm.doc,
                        callback: () => {
                            frm.reload_doc();
                        }
                    });
                }).addClass('btn-primary');
            }
            
            if (frm.doc.status === "In Progress") {
                frm.add_custom_button(__('Complete Cycle'), () => {
                    frappe.confirm(
                        __('Are you sure you want to complete this test cycle?'),
                        () => {
                            frappe.call({
                                method: 'complete_cycle',
                                doc: frm.doc,
                                callback: () => {
                                    frm.reload_doc();
                                }
                            });
                        }
                    );
                }).addClass('btn-success');
            }
            
            // Add test cases button
            frm.add_custom_button(__('Add Test Cases'), () => {
                show_test_case_selector(frm);
            });
            
            // Execute all tests
            frm.add_custom_button(__('Execute All Tests'), () => {
                execute_all_tests(frm);
            });
            
            // Show execution summary
            show_execution_dashboard(frm);
        }
        
        // Filter sprint by project
        frm.set_query('sprint', () => {
            return {
                filters: {
                    'project': frm.doc.project
                }
            };
        });
    },
    
    project(frm) {
        // Clear sprint if project changes
        if (frm.doc.sprint) {
            frm.set_value('sprint', '');
        }
        
        // Filter test cases by project
        frm.fields_dict['test_cases'].grid.get_field('test_case').get_query = function() {
            return {
                filters: {
                    'project': frm.doc.project,
                    'status': 'Approved'
                }
            };
        };
    },
    
    status(frm) {
        // Refresh to show/hide buttons
        frm.trigger('refresh');
    }
});

frappe.ui.form.on('Test Cycle Item', {
    test_case(frm, cdt, cdn) {
        // Auto-set execution status
        let row = locals[cdt][cdn];
        if (!row.execution_status) {
            row.execution_status = 'Not Run';
            frm.refresh_field('test_cases');
        }
    },
    
    test_cases_add(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        row.execution_status = 'Not Run';
        frm.refresh_field('test_cases');
    }
});

function show_test_case_selector(frm) {
    let d = new frappe.ui.Dialog({
        title: __('Add Test Cases'),
        fields: [
            {
                fieldtype: 'MultiSelectList',
                label: __('Select Test Cases'),
                fieldname: 'test_cases',
                options: [],
                get_data: () => {
                    return frappe.call({
                        method: 'frappe.client.get_list',
                        args: {
                            doctype: 'Test Case',
                            filters: {
                                'project': frm.doc.project,
                                'status': 'Approved'
                            },
                            fields: ['name', 'title', 'priority'],
                            limit_page_length: 0
                        }
                    }).then(r => {
                        return r.message.map(tc => ({
                            value: tc.name,
                            description: `${tc.title} (${tc.priority})`
                        }));
                    });
                }
            }
        ],
        primary_action_label: __('Add'),
        primary_action(values) {
            if (!values.test_cases || values.test_cases.length === 0) {
                frappe.msgprint(__('Please select at least one test case'));
                return;
            }
            
            frappe.call({
                method: 'add_test_cases_bulk',
                doc: frm.doc,
                args: {
                    test_cases: values.test_cases
                },
                callback: () => {
                    frm.reload_doc();
                    d.hide();
                }
            });
        }
    });
    d.show();
}

function execute_all_tests(frm) {
    frappe.confirm(
        __('This will create test executions for all test cases in this cycle. Continue?'),
        () => {
            frappe.call({
                method: 'erpnext_agile.test_management.api.bulk_create_executions',
                args: {
                    test_cycle: frm.doc.name
                },
                callback: (r) => {
                    if (r.message) {
                        frappe.show_alert({
                            message: __('Created {0} test execution(s)', [r.message]),
                            indicator: 'green'
                        });
                        frm.reload_doc();
                    }
                }
            });
        }
    );
}

function show_execution_dashboard(frm) {
    // Clear existing indicators
    frm.dashboard.clear_headline();
    
    if (frm.doc.total_tests > 0) {
        let progress = frm.doc.pass_rate || 0;
        let color = progress >= 80 ? 'green' : progress >= 50 ? 'orange' : 'red';
        
        frm.dashboard.add_progress(__('Execution Progress'), progress, __('Pass Rate: {0}%', [progress.toFixed(2)]));
        
        // Add metrics indicators
        if (frm.doc.passed_tests > 0) {
            frm.dashboard.add_indicator(__('Passed: {0}', [frm.doc.passed_tests]), 'green');
        }
        if (frm.doc.failed_tests > 0) {
            frm.dashboard.add_indicator(__('Failed: {0}', [frm.doc.failed_tests]), 'red');
        }
        if (frm.doc.blocked_tests > 0) {
            frm.dashboard.add_indicator(__('Blocked: {0}', [frm.doc.blocked_tests]), 'orange');
        }
        if (frm.doc.not_run_tests > 0) {
            frm.dashboard.add_indicator(__('Not Run: {0}', [frm.doc.not_run_tests]), 'grey');
        }
    }
}