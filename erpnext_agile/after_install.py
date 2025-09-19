import frappe

def after_install():
    """Setup default data after app installation"""
    create_default_issue_types()
    create_default_priorities() 
    create_default_statuses()
    create_default_workflows()
    create_default_permission_scheme()
    setup_custom_fields()
    create_sample_project()
    
    frappe.db.commit()
    print("ERPNext Agile installed successfully!")

def create_default_workflows():
    """Create default Jira-style workflow scheme"""
    try:
        if not frappe.db.exists("Agile Workflow Scheme", "Default Agile Workflow"):
            workflow_scheme = frappe.get_doc({
                "doctype": "Agile Workflow Scheme",
                "scheme_name": "Default Agile Workflow",
                "description": "Default Jira-style workflow scheme for agile projects",
                "transitions": [
                    {
                        "from_status": "Open",
                        "to_status": "In Progress",
                        "transition_name": "Start Progress",
                        "required_permission": "All"
                    },
                    {
                        "from_status": "Open",
                        "to_status": "Resolved",
                        "transition_name": "Resolve",
                        "required_permission": "Project Manager"
                    },
                    {
                        "from_status": "Open",
                        "to_status": "Closed",
                        "transition_name": "Close",
                        "required_permission": "Project Manager"
                    },
                    {
                        "from_status": "In Progress",
                        "to_status": "In Review",
                        "transition_name": "Send to Review",
                        "required_permission": "Developer"
                    },
                    {
                        "from_status": "In Progress",
                        "to_status": "Resolved",
                        "transition_name": "Resolve",
                        "required_permission": "Project Manager"
                    },
                    {
                        "from_status": "In Progress",
                        "to_status": "Closed",
                        "transition_name": "Close",
                        "required_permission": "Project Manager"
                    },
                    {
                        "from_status": "In Review",
                        "to_status": "In Progress",
                        "transition_name": "Return to Progress",
                        "required_permission": "Tester"
                    },
                    {
                        "from_status": "In Review",
                        "to_status": "Testing",
                        "transition_name": "Send to Testing",
                        "required_permission": "Tester"
                    },
                    {
                        "from_status": "In Review",
                        "to_status": "Resolved",
                        "transition_name": "Resolve",
                        "required_permission": "Project Manager"
                    },
                    {
                        "from_status": "Testing",
                        "to_status": "In Review",
                        "transition_name": "Return to Review",
                        "required_permission": "Tester"
                    },
                    {
                        "from_status": "Testing",
                        "to_status": "Resolved",
                        "transition_name": "Resolve",
                        "required_permission": "Project Manager"
                    },
                    {
                        "from_status": "Testing",
                        "to_status": "Closed",
                        "transition_name": "Close",
                        "required_permission": "Project Manager"
                    },
                    {
                        "from_status": "Resolved",
                        "to_status": "Closed",
                        "transition_name": "Close",
                        "required_permission": "Project Manager"
                    },
                    {
                        "from_status": "Resolved",
                        "to_status": "Reopened",
                        "transition_name": "Reopen",
                        "required_permission": "All"
                    },
                    {
                        "from_status": "Closed",
                        "to_status": "Reopened",
                        "transition_name": "Reopen",
                        "required_permission": "All"
                    }
                ]
            })
            workflow_scheme.insert()
            frappe.msgprint("Default workflow scheme 'Default Agile Workflow' created successfully")
    except Exception as e:
        frappe.log_error(f"Failed to create default workflow scheme: {str(e)}")

def create_default_permission_scheme():
    """Create default permission scheme for agile projects"""
    try:
        if not frappe.db.exists("Agile Permission Scheme", "Default Permission Scheme"):
            permission_scheme = frappe.get_doc({
                "doctype": "Agile Permission Scheme",
                "scheme_name": "Default Permission Scheme",
                "description": "Default permission scheme for agile projects",
                "permissions": [
                    {
                        "permission_type": "Resolve Issue",
                        "roles": ["Project Manager"]
                    },
                    {
                        "permission_type": "Close Issue",
                        "roles": ["Project Manager"]
                    },
                    {
                        "permission_type": "Assign Issue",
                        "roles": ["Project Manager", "Developer"]
                    },
                    {
                        "permission_type": "Create Issue",
                        "roles": ["Project Manager", "Developer", "Tester"]
                    },
                    {
                        "permission_type": "Edit Issue",
                        "roles": ["Project Manager", "Developer", "Tester"]
                    },
                    {
                        "permission_type": "All",
                        "roles": ["Project Manager", "Developer", "Tester", "Employee"]
                    }
                ]
            })
            permission_scheme.insert()
            frappe.msgprint("Default permission scheme 'Default Permission Scheme' created successfully")
    except Exception as e:
        frappe.log_error(f"Failed to create default permission scheme: {str(e)}")

