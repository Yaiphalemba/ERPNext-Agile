# erpnext_agile/notifications.py (Updated for native Task doctype)
import frappe
from frappe.utils import get_url_to_form

def send_task_notification(task_name, event, changed_field=None, old_value=None, new_value=None):
    """Send notification for task-related events in agile projects"""
    task = frappe.get_doc("Task", task_name)
    
    # Only send notifications for agile tasks
    if not is_agile_task(task):
        return
    
    project = frappe.get_doc("Project", task.project)
    
    # Check if notifications are enabled for this project
    if not getattr(project, 'enable_email_notifications', True):
        return
    
    # Determine recipients
    recipients = get_task_notification_recipients(task, project)
    if not recipients:
        return
    
    # Prepare notification content
    subject, message = get_task_notification_content(task, event, changed_field, old_value, new_value)
    
    # Send in-app notification
    send_in_app_notification(subject, message, recipients, task)
    
    # Send email notification if enabled in project settings
    if getattr(project, 'enable_email_notifications', True):
        send_email_notification(subject, message, recipients, task)

def send_sprint_notification(sprint_name, event):
    """Send notification for sprint-related events"""
    sprint = frappe.get_doc("Agile Sprint", sprint_name)
    project = frappe.get_doc("Project", sprint.project)
    
    # Determine recipients
    recipients = get_sprint_notification_recipients(sprint, project)
    if not recipients:
        return
    
    # Prepare notification content
    subject, message = get_sprint_notification_content(sprint, event)
    
    # Send in-app notification
    send_in_app_notification(subject, message, recipients, sprint)
    
    # Send email notification if enabled
    if getattr(project, 'enable_email_notifications', True):
        send_email_notification(subject, message, recipients, sprint)

def is_agile_task(task):
    """Check if task belongs to an agile project"""
    if hasattr(task, 'project') and task.project:
        project = frappe.get_cached_doc("Project", task.project)
        return getattr(project, 'enable_agile', False)
    return False

def get_task_notification_recipients(task, project):
    """Get recipients for task notifications"""
    recipients = set()
    
    # Add assignee
    if hasattr(task, 'assigned_to') and task.assigned_to:
        recipients.add(task.assigned_to)
    
    # Add reporter
    if hasattr(task, 'reporter') and task.reporter:
        recipients.add(task.reporter)
    
    # Add project lead
    if hasattr(project, 'project_lead') and project.project_lead:
        recipients.add(project.project_lead)
    
    # Add watchers from task
    if hasattr(task, 'watchers') and task.watchers:
        for watcher in task.watchers:
            if hasattr(watcher, 'user') and watcher.user:
                recipients.add(watcher.user)
    
    # Remove None, empty entries, and current user (don't notify yourself)
    current_user = frappe.session.user
    filtered_recipients = []
    for recipient in recipients:
        if (recipient and 
            recipient != current_user and 
            recipient != "Administrator" and
            frappe.db.exists("User", recipient)):
            filtered_recipients.append(recipient)
    
    return filtered_recipients

def get_sprint_notification_recipients(sprint, project):
    """Get recipients for sprint notifications"""
    recipients = set()
    
    # Add project lead
    if hasattr(project, 'project_lead') and project.project_lead:
        recipients.add(project.project_lead)
    
    # Add users assigned to tasks in this sprint
    task_assignees = frappe.get_all(
        "Task",
        filters={"current_sprint": sprint.name, "project": sprint.project},
        fields=["assigned_to"],
        distinct=True
    )
    for assignee_data in task_assignees:
        if assignee_data.assigned_to:
            recipients.add(assignee_data.assigned_to)
    
    # Remove None, empty entries, and Administrator
    filtered_recipients = []
    for recipient in recipients:
        if (recipient and 
            recipient != "Administrator" and
            frappe.db.exists("User", recipient)):
            filtered_recipients.append(recipient)
    
    return filtered_recipients

def get_task_notification_content(task, event, changed_field=None, old_value=None, new_value=None):
    """Generate subject and message for task notifications"""
    task_url = get_url_to_form("Task", task.name)
    issue_key = getattr(task, 'issue_key', None) or task.name
    subject = f"Task {issue_key}: {task.subject}"
    
    if event == "created":
        message = f"""
New task created in project {task.project}.
<br><b>Task:</b> <a href="{task_url}">{issue_key}</a>
<br><b>Subject:</b> {task.subject}
<br><b>Type:</b> {getattr(task, 'issue_type', 'Task')}
<br><b>Priority:</b> {getattr(task, 'issue_priority', 'Medium')}
<br><b>Assignee:</b> {getattr(task, 'assigned_to', 'Unassigned')}
"""
    elif event == "updated" and changed_field:
        field_display_name = get_field_display_name(changed_field)
        message = f"""
Task updated in project {task.project}.
<br><b>Task:</b> <a href="{task_url}">{issue_key}</a>
<br><b>Subject:</b> {task.subject}
<br><b>{field_display_name}:</b> {old_value or 'None'} → {new_value or 'None'}
"""
    else:
        message = f"""
Task updated in project {task.project}.
<br><b>Task:</b> <a href="{task_url}">{issue_key}</a>
<br><b>Subject:</b> {task.subject}
"""
    
    return subject, message.strip()

def get_field_display_name(field_name):
    """Convert field name to display name"""
    field_mapping = {
        "status": "Status",
        "assigned_to": "Assignee",
        "issue_priority": "Priority",
        "issue_type": "Issue Type",
        "current_sprint": "Sprint",
        "story_points": "Story Points",
        "description": "Description"
    }
    return field_mapping.get(field_name, field_name.replace('_', ' ').title())

