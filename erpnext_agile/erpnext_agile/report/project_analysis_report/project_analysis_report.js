// Copyright (c) 2026, Yanky and contributors
// For license information, please see license.txt

frappe.query_reports["Project Analysis Report"] = {
	"filters": [
		{
			"default": null,
			"fieldname": "project",
			"fieldtype": "Link",
			"label": "Project",
			"options": "Project",
			"on_change": function() {
                // Clear the sprint filter if the project changes
                frappe.query_report.set_filter_value('sprint', "");
            }
		},
		{
			"default": null,
			"fieldname": "sprint",
			"fieldtype": "Link",
			"label": "Sprint",
			"options": "Agile Sprint",
			"get_query": function() {
                const project = frappe.query_report.get_filter_value('project');
                if (!project) {
                    return {};
                }
                return {
                    filters: {
                        "project": project 
                    }
                };
			},
			"depends_on": "project"
		},
		{
			"default": null,
			"fieldname": "from_date",
			"fieldtype": "Date",
			"label": "From Date"
		},
		{
			"default": null,
			"fieldname": "to_date",
			"fieldtype": "Date",
			"label": "To Date"
		},
		{
			"default": null,
			"fieldname": "employee",
			"fieldtype": "Link",
			"label": "Employee",
			"options": "User"
		},
		{
			"default": "Overall",
			"fieldname": "view",
			"fieldtype": "Select",
			"label": "View",
			"options": "Overall\nPer Project"
		}
	]
};
