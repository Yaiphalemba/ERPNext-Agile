// Copyright (c) 2025, Yanky and contributors
// For license information, please see license.txt

frappe.ui.form.on('Test Execution', {
    onload(frm) {
        // Add custom styles
        if (!$('style#test-execution-styles').length) {
            $('<style id="test-execution-styles">')
                .text(`
                    .success-row { background-color: #d4edda !important; }
                    .fail-row { background-color: #f8d7da !important; }
                    .blocked-row { background-color: #fff3cd !important; }
                `)
                .appendTo('head');
        }
    },

    refresh(frm) {
        // Set execution_id as title
        frm.set_df_property('execution_id', 'bold', 1);
        
        if (!frm.is_new() && frm.doc.docstatus === 0) {
            // Quick action buttons
            frm.add_custom_button(__('Mark as Pass'), () => {
                mark_all_steps(frm, 'Pass');
                frm.set_value('status', 'Pass');
            }).addClass('btn-success');
            
            frm.add_custom_button(__('Mark as Fail'), () => {
                mark_all_steps(frm, 'Fail');
                frm.set_value('status', 'Fail');
            }).addClass('btn-danger');
            
            frm.add_custom_button(__('Mark as Blocked'), () => {
                mark_all_steps(frm, 'Blocked');
                frm.set_value('status', 'Blocked');
            }).addClass('btn-warning');

            // Create bug button for failed tests
            if (frm.doc.docstatus === 0 && frm.doc.status === 'Fail') {
                let has_bugs = frm.doc.defects && frm.doc.defects.length > 0;
                if (!has_bugs) {
                    frm.add_custom_button(__('Create Bug'), () => {
                        frappe.call({
                            method: 'create_bug',
                            doc: frm.doc,
                            callback: (r) => {
                                if (r.message) {
                                    frappe.show_alert({
                                        message: __('Bug {0} created', [r.message]),
                                        indicator: 'Green'
                                    });
                                    frm.reload_doc();
                                }
                            }
                        });
                    });
                }
            }
            
            // Load test steps
            if (!frm.doc.test_results || frm.doc.test_results.length === 0) {
                frm.add_custom_button(__('Load Test Steps'), () => {
                    frappe.call({
                        method: 'load_test_steps',
                        doc: frm.doc,
                        callback: () => {
                            frm.refresh_field('test_results');
                        }
                    });
                }).addClass('btn-danger');
            }
        }
        
        // Filter test_cycle by project
        frm.set_query('test_cycle', () => {
            return {
                filters: {
                    'status': ['in', ['Not Started', 'In Progress']]
                }
            };
        });
        
        // Show execution time info
        if (frm.doc.execution_time) {
            let hours = Math.floor(frm.doc.execution_time / 3600);
            let minutes = Math.floor((frm.doc.execution_time % 3600) / 60);
            let timeStr = hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`;
            frm.dashboard.add_indicator(__('Execution Time: {0}', [timeStr]), 'blue');
        }
    },
    
    test_case(frm) {
        if (frm.doc.test_case && frm.is_new()) {
            // Auto-load test steps when test case is selected
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Test Case',
                    name: frm.doc.test_case
                },
                callback: (r) => {
                    if (r.message) {
                        // Set description
                        if (!frm.doc.comments) {
                            frm.set_value('comments', r.message.description);
                        }
                        
                        // Auto-load test steps
                        if (!frm.doc.test_results || frm.doc.test_results.length === 0) {
                            frappe.call({
                                method: 'load_test_steps',
                                doc: frm.doc,
                                callback: () => {
                                    frm.refresh_field('test_results');
                                }
                            });
                        }
                    }
                }
            });
        }
    },
    
    test_cycle(frm) {
        // Get project from test cycle
        if (frm.doc.test_cycle) {
            frappe.db.get_value('Test Cycle', frm.doc.test_cycle, 'project', (r) => {
                if (r && r.project) {
                    // Filter test cases by project
                    frm.set_query('test_case', () => {
                        return {
                            filters: {
                                'project': r.project,
                                'status': 'Approved'
                            }
                        };
                    });
                }
            });
        }
    },

    status(frm) {
        if (frm.doc.status) {
            mark_all_steps(frm, frm.doc.status);
        }
    },
    
    before_save(frm) {
        // Auto-calculate overall status from step results
        if (frm.doc.test_results && frm.doc.test_results.length > 0) {
            let has_fail = frm.doc.test_results.some(r => r.step_status === 'Fail');
            let has_blocked = frm.doc.test_results.some(r => r.step_status === 'Blocked');
            let all_pass = frm.doc.test_results.every(r => r.step_status === 'Pass');
            
            if (has_fail) {
                frm.set_value('status', 'Fail');
            } else if (has_blocked) {
                frm.set_value('status', 'Blocked');
            } else if (all_pass) {
                frm.set_value('status', 'Pass');
            }
        }
    }
});

frappe.ui.form.on('Test Result', {
    step_status(frm, cdt, cdn) {
        // Update row styling based on status
        let row = locals[cdt][cdn];
        let grid_row = frm.fields_dict.test_results.grid.grid_rows_by_docname[cdn];
        
        if (grid_row) {
            grid_row.wrapper.removeClass('success-row fail-row blocked-row');
            
            if (row.step_status === 'Pass') {
                grid_row.wrapper.addClass('success-row');
            } else if (row.step_status === 'Fail') {
                grid_row.wrapper.addClass('fail-row');
            } else if (row.step_status === 'Blocked') {
                grid_row.wrapper.addClass('blocked-row');
            }
        }
    }
});

function mark_all_steps(frm, status) {
    if (frm.doc.test_results && frm.doc.test_results.length > 0) {
        frm.doc.test_results.forEach(row => {
            row.step_status = status;
        });
        frm.refresh_field('test_results');
        frappe.show_alert({
            message: __('All steps marked as {0}', [status]),
            indicator: status === 'Pass' ? 'green' : status === 'Fail' ? 'red' : 'orange'
        });
    }
}