def get_sprint_notification_content(sprint, event):
    """Generate subject and message for sprint notifications"""
    sprint_url = get_url_to_form("Agile Sprint", sprint.name)
    subject = f"Sprint {sprint.sprint_name}: {event.title()}"
    
    if event == "started":
        message = f"""
Sprint started in project {sprint.project}.
<br><b>Sprint:</b> <a href="{sprint_url}">{sprint.sprint_name}</a>
<br><b>Goal:</b> {getattr(sprint, 'sprint_goal', 'Not specified')}
<br><b>Start Date:</b> {getattr(sprint, 'start_date', 'Not specified')}
<br><b>End Date:</b> {getattr(sprint, 'end_date', 'Not specified')}
"""
    elif event == "completed":
        message = f"""
Sprint completed in project {sprint.project}.
<br><b>Sprint:</b> <a href="{sprint_url}">{sprint.sprint_name}</a>
<br><b>Total Points:</b> {getattr(sprint, 'total_points', 0)}
<br><b>Completed Points:</b> {getattr(sprint, 'completed_points', 0)}
"""
    else:
        message = f"""
Sprint {event} in project {sprint.project}.
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
                "docname": doc.name,
                "timestamp": frappe.utils.now()
            },
            user=recipients
        )
    except Exception as e:
        frappe.log_error(f"Failed to send in-app notification: {str(e)}", "In-App Notification Error")

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
        frappe.log_error(f"Failed to send email notification: {str(e)}", "Email Notification Error")

def on_task_update(doc, method):
    """Hook for Task updates in agile projects"""
    if method == "on_update" and is_agile_task(doc):
        # Check for specific field changes
        if hasattr(doc, '_doc_before_save'):
            old_doc = doc._doc_before_save
            
            # Check important fields for changes
            important_fields = ['status', 'assigned_to', 'issue_priority', 'current_sprint', 'story_points']
            
            for field in important_fields:
                old_value = getattr(old_doc, field, None) if old_doc else None
                new_value = getattr(doc, field, None)
                
                if old_value != new_value:
                    send_task_notification(
                        doc.name,
                        "updated",
                        field,
                        old_value,
                        new_value
                    )
                    break  # Send only one notification per update
    elif method == "after_insert" and is_agile_task(doc):
        send_task_notification(doc.name, "created")

def on_sprint_update(doc, method):
    """Hook for Agile Sprint updates"""
    if method == "on_update":
        if hasattr(doc, '_doc_before_save'):
            old_doc = doc._doc_before_save
            old_state = getattr(old_doc, 'sprint_state', None) if old_doc else None
            new_state = getattr(doc, 'sprint_state', None)
            
            if old_state != new_state:
                if new_state == "Active":
                    send_sprint_notification(doc.name, "started")
                elif new_state == "Completed":
                    send_sprint_notification(doc.name, "completed")

@frappe.whitelist()
def add_task_watcher(task_name, user):
    """Add a watcher to a task"""
    try:
        task = frappe.get_doc("Task", task_name)
        
        # Check if user already watching
        if hasattr(task, 'watchers') and task.watchers:
            for watcher in task.watchers:
                if hasattr(watcher, 'user') and watcher.user == user:
                    return {"message": "User is already watching this task"}
        
        # Add new watcher
        task.append("watchers", {"user": user})
        task.save()
        
        return {"message": f"Added {user} as watcher"}
    except Exception as e:
        frappe.throw(f"Failed to add watcher: {str(e)}")

@frappe.whitelist()
def remove_task_watcher(task_name, user):
    """Remove a watcher from a task"""
    try:
        task = frappe.get_doc("Task", task_name)
        
        # Find and remove watcher
        if hasattr(task, 'watchers') and task.watchers:
            for i, watcher in enumerate(task.watchers):
                if hasattr(watcher, 'user') and watcher.user == user:
                    del task.watchers[i]
                    task.save()
                    return {"message": f"Removed {user} from watchers"}
        
        return {"message": "User was not watching this task"}
    except Exception as e:
        frappe.throw(f"Failed to remove watcher: {str(e)}")

def notify_task_assignment(task_name, old_assignee, new_assignee):
    """Send notification when task assignment changes"""
    try:
        task = frappe.get_doc("Task", task_name)
        
        if not is_agile_task(task):
            return
        
        # Notify old assignee about unassignment
        if old_assignee and old_assignee != new_assignee:
            subject = f"Task unassigned: {getattr(task, 'issue_key', task.name)}"
            message = f"You have been unassigned from task: {task.subject}"
            send_in_app_notification(subject, message, [old_assignee], task)
        
        # Notify new assignee about assignment
        if new_assignee and new_assignee != old_assignee:
            subject = f"Task assigned: {getattr(task, 'issue_key', task.name)}"
            message = f"You have been assigned to task: {task.subject}"
            send_in_app_notification(subject, message, [new_assignee], task)
            
            # Send email notification too
            project = frappe.get_cached_doc("Project", task.project)
            if getattr(project, 'enable_email_notifications', True):
                send_email_notification(subject, message, [new_assignee], task)
    except Exception as e:
        frappe.log_error(f"Failed to notify task assignment: {str(e)}", "Task Assignment Notification Error")

def setup_notification_hooks():
    """Setup hooks for notifications - called from hooks.py"""
    return {
        "doc_events": {
            "Task": {
                "after_insert": "erpnext_agile.notifications.on_task_update",
                "on_update": "erpnext_agile.notifications.on_task_update"
            },
            "Agile Sprint": {
                "on_update": "erpnext_agile.notifications.on_sprint_update"
            }
        }
    }