frappe.query_reports["Test Execution Summary"] = {
    filters: [
        {
            fieldname: "project",
            label: __("Project"),
            fieldtype: "Link",
            options: "Project",
            reqd: 0
        },
        {
            fieldname: "status",
            label: __("Status"),
            fieldtype: "Select",
            options: "\nNot Started\nIn Progress\nCompleted\nOn Hold",
            reqd: 0
        },
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            reqd: 0
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            reqd: 0,
            default: frappe.datetime.get_today()
        }
    ],
    
    formatter: function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        
        if (column.fieldname === "pass_rate") {
            let rate = data.pass_rate || 0;
            let color = rate >= 80 ? "green" : rate >= 50 ? "orange" : "red";
            value = `<span style="color: ${color}; font-weight: bold;">${value}</span>`;
        }
        
        if (column.fieldname === "failed" && data.failed > 0) {
            value = `<span style="color: red; font-weight: bold;">${value}</span>`;
        }
        
        if (column.fieldname === "passed" && data.passed > 0) {
            value = `<span style="color: green; font-weight: bold;">${value}</span>`;
        }
        
        return value;
    }
};