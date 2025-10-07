# erpnext_agile/utils.py
"""
Utility functions for ERPNext Agile
"""

import frappe
from frappe import _
from frappe.utils import flt, cint, today, add_days, date_diff
import json

def get_project_metrics(project):
    """Get comprehensive project metrics"""
    
    # Issue counts
    total_issues = frappe.db.count('Task', {
        'project': project,
        'is_agile': 1,
        'status': ['!=', 'Cancelled']
    })
    
    done_statuses = get_done_statuses()
    completed_issues = frappe.db.count('Task', {
        'project': project,
        'is_agile': 1,
        'issue_status': ['in', done_statuses]
    })
    
    # Sprint metrics
    active_sprint = frappe.db.get_value('Agile Sprint', {
        'project': project,
        'sprint_state': 'Active'
    }, ['name', 'completed_points', 'total_points'], as_dict=True)
    
    # Backlog size
    backlog_size = frappe.db.count('Task', {
        'project': project,
        'is_agile': 1,
        'current_sprint': ['in', ['', None]],
        'status': ['!=', 'Cancelled']
    })
    
    return {
        'total_issues': total_issues,
        'completed_issues': completed_issues,
        'completion_rate': (completed_issues / total_issues * 100) if total_issues > 0 else 0,
        'backlog_size': backlog_size,
        'active_sprint': active_sprint
    }

def get_done_statuses():
    """Get all status names in Done category"""
    return [s.name for s in frappe.get_all(
        'Agile Issue Status',
        filters={'status_category': 'Done'},
        fields=['name']
    )]

def get_in_progress_statuses():
    """Get all status names in In Progress category"""
    return [s.name for s in frappe.get_all(
        'Agile Issue Status',
        filters={'status_category': 'In Progress'},
        fields=['name']
    )]

def calculate_velocity(project, sprint_count=5):
    """Calculate team velocity based on recent sprints"""
    
    completed_sprints = frappe.get_all('Agile Sprint',
        filters={'project': project, 'sprint_state': 'Completed'},
        fields=['name', 'completed_points'],
        order_by='end_date desc',
        limit=sprint_count
    )
    
    if not completed_sprints:
        return 0
    
    total_points = sum(s.get('completed_points', 0) for s in completed_sprints)
    return round(total_points / len(completed_sprints), 1)

def get_user_issue_count(user, status_filter=None):
    """Get issue count for a user"""
    filters = {
        'is_agile': 1,
        'status': ['!=', 'Cancelled']
    }
    
    if status_filter:
        filters['issue_status'] = status_filter
    
    # Get issues where user is assigned
    count = frappe.db.sql("""
        SELECT COUNT(DISTINCT t.name)
        FROM `tabTask` t
        INNER JOIN `tabTask Assigned To` ta ON ta.parent = t.name
        WHERE ta.user = %s
        AND t.is_agile = 1
        AND t.status != 'Cancelled'
        {status_condition}
    """.format(
        status_condition=f"AND t.issue_status IN ({','.join(['%s'] * len(status_filter))})" 
        if status_filter else ""
    ), [user] + (status_filter if status_filter else []))[0][0]
    
    return count

def validate_sprint_capacity(sprint_name):
    """Validate if sprint capacity is exceeded"""
    
    sprint_doc = frappe.get_doc('Agile Sprint', sprint_name)
    project_doc = frappe.get_doc('Project', sprint_doc.project)
    
    # Get sprint issues
    sprint_points = frappe.db.sql("""
        SELECT SUM(story_points) 
        FROM `tabTask`
        WHERE current_sprint = %s AND is_agile = 1
    """, sprint_name)[0][0] or 0
    
    # Get team velocity
    team_velocity = calculate_velocity(sprint_doc.project)
    
    # Calculate sprint duration in days
    sprint_days = date_diff(sprint_doc.end_date, sprint_doc.start_date) or 14
    
    # Expected capacity (velocity * weeks)
    weeks = sprint_days / 7
    expected_capacity = team_velocity * weeks
    
    if sprint_points > expected_capacity * 1.2:  # 20% over capacity
        return {
            'over_capacity': True,
            'sprint_points': sprint_points,
            'expected_capacity': expected_capacity,
            'percentage': (sprint_points / expected_capacity * 100) if expected_capacity > 0 else 0
        }
    
    return {'over_capacity': False}

def get_issue_link(issue_key):
    """Get full URL to an issue"""
    site_url = frappe.utils.get_url()
    task_name = frappe.db.get_value('Task', {'issue_key': issue_key}, 'name')
    if task_name:
        return f"{site_url}/app/task/{task_name}"
    return None

def format_story_points(points):
    """Format story points for display"""
    if not points:
        return "Unestimated"
    return f"{flt(points)} pts"

