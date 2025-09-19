import frappe
from frappe.utils import get_url_to_form

def send_issue_notification(issue_name, event, changed_field=None, old_value=None, new_value=None):
    """Send notification for issue-related events"""
    issue = frappe.get_doc("Agile Issue", issue_name)
    agile_project = frappe.get_doc("Agile Project", issue.agile_project)
    
    # Determine recipients
    recipients = get_issue_notification_recipients(issue, agile_project)
    if not recipients:
        return
    
    # Prepare notification content
    subject, message = get_issue_notification_content(issue, event, changed_field, old_value, new_value)
    
    # Send in-app notification
    send_in_app_notification(subject, message, recipients, issue)
    
    # Send email notification if enabled in project settings
    if agile_project.get("enable_email_notifications", 1):
        send_email_notification(subject, message, recipients, issue)

def send_sprint_notification(sprint_name, event):
    """Send notification for sprint-related events"""
    sprint = frappe.get_doc("Agile Sprint", sprint_name)
    agile_project = frappe.get_doc("Agile Project", sprint.agile_project)
    
    # Determine recipients
    recipients = get_sprint_notification_recipients(sprint, agile_project)
    if not recipients:
        return
    
    # Prepare notification content
    subject, message = get_sprint_notification_content(sprint, event)
    
    # Send in-app notification
    send_in_app_notification(subject, message, recipients, sprint)
    
    # Send email notification if enabled
    if agile_project.get("enable_email_notifications", 1):
        send_email_notification(subject, message, recipients, sprint)

def get_issue_notification_recipients(issue, agile_project):
    """Get recipients for issue notifications"""
    recipients = set()
    
    # Add assignee
    if issue.assignee:
        recipients.add(issue.assignee)
    
    # Add reporter
    if issue.reporter:
        recipients.add(issue.reporter)
    
    # Add project lead
    if agile_project.project_lead:
        recipients.add(agile_project.project_lead)
    
    # Add watchers
    for watcher in issue.watchers or []:
        if watcher.user:
            recipients.add(watcher.user)
    
    # Remove None or empty entries
    return [r for r in recipients if r and frappe.db.exists("User", r)]

def get_sprint_notification_recipients(sprint, agile_project):
    """Get recipients for sprint notifications"""
    recipients = set()
    
    # Add project lead
    if agile_project.project_lead:
        recipients.add(agile_project.project_lead)
    
    # Add users assigned to issues in this sprint
    issue_assignees = frappe.get_all(
        "Agile Issue",
        filters={"current_sprint": sprint.name},
        fields=["assignee"],
        distinct=True
    )
    for assignee in issue_assignees:
        if assignee.assignee:
            recipients.add(assignee.assignee)
    
    # Remove None or empty entries
    return [r for r in recipients if r and frappe.db.exists("User", r)]

def get_issue_notification_content(issue, event, changed_field=None, old_value=None, new_value=None):
    """Generate subject and message for issue notifications"""
    issue_url = get_url_to_form("Agile Issue", issue.name)
    subject = f"Issue {issue.issue_key}: {issue.summary}"
    
    if event == "created":
        message = f"""
New issue created in project {issue.agile_project}.
<br><b>Issue:</b> <a href="{issue_url}">{issue.issue_key}</a>
<br><b>Summary:</b> {issue.summary}
<br><b>Type:</b> {issue.issue_type}
<br><b>Priority:</b> {issue.priority}
<br><b>Assignee:</b> {issue.assignee or 'Unassigned'}
"""
    elif event == "updated" and changed_field:
        message = f"""
Issue updated in project {issue.agile_project}.
<br><b>Issue:</b> <a href="{issue_url}">{issue.issue_key}</a>
<br><b>Summary:</b> {issue.summary}
<br><b>{changed_field.replace('_', ' ').title()}:</b> {old_value or 'None'} → {new_value or 'None'}
"""
    else:
        message = f"""
Issue updated in project {issue.agile_project}.
<br><b>Issue:</b> <a href="{issue_url}">{issue.issue_key}</a>
<br><b>Summary:</b> {issue.summary}
"""
    
    return subject, message.strip()

def get_sprint_notification_content(sprint, event):
    """Generate subject and message for sprint notifications"""
    sprint_url = get_url_to_form("Agile Sprint", sprint.name)
    subject = f"Sprint {sprint.sprint_name}: {event.title()}"
    
    if event == "started":
        message = f"""
Sprint started in project {sprint.agile_project}.
<br><b>Sprint:</b> <a href="{sprint_url}">{sprint.sprint_name}</a>
<br><b>Goal:</b> {sprint.sprint_goal or 'Not specified'}
<br><b>Start Date:</b> {sprint.start_date}
<br><b>End Date:</b> {sprint.end_date}
"""
    elif event == "completed":
        message = f"""
Sprint completed in project {sprint.agile_project}.
<br><b>Sprint:</b> <a href="{sprint_url}">{sprint.sprint_name}</a>
<br><b>Total Points:</b> {sprint.total_points or 0}
<br><b>Completed Points:</b> {sprint.completed_points or 0}
"""
    else:
        message = f"""
Sprint {event} in project {sprint.agile_project}.
<br><b>Sprint:</b> <a href="{sprint_url}">{sprint.sprint_name}</a>
"""
    
    return subject, message.strip()

def send_in_app_notification(subject, message, recipients, doc):
    """Send real-time in-app notification"""
    try:
        frappe.publish_realtime(
            event="agile_notification",
            message={
                "subject": subject,
                "message": message,
                "doctype": doc.doctype,
                "docname": doc.name
            },
            user=recipients
        )
    except Exception as e:
        frappe.log_error(f"Failed to send in-app notification: {str(e)}")

def send_email_notification(subject, message, recipients, doc):
    """Send email notification"""
    try:
        frappe.sendmail(
            recipients=recipients,
            subject=subject,
            message=message,
            reference_doctype=doc.doctype,
            reference_name=doc.name,
            template="agile_notification",  # Optional: Use a custom template
            args={
                "doc": doc,
                "url": get_url_to_form(doc.doctype, doc.name)
            }
        )
    except Exception as e:
        frappe.log_error(f"Failed to send email notification: {str(e)}")

def on_issue_update(doc, method):
    """Hook for Agile Issue updates"""
    if method == "on_update":
        # Check for specific field changes
        changed_fields = doc.get_changed()
        for field in changed_fields:
            old_value, new_value = changed_fields[field]
            if field in ["status", "assignee", "priority", "current_sprint"]:
                send_issue_notification(
                    doc.name,
                    "updated",
                    field,
                    old_value,
                    new_value
                )
    elif method == "after_insert":
        send_issue_notification(doc.name, "created")

def on_sprint_update(doc, method):
    """Hook for Agile Sprint updates"""
    if method == "on_update":
        if doc.has_value_changed("sprint_state"):
            old_state, new_state = doc.get_change("sprint_state")
            if new_state == "Active":
                send_sprint_notification(doc.name, "started")
            elif new_state == "Completed":
                send_sprint_notification(doc.name, "completed")

def setup_notification_hooks():
    """Setup hooks for notifications"""
    # These would typically be defined in hooks.py, but included here for completeness
    frappe.get_hooks().setdefault("doc_events", {}).setdefault("Agile Issue", {
        "after_insert": "erpnext_agile.notifications.on_issue_update",
        "on_update": "erpnext_agile.notifications.on_issue_update"
    })
    frappe.get_hooks().setdefault("doc_events", {}).setdefault("Agile Sprint", {
        "on_update": "erpnext_agile.notifications.on_sprint_update"
    })