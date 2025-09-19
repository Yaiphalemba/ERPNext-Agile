frappe.ui.form.on('Project', {
    refresh: function(frm) {
        if (frm.doc.custom_agile_project) {
            frm.add_custom_button(__('View Agile Project'), function() {
                frappe.set_route('Form', 'Agile Project', frm.doc.custom_agile_project);
            });
        }
    }
});