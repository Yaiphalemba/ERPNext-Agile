# erpnext_agile/overrides/task.py
import frappe
from frappe import _
import re
from erpnext.projects.doctype.task.task import Task
from erpnext_agile.erpnext_agile.doctype.agile_issue_activity.agile_issue_activity import (
    log_issue_activity,
)

class AgileTask(Task):
    def after_insert(self):
        """Log creation activity"""
        if self.is_agile:
            log_issue_activity(self.name, "created this issue")
    
    def validate(self):
        super().validate()
        if self.is_agile:
            self.validate_agile_fields()
        if self.parent_issue:
            self.sync_parent_task()
        # sync original_estimate → expected_time
        if self.original_estimate or self.expected_time:
            self.sync_expected_time()
        # sync agile status → task status
        if self.issue_status:
            self.status = map_agile_status_to_task_status(self.issue_status)
        
        # sync agile priority → task priority
        if self.issue_priority:
            self.priority = map_agile_priority_to_task_priority(self.issue_priority)
    
    def on_update(self):
        """Track field changes after update"""
        super().on_update()
        if self.is_agile:
            self.handle_issue_activity_update()
    
    def handle_issue_activity_update(self):
        """Handle activity tracking for field changes"""
        # Field mapping for better display names
        field_maps = {
            "issue_status": "status",
            "issue_priority": "priority",
            "current_sprint": "sprint",
            "issue_type": "type",
            "reporter": "reporter",
            "story_points": "story points",
            "parent_issue": "parent issue",
            "original_estimate": "original estimate",
            "remaining_estimate": "remaining estimate",
        }
        
        # Track specific field changes
        for field in field_maps.keys():
            if self.has_value_changed(field):
                old_value = self.get_doc_before_save().get(field) if self.get_doc_before_save() else None
                new_value = self.get(field)
                
                # Format the activity message
                display_field = field_maps.get(field, field)
                
                # Special handling for status changes
                if field == "issue_status":
                    log_issue_activity(
                        self.name,
                        f"changed status from {old_value} to {new_value}",
                        data={"from_status": old_value, "to_status": new_value}
                    )
                elif field == "current_sprint":
                    if new_value and not old_value:
                        log_issue_activity(
                            self.name,
                            f"added to sprint {new_value}",
                            data={"sprint": new_value}
                        )
                    elif old_value and not new_value:
                        log_issue_activity(
                            self.name,
                            f"removed from sprint {old_value}",
                            data={"sprint": old_value}
                        )
                    else:
                        log_issue_activity(
                            self.name,
                            f"moved from sprint {old_value} to {new_value}",
                            data={"from_sprint": old_value, "to_sprint": new_value}
                        )
                elif field in ["original_estimate", "remaining_estimate"]:
                    log_issue_activity(
                        self.name,
                        f"updated {display_field} from {format_seconds(old_value)} to {format_seconds(new_value)}",
                        data={"old_value": format_seconds(old_value), "new_value": format_seconds(new_value)}
                    )
                else:
                    log_issue_activity(
                        self.name,
                        f"set {display_field} to {new_value}",
                        data={"old_value": str(old_value), "new_value": str(new_value)}
                    )
        
        # Track assignee changes
        if self.has_value_changed("assigned_to_users"):
            self.track_assignee_changes()
        
        # Track watcher changes
        if self.has_value_changed("watchers"):
            self.track_watcher_changes()
    
    def track_assignee_changes(self):
        """Track changes to assignees"""
        old_doc = self.get_doc_before_save()
        if not old_doc:
            return
        
        old_assignees = set([d.user for d in old_doc.get("assigned_to_users", [])])
        new_assignees = set([d.user for d in self.get("assigned_to_users", [])])
        
        added = new_assignees - old_assignees
        removed = old_assignees - new_assignees
        
        if added:
            assignee_names = [frappe.get_cached_value("User", user, "full_name") for user in added]
            log_issue_activity(
                self.name,
                f"assigned to {', '.join(assignee_names)}",
                data={"assignees": list(added)}
            )
        
        if removed:
            assignee_names = [frappe.get_cached_value("User", user, "full_name") for user in removed]
            log_issue_activity(
                self.name,
                f"unassigned from {', '.join(assignee_names)}",
                data={"unassigned": list(removed)}
            )
    
    def track_watcher_changes(self):
        """Track changes to watchers"""
        old_doc = self.get_doc_before_save()
        if not old_doc:
            return
        
        old_watchers = set([d.user for d in old_doc.get("watchers", [])])
        new_watchers = set([d.user for d in self.get("watchers", [])])
        
        added = new_watchers - old_watchers
        removed = old_watchers - new_watchers
        
        if added:
            for user in added:
                user_name = frappe.get_cached_value("User", user, "full_name")
                log_issue_activity(self.name, f"added watcher {user_name}", data={"watcher": user})
        
        if removed:
            for user in removed:
                user_name = frappe.get_cached_value("User", user, "full_name")
                log_issue_activity(self.name, f"removed watcher {user_name}", data={"watcher": user})

    def sync_parent_task(self):
        """Keep parent_task and parent_issue in sync"""
        if self.parent_issue:
            self.parent_task = self.parent_issue
            
    def sync_expected_time(self):
        """Sync original_estimate to expected_time"""
        if self.original_estimate:
            self.expected_time = self.original_estimate/3600  # convert seconds to hours
            
        if self.expected_time:
            self.original_estimate = self.expected_time*3600  # convert hours to seconds
    
    def validate_agile_fields(self):
        """Validate agile-specific fields"""
        if self.issue_type and not frappe.db.exists("Agile Issue Type", self.issue_type):
            frappe.throw(f"Invalid Issue Type: {self.issue_type}")
        
        if self.issue_priority and not frappe.db.exists("Agile Issue Priority", self.issue_priority):
            frappe.throw(f"Invalid Priority: {self.issue_priority}")


def format_seconds(seconds):
    """Format seconds to human readable time"""
    if not seconds:
        return "0m"
    
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    
    if hours > 0:
        return f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
    return f"{minutes}m"


def map_agile_status_to_task_status(agile_status):
    """Map agile status to ERPNext task status"""
    status_mapping = {
        "Open": "Open",
        "In Progress": "Working", 
        "In Review": "Pending Review",
        "Testing": "Pending Review",
        "Resolved": "Completed",
        "Closed": "Completed",
        "Reopened": "Open",
        "Blocked": "Open",
        "To Do": "Open",
        "Done": "Completed"
    }
    return status_mapping.get(agile_status, "Open")


def map_agile_priority_to_task_priority(agile_priority: str) -> str:
    """Map agile priority scale to ERPNext Task priority."""
    priority_mapping = {
        "Lowest": "Low",
        "Low": "Low",
        "Medium": "Medium",
        "High": "High",
        "Critical": "Urgent"
    }
    return priority_mapping.get(agile_priority, "Medium")