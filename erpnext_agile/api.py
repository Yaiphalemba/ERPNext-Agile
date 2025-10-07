"""
Agile API Endpoints - Whitelisted methods for frontend/external access
"""

import frappe
from frappe import _
import json

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
    return manager.create_agile_issue(issue_data).as_dict()

@frappe.whitelist()
def transition_issue(task_name, from_status, to_status, comment=None):
    """Transition issue status"""
    from erpnext_agile.agile_issue_manager import AgileIssueManager
    manager = AgileIssueManager()
    return manager.transition_issue(task_name, from_status, to_status, comment).as_dict()

@frappe.whitelist()
def assign_issue(task_name, assignees, notify=True):
    """Assign issue to users"""
    if isinstance(assignees, str):
        assignees = json.loads(assignees)
    
    from erpnext_agile.agile_issue_manager import AgileIssueManager
    manager = AgileIssueManager()
    return manager.assign_issue(task_name, assignees, notify).as_dict()

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
    return manager.start_sprint(sprint_name).as_dict()

@frappe.whitelist()
def complete_sprint(sprint_name):
    """Complete a sprint"""
    from erpnext_agile.agile_sprint_manager import AgileSprintManager
    manager = AgileSprintManager()
    return manager.complete_sprint(sprint_name).as_dict()

@frappe.whitelist()
def add_issues_to_sprint(sprint_name, issue_keys):
    """Add issues to sprint"""
    if isinstance(issue_keys, str):
        issue_keys = json.loads(issue_keys)
    
    from erpnext_agile.agile_sprint_manager import AgileSprintManager
    manager = AgileSprintManager()
    return manager.add_issues_to_sprint(sprint_name, issue_keys)

@frappe.whitelist()
def remove_issues_from_sprint(sprint_name, issue_keys):
    """Remove issues from sprint"""
    if isinstance(issue_keys, str):
        issue_keys = json.loads(issue_keys)
    
    from erpnext_agile.agile_sprint_manager import AgileSprintManager
    manager = AgileSprintManager()
    return manager.remove_issues_from_sprint(sprint_name, issue_keys)

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
    from erpnext_agile.agile_backlog_manager import AgileBacklogManager
    manager = AgileBacklogManager()
    return manager.estimate_backlog_item(task_name, story_points, estimation_method)

@frappe.whitelist()
def split_story(task_name, split_data):
    """Split a user story into multiple stories"""
    if isinstance(split_data, str):
        split_data = json.loads(split_data)
    
    from erpnext_agile.agile_backlog_manager import AgileBacklogManager
    manager = AgileBacklogManager()
    return manager.split_story(task_name, split_data)

@frappe.whitelist()
def get_backlog_metrics(project):
    """Get backlog health metrics"""
    from erpnext_agile.agile_backlog_manager import AgileBacklogManager
    manager = AgileBacklogManager()
    return manager.get_backlog_metrics(project)

@frappe.whitelist()
def get_epic_progress(epic_name):
    """Get epic progress"""
    from erpnext_agile.agile_backlog_manager import AgileBacklogManager
    manager = AgileBacklogManager()
    return manager.get_epic_progress(epic_name)

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
    from erpnext_agile.agile_board_manager import AgileBoardManager
    manager = AgileBoardManager()
    return manager.move_issue(task_name, from_status, to_status, position)

@frappe.whitelist()
def quick_create_issue(project, status, issue_data):
    """Quick create issue from board"""
    if isinstance(issue_data, str):
        issue_data = json.loads(issue_data)
    
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
def get_swimlane_data(project, sprint=None, swimlane_by='epic'):
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

# ====================
# GITHUB INTEGRATION
# ====================

@frappe.whitelist()
def sync_agile_issue_to_github(task_name):
    """Sync agile issue to GitHub"""
    from erpnext_agile.agile_github_integration import AgileGitHubIntegration
    integration = AgileGitHubIntegration()
    return integration.sync_agile_issue_to_github(task_name)

@frappe.whitelist()
def sync_github_issue_to_agile(repo_issue_name):
    """Sync GitHub issue to agile task"""
    from erpnext_agile.agile_github_integration import AgileGitHubIntegration
    integration = AgileGitHubIntegration()
    return integration.sync_github_issue_to_agile(repo_issue_name).as_dict()

@frappe.whitelist()
def bulk_sync_project_issues(project_name):
    """Bulk sync all GitHub issues for a project"""
    from erpnext_agile.agile_github_integration import AgileGitHubIntegration
    integration = AgileGitHubIntegration()
    return integration.bulk_sync_project_issues(project_name)

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
    
    # Epic progress
    epics = frappe.get_all('Agile Epic',
        filters={'project': project},
        fields=['name', 'epic_name', 'status']
    )
    
    return {
        'project': project_doc.as_dict(),
        'active_sprint': active_sprint,
        'statistics': {
            'total_issues': total_issues,
            'completed_issues': completed_issues,
            'completion_percentage': (completed_issues / total_issues * 100) if total_issues > 0 else 0,
            'backlog_size': backlog_size
        },
        'epics': epics
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
        if filters.get('epic'):
            search_filters['epic'] = filters['epic']
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