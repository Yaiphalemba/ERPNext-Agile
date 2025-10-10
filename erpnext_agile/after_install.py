# erpnext_agile/patches/after_install.py
"""
Setup script to run after app installation
Creates necessary configurations, custom fields, and default data
"""

import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def setup_agile():
    """Main setup function"""
    print("Setting up ERPNext Agile...")
    
    # Create custom fields
    create_agile_custom_fields()
    
    # Create default statuses, priorities, and types
    create_default_issue_statuses()
    create_default_issue_priorities()
    create_default_issue_types()
    
    # Create roles
    create_agile_roles()
    
    # Setup permissions
    setup_agile_permissions()
    
    # Create email templates
    create_email_templates()
    
    # Create default workflow scheme
    create_default_workflow_scheme()
    
    print("ERPNext Agile setup completed successfully!")

def create_agile_custom_fields():
    """Create custom fields for Task and Project doctypes"""
    
    custom_fields = {
        'Task': [
            {
                'fieldname': 'is_agile',
                'label': 'Is Agile Issue',
                'fieldtype': 'Check',
                'insert_after': 'type',
                'default': '0'
            },
            {
                'fieldname': 'column_break_agile',
                'fieldtype': 'Column Break',
                'insert_after': 'is_agile'
            },
            {
                'fieldname': 'agile_details_section',
                'label': 'Agile Issue Details',
                'fieldtype': 'Section Break',
                'insert_after': 'description',
                'collapsible': 1,
                'depends_on': 'eval:doc.is_agile==1'
            },
            {
                'fieldname': 'issue_key',
                'label': 'Issue Key',
                'fieldtype': 'Data',
                'insert_after': 'agile_details_section',
                'read_only': 1,
                'unique': 1,
                'depends_on': 'eval:doc.is_agile==1'
            },
            {
                'fieldname': 'issue_type',
                'label': 'Issue Type',
                'fieldtype': 'Link',
                'options': 'Agile Issue Type',
                'insert_after': 'issue_key',
                'depends_on': 'eval:doc.is_agile==1'
            },
            {
                'fieldname': 'column_break_issue_details',
                'fieldtype': 'Column Break',
                'insert_after': 'issue_type'
            },
            {
                'fieldname': 'issue_status',
                'label': 'Issue Status',
                'fieldtype': 'Link',
                'options': 'Agile Issue Status',
                'insert_after': 'column_break_issue_details',
                'depends_on': 'eval:doc.is_agile==1'
            },
            {
                'fieldname': 'issue_priority',
                'label': 'Issue Priority',
                'fieldtype': 'Link',
                'options': 'Agile Issue Priority',
                'insert_after': 'issue_status',
                'depends_on': 'eval:doc.is_agile==1'
            },
            {
                'fieldname': 'reporter',
                'label': 'Reporter',
                'fieldtype': 'Link',
                'options': 'User',
                'insert_after': 'issue_priority',
                'default': '__user',
                'depends_on': 'eval:doc.is_agile==1'
            },
            {
                'fieldname': 'agile_planning_section',
                'label': 'Agile Planning',
                'fieldtype': 'Section Break',
                'insert_after': 'reporter',
                'collapsible': 1,
                'depends_on': 'eval:doc.is_agile==1'
            },
            {
                'fieldname': 'story_points',
                'label': 'Story Points',
                'fieldtype': 'Int',
                'insert_after': 'agile_planning_section',
                'depends_on': 'eval:doc.is_agile==1'
            },
            {
                'fieldname': 'current_sprint',
                'label': 'Sprint',
                'fieldtype': 'Link',
                'options': 'Agile Sprint',
                'insert_after': 'story_points',
                'depends_on': 'eval:doc.is_agile==1'
            },
            {
                'fieldname': 'column_break_planning',
                'fieldtype': 'Column Break',
                'insert_after': 'current_sprint'
            },
            {
                'fieldname': 'parent_issue',
                'label': 'Parent Issue',
                'fieldtype': 'Link',
                'options': 'Task',
                'insert_after': 'sprint',
                'depends_on': 'eval:doc.is_agile==1'
            },
            {
                'fieldname': 'time_tracking_section',
                'label': 'Time Tracking',
                'fieldtype': 'Section Break',
                'insert_after': 'parent_issue',
                'collapsible': 1,
                'depends_on': 'eval:doc.is_agile==1'
            },
            {
                'fieldname': 'original_estimate',
                'label': 'Original Estimate',
                'fieldtype': 'Int',
                'insert_after': 'time_tracking_section',
                'depends_on': 'eval:doc.is_agile==1'
            },
            {
                'fieldname': 'remaining_estimate',
                'label': 'Remaining Estimate',
                'fieldtype': 'Int',
                'insert_after': 'original_estimate',
                'depends_on': 'eval:doc.is_agile==1'
            },
            {
                'fieldname': 'time_spent',
                'label': 'Time Spent',
                'fieldtype': 'Int',
                'insert_after': 'remaining_estimate',
                'read_only': 1,
                'depends_on': 'eval:doc.is_agile==1'
            },
            {
                'fieldname': 'work_logs',
                'label': 'Work Logs',
                'fieldtype': 'Table',
                'options': 'Agile Issue Work Log',
                'insert_after': 'time_spent',
                'depends_on': 'eval:doc.is_agile==1'
            },
            {
                'fieldname': 'watchers',
                'label': 'Watchers',
                'fieldtype': 'Table',
                'options': 'Agile Issue Watcher',
                'insert_after': 'work_logs',
                'depends_on': 'eval:doc.is_agile==1'
            },
            {
                'fieldname': 'github_integration_section',
                'label': 'GitHub Integration',
                'fieldtype': 'Section Break',
                'insert_after': 'watchers',
                'collapsible': 1,
                'depends_on': 'eval:doc.is_agile==1'
            },
            {
                'fieldname': 'github_repo',
                'label': 'GitHub Repository',
                'fieldtype': 'Link',
                'options': 'Repository',
                'insert_after': 'github_integration_section',
                'depends_on': 'eval:doc.is_agile==1'
            },
            {
                'fieldname': 'github_issue_number',
                'label': 'GitHub Issue #',
                'fieldtype': 'Int',
                'insert_after': 'github_repo',
                'read_only': 1,
                'depends_on': 'eval:doc.is_agile==1'
            },
            {
                'fieldname': 'github_issue_doc',
                'label': 'GitHub Issue Doc',
                'fieldtype': 'Link',
                'options': 'Repository Issue',
                'insert_after': 'github_issue_number',
                'read_only': 1,
                'depends_on': 'eval:doc.is_agile==1'
            }
        ],
        'Project': [
            {
                'fieldname': 'agile_section',
                'label': 'Agile Configuration',
                'fieldtype': 'Section Break',
                'insert_after': 'project_name'
            },
            {
                'fieldname': 'enable_agile',
                'label': 'Enable Agile Features',
                'fieldtype': 'Check',
                'insert_after': 'agile_section',
                'default': '0'
            },
            {
                'fieldname': 'project_key',
                'label': 'Project Key',
                'fieldtype': 'Data',
                'insert_after': 'enable_agile',
                'unique': 1,
                'depends_on': 'enable_agile',
                'mandatory_depends_on': 'enable_agile',
                'description': 'Unique prefix for issue keys (e.g., PROJ)'
            },
            {
                'fieldname': 'column_break_agile',
                'fieldtype': 'Column Break',
                'insert_after': 'project_key'
            },
            {
                'fieldname': 'project_type_agile',
                'label': 'Agile Project Type',
                'fieldtype': 'Select',
                'options': 'Scrum\nKanban\nBug Tracking\nCustom',
                'insert_after': 'column_break_agile',
                'default': 'Scrum',
                'depends_on': 'enable_agile'
            },
            {
                'fieldname': 'workflow_section',
                'label': 'Workflow & Permissions',
                'fieldtype': 'Section Break',
                'insert_after': 'project_type_agile',
                'collapsible': 1,
                'depends_on': 'enable_agile'
            },
            {
                'fieldname': 'workflow_scheme',
                'label': 'Workflow Scheme',
                'fieldtype': 'Link',
                'options': 'Agile Workflow Scheme',
                'insert_after': 'workflow_section',
                'depends_on': 'enable_agile'
            },
            {
                'fieldname': 'permission_scheme',
                'label': 'Permission Scheme',
                'fieldtype': 'Link',
                'options': 'Agile Permission Scheme',
                'insert_after': 'workflow_scheme',
                'depends_on': 'enable_agile'
            },
            {
                'fieldname': 'issue_types_allowed',
                'label': 'Issue Types Allowed',
                'fieldtype': 'Table',
                'options': 'Agile Issue Types Allowed',
                'insert_after': 'permission_scheme',
                'depends_on': 'enable_agile'
            }
        ]
    }
    
    create_custom_fields(custom_fields, update=True)
    print("Custom fields created successfully")

