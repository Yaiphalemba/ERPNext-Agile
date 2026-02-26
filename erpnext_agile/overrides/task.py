# erpnext_agile/overrides/task.py
import frappe
from frappe import _
import re
from frappe.desk.form.assign_to import add, clear
from erpnext.projects.doctype.task.task import Task
from erpnext_agile.erpnext_agile.doctype.agile_issue_activity.agile_issue_activity import (
    log_issue_activity,
)
from frappe.utils import getdate

class AgileTask(Task):
    def after_insert(self):
        """Log creation activity"""
        if self.is_agile:
            log_issue_activity(self.name, "created this issue")
            self.handle_assignment_for_new_tasks()
    
    def validate(self):
        super().validate()
        if self.is_agile:
            self.validate_agile_fields()
            # Validate workflow transitions BEFORE other validations
            self.validate_workflow_transition()
        if self.parent_issue:
            self.sync_parent_task()
        # sync original_estimate → expected_time
        if self.expected_time:
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
            
            # Update parent task progress if this is a subtask
            if self.parent_issue:
                self.update_parent_progress()
            
            # Update sprint metrics if task is in a sprint
            if self.current_sprint and self.has_value_changed("issue_status"):
                self.update_sprint_metrics()
                
    def update_parent_progress(self):
        """Update parent task's completion percentage"""
        if not self.parent_issue:
            return
        
        # Get all subtasks
        subtasks = frappe.get_all(
            "Task",
            filters={"parent_issue": self.parent_issue},
            fields=["name", "issue_status"]
        )
        
        if not subtasks:
            return
        
        # Count completed subtasks
        completed = len([
            t for t in subtasks 
            if frappe.db.get_value("Agile Issue Status", t.issue_status, "status_category") == "Done"
        ])
        
        total = len(subtasks)
        progress = (completed / total * 100) if total > 0 else 0
        
        # Update parent
        frappe.db.set_value("Task", self.parent_issue, "progress", progress, update_modified=False)
    
    def update_sprint_metrics(self):
        """Update sprint metrics when task status changes"""
        if not self.current_sprint:
            return
        
        try:
            sprint = frappe.get_doc("Agile Sprint", self.current_sprint)
            sprint.calculate_metrics()
        except Exception as e:
            frappe.log_error(f"Error updating sprint metrics: {str(e)}")
            
    def validate_workflow_transition(self):
        """
        Validate status transitions based on workflow scheme
        This is the key method for conditional workflow validation
        """
        # Skip for new documents
        if self.is_new():
            return
        
        # Skip if no status change
        if not self.has_value_changed("issue_status"):
            return
        
        # Get old status
        old_doc = self.get_doc_before_save()
        if not old_doc or not old_doc.issue_status:
            return
        
        old_status = old_doc.issue_status
        new_status = self.issue_status
        
        # Get project's workflow scheme
        if not self.project:
            return
        
        project = frappe.get_cached_doc("Project", self.project)
        
        # If no workflow scheme, allow any transition
        if not project.enable_agile or not project.workflow_scheme:
            return
        
        # Validate the transition
        scheme = frappe.get_doc("Agile Workflow Scheme", project.workflow_scheme)
        
        is_valid, error_message = scheme.validate_transition(
            from_status=old_status,
            to_status=new_status,
            doc=self,
            user=frappe.session.user
        )
        
        if not is_valid:
            frappe.throw(
                _("Workflow Transition Error: {0}").format(error_message),
                title=_("Invalid Status Change")
            )
    
    def validate_issue_type_allowed(self):
        """Check if issue type is allowed in this project"""
        project = frappe.get_cached_doc("Project", self.project)
        
        if not project.issue_types_allowed:
            return  # No restrictions
        
        allowed_types = [row.issue_type for row in project.issue_types_allowed]
        
        if self.issue_type not in allowed_types:
            frappe.throw(
                _("Issue Type '{0}' is not allowed in project '{1}'").format(
                    self.issue_type, 
                    self.project
                )
            )
    
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
            user_id = list(added)
            add({
                    "assign_to": user_id,
                    "doctype": "Task",
                    "name": self.name,
                    "description": self.subject
                })
            log_issue_activity(
                self.name,
                f"assigned to {', '.join(assignee_names)}",
                data={"assignees": list(added)}
            )
        
        if removed:
            assignee_names = [frappe.get_cached_value("User", user, "full_name") for user in removed]
            clear("Task", self.name)
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

    def handle_assignment_for_new_tasks(self):
        # For new documents, assign to users in assigned_to_users field
        new_assignees = set([d.user for d in self.get("assigned_to_users", [])])
        if new_assignees:
            assignee_names = [frappe.get_cached_value("User", user, "full_name") for user in new_assignees]
            user_id = list(new_assignees)
            add({
                    "assign_to": user_id,
                    "doctype": "Task",
                    "name": self.name,
                    "description": self.subject
                })
            log_issue_activity(
                self.name,
                f"assigned to {', '.join(assignee_names)}",
                data={"assignees": user_id}
            )

    def sync_parent_task(self):
        """Keep parent_task and parent_issue in sync"""
        if self.parent_issue:
            self.parent_task = self.parent_issue
            
    def sync_expected_time(self):
        """Sync original_estimate to expected_time"""
        # if self.original_estimate:
        #     self.expected_time = self.original_estimate/3600  # convert seconds to hours
            
        if self.expected_time:
            self.original_estimate = self.expected_time*3600  # convert hours to seconds
    
    def validate_agile_fields(self):
        """Validate agile-specific fields"""
        if self.issue_type and not frappe.db.exists("Agile Issue Type", self.issue_type):
            frappe.throw(f"Invalid Issue Type: {self.issue_type}")
        
        # Validate issue type is allowed in project
        if self.issue_type and self.project:
            self.validate_issue_type_allowed()
        
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

