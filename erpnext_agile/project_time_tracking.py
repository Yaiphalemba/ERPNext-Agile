# erpnext_agile/project_time_tracking.py
"""
Enhanced time tracking and status monitoring for Project doctype
Aggregates task-level time data to Project User records
"""

import frappe
from frappe import _
from frappe.utils import getdate, today
import json
from collections import defaultdict


class ProjectTimeTracker:
    """Manages time aggregation and status tracking for Project Users"""
    
    def __init__(self, project_name):
        self.project_name = project_name
        self.project_doc = frappe.get_doc('Project', project_name)
    
    def update_all_user_time_data(self):
        """
        Main entry point: Recalculate time_utilized and status for all project users
        Should be called on Task save/update or via scheduled task
        """
        if not self.project_doc.enable_agile:
            return
        
        project_users = self.project_doc.get('users', [])
        
        for pu in project_users:
            user = pu.user
            
            # Get all tasks assigned to this user in this project
            user_tasks = self.get_user_tasks(user)
            
            if user_tasks:
                # Calculate time metrics
                time_data = self.calculate_user_time_metrics(user, user_tasks)
                status = self.determine_user_status(user_tasks)
                
                # Update Project User row
                frappe.db.set_value(pu.doctype, pu.name, {
                    'custom_time_utilized': time_data['total_time_spent'],
                    'custom_time_allocated': time_data['total_estimated'],
                    'custom_designated_task_status': status
                })
        
        frappe.db.commit()
    
    def get_user_tasks(self, user):
        """
        Fetch all tasks assigned to user in this project
        Returns tasks with agile fields populated
        Supports both custom 'assigned_to_users' child table and standard assignment
        """
        # Try using custom child table first (if it exists)
        try:
            tasks = frappe.db.sql("""
                SELECT 
                    t.name,
                    t.subject,
                    t.issue_key,
                    t.issue_status,
                    t.status,
                    t.time_spent,
                    t.original_estimate,
                    t.remaining_estimate,
                    t.is_agile,
                    t.current_sprint,
                    GROUP_CONCAT(wl.time_spent_seconds) as work_log_times
                FROM `tabTask` t
                LEFT JOIN `tabAgile Issue Work Log` wl ON wl.parent = t.name
                INNER JOIN `tabAssigned To Users` atu ON atu.parent = t.name
                WHERE atu.user = %s 
                    AND t.project = %s
                    AND t.status != 'Cancelled'
                GROUP BY t.name
                ORDER BY t.modified DESC
            """, (user, self.project_name), as_dict=True)
            
            return tasks
            
        except Exception as e:
            # Fallback: Use standard ERPNext assignment via owner or _assign
            frappe.log_error(f"Custom child table not found, using fallback: {str(e)}")
            
            tasks = frappe.db.sql("""
                SELECT 
                    t.name,
                    t.subject,
                    t.issue_key,
                    t.issue_status,
                    t.status,
                    t.time_spent,
                    t.original_estimate,
                    t.remaining_estimate,
                    t.is_agile,
                    t.current_sprint
                FROM `tabTask` t
                WHERE (
                    t.owner = %s 
                    OR FIND_IN_SET(%s, COALESCE(t._assign, ''))
                )
                    AND t.project = %s
                    AND t.status != 'Cancelled'
                    AND t.is_agile = 1
                ORDER BY t.modified DESC
            """, (user, user, self.project_name), as_dict=True)
            
            return tasks
    
    def calculate_user_time_metrics(self, user, user_tasks):
        """
        Calculate comprehensive time metrics for a user
        Returns: {total_time_spent, total_estimated, total_remaining, ...}
        """
        total_time_spent = 0
        total_estimated = 0
        total_remaining = 0
        task_count = len(user_tasks)
        working_count = 0
        completed_count = 0
        
        for task in user_tasks:
            # Sum time spent (in seconds, stored in time_spent field)
            if task.time_spent:
                total_time_spent += task.time_spent
            
            # Sum estimates
            if task.original_estimate:
                total_estimated += task.original_estimate
            if task.remaining_estimate:
                total_remaining += task.remaining_estimate
            
            # Count by status
            if task.status == 'Working':
                working_count += 1
            elif task.status == 'Completed':
                completed_count += 1
        
        # Calculate utilization percentage
        utilization = 0
        if total_estimated > 0:
            utilization = round((total_time_spent / total_estimated) * 100, 1)
        
        return {
            'total_time_spent': total_time_spent,
            'total_estimated': total_estimated,
            'total_remaining': total_remaining,
            'utilization_percentage': utilization,
            'task_count': task_count,
            'working_count': working_count,
            'completed_count': completed_count
        }
    
    def determine_user_status(self, user_tasks):
        """
        Determine the designated task status based on task statuses
        Priority: Working > Completed > Cancelled > Open
        """
        if not user_tasks:
            return 'Open'
        
        statuses = [t.status for t in user_tasks]
        
        # If any task is being worked on
        if any(status in statuses for status in ['Working', 'Overdue', 'Pending Review']):
            return 'Working'
        
        # If all completed
        if all(status == 'Completed' for status in statuses):
            return 'Completed'
        
        # If all cancelled
        if all(status == 'Cancelled' for status in statuses):
            return 'Cancelled'
        
        # Default: Open (has some pending tasks)
        return 'Open'
    
    def get_user_summary(self, user):
        """Get formatted summary for a specific user"""
        user_tasks = self.get_user_tasks(user)
        
        if not user_tasks:
            return None
        
        metrics = self.calculate_user_time_metrics(user, user_tasks)
        status = self.determine_user_status(user_tasks)
        
        return {
            'user': user,
            'status': status,
            'total_time_spent': self.format_seconds(metrics['total_time_spent']),
            'total_estimated': self.format_seconds(metrics['total_estimated']),
            'total_remaining': self.format_seconds(metrics['total_remaining']),
            'utilization_percentage': metrics['utilization_percentage'],
            'task_summary': {
                'total': metrics['task_count'],
                'working': metrics['working_count'],
                'completed': metrics['completed_count']
            }
        }
    
    @staticmethod
    def format_seconds(seconds):
        """Convert seconds to human-readable format"""
        if not seconds:
            return "0m"
        
        seconds = int(seconds)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        
        if hours > 0 and minutes > 0:
            return f"{hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h"
        else:
            return f"{minutes}m"