def create_default_issue_statuses():
    """Create default issue statuses"""
    
    statuses = [
        {'status_name': 'To Do', 'status_category': 'To Do', 'color': '#808080', 'sort_order': 1},
        {'status_name': 'In Progress', 'status_category': 'In Progress', 'color': '#0066ff', 'sort_order': 2},
        {'status_name': 'In Review', 'status_category': 'In Progress', 'color': '#9966ff', 'sort_order': 3},
        {'status_name': 'Done', 'status_category': 'Done', 'color': '#00aa00', 'sort_order': 4},
        {'status_name': 'Blocked', 'status_category': 'To Do', 'color': '#ff0000', 'sort_order': 5}
    ]
    
    for status in statuses:
        if not frappe.db.exists('Agile Issue Status', {'status_name': status['status_name']}):
            doc = frappe.get_doc({
                'doctype': 'Agile Issue Status',
                **status
            })
            doc.insert(ignore_permissions=True)
    
    print("Default issue statuses created")

def create_default_issue_priorities():
    """Create default issue priorities"""
    
    priorities = [
        {'priority_name': 'Critical', 'color': '#ff0000', 'sort_order': 1, 'description': 'Highest priority'},
        {'priority_name': 'High', 'color': '#ff9900', 'sort_order': 2, 'description': 'High priority'},
        {'priority_name': 'Medium', 'color': '#ffcc00', 'sort_order': 3, 'description': 'Medium priority'},
        {'priority_name': 'Low', 'color': '#0066ff', 'sort_order': 4, 'description': 'Low priority'}
    ]
    
    for priority in priorities:
        if not frappe.db.exists('Agile Issue Priority', {'priority_name': priority['priority_name']}):
            doc = frappe.get_doc({
                'doctype': 'Agile Issue Priority',
                **priority
            })
            doc.insert(ignore_permissions=True)
    
    print("Default issue priorities created")

