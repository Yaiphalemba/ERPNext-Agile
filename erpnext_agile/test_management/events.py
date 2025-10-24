# Copyright (c) 2025, Yanky and contributors
# For license information, please see license.txt

import frappe
from frappe import _

# Test Execution Events
def test_execution_on_submit(doc, method):
    """Handle test execution submission"""
    # Log activity
    log_test_activity(doc, "executed")
    
    # Send notification to watchers
    send_execution_notification(doc)

def test_execution_on_cancel(doc, method):
    """Handle test execution cancellation"""
    log_test_activity(doc, "cancelled")

# Test Cycle Events
def test_cycle_on_update(doc, method):
    """Handle test cycle updates"""
    # Check if status changed to Completed
    if doc.has_value_changed("status") and doc.status == "Completed":
        send_cycle_completion_notification(doc)

def test_cycle_validate(doc, method):
    """Validate test cycle"""
    # Check if all tests are executed before completing
    if doc.status == "Completed" and doc.not_run_tests > 0:
        frappe.throw(
            _("Cannot complete cycle with {0} tests not run").format(doc.not_run_tests)
        )

# Task Events
def task_check_test_coverage(doc, method):
    """Check if task has test coverage"""
    if doc.is_new():
        return
    
    # Only for user stories and features
    if doc.type not in ["Task", "Feature"]:
        return
    
    # Check if task has linked test cases
    has_tests = frappe.db.exists("Test Case Link", {
        "link_doctype": "Task",
        "link_name": doc.name
    })
    
    if not has_tests and doc.status not in ["Completed", "Cancelled"]:
        # Add comment suggesting to add test cases
        if not frappe.db.exists("Comment", {
            "reference_doctype": "Task",
            "reference_name": doc.name,
            "content": ["like", "%No test cases linked%"]
        }):
            doc.add_comment(
                "Comment",
                _("Note: No test cases linked to this task. Consider adding test cases for better coverage.")
            )

# Helper Functions
def log_test_activity(execution_doc, action):
    """Log test execution activity"""
    frappe.get_doc({
        "doctype": "Activity Log",
        "subject": f"Test {action}: {execution_doc.test_case}",
        "status": "Closed",
        "communication_date": frappe.utils.now(),
        "reference_doctype": "Test Execution",
        "reference_name": execution_doc.name,
        "full_name": execution_doc.executed_by
    }).insert(ignore_permissions=True)

def send_execution_notification(execution_doc):
    """Send notification for test execution"""
    # Get test case watchers
    test_case = frappe.get_doc("Test Case", execution_doc.test_case)
    
    # Get QA lead from cycle
    cycle = frappe.get_doc("Test Cycle", execution_doc.test_cycle)
    
    recipients = []
    if cycle.owner_user:
        recipients.append(cycle.owner_user)
    
    if not recipients:
        return
    
    # Prepare notification
    subject = f"Test Execution: {execution_doc.test_case} - {execution_doc.status}"
    
    message = f"""
    <h3>Test Execution Update</h3>
    <p><b>Test Case:</b> {execution_doc.test_case}</p>
    <p><b>Test Cycle:</b> {execution_doc.test_cycle}</p>
    <p><b>Status:</b> <span style="color: {'green' if execution_doc.status == 'Pass' else 'red'};">{execution_doc.status}</span></p>
    <p><b>Executed By:</b> {execution_doc.executed_by}</p>
    <p><b>Environment:</b> {execution_doc.environment}</p>
    """
    
    if execution_doc.comments:
        message += f"<p><b>Comments:</b><br>{execution_doc.comments}</p>"
    
    if execution_doc.defects:
        message += "<p><b>Linked Bugs:</b></p><ul>"
        for defect in execution_doc.defects:
            message += f"<li>{defect.bug_task} ({defect.severity})</li>"
        message += "</ul>"
    
    try:
        for recipient in recipients:
            email = frappe.db.get_value("User", recipient, "email")
            if email:
                frappe.sendmail(
                    recipients=[email],
                    subject=subject,
                    message=message,
                    delayed=True
                )
    except Exception as e:
        frappe.log_error(f"Error sending notification: {str(e)}")

def send_cycle_completion_notification(cycle_doc):
    """Send notification when cycle is completed"""
    if not cycle_doc.owner_user:
        return
    
    recipient = frappe.db.get_value("User", cycle_doc.owner_user, "email")
    if not recipient:
        return
    
    summary = cycle_doc.get_execution_summary()
    
    subject = f"Test Cycle Completed: {cycle_doc.title}"
    message = f"""
    <h3>Test Cycle Completed</h3>
    <p>The test cycle <b>{cycle_doc.title}</b> has been completed.</p>
    
    <h4>Execution Summary:</h4>
    <ul>
        <li><b>Total Tests:</b> {summary['total']}</li>
        <li><b>Passed:</b> <span style="color: green;">{summary['passed']}</span></li>
        <li><b>Failed:</b> <span style="color: red;">{summary['failed']}</span></li>
        <li><b>Blocked:</b> {summary['blocked']}</li>
        <li><b>Pass Rate:</b> {summary['pass_rate']:.2f}%</li>
    </ul>
    
    <p>Project: {cycle_doc.project}</p>
    <p>Duration: {cycle_doc.actual_start_date} to {cycle_doc.actual_end_date}</p>
    """
    
    try:
        frappe.sendmail(
            recipients=[recipient],
            subject=subject,
            message=message,
            delayed=True
        )
    except Exception as e:
        frappe.log_error(f"Error sending completion notification: {str(e)}")