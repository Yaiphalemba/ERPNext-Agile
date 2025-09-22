import frappe

def after_install():
    """Setup default data after app installation"""
    create_default_statuses()
    frappe.db.commit()
    create_default_issue_types()
    frappe.db.commit()
    create_default_priorities()
    frappe.db.commit()
    create_default_roles()
    frappe.db.commit()
    create_default_workflows()
    frappe.db.commit()
    create_default_permission_scheme()
    frappe.db.commit()
    setup_custom_fields()
    frappe.db.commit()
    create_sample_project()
    frappe.db.commit()
    print("ERPNext Agile installed successfully!")

def create_default_roles():
    """Create required roles for agile projects"""
    try:
        roles = ["Project Manager", "Developer", "Tester", "Employee"]
        for role in roles:
            if not frappe.db.exists("Role", role):
                frappe.get_doc({
                    "doctype": "Role",
                    "role_name": role
                }).insert()
        frappe.msgprint("Default roles created successfully")
    except Exception as e:
        frappe.log_error(f"Failed to create default roles: {str(e)}"[:140], "Role Creation Error")

def create_default_workflows():
    """Create default Jira-style workflow scheme"""
    try:
        # Validate that required statuses exist
        required_statuses = [
            "Open", "In Progress", "In Review", "Testing", 
            "Resolved", "Closed", "Reopened"
        ]
        for status in required_statuses:
            if not frappe.db.exists("Agile Issue Status", status):
                frappe.log_error(f"Missing required status: {status}"[:140], "Workflow Creation Error")
                return
        
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
        frappe.log_error(f"Failed to create default workflow scheme: {str(e)}"[:140], "Workflow Creation Error")

def create_default_permission_scheme():
    """Create default permission scheme for agile projects"""
    try:
        if not frappe.db.exists("Agile Permission Scheme", "Default Permission Scheme"):
            # Validate roles
            valid_roles = []
            required_roles = ["Project Manager", "Developer", "Tester", "Employee"]
            for role in required_roles:
                if frappe.db.exists("Role", role):
                    valid_roles.append(role)
                else:
                    frappe.log_error(f"Role {role} not found, skipping in permission scheme"[:140], "Permission Scheme Role Error")
            
            if not valid_roles:
                frappe.log_error("No valid roles found for permission scheme"[:140], "Permission Scheme Creation Error")
                return

            permission_scheme = frappe.get_doc({
                "doctype": "Agile Permission Scheme",
                "scheme_name": "Default Permission Scheme",
                "description": "Default permission scheme for agile projects",
                "permissions": [
                    {
                        "permission_type": "Resolve Issue",
                        "roles": [role for role in ["Project Manager"] if role in valid_roles]
                    },
                    {
                        "permission_type": "Close Issue",
                        "roles": [role for role in ["Project Manager"] if role in valid_roles]
                    },
                    {
                        "permission_type": "Assign Issue",
                        "roles": [role for role in ["Project Manager", "Developer"] if role in valid_roles]
                    },
                    {
                        "permission_type": "Create Issue",
                        "roles": [role for role in ["Project Manager", "Developer", "Tester"] if role in valid_roles]
                    },
                    {
                        "permission_type": "Edit Issue",
                        "roles": [role for role in ["Project Manager", "Developer", "Tester"] if role in valid_roles]
                    },
                    {
                        "permission_type": "All",
                        "roles": [role for role in valid_roles]
                    }
                ]
            })
            permission_scheme.insert()
            frappe.msgprint("Default permission scheme 'Default Permission Scheme' created successfully")
    except Exception as e:
        frappe.log_error(f"Failed to create default permission scheme: {str(e)}"[:140], "Permission Scheme Creation Error")

def setup_custom_fields():
    """Add custom fields to existing doctypes"""
    try:
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
    except Exception as e:
        frappe.log_error(f"Failed to setup custom fields: {str(e)}"[:140], "Custom Field Creation Error")

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
    try:
        if not frappe.db.exists("Agile Project", "Sample Agile Project"):
            # Validate workflow and permission schemes
            if not frappe.db.exists("Agile Workflow Scheme", "Default Agile Workflow"):
                frappe.log_error("Default Agile Workflow not found, skipping sample project creation"[:140], "Sample Project Creation Error")
                return
            if not frappe.db.exists("Agile Permission Scheme", "Default Permission Scheme"):
                frappe.log_error("Default Permission Scheme not found, skipping sample project creation"[:140], "Sample Project Creation Error")
                return

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
            
            # Create sample epic
            if not frappe.db.exists("Agile Epic", "Sample Epic"):
                sample_epic = frappe.get_doc({
                    "doctype": "Agile Epic",
                    "epic_name": "Sample Epic",
                    "agile_project": sample_project.name,
                    "description": "Sample epic for demonstration",
                    "status": "Open"
                })
                sample_epic.insert()
            
            # Create sample issues
            create_sample_issues(sample_project.name, sample_epic.name)
            frappe.msgprint("Sample Agile Project created successfully")
    except Exception as e:
        frappe.log_error(f"Failed to create sample project: {str(e)}"[:140], "Sample Project Creation Error")