def setup_custom_fields():
    """Add custom fields to existing doctypes"""
    
    # Add fields to Project doctype
    project_fields = [
        {
            "fieldname": "custom_agile_project",
            "fieldtype": "Link",
            "label": "Agile Project",
            "options": "Agile Project",
            "insert_after": "project_name"
        },
        {
            "fieldname": "custom_enable_agile",
            "fieldtype": "Check", 
            "label": "Enable Agile Features",
            "insert_after": "custom_agile_project"
        }
    ]
    
    for field in project_fields:
        create_custom_field("Project", field)
    
    # Add fields to Task doctype
    task_fields = [
        {
            "fieldname": "custom_agile_issue",
            "fieldtype": "Link",
            "label": "Agile Issue", 
            "options": "Agile Issue",
            "insert_after": "subject"
        },
        {
            "fieldname": "custom_issue_key",
            "fieldtype": "Data",
            "label": "Issue Key",
            "read_only": 1,
            "insert_after": "custom_agile_issue"
        },
        {
            "fieldname": "custom_story_points",
            "fieldtype": "Int",
            "label": "Story Points",
            "insert_after": "custom_issue_key"
        }
    ]
    
    for field in task_fields:
        create_custom_field("Task", field)
    
    # Add GitHub username to User doctype
    user_fields = [
        {
            "fieldname": "github_username",
            "fieldtype": "Data",
            "label": "GitHub Username",
            "insert_after": "email"
        }
    ]
    
    for field in user_fields:
        create_custom_field("User", field)

def create_custom_field(doctype, field_config):
    """Create custom field if it doesn't exist"""
    if not frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": field_config["fieldname"]}):
        custom_field = frappe.get_doc({
            "doctype": "Custom Field",
            "dt": doctype,
            **field_config
        })
        custom_field.insert()

def create_sample_project():
    """Create a sample agile project for demonstration"""
    if not frappe.db.exists("Agile Project", "Sample Agile Project"):
        sample_project = frappe.get_doc({
            "doctype": "Agile Project",
            "project_name": "Sample Agile Project",
            "project_key": "SAMPLE",
            "project_type": "Scrum",
            "project_lead": "Administrator",
            "workflow_scheme": "Default Agile Workflow",
            "permission_scheme": "Default Permission Scheme",
            "enable_email_notifications": 1
        })
        sample_project.insert()
        
        # Create sample issues
        create_sample_issues(sample_project.name)

def create_sample_issues(agile_project):
    """Create sample issues for demonstration"""
    sample_issues = [
        {
            "summary": "User authentication system",
            "issue_type": "Story",
            "priority": "High",
            "story_points": 8,
            "description": "Implement user login and registration functionality",
            "watchers": [{"user": "Administrator"}]
        },
        {
            "summary": "Fix login validation bug",
            "issue_type": "Bug", 
            "priority": "Critical",
            "story_points": 3,
            "description": "Login form doesn't validate email format properly",
            "watchers": [{"user": "Administrator"}]
        },
        {
            "summary": "Add dark mode toggle",
            "issue_type": "Task",
            "priority": "Medium", 
            "story_points": 5,
            "description": "Allow users to switch between light and dark themes",
            "watchers": [{"user": "Administrator"}]
        }
    ]
    
    for issue_data in sample_issues:
        issue = frappe.get_doc({
            "doctype": "Agile Issue",
            "agile_project": agile_project,
            **issue_data
        })
        issue.insert()
        
def create_default_issue_types():
    """Create Jira-style issue types"""
    issue_types = [
        {"name": "Story", "icon": "📖", "color": "#65ba43", "description": "User story"},
        {"name": "Bug", "icon": "🐛", "color": "#d73027", "description": "Software bug"},
        {"name": "Task", "icon": "✓", "color": "#4a90e2", "description": "General task"},
        {"name": "Epic", "icon": "🏛️", "color": "#998dd9", "description": "Large feature"},
        {"name": "Sub-task", "icon": "⚡", "color": "#707070", "description": "Subtask"},
        {"name": "Spike", "icon": "🔍", "color": "#f79232", "description": "Research task"}
    ]
    
    for issue_type in issue_types:
        if not frappe.db.exists("Agile Issue Type", issue_type["name"]):
            doc = frappe.get_doc({
                "doctype": "Agile Issue Type",
                **issue_type
            })
            doc.insert()

def create_default_priorities():
    """Create Jira-style priorities"""
    priorities = [
        {"name": "Critical", "color": "#d73027", "sort_order": 1},
        {"name": "High", "color": "#fc8d59", "sort_order": 2},
        {"name": "Medium", "color": "#fee08b", "sort_order": 3},
        {"name": "Low", "color": "#99d594", "sort_order": 4},
        {"name": "Lowest", "color": "#91bfdb", "sort_order": 5}
    ]
    
    for priority in priorities:
        if not frappe.db.exists("Agile Issue Priority", priority["name"]):
            doc = frappe.get_doc({
                "doctype": "Agile Issue Priority",
                **priority
            })
            doc.insert()

def create_default_statuses():
    """Create Jira-style statuses"""
    statuses = [
        {"name": "Open", "status_category": "To Do", "color": "#b3b3b3", "sort_order": 1},
        {"name": "In Progress", "status_category": "In Progress", "color": "#4a90e2", "sort_order": 2},
        {"name": "In Review", "status_category": "In Progress", "color": "#f79232", "sort_order": 3},
        {"name": "Testing", "status_category": "In Progress", "color": "#998dd9", "sort_order": 4},
        {"name": "Resolved", "status_category": "Done", "color": "#65ba43", "sort_order": 5},
        {"name": "Closed", "status_category": "Done", "color": "#999999", "sort_order": 6},
        {"name": "Reopened", "status_category": "To Do", "color": "#d73027", "sort_order": 7}
    ]
    
    for status in statuses:
        if not frappe.db.exists("Agile Issue Status", status["name"]):
            doc = frappe.get_doc({
                "doctype": "Agile Issue Status",
                **status
            })
            doc.insert()