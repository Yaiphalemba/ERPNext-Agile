"""
Agile API Endpoints - Whitelisted methods for frontend/external access
"""

import frappe
from frappe import _
import json
from erpnext_agile.erpnext_agile.doctype.agile_issue_activity.agile_issue_activity import (
    log_issue_activity,
)

# ====================
# ISSUE MANAGEMENT
# ====================

@frappe.whitelist()
def create_agile_issue(issue_data):
    """Create a new agile issue"""
    if isinstance(issue_data, str):
        issue_data = json.loads(issue_data)
    
    from erpnext_agile.agile_issue_manager import AgileIssueManager
    manager = AgileIssueManager()
    task = manager.create_agile_issue(issue_data)
    
    # Activity is automatically logged in after_insert hook
    return task.as_dict()


@frappe.whitelist()
def transition_issue(task_name, from_status, to_status, comment=None):
    """Transition issue status"""
    task = frappe.get_doc('Task', task_name)
    
    # Validate transition is allowed
    if not is_valid_transition(task.project, from_status, to_status):
        frappe.throw(f"Invalid transition from {from_status} to {to_status}")
    
    # Update status
    task.issue_status = to_status
    task.save()
    
    # Activity is automatically logged by handle_issue_activity_update()
    # but we can add the comment if provided
    if comment:
        log_issue_activity(
            task.name,
            f"transitioned from {from_status} to {to_status}",
            data={'from_status': from_status, 'to_status': to_status},
            comment=comment
        )
    
    return task.as_dict()


@frappe.whitelist()
def assign_issue(task_name, assignees, notify=True):
    """Assign issue to users"""
    if isinstance(assignees, str):
        assignees = json.loads(assignees)
    
    task = frappe.get_doc('Task', task_name)
    
    # Clear existing assignments in assigned_to_users table
    task.set('assigned_to_users', [])
    
    # Add new assignments
    for assignee in assignees:
        task.append('assigned_to_users', {'user': assignee})
    
    task.save()
    
    # Activity is automatically logged by track_assignee_changes()
    
    if notify:
        # Send notification to assignees
        for assignee in assignees:
            frappe.publish_realtime(
                event='task_assigned',
                message={'task': task_name, 'assignee': assignee},
                user=assignee
            )
    
    return task.as_dict()


@frappe.whitelist()
def sync_github_issue_to_agile(repo_issue_name):
    """Sync GitHub issue to agile task"""
    from erpnext_agile.agile_github_integration import AgileGitHubIntegration
    integration = AgileGitHubIntegration()
    task = integration.sync_github_issue_to_agile(repo_issue_name)
    
    # Log activity
    log_issue_activity(
        task.name,
        "synced from GitHub",
        data={'github_issue': repo_issue_name}
    )
    
    return task.as_dict()


@frappe.whitelist()
def bulk_sync_project_issues(project_name):
    """Bulk sync all GitHub issues for a project"""
    from erpnext_agile.agile_github_integration import AgileGitHubIntegration
    integration = AgileGitHubIntegration()
    return integration.bulk_sync_project_issues(project_name)

# ====================
# WATCHER MANAGEMENT
# ====================

@frappe.whitelist()
def add_watcher(task_name, user):
    """Add a watcher to an issue"""
    task = frappe.get_doc('Task', task_name)
    
    # Check if watcher already exists
    existing = [w.user for w in task.get('watchers', [])]
    if user not in existing:
        task.append('watchers', {'user': user})
        task.save()
        
        # Activity is automatically logged by track_watcher_changes()
        
        return {"success": True, "message": "Watcher added"}
    
    return {"success": False, "message": "User is already a watcher"}


@frappe.whitelist()
def remove_watcher(task_name, user):
    """Remove a watcher from an issue"""
    task = frappe.get_doc('Task', task_name)
    
    # Find and remove watcher
    for watcher in task.get('watchers', []):
        if watcher.user == user:
            task.remove(watcher)
            task.save()
            
            # Activity is automatically logged by track_watcher_changes()
            
            return {"success": True, "message": "Watcher removed"}
    
    return {"success": False, "message": "User is not a watcher"}

