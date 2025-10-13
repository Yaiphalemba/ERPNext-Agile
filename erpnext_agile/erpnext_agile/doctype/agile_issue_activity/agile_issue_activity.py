import frappe
from frappe.model.document import Document
import json


class AgileIssueActivity(Document):
    def before_insert(self):
        """Set timestamp and user"""
        if not self.timestamp:
            self.timestamp = frappe.utils.now_datetime()
        if not self.user:
            self.user = frappe.session.user


def log_issue_activity(issue, action, data=None, comment=None):
    """
    Helper function to log activity for an agile issue.
    
    Args:
        issue: Task document name
        action: Activity description (e.g., "created this issue", "set status to In Progress")
        data: Optional dict of additional data to store as JSON
        comment: Optional comment text
    """
    activity_doc = frappe.get_doc({
        "doctype": "Agile Issue Activity",
        "issue": issue,
        "activity_type": determine_activity_type(action),
        "user": frappe.session.user,
        "timestamp": frappe.utils.now_datetime(),
        "data": json.dumps(data) if data else None,
        "comment": comment
    })
    
    activity_doc.insert(ignore_permissions=True)
    return activity_doc


def determine_activity_type(action):
    """Determine activity type from action string"""
    action_lower = action.lower()
    
    if "created" in action_lower:
        return "created"
    elif "status" in action_lower or "transitioned" in action_lower:
        return "status_changed"
    elif "assigned" in action_lower and "watcher" not in action_lower:
        return "assigned"
    elif "unassigned" in action_lower and "watcher" not in action_lower:
        return "unassigned"
    elif "added watcher" in action_lower:
        return "watcher_added"
    elif "removed watcher" in action_lower:
        return "watcher_removed"
    elif "comment" in action_lower:
        return "commented"
    elif "work" in action_lower or "logged" in action_lower:
        return "work_logged"
    elif "estimate" in action_lower or "estimation" in action_lower:
        return "estimation_changed"
    elif "sprint" in action_lower and "added" in action_lower:
        return "sprint_added"
    elif "sprint" in action_lower and "removed" in action_lower:
        return "sprint_removed"
    elif "priority" in action_lower:
        return "status_changed"
    else:
        return "commented"