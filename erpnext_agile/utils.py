import frappe
from frappe.utils import now, add_days, nowdate

def sync_github_data():
    """Daily sync of GitHub data for all agile projects"""
    agile_projects = frappe.get_all("Agile Project", {
        "github_repository": ["!=", ""]
    }, ["name", "github_repository"])
    
    for project in agile_projects:
        try:
            sync_project_github_data(project.name, project.github_repository)
        except Exception as e:
            frappe.log_error(f"GitHub sync failed for {project.name}: {str(e)}")

def sync_project_github_data(agile_project, repository):
    """Sync GitHub data for specific project"""
    # Sync issues
    github_issues = frappe.call(
        'erpnext_github_integration.github_api.list_issues',
        repository=repository
    )
    
    for gh_issue in github_issues:
        sync_github_issue_to_agile(gh_issue, agile_project)
    
    # Sync pull requests
    github_prs = frappe.call(
        'erpnext_github_integration.github_api.list_pull_requests',
        repository=repository
    )
    
    for gh_pr in github_prs:
        sync_github_pr_to_agile(gh_pr, agile_project)

def sync_github_issue_to_agile(gh_issue, agile_project):
    """Sync a GitHub issue to an Agile Issue"""
    try:
        issue_key = f"{agile_project}-{gh_issue['number']}"
        existing_issue = frappe.db.get_value("Agile Issue", {
            "agile_project": agile_project,
            "github_issue_number": gh_issue['number']
        }, "name")
        
        issue_data = {
            "doctype": "Agile Issue",
            "agile_project": agile_project,
            "issue_key": issue_key,
            "summary": gh_issue['title'],
            "description": gh_issue['body'] or "",
            "github_issue_number": gh_issue['number'],
            "status": map_github_status_to_agile(gh_issue['state']),
            "reporter": gh_issue['user']['login'] if gh_issue.get('user') else None,
            "assignee": gh_issue['assignee']['login'] if gh_issue.get('assignee') else None
        }
        
        if existing_issue:
            issue = frappe.get_doc("Agile Issue", existing_issue)
            issue.update(issue_data)
        else:
            issue = frappe.get_doc(issue_data)
        
        issue.insert(ignore_if_duplicate=True)
    except Exception as e:
        frappe.log_error(f"Failed to sync GitHub issue {gh_issue.get('number')} for project {agile_project}: {str(e)}")

def sync_github_pr_to_agile(gh_pr, agile_project):
    """Sync a GitHub pull request to an Agile Issue"""
    try:
        # Find the related Agile Issue by parsing the PR title or body for an issue key
        issue_key = extract_issue_key_from_pr(gh_pr)
        if not issue_key:
            return
        
        existing_issue = frappe.db.get_value("Agile Issue", {
            "agile_project": agile_project,
            "issue_key": issue_key
        }, "name")
        
        if existing_issue:
            issue = frappe.get_doc("Agile Issue", existing_issue)
            issue.github_pull_request = gh_pr['html_url']
            issue.github_branch = gh_pr['head']['ref'] if gh_pr.get('head') else None
            issue.status = "In Review" if gh_pr['state'] == "open" else issue.status
            issue.save()
    except Exception as e:
        frappe.log_error(f"Failed to sync GitHub PR {gh_pr.get('number')} for project {agile_project}: {str(e)}")

def extract_issue_key_from_pr(gh_pr):
    """Extract Agile Issue key from PR title or body"""
    # Example: PR title or body contains "SAMPLE-123"
    import re
    pattern = r"[A-Z]+-\d+"
    title = gh_pr.get('title', '')
    body = gh_pr.get('body', '') or ''
    match = re.search(pattern, title) or re.search(pattern, body)
    return match.group(0) if match else None

def create_agile_issue_from_task(task_doc, method):
    """Create agile issue when task is created in agile project"""
    # Check if task belongs to agile project
    if task_doc.project:
        agile_project = frappe.db.get_value("Agile Project", {"project": task_doc.project})
        if agile_project:
            create_linked_agile_issue(task_doc, agile_project)