# ====================
# PROJECT QUERIES
# ====================

@frappe.whitelist()
def get_project_overview(project):
    """Get comprehensive project overview"""
    project_doc = frappe.get_doc('Project', project)
    
    # Sprint data
    active_sprint = frappe.db.get_value('Agile Sprint',
        {'project': project, 'sprint_state': 'Active'},
        ['name', 'sprint_name', 'start_date', 'end_date', 'sprint_goal'],
        as_dict=True
    )
    
    # Issue statistics
    total_issues = frappe.db.count('Task', {'project': project, 'is_agile': 1})
    
    done_statuses = [s.name for s in frappe.get_all('Agile Issue Status',
        filters={'status_category': 'Done'}, fields=['name'])]
    
    completed_issues = frappe.db.count('Task', {
        'project': project,
        'is_agile': 1,
        'issue_status': ['in', done_statuses]
    })
    
    backlog_size = frappe.db.count('Task', {
        'project': project,
        'is_agile': 1,
        'current_sprint': ['in', ['', None]]
    })
    
    return {
        'project': project_doc.as_dict(),
        'active_sprint': active_sprint,
        'statistics': {
            'total_issues': total_issues,
            'completed_issues': completed_issues,
            'completion_percentage': (completed_issues / total_issues * 100) if total_issues > 0 else 0,
            'backlog_size': backlog_size
        }
    }


@frappe.whitelist()
def search_issues(query, project=None, filters=None):
    """Search issues with filters"""
    if isinstance(filters, str):
        filters = json.loads(filters) if filters else {}
    
    # Build search filters
    search_filters = {'is_agile': 1}
    
    if project:
        search_filters['project'] = project
    
    if filters:
        if filters.get('sprint'):
            search_filters['current_sprint'] = filters['sprint']
        if filters.get('status'):
            search_filters['issue_status'] = filters['status']
        if filters.get('assignee'):
            # Need to join with Task Assigned To
            pass
    
    # Search in subject and issue_key
    or_filters = [
        ['subject', 'like', f'%{query}%'],
        ['issue_key', 'like', f'%{query}%'],
        ['description', 'like', f'%{query}%']
    ]
    
    issues = frappe.get_all('Task',
        filters=search_filters,
        or_filters=or_filters,
        fields=['name', 'subject', 'issue_key', 'issue_type', 'issue_priority', 'issue_status'],
        limit=20
    )
    
    return issues


@frappe.whitelist()
def get_user_dashboard():
    """Get current user's agile dashboard"""
    user = frappe.session.user
    
    # My assigned issues
    assigned_issues = frappe.db.sql("""
        SELECT t.name, t.subject, t.issue_key, t.issue_type, 
               t.issue_priority, t.issue_status, t.project
        FROM `tabTask` t
        INNER JOIN `tabTask Assigned To` ta ON ta.parent = t.name
        WHERE ta.user = %s AND t.is_agile = 1
        ORDER BY t.modified DESC
        LIMIT 10
    """, user, as_dict=True)
    
    # My reported issues
    reported_issues = frappe.get_all('Task',
        filters={'reporter': user, 'is_agile': 1},
        fields=['name', 'subject', 'issue_key', 'issue_status', 'project'],
        order_by='modified desc',
        limit=10
    )
    
    # My projects
    projects = frappe.get_all('Project',
        filters={'enable_agile': 1},
        or_filters=[
            ['project_manager', '=', user],
            ['name', 'in', [p['parent'] for p in frappe.get_all('Project User', 
                filters={'user': user}, fields=['parent'])]]
        ],
        fields=['name', 'project_name', 'status']
    )
    
    return {
        'assigned_issues': assigned_issues,
        'reported_issues': reported_issues,
        'projects': projects
    }


@frappe.whitelist()
def get_issue_activity(task_name, limit=50):
    """Get activity timeline for an issue"""
    activities = frappe.get_all('Agile Issue Activity',
        filters={'issue': task_name},
        fields=['name', 'activity_type', 'user', 'timestamp', 'data', 'comment'],
        order_by='timestamp desc',
        limit=limit
    )
    
    return activities


# ====================
# HELPER FUNCTIONS
# ====================

