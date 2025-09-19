frappe.pages['agile-board'].on_page_load = function(wrapper) {
    let page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Agile Board',
        single_column: true
    });
    
    page.agile_board = new erpnext_agile.AgileBoard(wrapper);
};