@frappe.whitelist()
def map_agile_status_to_task_status(agile_status):
    """Map agile status to ERPNext task status"""
    status_mapping = {
        "Open": "Open",
        "In Progress": "Working",
        "In Review": "Pending Review",
        "QA Review": "Pending Review",
        "Testing": "Pending Review",
        "Resolved": "Pending Review",
        "Closed": "Completed",
        "Reopened": "Open",
        "Blocked": "Open",
        "To Do": "Open",
        "Done": "Completed",
    }
    if status_mapping.get(agile_status):
        return status_mapping.get(agile_status, "Open")
    else:
        status_category = frappe.db.get_value("Agile Issue Status", agile_status, "status_category")
        if status_category:
            return status_mapping.get(status_category, "Open")


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


def get_allowed_status_changes(doc):
    """
    Get list of allowed status changes for a task
    Used in UI to show only valid transitions
    """
    if not doc.is_agile or not doc.issue_status:
        return []
    
    # Get project's workflow scheme
    try:
        project = frappe.get_doc("Project", doc.project)
        if not project.enable_agile or not project.workflow_scheme:
            # No workflow scheme, return all statuses
            return frappe.get_all(
                "Agile Issue Status",
                pluck="name",
                order_by="sort_order"
            )
         
        # Get allowed transitions from workflow scheme
        scheme = frappe.get_doc("Agile Workflow Scheme", project.workflow_scheme)
        transitions = scheme.get_transitions(doc.issue_status, doc)
        
        # Filter by user permissions
        user = frappe.session.user
        allowed_statuses = [doc.issue_status]  # Always allow current status
        
        for t in transitions:
            if t['required_permission']:
                if scheme.check_user_permission(user, t['required_permission']):
                    allowed_statuses.append(t['to_status'])
            else:
                allowed_statuses.append(t['to_status'])
        
        return allowed_statuses
        
    except Exception as e:
        frappe.log_error(f"Error getting allowed status changes: {str(e)}")
        # On error, return all statuses to not block user
        return frappe.get_all(
            "Agile Issue Status",
            pluck="name",
            order_by="sort_order"
        )


# Whitelisted method for client-side use
@frappe.whitelist()
def get_project_users(project):
    """Get users from Project → project_users child table"""
    if not project:
        return []
    
    users = frappe.get_all("Project User", 
        filters={"parent": project},
        fields=["user"],
        pluck="user"
    )
    return users

@frappe.whitelist()
def get_task_allowed_statuses(task_name):
    """
    Get allowed status transitions for a task
    Called from JavaScript to dynamically filter status dropdown
    """
    if not frappe.db.exists("Task", task_name):
        return []
    
    doc = frappe.get_doc("Task", task_name)
    return get_allowed_status_changes(doc)


@frappe.whitelist()
def transition_task_status(task_name, to_status, comment=None, completed_by=None, completed_on=None):
    """
    Transition task to new status with workflow validation
    
    Args:
        task_name: Name of task
        to_status: Target status
        comment: Optional comment for the transition
    """
    if not frappe.db.exists("Task", task_name):
        frappe.throw(_("Task not found"))
    
    doc = frappe.get_doc("Task", task_name)
    
    # Validate transition
    if doc.project:
        project = frappe.get_doc("Project", doc.project)
        if project.enable_agile and project.workflow_scheme:
            scheme = frappe.get_doc("Agile Workflow Scheme", project.workflow_scheme)
            is_valid, error_message = scheme.validate_transition(
                from_status=doc.issue_status,
                to_status=to_status,
                doc=doc,
                user=frappe.session.user
            )
            
            if not is_valid:
                frappe.throw(error_message)
    
    # Update status
    old_status = doc.issue_status
    doc.issue_status = to_status    

    if completed_by:
        doc.completed_by = completed_by
    if completed_on:
        doc.completed_on = getdate(completed_on)
        doc.progress = 100  # Mark as complete if completed_on is set
    if to_status in ["Blocked", "On Hold"]:
        doc.exp_end_date = None  # Clear end date if blocked
    doc.save()
    
    # Add comment if provided
    if comment:
        doc.add_comment(
            "Comment",
            f"Status changed from {old_status} to {to_status}: {comment}"
        )
    
    # Log activity
    frappe.get_doc({
        "doctype": "Agile Issue Activity",
        "issue": task_name,
        "activity_type": "status_changed",
        "user": frappe.session.user,
        "data": frappe.as_json({
            "old_status": old_status,
            "new_status": to_status,
            "comment": comment
        })
    }).insert(ignore_permissions=True)
    
    return {
        "success": True,
        "message": _("Status updated to {0}").format(to_status)
    }