def is_valid_transition(project, from_status, to_status):
    """Check if status transition is valid based on workflow"""
    # Get workflow scheme from project
    workflow_scheme = frappe.db.get_value("Project", project, "workflow_scheme")
    
    if not workflow_scheme:
        return True  # No workflow restriction
    
    # Check if transition exists in workflow
    transition = frappe.db.exists("Agile Workflow Transition", {
        "parent": workflow_scheme,
        "from_status": from_status,
        "to_status": to_status
    })
    
    return bool(transition)


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


def parse_time_to_seconds(time_str):
    """Parse time string like '2h 30m' or '1.5h' to seconds"""
    import re
    
    time_str = time_str.lower().strip()
    seconds = 0
    
    # Match hours (e.g., "2h" or "2.5h")
    hours_match = re.search(r'(\d+\.?\d*)\s*h', time_str)
    if hours_match:
        seconds += float(hours_match.group(1)) * 3600
    
    # Match minutes (e.g., "30m")
    minutes_match = re.search(r'(\d+\.?\d*)\s*m', time_str)
    if minutes_match:
        seconds += float(minutes_match.group(1)) * 60
    
    # If no unit specified, assume hours
    if not hours_match and not minutes_match:
        try:
            seconds = float(time_str) * 3600
        except ValueError:
            frappe.throw(f"Invalid time format: {time_str}")
    
    return int(seconds)


@frappe.whitelist()
def get_issue_details(task_name):
    """Get detailed issue information"""
    task_doc = frappe.get_doc('Task', task_name)
    
    # Get additional agile data
    assignees = frappe.get_all('Task Assigned To',
        filters={'parent': task_name},
        fields=['user'],
        pluck='user'
    )
    
    watchers = [w.user for w in task_doc.get('watchers', [])]
    
    return {
        'task': task_doc.as_dict(),
        'assignees': assignees,
        'watchers': watchers,
        'has_github_link': bool(task_doc.github_issue_number)
    }

# ====================
# SPRINT MANAGEMENT
# ====================

@frappe.whitelist()
def create_sprint(sprint_data):
    """Create a new sprint"""
    if isinstance(sprint_data, str):
        sprint_data = json.loads(sprint_data)
    
    from erpnext_agile.agile_sprint_manager import AgileSprintManager
    manager = AgileSprintManager()
    return manager.create_sprint(sprint_data).as_dict()


@frappe.whitelist()
def start_sprint(sprint_name):
    """Start a sprint"""
    from erpnext_agile.agile_sprint_manager import AgileSprintManager
    manager = AgileSprintManager()
    sprint = manager.start_sprint(sprint_name)
    
    # Log activity for all issues in the sprint
    issues = frappe.get_all('Task',
        filters={'current_sprint': sprint_name, 'is_agile': 1},
        fields=['name']
    )
    
    for issue in issues:
        log_issue_activity(
            issue['name'],
            f"sprint {sprint_name} started"
        )
    
    return sprint.as_dict()


@frappe.whitelist()
def complete_sprint(sprint_name):
    """Complete a sprint"""
    from erpnext_agile.agile_sprint_manager import AgileSprintManager
    manager = AgileSprintManager()
    sprint = manager.complete_sprint(sprint_name)
    
    # Log activity for all issues in the sprint
    issues = frappe.get_all('Task',
        filters={'current_sprint': sprint_name, 'is_agile': 1},
        fields=['name']
    )
    
    for issue in issues:
        log_issue_activity(
            issue['name'],
            f"sprint {sprint_name} completed"
        )
    
    return sprint.as_dict()


@frappe.whitelist()
def add_issues_to_sprint(sprint_name, issue_keys):
    """Add issues to sprint"""
    if isinstance(issue_keys, str):
        issue_keys = json.loads(issue_keys)
    
    added = 0
    
    for issue_key in issue_keys:
        task = frappe.db.get_value("Task", {"issue_key": issue_key}, "name")
        if task:
            task_doc = frappe.get_doc("Task", task)
            task_doc.current_sprint = sprint_name
            task_doc.save()
            
            # Activity is automatically logged by handle_issue_activity_update()
            added += 1
    
    return {"success": True, "added": added}


