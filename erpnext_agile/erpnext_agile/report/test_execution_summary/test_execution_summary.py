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
            "fieldname": "test_cycle",
            "label": _("Test Cycle"),
            "fieldtype": "Link",
            "options": "Test Cycle",
            "width": 200
        },
        {
            "fieldname": "project",
            "label": _("Project"),
            "fieldtype": "Link",
            "options": "Project",
            "width": 150
        },
        {
            "fieldname": "total",
            "label": _("Total Tests"),
            "fieldtype": "Int",
            "width": 100
        },
        {
            "fieldname": "passed",
            "label": _("Passed"),
            "fieldtype": "Int",
            "width": 80
        },
        {
            "fieldname": "failed",
            "label": _("Failed"),
            "fieldtype": "Int",
            "width": 80
        },
        {
            "fieldname": "blocked",
            "label": _("Blocked"),
            "fieldtype": "Int",
            "width": 80
        },
        {
            "fieldname": "not_run",
            "label": _("Not Run"),
            "fieldtype": "Int",
            "width": 80
        },
        {
            "fieldname": "pass_rate",
            "label": _("Pass Rate (%)"),
            "fieldtype": "Percent",
            "width": 120
        },
        {
            "fieldname": "status",
            "label": _("Status"),
            "fieldtype": "Data",
            "width": 100
        }
    ]

def get_data(filters):
    conditions = get_conditions(filters)
    
    cycles = frappe.db.sql("""
        SELECT 
            tc.name as test_cycle,
            tc.project,
            tc.status,
            tc.total_tests as total,
            tc.passed_tests as passed,
            tc.failed_tests as failed,
            tc.blocked_tests as blocked,
            tc.not_run_tests as not_run,
            tc.pass_rate
        FROM `tabTest Cycle` tc
        WHERE 1=1 {conditions}
        ORDER BY tc.creation DESC
    """.format(conditions=conditions), filters, as_dict=1)
    
    return cycles

def get_conditions(filters):
    conditions = ""
    
    if filters.get("project"):
        conditions += " AND tc.project = %(project)s"
    
    if filters.get("status"):
        conditions += " AND tc.status = %(status)s"
    
    if filters.get("from_date"):
        conditions += " AND tc.planned_start_date >= %(from_date)s"
    
    if filters.get("to_date"):
        conditions += " AND tc.planned_end_date <= %(to_date)s"
    
    return conditions

def get_chart_data(data, filters):
    if not data:
        return None
    
    labels = [d.get("test_cycle") for d in data]
    
    return {
        "data": {
            "labels": labels[:10],  # Limit to 10 most recent
            "datasets": [
                {
                    "name": "Passed",
                    "values": [d.get("passed", 0) for d in data[:10]]
                },
                {
                    "name": "Failed",
                    "values": [d.get("failed", 0) for d in data[:10]]
                },
                {
                    "name": "Blocked",
                    "values": [d.get("blocked", 0) for d in data[:10]]
                },
                {
                    "name": "Not Run",
                    "values": [d.get("not_run", 0) for d in data[:10]]
                }
            ]
        },
        "type": "bar",
        "colors": ["#28a745", "#dc3545", "#ffc107", "#6c757d"],
        "barOptions": {
            "stacked": 1
        }
    }