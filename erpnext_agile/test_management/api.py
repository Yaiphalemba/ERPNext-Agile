# Copyright (c) 2025, Yanky and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import now_datetime

@frappe.whitelist()
def create_test_execution(test_case, test_cycle, assigned_to=None, environment="Dev", build_version=None):
    """Create a test execution from test case"""
    # Validate inputs
    if not frappe.db.exists("Test Case", test_case):
        frappe.throw(_("Invalid Test Case"))
    
    if not frappe.db.exists("Test Cycle", test_cycle):
        frappe.throw(_("Invalid Test Cycle"))
    
    # Create execution
    execution = frappe.get_doc({
        "doctype": "Test Execution",
        "test_case": test_case,
        "test_cycle": test_cycle,
        "executed_by": assigned_to or frappe.session.user,
        "execution_date": now_datetime(),
        "status": "Not Run",
        "environment": environment,
        "build_version": build_version
    })
    
    execution.insert()
    
    return execution.name

@frappe.whitelist()
def bulk_create_executions(test_cycle):
    """Create test executions for all test cases in a cycle"""
    if not frappe.db.exists("Test Cycle", test_cycle):
        frappe.throw(_("Invalid Test Cycle"))
    
    cycle = frappe.get_doc("Test Cycle", test_cycle)
    
    if not cycle.test_cases:
        frappe.throw(_("No test cases found in this cycle"))
    
    created_count = 0
    
    for item in cycle.test_cases:
        # Check if execution already exists
        existing = frappe.db.exists("Test Execution", {
            "test_cycle": test_cycle,
            "test_case": item.test_case
        })
        
        if not existing:
            execution = frappe.get_doc({
                "doctype": "Test Execution",
                "test_case": item.test_case,
                "test_cycle": test_cycle,
                "executed_by": item.assigned_to or frappe.session.user,
                "execution_date": now_datetime(),
                "status": "Not Run",
                "environment": "Dev"
            })
            
            execution.insert()
            created_count += 1
    
    return created_count

@frappe.whitelist()
def get_test_execution_summary(test_cycle):
    """Get execution summary for a test cycle"""
    if not frappe.db.exists("Test Cycle", test_cycle):
        frappe.throw(_("Invalid Test Cycle"))
    
    cycle = frappe.get_doc("Test Cycle", test_cycle)
    return cycle.get_execution_summary()

@frappe.whitelist()
def clone_test_case(source_name):
    """Clone a test case"""
    if not frappe.db.exists("Test Case", source_name):
        frappe.throw(_("Invalid Test Case"))
    
    source = frappe.get_doc("Test Case", source_name)
    return source.clone_test_case()

@frappe.whitelist()
def get_test_coverage(project):
    """Get test coverage statistics for a project"""
    if not frappe.db.exists("Project", project):
        frappe.throw(_("Invalid Project"))
    
    # Get total tasks
    total_tasks = frappe.db.count("Task", {
        "project": project,
        "is_group": 0
    })
    
    # Get tasks with linked test cases
    linked_tasks = frappe.db.sql("""
        SELECT DISTINCT tcl.link_name
        FROM `tabTest Case Link` tcl
        INNER JOIN `tabTest Case` tc ON tcl.parent = tc.name
        WHERE tcl.link_doctype = 'Task'
        AND tc.project = %s
        AND tc.status = 'Active'
    """, project)
    
    tasks_with_tests = len(linked_tasks)
    coverage_percentage = (tasks_with_tests / total_tasks * 100) if total_tasks > 0 else 0
    
    return {
        "total_tasks": total_tasks,
        "tasks_with_tests": tasks_with_tests,
        "tasks_without_tests": total_tasks - tasks_with_tests,
        "coverage_percentage": coverage_percentage
    }

@frappe.whitelist()
def get_defect_metrics(test_cycle=None, project=None):
    """Get defect metrics"""
    filters = {}
    
    if test_cycle:
        filters["test_cycle"] = test_cycle
    
    if project and not test_cycle:
        # Get all cycles for the project
        cycles = frappe.get_all("Test Cycle", filters={"project": project}, pluck="name")
        if cycles:
            filters["test_cycle"] = ["in", cycles]
    
    # Get all defects
    defects = frappe.db.sql("""
        SELECT 
            ted.bug_task,
            ted.severity,
            t.status as bug_status,
            te.test_case,
            te.execution_date
        FROM `tabTest Execution Defect` ted
        INNER JOIN `tabTest Execution` te ON ted.parent = te.name
        INNER JOIN `tabTask` t ON ted.bug_task = t.name
        WHERE t.type = 'Bug'
        {conditions}
        ORDER BY te.execution_date DESC
    """.format(
        conditions="AND te.test_cycle = %(test_cycle)s" if test_cycle else ""
    ), filters, as_dict=1)
    
    # Calculate metrics
    total_defects = len(defects)
    open_defects = len([d for d in defects if d.bug_status not in ["Closed", "Completed"]])
    closed_defects = total_defects - open_defects
    
    by_severity = {
        "Critical": len([d for d in defects if d.severity == "Critical"]),
        "Major": len([d for d in defects if d.severity == "Major"]),
        "Minor": len([d for d in defects if d.severity == "Minor"])
    }
    
    return {
        "total_defects": total_defects,
        "open_defects": open_defects,
        "closed_defects": closed_defects,
        "by_severity": by_severity,
        "defects": defects
    }

@frappe.whitelist()
def get_test_execution_trend(project, days=30):
    """Get test execution trend for the last N days"""
    from frappe.utils import add_days, today
    
    start_date = add_days(today(), -days)
    
    trend_data = frappe.db.sql("""
        SELECT 
            DATE(te.execution_date) as date,
            COUNT(*) as total,
            SUM(CASE WHEN te.status = 'Pass' THEN 1 ELSE 0 END) as passed,
            SUM(CASE WHEN te.status = 'Fail' THEN 1 ELSE 0 END) as failed,
            SUM(CASE WHEN te.status = 'Blocked' THEN 1 ELSE 0 END) as blocked
        FROM `tabTest Execution` te
        INNER JOIN `tabTest Cycle` tc ON te.test_cycle = tc.name
        WHERE tc.project = %s
        AND te.docstatus = 1
        AND DATE(te.execution_date) >= %s
        GROUP BY DATE(te.execution_date)
        ORDER BY date
    """, (project, start_date), as_dict=1)
    
    return trend_data

@frappe.whitelist()
def link_test_case_to_task(test_case, task):
    """Link a test case to a task"""
    if not frappe.db.exists("Test Case", test_case):
        frappe.throw(_("Invalid Test Case"))
    
    if not frappe.db.exists("Task", task):
        frappe.throw(_("Invalid Task"))
    
    test_case_doc = frappe.get_doc("Test Case", test_case)
    
    # Check if already linked
    for link in test_case_doc.linked_items:
        if link.link_doctype == "Task" and link.link_name == task:
            frappe.throw(_("Test Case is already linked to this Task"))
    
    test_case_doc.append("linked_items", {
        "link_doctype": "Task",
        "link_name": task
    })
    
    test_case_doc.save()
    
    return test_case_doc.name