@frappe.whitelist()
def remove_issues_from_sprint(sprint_name, issue_keys):
    """Remove issues from sprint"""
    if isinstance(issue_keys, str):
        issue_keys = json.loads(issue_keys)
    
    removed = 0
    
    for issue_key in issue_keys:
        task = frappe.db.get_value("Task", {"issue_key": issue_key}, "name")
        if task:
            task_doc = frappe.get_doc("Task", task)
            task_doc.current_sprint = None
            task_doc.save()
            
            # Activity is automatically logged by handle_issue_activity_update()
            removed += 1
    
    return {"success": True, "removed": removed}


@frappe.whitelist()
def get_sprint_report(sprint_name):
    """Get comprehensive sprint report"""
    from erpnext_agile.agile_sprint_manager import AgileSprintManager
    manager = AgileSprintManager()
    return manager.get_sprint_report(sprint_name)


@frappe.whitelist()
def get_sprint_burndown(sprint_name):
    """Get sprint burndown data"""
    from erpnext_agile.agile_sprint_manager import AgileSprintManager
    manager = AgileSprintManager()
    return manager.get_sprint_burndown(sprint_name)

# ====================
# BACKLOG MANAGEMENT
# ====================

@frappe.whitelist()
def get_backlog(project, filters=None):
    """Get project backlog"""
    if isinstance(filters, str):
        filters = json.loads(filters)
    
    from erpnext_agile.agile_backlog_manager import AgileBacklogManager
    manager = AgileBacklogManager(project)
    return manager.get_backlog(project, filters)


@frappe.whitelist()
def estimate_backlog_item(task_name, story_points, estimation_method='planning_poker'):
    """Estimate story points for backlog item"""
    task = frappe.get_doc('Task', task_name)
    old_points = task.story_points
    
    task.story_points = story_points
    task.save()
    
    # Activity is automatically logged by handle_issue_activity_update()
    
    return {"success": True, "story_points": story_points}


@frappe.whitelist()
def split_story(task_name, split_data):
    """Split a user story into multiple stories"""
    if isinstance(split_data, str):
        split_data = json.loads(split_data)
    
    from erpnext_agile.agile_backlog_manager import AgileBacklogManager
    manager = AgileBacklogManager()
    result = manager.split_story(task_name, split_data)
    
    # Log activity for original story
    log_issue_activity(
        task_name,
        f"split into {len(split_data.get('stories', []))} stories",
        data={'split_count': len(split_data.get('stories', []))}
    )
    
    return result


@frappe.whitelist()
def get_backlog_metrics(project):
    """Get backlog health metrics"""
    from erpnext_agile.agile_backlog_manager import AgileBacklogManager
    manager = AgileBacklogManager()
    return manager.get_backlog_metrics(project)

# ====================
# BOARD MANAGEMENT
# ====================

@frappe.whitelist()
def get_board_data(project, sprint=None, view_type='sprint'):
    """Get board data for Kanban/Scrum board"""
    from erpnext_agile.agile_board_manager import AgileBoardManager
    manager = AgileBoardManager(project, sprint)
    return manager.get_board_data(project, sprint, view_type)


@frappe.whitelist()
def move_issue(task_name, from_status, to_status, position=None):
    """Move issue on board (drag & drop)"""
    task = frappe.get_doc('Task', task_name)
    task.issue_status = to_status
    task.save()
    
    # Activity is automatically logged by handle_issue_activity_update()
    
    return {"success": True, "new_status": to_status}


@frappe.whitelist()
def quick_create_issue(project, status, issue_data):
    """Quick create issue from board"""
    if isinstance(issue_data, str):
        issue_data = json.loads(issue_data)
    
    issue_data['project'] = project
    issue_data['issue_status'] = status
    
    from erpnext_agile.agile_board_manager import AgileBoardManager
    manager = AgileBoardManager()
    return manager.quick_create_issue(project, status, issue_data)


@frappe.whitelist()
def get_board_metrics(project, sprint=None):
    """Get board metrics"""
    from erpnext_agile.agile_board_manager import AgileBoardManager
    manager = AgileBoardManager()
    return manager.get_board_metrics(project, sprint)