# ============================================
# FRAPPE HOOKS & EVENT HANDLERS
# ============================================

def update_project_user_time_on_task_update(doc, method):
    """
    Hook: Called when a Task is saved
    Updates the Project User's time_utilized and status
    """
    if not doc.project or not doc.is_agile:
        return
    
    # Get project and check if it's agile-enabled
    try:
        project_doc = frappe.get_cached_doc('Project', doc.project)
        if not project_doc.enable_agile:
            return
    except:
        return
    
    # Update time data for all assigned users
    for assignee_row in doc.get('assigned_to_users', []):
        user = assignee_row.user
        frappe.logger().info(f"Updating metrics for {user} in project {doc.project}")
        update_project_user_metrics(doc.project, user)


def update_project_user_time_on_work_log(doc, method):
    """
    Hook: Called when a work log is added to a Task
    Updates the parent Task's time_spent and cascades to Project User
    """
    if not doc.parent:
        return
    
    # Get parent task
    try:
        task_doc = frappe.get_doc('Task', doc.parent)
        if task_doc.project and task_doc.is_agile:
            # Recalculate task time_spent
            total_time = sum(
                wl.get('time_spent_seconds', 0) 
                for wl in task_doc.get('work_logs', [])
            )
            task_doc.db_set('time_spent', total_time, update_modified=False)
            
            # Update project user metrics
            for assignee_row in task_doc.get('assigned_to_users', []):
                update_project_user_metrics(task_doc.project, assignee_row.user)
    except Exception as e:
        frappe.log_error(f"Error updating project user time on work log: {str(e)}")


