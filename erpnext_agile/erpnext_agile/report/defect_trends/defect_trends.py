# Copyright (c) 2025, Yanky and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart_data(data, filters)
    
    return columns, data, None, chart

def get_columns():
    return [
        {
            "fieldname": "bug_task",
            "label": _("Bug"),
            "fieldtype": "Link",
            "options": "Task",
            "width": 150
        },
        {
            "fieldname": "test_case",
            "label": _("Test Case"),
            "fieldtype": "Link",
            "options": "Test Case",
            "width": 200
        },
        {
            "fieldname": "test_execution",
            "label": _("Test Execution"),
            "fieldtype": "Link",
            "options": "Test Execution",
            "width": 150
        },
        {
            "fieldname": "severity",
            "label": _("Severity"),
            "fieldtype": "Data",
            "width": 100
        },
        {
            "fieldname": "bug_status",
            "label": _("Bug Status"),
            "fieldtype": "Data",
            "width": 120
        },
        {
            "fieldname": "project",
            "label": _("Project"),
            "fieldtype": "Link",
            "options": "Project",
            "width": 150
        },
        {
            "fieldname": "created_on",
            "label": _("Created On"),
            "fieldtype": "Date",
            "width": 120
        },
        {
            "fieldname": "age_days",
            "label": _("Age (Days)"),
            "fieldtype": "Int",
            "width": 100
        }
    ]

def get_data(filters):
    conditions = get_conditions(filters)
    
    defects = frappe.db.sql("""
        SELECT 
            ted.bug_task,
            te.test_case,
            te.name as test_execution,
            ted.severity,
            t.status as bug_status,
            t.project,
            DATE(t.creation) as created_on,
            DATEDIFF(CURDATE(), DATE(t.creation)) as age_days
        FROM `tabTest Execution Defect` ted
        INNER JOIN `tabTest Execution` te ON ted.parent = te.name
        INNER JOIN `tabTask` t ON ted.bug_task = t.name
        INNER JOIN `tabTest Cycle` tc ON te.test_cycle = tc.name
        WHERE t.type = 'Bug'
        {conditions}
        ORDER BY t.creation DESC
    """.format(conditions=conditions), filters, as_dict=1)
    
    return defects

def get_conditions(filters):
    conditions = ""
    
    if filters.get("project"):
        conditions += " AND t.project = %(project)s"
    
    if filters.get("severity"):
        conditions += " AND ted.severity = %(severity)s"
    
    if filters.get("bug_status"):
        conditions += " AND t.status = %(bug_status)s"
    
    if filters.get("from_date"):
        conditions += " AND DATE(t.creation) >= %(from_date)s"
    
    if filters.get("to_date"):
        conditions += " AND DATE(t.creation) <= %(to_date)s"
    
    if filters.get("test_cycle"):
        conditions += " AND te.test_cycle = %(test_cycle)s"
    
    return conditions

def get_chart_data(data, filters):
    if not data:
        return None
    
    # Chart 1: Defects by Severity
    severity_data = {
        "Critical": len([d for d in data if d.severity == "Critical"]),
        "Major": len([d for d in data if d.severity == "Major"]),
        "Minor": len([d for d in data if d.severity == "Minor"])
    }
    
    return {
        "data": {
            "labels": list(severity_data.keys()),
            "datasets": [
                {
                    "name": "Defects",
                    "values": list(severity_data.values())
                }
            ]
        },
        "type": "bar",
        "colors": ["#dc3545", "#fd7e14", "#ffc107"]
    }