def create_default_issue_types():
    """Create default issue types"""
    
    types = [
        {'issue_type_name': 'Story', 'icon': '📖', 'color': '#4CAF50', 'description': 'User story'},
        {'issue_type_name': 'Task', 'icon': '✓', 'color': '#2196F3', 'description': 'General task'},
        {'issue_type_name': 'Bug', 'icon': '🐛', 'color': '#F44336', 'description': 'Bug or defect'},
        {'issue_type_name': 'Epic', 'icon': '🎯', 'color': '#9C27B0', 'description': 'Large feature or initiative'},
        {'issue_type_name': 'Spike', 'icon': '🔬', 'color': '#FF9800', 'description': 'Research or investigation'},
        {'issue_type_name': 'Sub-task', 'icon': '📝', 'color': '#607D8B', 'description': 'Sub-task of another issue'}
    ]
    
    for issue_type in types:
        if not frappe.db.exists('Agile Issue Type', {'issue_type_name': issue_type['issue_type_name']}):
            doc = frappe.get_doc({
                'doctype': 'Agile Issue Type',
                **issue_type
            })
            doc.insert(ignore_permissions=True)
    
    print("Default issue types created")

def create_agile_roles():
    """Create agile-specific roles"""
    
    roles = [
        {
            'role_name': 'Agile Admin',
            'desk_access': 1
        },
        {
            'role_name': 'Scrum Master',
            'desk_access': 1
        },
        {
            'role_name': 'Product Owner',
            'desk_access': 1
        }
    ]
    
    for role_data in roles:
        if not frappe.db.exists('Role', role_data['role_name']):
            doc = frappe.get_doc({
                'doctype': 'Role',
                **role_data
            })
            doc.insert(ignore_permissions=True)
    
    print("Agile roles created")

def setup_agile_permissions():
    """Setup permissions for agile doctypes"""
    
    doctypes = [
        'Agile Sprint',
        'Agile Issue Status',
        'Agile Issue Priority',
        'Agile Issue Type',
        'Agile Workflow Scheme',
        'Agile Permission Scheme'
    ]
    
    for doctype in doctypes:
        # System Manager - full access
        if not frappe.db.exists('Custom DocPerm', {'parent': doctype, 'role': 'System Manager'}):
            add_permission(doctype, 'System Manager', 0, read=1, write=1, create=1, delete=1, submit=0, cancel=0, amend=0)
        
        # Agile Admin - full access
        if not frappe.db.exists('Custom DocPerm', {'parent': doctype, 'role': 'Agile Admin'}):
            add_permission(doctype, 'Agile Admin', 0, read=1, write=1, create=1, delete=1, submit=0, cancel=0, amend=0)
        
        # Project Manager - read/write
        if not frappe.db.exists('Custom DocPerm', {'parent': doctype, 'role': 'Project Manager'}):
            add_permission(doctype, 'Project Manager', 0, read=1, write=1, create=1, delete=0, submit=0, cancel=0, amend=0)
    
    frappe.db.commit()
    print("Agile permissions setup completed")