@frappe.whitelist()
def filter_board(project, sprint=None, filters=None):
    """Filter board by criteria"""
    if isinstance(filters, str):
        filters = json.loads(filters)
    
    from erpnext_agile.agile_board_manager import AgileBoardManager
    manager = AgileBoardManager()
    return manager.filter_board(project, sprint, filters)


@frappe.whitelist()
def get_swimlane_data(project, sprint=None, swimlane_by='issue_type'):
    """Get swimlane data"""
    from erpnext_agile.agile_board_manager import AgileBoardManager
    manager = AgileBoardManager()
    return manager.get_swimlane_data(project, sprint, swimlane_by)

# ====================
# TIME TRACKING
# ====================

@frappe.whitelist()
def log_work(task_name, time_spent, work_description, work_date=None):
    """Log work on an issue"""
    from erpnext_agile.agile_time_tracking import AgileTimeTracking
    tracker = AgileTimeTracking()
    return tracker.log_work(task_name, time_spent, work_description, work_date)


@frappe.whitelist()
def update_estimate(task_name, estimate_type, time_value):
    """Update time estimates"""
    from erpnext_agile.agile_time_tracking import AgileTimeTracking
    tracker = AgileTimeTracking()
    return tracker.update_estimate(task_name, estimate_type, time_value)


@frappe.whitelist()
def get_time_tracking_report(task_name):
    """Get time tracking report for issue"""
    from erpnext_agile.agile_time_tracking import AgileTimeTracking
    tracker = AgileTimeTracking()
    return tracker.get_time_tracking_report(task_name)


@frappe.whitelist()
def get_team_time_report(project, start_date=None, end_date=None):
    """Get team time tracking report"""
    from erpnext_agile.agile_time_tracking import AgileTimeTracking
    tracker = AgileTimeTracking()
    return tracker.get_team_time_report(project, start_date, end_date)


@frappe.whitelist()
def start_timer(task_name):
    """Start work timer"""
    from erpnext_agile.agile_time_tracking import AgileTimeTracking
    tracker = AgileTimeTracking()
    return tracker.start_timer(task_name)


@frappe.whitelist()
def stop_timer(timer_name, work_description=''):
    """Stop work timer"""
    from erpnext_agile.agile_time_tracking import AgileTimeTracking
    tracker = AgileTimeTracking()
    return tracker.stop_timer(timer_name, work_description)


@frappe.whitelist()
def get_active_timer(task_name=None):
    """Get active timer for current user"""
    from erpnext_agile.agile_time_tracking import AgileTimeTracking
    tracker = AgileTimeTracking()
    return tracker.get_active_timer(task_name)


@frappe.whitelist()
def cancel_timer(timer_name):
    """Cancel a running timer without logging work"""
    timer_doc = frappe.get_doc('Agile Work Timer', timer_name)
    
    if timer_doc.status != 'Running':
        frappe.throw(_("Timer is not running"))
    
    if timer_doc.user != frappe.session.user:
        frappe.throw(_("You can only cancel your own timers"))
    
    # Update timer status
    timer_doc.status = 'Cancelled'
    timer_doc.end_time = frappe.utils.now_datetime()
    timer_doc.save(ignore_permissions=True)
    
    # Update task timer status
    frappe.db.set_value('Task', timer_doc.task, 'custom_timer_status', 0, update_modified=False)
    frappe.db.commit()
    
    # Log activity
    from erpnext_agile.erpnext_agile.doctype.agile_issue_activity.agile_issue_activity import (
        log_issue_activity,
    )
    log_issue_activity(
        timer_doc.task,
        "cancelled work timer"
    )
    
    return {
        'success': True,
        'message': 'Timer cancelled'
    }

# ====================
# GITHUB INTEGRATION
# ====================

@frappe.whitelist()
def sync_agile_issue_to_github(task_name):
    """Sync agile issue to GitHub"""
    from erpnext_agile.agile_github_integration import AgileGitHubIntegration
    integration = AgileGitHubIntegration()
    result = integration.sync_agile_issue_to_github(task_name)
    
    # Log activity