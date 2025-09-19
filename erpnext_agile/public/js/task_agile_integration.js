frappe.ui.form.on('Task', {
    refresh: function(frm) {
        if (frm.doc.custom_agile_issue) {
            frm.add_custom_button(__('View Agile Issue'), function() {
                frappe.set_route('Form', 'Agile Issue', frm.doc.custom_agile_issue);
            });
        }
    }
});