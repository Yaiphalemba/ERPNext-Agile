# Copyright (c) 2025, Yanky and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import today, add_days

def update_cycle_metrics():
    """Daily job to update all active test cycle metrics"""
    active_cycles = frappe.get_all(
        "Test Cycle",
        filters={"status": "In Progress"},
        pluck="name"
    )
    
    for cycle_name in active_cycles:
        try:
            cycle = frappe.get_doc("Test Cycle", cycle_name)
            cycle.calculate_metrics()
            frappe.db.commit()
        except Exception as e:
            frappe.log_error(f"Error updating metrics for {cycle_name}: {str(e)}")

def send_test_reminders():
    """Send reminders for pending test executions"""
    # Get cycles ending in next 3 days with pending tests
    upcoming_end = add_days(today(), 3)
    
    cycles = frappe.db.sql("""
        SELECT 
            tc.name,
            tc.title,
            tc.owner_user,
            tc.project,
            tc.planned_end_date,
            tc.not_run_tests
        FROM `tabTest Cycle` tc
        WHERE tc.status = 'In Progress'
        AND tc.planned_end_date <= %s
        AND tc.not_run_tests > 0
    """, upcoming_end, as_dict=1)
    
    for cycle in cycles:
        send_reminder_email(cycle)

def send_reminder_email(cycle):
    """Send reminder email to QA lead"""
    if not cycle.owner_user:
        return
    
    # Get recipient email
    recipient = frappe.db.get_value("User", cycle.owner_user, "email")
    if not recipient:
        return
    
    # Prepare email
    subject = f"Test Cycle Reminder: {cycle.title}"
    message = f"""
    <h3>Test Cycle Reminder</h3>
    <p>Dear {cycle.owner_user},</p>
    
    <p>This is a reminder that the following test cycle is ending soon:</p>
    
    <ul>
        <li><b>Test Cycle:</b> {cycle.title}</li>
        <li><b>Project:</b> {cycle.project}</li>
        <li><b>End Date:</b> {cycle.planned_end_date}</li>
        <li><b>Pending Tests:</b> {cycle.not_run_tests}</li>
    </ul>
    
    <p>Please ensure all tests are executed before the end date.</p>
    
    <p>Best regards,<br>Test Management System</p>
    """
    
    try:
        frappe.sendmail(
            recipients=[recipient],
            subject=subject,
            message=message,
            delayed=False
        )
    except Exception as e:
        frappe.log_error(f"Error sending reminder for {cycle.name}: {str(e)}")