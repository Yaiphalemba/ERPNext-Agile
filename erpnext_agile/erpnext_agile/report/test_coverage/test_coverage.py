# Copyright (c) 2025, Yanky and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
    if not filters.get("project"):
        frappe.throw(_("Please select a Project"))
    
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart_data(data, filters)
    
    return columns, data, None, chart

def get_columns():
    return [
        {
            "fieldname": "task",
            "label": _("Task"),
            "fieldtype": "Link",
            "options": "Task",
            "width": 200
        },
        {
            "fieldname": "task_type",
            "label": _("Type"),
            "fieldtype": "Data",
            "width": 100
        },
        {
            "fieldname": "priority",
            "label": _("Priority"),
            "fieldtype": "Data",
            "width": 100
        },
        {
            "fieldname": "has_test_case",
            "label": _("Has Test Case"),
            "fieldtype": "Check",
            "width": 120
        },
        {
            "fieldname": "test_cases",
            "label": _("Test Cases"),
            "fieldtype": "Data",
            "width": 300
        },
        {
            "fieldname": "test_count",
            "label": _("Test Count"),
            "fieldtype": "Int",
            "width": 100
        }
    ]

def get_data(filters):
    project = filters.get("project")
    
    # Get all tasks
    tasks = frappe.get_all(
        "Task",
        filters={
            "project": project,
            "is_group": 0
        },
        fields=["name", "subject", "type", "priority"]
    )
    
    data = []
    
    for task in tasks:
        # Get linked test cases
        test_cases = frappe.db.sql("""
            SELECT tc.name, tc.title
            FROM `tabTest Case Link` tcl
            INNER JOIN `tabTest Case` tc ON tcl.parent = tc.name
            WHERE tcl.link_doctype = 'Task'
            AND tcl.link_name = %s
            AND tc.status = 'Active'
        """, task.name, as_dict=1)
        
        test_case_names = ", ".join([tc.title for tc in test_cases])
        
        data.append({
            "task": task.name,
            "task_type": task.type or "Task",
            "priority": task.priority or "Medium",
            "has_test_case": 1 if test_cases else 0,
            "test_cases": test_case_names or "No test cases",
            "test_count": len(test_cases)
        })
    
    return data

def get_chart_data(data, filters):
    if not data:
        return None
    
    with_tests = len([d for d in data if d["has_test_case"]])
    without_tests = len(data) - with_tests
    coverage_percentage = (with_tests / len(data) * 100) if data else 0
    
    return {
        "data": {
            "labels": ["With Tests", "Without Tests"],
            "datasets": [
                {
                    "name": "Tasks",
                    "values": [with_tests, without_tests]
                }
            ]
        },
        "type": "donut",
        "colors": ["#28a745", "#dc3545"],
        "title": f"Test Coverage: {coverage_percentage:.1f}%"
    }