def create_linked_agile_issue(task_doc, agile_project):
    """Create agile issue linked to task"""
    agile_issue = frappe.get_doc({
        "doctype": "Agile Issue",
        "summary": task_doc.subject,
        "description": task_doc.description,
        "agile_project": agile_project,
        "issue_type": "Task",
        "priority": "Medium",
        "assignee": getattr(task_doc, 'custom_assigned_to', None),
        "task": task_doc.name
    })
    
    agile_issue.insert()
    
    # Link back to task
    frappe.db.set_value("Task", task_doc.name, "custom_agile_issue", agile_issue.name)

def sync_task_to_agile_issue(doc, method):
    """Sync Task updates to Agile Issue"""
    if not doc.project:
        return
    
    agile_project = frappe.db.get_value("Agile Project", {"project": doc.project}, "name")
    if not agile_project:
        return
    
    issue = frappe.db.get_value("Agile Issue", {
        "task": doc.name,
        "agile_project": agile_project
    }, "name")
    
    if issue:
        issue_doc = frappe.get_doc("Agile Issue", issue)
        issue_doc.summary = doc.subject
        issue_doc.description = doc.description
        issue_doc.status = map_task_status_to_agile(doc.status)
        issue_doc.save()

def update_sprint_progress():
    """Update sprint progress metrics"""
    active_sprints = frappe.get_all("Agile Sprint", {
        "sprint_state": "Active"
    }, ["name", "agile_project"])
    
    for sprint in active_sprints:
        try:
            issues = frappe.get_all("Agile Issue", {
                "current_sprint": sprint.name,
                "agile_project": sprint.agile_project
            }, ["story_points", "status"])
            
            total_points = sum(issue.story_points or 0 for issue in issues)
            completed_points = sum(
                issue.story_points or 0 
                for issue in issues 
                if issue.status in ["Resolved", "Closed"]
            )
            
            sprint_doc = frappe.get_doc("Agile Sprint", sprint.name)
            sprint_doc.total_points = total_points
            sprint_doc.completed_points = completed_points
            sprint_doc.progress_percentage = (completed_points / total_points * 100) if total_points else 0
            sprint_doc.save()
            
        except Exception as e:
            frappe.log_error(f"Failed to update sprint {sprint.name}: {str(e)}")

def map_task_status_to_agile(task_status):
    """Map ERPNext Task status to Agile Issue status"""
    status_map = {
        "Open": "Open",
        "Working": "In Progress",
        "Completed": "Closed",
        "Cancelled": "Closed"
    }
    return status_map.get(task_status, "Open")

def map_github_status_to_agile(github_status):
    """Map GitHub issue status to Agile Issue status"""
    status_map = {
        "open": "Open",
        "closed": "Closed"
    }
    return status_map.get(github_status, "Open")

def check_agile_project_creation(doc, method):
    """Check and setup Agile Project on creation"""
    if not frappe.db.exists("Agile Project", {"project": doc.name}):
        agile_project = frappe.get_doc({
            "doctype": "Agile Project",
            "project": doc.name,
            "project_name": doc.project_name,
            "creation_date": nowdate(),
            "project_lead": doc.owner
        })
        agile_project.insert()
        
        # Create default workflow scheme
        create_default_workflows(agile_project)

def create_default_workflows(agile_project):
    """Create default workflow scheme and transitions for a new Agile Project"""
    try:
        workflow_scheme = frappe.get_doc({
            "doctype": "Agile Workflow Scheme",
            "scheme_name": f"Default Workflow for {agile_project.project_name}",
            "description": f"Default workflow scheme for {agile_project.project_name}",
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
        
        # Assign the workflow scheme to the Agile Project
        agile_project.workflow_scheme = workflow_scheme.name
        agile_project.save()
        
        frappe.msgprint(f"Default workflow scheme created for {agile_project.project_name}")
        
    except Exception as e:
        frappe.log_error(f"Failed to create default workflow for {agile_project.project_name}: {str(e)}")