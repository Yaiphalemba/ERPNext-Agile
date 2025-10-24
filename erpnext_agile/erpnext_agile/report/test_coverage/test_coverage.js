// Copyright (c) 2025, Yanky and contributors
// For license information, please see license.txt

frappe.query_reports["Test Coverage"] = {
    filters: [
        {
            fieldname: "project",
            label: __("Project"),
            fieldtype: "Link",
            options: "Project",
            reqd: 1
        }
    ],
    
    formatter: function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        
        if (column.fieldname === "has_test_case") {
            if (data.has_test_case) {
                value = '<span class="indicator-pill green">Yes</span>';
            } else {
                value = '<span class="indicator-pill red">No</span>';
            }
        }
        
        if (column.fieldname === "test_count") {
            let color = data.test_count > 0 ? "green" : "red";
            value = `<span style="color: ${color}; font-weight: bold;">${value}</span>`;
        }
        
        return value;
    }
};