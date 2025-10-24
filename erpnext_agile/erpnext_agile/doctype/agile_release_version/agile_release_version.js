// Copyright (c) 2025, Yanky and contributors
// For license information, please see license.txt

frappe.ui.form.on('Agile Release Version', {
    repository: function(frm) {
        // Refresh branch query when repository changes
        frm.fields_dict.branch_name.get_query = function() {
            return {
                filters: {
                    "parent": frm.doc.repository
                }
            };
        };
        
        // Clear branch and commit_sha when repository changes
        frm.set_value('branch_name', '');
        frm.set_value('commit_sha', '');
    },
    
    branch_name: function(frm) {
        if (!frm.doc.branch_name || !frm.doc.repository) {
            frm.set_value('commit_sha', '');
            return;
        }
        else {
            frappe.call({
                method: 'erpnext_agile.erpnext_agile.doctype.agile_release_version.agile_release_version.get_branch_commit_sha',
                args: {
                    branch_name: frm.doc.branch_name,
                    repository: frm.doc.repository
                },
                callback: function(r) {
                    if (r.message) {
                        frm.set_value('commit_sha', r.message);
                    } else {
                        frm.set_value('commit_sha', '');
                    }
                }
            });
        }
    },

    refresh(frm) {
        // Set initial query for branch_name field
        frm.fields_dict.branch_name.get_query = function() {
            return {
                filters: {
                    "parent": frm.doc.repository
                }
            };
        };
        // When project changes, update filters in child tables
        frm.fields_dict.linked_tasks.grid.get_field("task").get_query = function (doc, cdt, cdn) {
            const child = locals[cdt][cdn];
            return {
                filters: {
                    project: frm.doc.project || ""
                }
            };
        };

        frm.fields_dict.linked_test_cases.grid.get_field("test_case").get_query = function (doc, cdt, cdn) {
            const child = locals[cdt][cdn];
            return {
                filters: {
                    project: frm.doc.project || ""
                }
            };
        };
    },

    project(frm) {
        // Reset child tables if project changes
        frm.clear_table("linked_tasks");
        frm.clear_table("linked_test_cases");
        frm.refresh_field("linked_tasks");
        frm.refresh_field("linked_test_cases");
    }
});