def update_project_user_metrics(project_name, user):
    """
    Utility function to update a specific user's metrics in Project
    Uses database direct update for performance
    """
    try:
        # Calculate metrics
        tracker = ProjectTimeTracker(project_name)
        user_tasks = tracker.get_user_tasks(user)
        
        if not user_tasks:
            return
        
        time_data = tracker.calculate_user_time_metrics(user, user_tasks)
        status = tracker.determine_user_status(user_tasks)
        
        # Calculate time_allocated from original estimates
        time_allocated = time_data['total_estimated']
        
        # Use direct database update (faster, no full document load)
        frappe.db.sql("""
            UPDATE `tabProject User`
            SET custom_time_utilized = %s,
                custom_time_allocated = %s,
                custom_designated_task_status = %s,
                modified = NOW(),
                modified_by = %s
            WHERE parent = %s AND user = %s
        """, (
            time_data['total_time_spent'],
            time_allocated,
            status,
            frappe.session.user,
            project_name,
            user
        ))
        
        frappe.db.commit()
        
        # Clear the cache so next read gets fresh data
        frappe.clear_cache()
            
    except Exception as e:
        frappe.log_error(f"Error updating project user metrics: {str(e)}")


def recalculate_all_project_times_scheduled():
    """
    Scheduled task: Run hourly to ensure all project user times are accurate
    Handles edge cases where individual hooks might have missed updates
    """
    # Get all agile-enabled projects
    projects = frappe.get_all('Project', 
        filters={'enable_agile': 1},
        fields=['name']
    )
    
    for project_rec in projects:
        try:
            project_doc = frappe.get_doc('Project', project_rec.name)
            
            # Update each user
            for pu in project_doc.get('users', []):
                update_project_user_metrics(project_rec.name, pu.user)
            
        except Exception as e:
            frappe.log_error(f"Error recalculating project times for {project_rec.name}: {str(e)}")


# ============================================
# WHITELISTED API ENDPOINTS
# ============================================

@frappe.whitelist()
def get_project_user_time_summary(project_name):
    """
    Get time tracking summary for all users in a project
    Returns: List of user summaries with time data
    """
    if not frappe.has_permission('Project', 'read', project_name):
        frappe.throw(_('Not permitted'))
    
    tracker = ProjectTimeTracker(project_name)
    project_doc = frappe.get_doc('Project', project_name)
    
    summaries = []
    for pu in project_doc.get('users', []):
        summary = tracker.get_user_summary(pu.user)
        if summary:
            summaries.append(summary)
    
    return summaries


@frappe.whitelist()
def get_user_time_details(project_name, user):
    """
    Get detailed time tracking for a specific user in a project
    Returns: Detailed breakdown of tasks and time logs
    """
    if not frappe.has_permission('Project', 'read', project_name):
        frappe.throw(_('Not permitted'))
    
    tracker = ProjectTimeTracker(project_name)
    user_tasks = tracker.get_user_tasks(user)
    
    task_details = []
    for task in user_tasks:
        task_details.append({
            'task_name': task.name,
            'issue_key': task.issue_key,
            'subject': task.subject,
            'status': task.status,
            'time_spent': tracker.format_seconds(task.time_spent or 0),
            'estimated': tracker.format_seconds(task.original_estimate or 0),
            'remaining': tracker.format_seconds(task.remaining_estimate or 0),
            'sprint': task.current_sprint
        })
    
    return {
        'user': user,
        'project': project_name,
        'tasks': task_details,
        'total_tasks': len(task_details)
    }


@frappe.whitelist()
def force_recalculate_project_times(project_name):
    """
    Manually trigger recalculation of all time metrics for a project
    Useful for data corrections or cleanup
    """
    if not frappe.has_permission('Project', 'write', project_name):
        frappe.throw(_('Not permitted'))
    
    try:
        tracker = ProjectTimeTracker(project_name)
        project_doc = frappe.get_doc('Project', project_name)
        
        tracker.update_all_user_time_data()
        project_doc.save(ignore_permissions=True)
        
        return {
            'success': True,
            'message': _('Project time metrics recalculated successfully')
        }
    except Exception as e:
        frappe.throw(f"Error recalculating times: {str(e)}")