def get_available_transitions(task_name, current_status):
    """Get available transitions for an issue"""
    
    task_doc = frappe.get_doc('Task', task_name)
    project_doc = frappe.get_doc('Project', task_doc.project)
    
    workflow_scheme = project_doc.get('workflow_scheme')
    
    if workflow_scheme:
        scheme_doc = frappe.get_doc('Agile Workflow Scheme', workflow_scheme)
        return scheme_doc.get_transitions(current_status)
    else:
        # Default transitions
        return [
            {'to_status': 'In Progress', 'transition_name': 'Start Progress'},
            {'to_status': 'Done', 'transition_name': 'Complete'},
            {'to_status': 'Blocked', 'transition_name': 'Block'}
        ]

def check_issue_permission(task_name, permission_type, user=None):
    """Check if user has permission for an operation"""
    
    if not user:
        user = frappe.session.user
    
    task_doc = frappe.get_doc('Task', task_name)
    project_doc = frappe.get_doc('Project', task_doc.project)
    
    # Check permission scheme
    permission_scheme = project_doc.get('permission_scheme')
    
    if permission_scheme:
        scheme_doc = frappe.get_doc('Agile Permission Scheme', permission_scheme)
        return scheme_doc.has_permission(permission_type, user)
    
    # Default: allow all for now
    return True

def create_default_agile_configuration(project):
    """Create default agile configuration for a project"""
    
    project_doc = frappe.get_doc('Project', project)
    
    # Create default issue types if not exists
    default_types = ['Story', 'Task', 'Bug', 'Epic']
    for type_name in default_types:
        if not frappe.db.exists('Agile Issue Type', type_name):
            frappe.get_doc({
                'doctype': 'Agile Issue Type',
                'issue_type_name': type_name,
                'icon': get_default_icon(type_name)
            }).insert()
        
        # Add to project
        project_doc.append('issue_types_allowed', {
            'issue_type': type_name
        })
    
    # Create default statuses if not exists
    default_statuses = [
        {'name': 'To Do', 'category': 'To Do', 'color': '#808080'},
        {'name': 'In Progress', 'category': 'In Progress', 'color': '#0066ff'},
        {'name': 'Done', 'category': 'Done', 'color': '#00aa00'},
        {'name': 'Blocked', 'category': 'To Do', 'color': '#ff0000'}
    ]
    
    for status in default_statuses:
        if not frappe.db.exists('Agile Issue Status', status['name']):
            frappe.get_doc({
                'doctype': 'Agile Issue Status',
                'status_name': status['name'],
                'status_category': status['category'],
                'color': status['color']
            }).insert()
    
    # Create default priorities if not exists
    default_priorities = [
        {'name': 'Critical', 'color': '#ff0000', 'sort_order': 1},
        {'name': 'High', 'color': '#ff9900', 'sort_order': 2},
        {'name': 'Medium', 'color': '#ffcc00', 'sort_order': 3},
        {'name': 'Low', 'color': '#0066ff', 'sort_order': 4}
    ]
    
    for priority in default_priorities:
        if not frappe.db.exists('Agile Issue Priority', priority['name']):
            frappe.get_doc({
                'doctype': 'Agile Issue Priority',
                'priority_name': priority['name'],
                'color': priority['color'],
                'sort_order': priority['sort_order']
            }).insert()
    
    project_doc.save()

def get_default_icon(issue_type):
    """Get default icon for issue type"""
    icons = {
        'Story': '📖',
        'Task': '✓',
        'Bug': '🐛',
        'Epic': '🎯'
    }
    return icons.get(issue_type, '📝')

def cleanup_completed_sprint(sprint_name):
    """Clean up after sprint completion"""
    
    sprint_doc = frappe.get_doc('Agile Sprint', sprint_name)
    
    # Move incomplete issues to backlog
    incomplete_issues = frappe.get_all('Task',
        filters={
            'current_sprint': sprint_name,
            'is_agile': 1,
            'issue_status': ['not in', get_done_statuses()]
        }
    )
    
    for issue in incomplete_issues:
        frappe.db.set_value('Task', issue.name, 'current_sprint', '')
    
    return len(incomplete_issues)

def get_sprint_health(sprint_name):
    """Get sprint health indicators"""
    
    sprint_doc = frappe.get_doc('Agile Sprint', sprint_name)
    
    # Calculate days remaining
    days_total = date_diff(sprint_doc.end_date, sprint_doc.start_date) or 1
    days_passed = date_diff(today(), sprint_doc.actual_start_date or sprint_doc.start_date)
    days_remaining = days_total - days_passed
    
    # Calculate progress
    total_points = sprint_doc.total_points or 0
    completed_points = sprint_doc.completed_points or 0
    
    expected_completion = (days_passed / days_total) * 100 if days_total > 0 else 0
    actual_completion = (completed_points / total_points) * 100 if total_points > 0 else 0
    
    # Determine health
    health = 'green'
    if actual_completion < expected_completion - 20:
        health = 'red'
    elif actual_completion < expected_completion - 10:
        health = 'yellow'
    
    return {
        'health': health,
        'days_remaining': days_remaining,
        'expected_completion': round(expected_completion, 1),
        'actual_completion': round(actual_completion, 1),
        'on_track': actual_completion >= expected_completion
    }

@frappe.whitelist()
def get_available_transitions_api(task_name, from_status):
    """API method to get available transitions"""
    return get_available_transitions(task_name, from_status)