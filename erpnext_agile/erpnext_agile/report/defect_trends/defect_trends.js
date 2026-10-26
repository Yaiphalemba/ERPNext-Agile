// Copyright (c) 2025, Yanky and contributors
// For license information, please see license.txt

frappe.query_reports["Defect Trends"] = {
    filters: [
        {
            fieldname: "project",
            label: __("Project"),
            fieldtype: "Link",
            options: "Project",
            reqd: 0
        },
        {
            fieldname: "test_cycle",
            label: __("Test Cycle"),
            fieldtype: "Link",
            options: "Test Cycle",
            reqd: 0,
            get_query: function() {
                let project = frappe.query_report.get_filter_value('project');
                if (project) {
                    return {
                        filters: {
                            'project': project
                        }
                    };
                }
            }
        },
        {
            fieldname: "severity",
            label: __("Severity"),
            fieldtype: "Select",
            options: "\nCritical\nMajor\nMinor",
            reqd: 0
        },
        {
            fieldname: "bug_status",
            label: __("Bug Status"),
            fieldtype: "Select",
            options: "\nOpen\nWorking\nPending Review\nCompleted\nCancelled",
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
        
        if (column.fieldname === "severity") {
            let color = "grey";
            if (data.severity === "Critical") {
                color = "red";
            } else if (data.severity === "Major") {
                color = "orange";
            } else if (data.severity === "Minor") {
                color = "yellow";
            }
            value = `<span class="indicator-pill ${color}">${value}</span>`;
        }
        
        if (column.fieldname === "age_days") {
            let color = data.age_days > 30 ? "red" : data.age_days > 14 ? "orange" : "green";
            value = `<span style="color: ${color}; font-weight: bold;">${value}</span>`;
        }
        
        return value;
    }
};