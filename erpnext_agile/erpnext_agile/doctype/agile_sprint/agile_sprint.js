frappe.ui.form.on('Agile Sprint', {
    refresh(frm) {
        if (frm.doc.sprint_state === "Future") {
            frm.add_custom_button(__('Start Sprint'), () => {
                frappe.call({
                    method: "erpnext_agile.api.start_sprint",
                    args: {
                        sprint_name: frm.doc.name
                    },
                    callback: function(r) {
                        if (!r.exc) {
                            frm.reload_doc();
                        }
                    }
                });
            }).addClass('btn-primary');
        }
        if (frm.doc.sprint_state === "Active") {
            frm.add_custom_button(__('Complete Sprint'), () => {
                frappe.confirm(
                    __('Are you sure you want to complete this sprint?'),
                    () => {
                        frappe.call({
                            method: "erpnext_agile.api.complete_sprint",
                            args: {
                                sprint_name: frm.doc.name
                            },
                            callback: function(r) {
                                if (!r.exc) {
                                    frappe.show_alert({
                                        message: __('Sprint completed successfully!'),
                                        indicator: 'green'
                                    });
                                    frm.reload_doc();
                                }
                            }
                        });
                    },
                    () => {
                        frappe.show_alert({
                            message: __('Sprint completion cancelled'),
                            indicator: 'orange'
                        });
                    }
                );
            }).addClass('btn-danger');
        }
    }
});