def create_sample_issues(agile_project, epic=None):
    """Create sample issues for demonstration"""
    try:
        project_key = frappe.db.get_value("Agile Project", agile_project, "project_key")
        # Get the last issue number for this project to generate unique issue_key
        last_issue = frappe.db.sql("""
            SELECT issue_key FROM `tabAgile Issue`
            WHERE agile_project = %s
            ORDER BY creation DESC LIMIT 1
        """, agile_project)
        start_number = int(last_issue[0][0].split('-')[-1]) + 1 if last_issue else 1

        sample_issues = [
            {
                "issue_key": f"{project_key}-{start_number}",
                "summary": "User authentication system",
                "issue_type": "Story",
                "priority": "High",
                "status": "Open",
                "epic": epic,
                "agile_project": agile_project,
                "story_points": 8,
                "description": "Implement user login and registration functionality",
                "assignee": "Administrator",
                "reporter": "Administrator",
                "watchers": [{"user": "Administrator"}]
            },
            {
                "issue_key": f"{project_key}-{start_number + 1}",
                "summary": "Fix login validation bug",
                "issue_type": "Bug",
                "priority": "Critical",
                "status": "Open",
                "epic": epic,
                "agile_project": agile_project,
                "story_points": 3,
                "description": "Login form doesn't validate email format properly",
                "assignee": "Administrator",
                "reporter": "Administrator",
                "watchers": [{"user": "Administrator"}]
            },
            {
                "issue_key": f"{project_key}-{start_number + 2}",
                "summary": "Add dark mode toggle",
                "issue_type": "Task",
                "priority": "Medium",
                "status": "Open",
                "epic": epic,
                "agile_project": agile_project,
                "story_points": 5,
                "description": "Allow users to switch between light and dark themes",
                "assignee": "Administrator",
                "reporter": "Administrator",
                "watchers": [{"user": "Administrator"}]
            }
        ]
        
        for issue_data in sample_issues:
            issue = frappe.get_doc({
                "doctype": "Agile Issue",
                **issue_data
            })
            issue.insert()
        frappe.msgprint("Sample issues created successfully")
    except Exception as e:
        frappe.log_error(f"Failed to create sample issues: {str(e)}"[:140], "Sample Issue Creation Error")

def create_default_issue_types():
    """Create Jira-style issue types"""
    try:
        issue_types = [
            {"issue_type_name": "Story", "icon": "📖", "color": "#65ba43", "description": "User story"},
            {"issue_type_name": "Bug", "icon": "🐛", "color": "#d73027", "description": "Software bug"},
            {"issue_type_name": "Task", "icon": "✓", "color": "#4a90e2", "description": "General task"},
            {"issue_type_name": "Epic", "icon": "🏛️", "color": "#998dd9", "description": "Large feature"},
            {"issue_type_name": "Sub-task", "icon": "⚡", "color": "#707070", "description": "Subtask"},
            {"issue_type_name": "Spike", "icon": "🔍", "color": "#f79232", "description": "Research task"}
        ]
        
        for issue_type in issue_types:
            if not frappe.db.exists("Agile Issue Type", issue_type["issue_type_name"]):
                doc = frappe.get_doc({
                    "doctype": "Agile Issue Type",
                    **issue_type
                })
                doc.insert()
        frappe.msgprint("Default issue types created successfully")
    except Exception as e:
        frappe.log_error(f"Failed to create default issue types: {str(e)}"[:140], "Issue Type Creation Error")

def create_default_priorities():
    """Create Jira-style priorities"""
    try:
        priorities = [
            {"priority_name": "Critical", "color": "#d73027", "sort_order": 1},
            {"priority_name": "High", "color": "#fc8d59", "sort_order": 2},
            {"priority_name": "Medium", "color": "#fee08b", "sort_order": 3},
            {"priority_name": "Low", "color": "#99d594", "sort_order": 4},
            {"priority_name": "Lowest", "color": "#91bfdb", "sort_order": 5}
        ]
        
        for priority in priorities:
            if not frappe.db.exists("Agile Issue Priority", {"priority_name": priority["priority_name"]}):
                doc = frappe.get_doc({
                    "doctype": "Agile Issue Priority",
                    **priority
                })
                doc.insert()
        frappe.msgprint("Default priorities created successfully")
    except Exception as e:
        frappe.log_error(f"Failed to create default priorities: {str(e)}"[:140], "Priority Creation Error")

def create_default_statuses():
    """Create Jira-style statuses"""
    try:
        statuses = [
            {"status_name": "Open", "status_category": "To Do", "color": "#b3b3b3", "sort_order": 1},
            {"status_name": "In Progress", "status_category": "In Progress", "color": "#4a90e2", "sort_order": 2},
            {"status_name": "In Review", "status_category": "In Progress", "color": "#f79232", "sort_order": 3},
            {"status_name": "Testing", "status_category": "In Progress", "color": "#998dd9", "sort_order": 4},
            {"status_name": "Resolved", "status_category": "Done", "color": "#65ba43", "sort_order": 5},
            {"status_name": "Closed", "status_category": "Done", "color": "#999999", "sort_order": 6},
            {"status_name": "Reopened", "status_category": "To Do", "color": "#d73027", "sort_order": 7}
        ]
        
        for status in statuses:
            if not frappe.db.exists("Agile Issue Status", status["status_name"]):
                doc = frappe.get_doc({
                    "doctype": "Agile Issue Status",
                    **status
                })
                doc.insert()
        frappe.msgprint("Default statuses created successfully")
    except Exception as e:
        frappe.log_error(f"Failed to create default statuses: {str(e)}"[:140], "Status Creation Error")