def add_permission(doctype, role, perm_level, read=0, write=0, create=0, delete=0, submit=0, cancel=0, amend=0):
    """Add custom permission"""
    perm = frappe.get_doc({
        'doctype': 'Custom DocPerm',
        'parent': doctype,
        'role': role,
        'permlevel': perm_level,
        'read': read,
        'write': write,
        'create': create,
        'delete': delete,
        'submit': submit,
        'cancel': cancel,
        'amend': amend
    })
    perm.insert(ignore_permissions=True)

def create_email_templates():
    """Create email templates for notifications"""
    
    templates = [
        {
            'name': 'Agile Issue Notification',
            'subject': '[{{ task.issue_key }}] {{ event_type }} - {{ task.subject }}',
            'response': '''
                <p>Hello,</p>
                <p>Issue <strong>{{ task.issue_key }}</strong> has been {{ event_type }}.</p>
                <h3>{{ task.subject }}</h3>
                <p><strong>Type:</strong> {{ task.issue_type }}</p>
                <p><strong>Priority:</strong> {{ task.issue_priority }}</p>
                <p><strong>Status:</strong> {{ task.issue_status }}</p>
                <p><strong>Reporter:</strong> {{ task.reporter }}</p>
                <p><a href="{{ site_url }}/app/task/{{ task.name }}">View Issue</a></p>
            '''
        },
        {
            'name': 'Agile Sprint Notification',
            'subject': 'Sprint {{ event_type }}: {{ sprint.sprint_name }}',
            'response': '''
                <p>Hello,</p>
                <p>Sprint <strong>{{ sprint.sprint_name }}</strong> has been {{ event_type }}.</p>
                <p><strong>Sprint Goal:</strong> {{ sprint.sprint_goal }}</p>
                <p><strong>Start Date:</strong> {{ sprint.start_date }}</p>
                <p><strong>End Date:</strong> {{ sprint.end_date }}</p>
                <p><a href="{{ site_url }}/app/agile-sprint/{{ sprint.name }}">View Sprint</a></p>
            '''
        }
    ]
    
    for template in templates:
        if not frappe.db.exists('Email Template', template['name']):
            doc = frappe.get_doc({
                'doctype': 'Email Template',
                **template
            })
            doc.insert(ignore_permissions=True)
    
    print("Email templates created")

def create_default_workflow_scheme():
    """Create a default workflow scheme"""
    
    if not frappe.db.exists('Agile Workflow Scheme', 'Default Scrum Workflow'):
        workflow = frappe.get_doc({
            'doctype': 'Agile Workflow Scheme',
            'scheme_name': 'Default Scrum Workflow',
            'description': 'Standard Scrum workflow with common transitions'
        })
        
        # Add transitions
        transitions = [
            {'from_status': 'To Do', 'to_status': 'In Progress', 'transition_name': 'Start Progress'},
            {'from_status': 'To Do', 'to_status': 'Blocked', 'transition_name': 'Block'},
            {'from_status': 'In Progress', 'to_status': 'In Review', 'transition_name': 'Submit for Review'},
            {'from_status': 'In Progress', 'to_status': 'Blocked', 'transition_name': 'Block'},
            {'from_status': 'In Progress', 'to_status': 'To Do', 'transition_name': 'Stop Progress'},
            {'from_status': 'In Review', 'to_status': 'Done', 'transition_name': 'Approve'},
            {'from_status': 'In Review', 'to_status': 'In Progress', 'transition_name': 'Request Changes'},
            {'from_status': 'Blocked', 'to_status': 'To Do', 'transition_name': 'Unblock'},
            {'from_status': 'Done', 'to_status': 'In Progress', 'transition_name': 'Reopen'}
        ]
        
        for trans in transitions:
            workflow.append('transitions', trans)
        
        workflow.insert(ignore_permissions=True)
        print("Default workflow scheme created")