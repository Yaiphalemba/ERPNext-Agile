frappe.listview_settings['Task'] = {
    onload: function(listview) {
        if (listview.page.fields_dict['current_sprint']) {
            
            listview.page.fields_dict['current_sprint'].get_query = function() {
                let selected_project = listview.page.fields_dict['project'] ? listview.page.fields_dict['project'].get_value() : null;

                if (selected_project) {
                    return {
                        filters: {
                            'project': selected_project
                        }
                    };
                }
                
                return {};
            };
        }
    }
};