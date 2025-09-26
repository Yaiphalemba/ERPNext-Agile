# erpnext_agile/utils.py (Updated for native doctypes)
import frappe
import re
from frappe.utils import nowdate, now

def sync_github_data():
    """Daily sync of GitHub data for all agile projects"""
    try:
        if not frappe.db.exists("App", "erpnext_github_integration"):
            return  # Skip if GitHub integration app is not installed
        
        agile_projects = frappe.get_all("Project", {
            "enable_agile": 1,
            "github_repository": ["!=", ""],
            "auto_create_github_issues": 1
        }, ["name", "github_repository"])
        
        for project in agile_projects:
            sync_project_github_data(project.name, project.github_repository)
    except Exception as e:
        frappe.log_error(f"GitHub sync failed: {str(e)}"[:140], "GitHub Sync Error")

def sync_project_github_data(project, repository):
    """Sync GitHub data for specific agile project"""
    try:
        # Sync issues
        github_issues = frappe.call(
            'erpnext_github_integration.github_api.list_issues',
            repository=repository
        ) or []
        
        for gh_issue in github_issues:
            sync_github_issue_to_task(gh_issue, project)
        
        # Sync pull requests
        github_prs = frappe.call(
            'erpnext_github_integration.github_api.list_pull_requests',
            repository=repository
        ) or []
        
        for gh_pr in github_prs:
            sync_github_pr_to_task(gh_pr, project)
    except Exception as e:
        frappe.log_error(f"GitHub sync failed for project {project}: {str(e)}"[:140], "Project GitHub Sync Error")

def sync_github_issue_to_task(gh_issue, project):
    """Sync a GitHub issue to a Task (formerly Agile Issue)"""
    try:
        project_doc = frappe.get_cached_doc("Project", project)
        if not project_doc.project_key:
            return
            
        issue_key = f"{project_doc.project_key}-{gh_issue['number']}"
        existing_task = frappe.db.get_value("Task", {
            "project": project,
            "github_issue_number": gh_issue['number']
        }, "name")
        
        task_data = {
            "doctype": "Task",
            "project": project,
            "issue_key": issue_key,
            "subject": gh_issue['title'],
            "description": gh_issue['body'] or "",
            "github_issue_number": gh_issue['number'],
            "status": map_github_status_to_task_status(gh_issue['state']),
            "reporter": get_user_by_github_username(gh_issue['user']['login']) if gh_issue.get('user') else None,
            "assigned_to": get_user_by_github_username(gh_issue['assignee']['login']) if gh_issue.get('assignee') else None
        }
        
        if existing_task:
            task = frappe.get_doc("Task", existing_task)
            task.update(task_data)
        else:
            task = frappe.get_doc(task_data)
        
        task.flags.ignore_validate = True  # Skip validation during sync
        task.save()
    except Exception as e:
        frappe.log_error(f"Failed to sync GitHub issue {gh_issue.get('number')} for project {project}: {str(e)}"[:140], "GitHub Issue Sync Error")

def sync_github_pr_to_task(gh_pr, project):
    """Sync a GitHub pull request to a Task"""
    try:
        issue_key = extract_issue_key_from_pr(gh_pr)
        if not issue_key:
            return
        
        existing_task = frappe.db.get_value("Task", {
            "project": project,
            "issue_key": issue_key
        }, "name")
        
        if existing_task:
            task = frappe.get_doc("Task", existing_task)
            task.github_pull_request = gh_pr['number']
            task.github_branch = gh_pr['head']['ref'] if gh_pr.get('head') else None
            if gh_pr['state'] == "open":
                task.status = "Pending Review"
            elif gh_pr.get('merged'):
                task.status = "Completed"
            task.save()
    except Exception as e:
        frappe.log_error(f"Failed to sync GitHub PR {gh_pr.get('number')} for project {project}: {str(e)}"[:140], "GitHub PR Sync Error")

def extract_issue_key_from_pr(gh_pr):
    """Extract Task issue key from PR title or body"""
    try:
        pattern = r"[A-Z]+-\d+"
        title = gh_pr.get('title', '')
        body = gh_pr.get('body', '') or ''
        match = re.search(pattern, title) or re.search(pattern, body)
        return match.group(0) if match else None
    except Exception as e:
        frappe.log_error(f"Failed to extract issue key from PR: {str(e)}"[:140], "Issue Key Extraction Error")
        return None

def get_user_by_github_username(github_username):
    """Get ERPNext user by GitHub username"""
    try:
        return frappe.db.get_value("User", {"github_username": github_username}, "name")
    except Exception:
        return None

def setup_default_agile_data(doc, method):
    """Setup default agile data when project enables agile features"""
    try:
        if doc.enable_agile and not doc.workflow_scheme:
            # Assign default workflow scheme
            default_scheme = frappe.db.get_value("Agile Workflow Scheme", 
                                               {"scheme_name": "Default Agile Workflow"}, "name")
            if default_scheme:
                frappe.db.set_value("Project", doc.name, "workflow_scheme", default_scheme)
            
            # Assign default permission scheme
            default_permission = frappe.db.get_value("Agile Permission Scheme",
                                                    {"scheme_name": "Default Permission Scheme"}, "name") 
            if default_permission:
                frappe.db.set_value("Project", doc.name, "permission_scheme", default_permission)
                
            frappe.db.commit()
    except Exception as e:
        frappe.log_error(f"Failed to setup default agile data: {str(e)}"[:140], "Setup Agile Data Error")

def setup_agile_task_data(doc, method):
    """Setup agile data for new tasks in agile projects"""
    try:
        if doc.project:
            project = frappe.get_cached_doc("Project", doc.project)
            if project.enable_agile:
                # Auto-assign default values if not set
                if not doc.issue_type:
                    doc.issue_type = "Task"
                if not doc.issue_priority:
                    doc.issue_priority = "Medium"
                if not doc.reporter:
                    doc.reporter = frappe.session.user
                
                # Generate issue key if not present
                if not doc.issue_key:
                    doc.issue_key = generate_task_issue_key(doc.project)
    except Exception as e:
        frappe.log_error(f"Failed to setup agile task data: {str(e)}"[:140], "Setup Agile Task Error")

def generate_task_issue_key(project):
    """Generate unique issue key for task"""
    try:
        project_doc = frappe.get_cached_doc("Project", project)
        if not project_doc.project_key:
            return None
        
        # Get next number for this project
        last_task = frappe.db.sql("""
            SELECT issue_key FROM `tabTask` 
            WHERE project = %s AND issue_key IS NOT NULL AND issue_key != ''
            ORDER BY creation DESC LIMIT 1
        """, project)
        
        if last_task and last_task[0][0]:
            # Extract number from last issue key
            last_number = int(last_task[0][0].split('-')[-1])
            next_number = last_number + 1
        else:
            next_number = 1
        
        return f"{project_doc.project_key}-{next_number}"
    except Exception as e:
        frappe.log_error(f"Failed to generate task issue key: {str(e)}"[:140], "Generate Issue Key Error")
        return None

def validate_agile_task(doc, method):
    """Validate agile task before saving"""
    try:
        if doc.project:
            project = frappe.get_cached_doc("Project", doc.project)
            if project.enable_agile:
                # Validate issue key uniqueness
                if doc.issue_key:
                    existing = frappe.db.exists("Task", {
                        "issue_key": doc.issue_key,
                        "name": ["!=", doc.name]
                    })
                    if existing:
                        frappe.throw(f"Issue key {doc.issue_key} already exists")
                
                # Validate issue type and priority
                if doc.issue_type and not frappe.db.exists("Agile Issue Type", doc.issue_type):
                    frappe.throw(f"Invalid Issue Type: {doc.issue_type}")
                
                if doc.issue_priority and not frappe.db.exists("Agile Issue Priority", doc.issue_priority):
                    frappe.throw(f"Invalid Priority: {doc.issue_priority}")
    except Exception as e:
        frappe.log_error(f"Failed to validate agile task: {str(e)}"[:140], "Validate Agile Task Error")
        raise

def sync_agile_task_changes(doc, method):
    """Sync task changes to GitHub and other integrations"""
    try:
        if doc.project:
            project = frappe.get_cached_doc("Project", doc.project)
            if project.enable_agile and project.auto_create_github_issues:
                sync_task_to_github(doc, project)
    except Exception as e:
        frappe.log_error(f"Failed to sync task changes: {str(e)}"[:140], "Sync Task Changes Error")

def sync_task_to_github(task, project):
    """Sync task changes to GitHub"""
    try:
        if not project.github_repository:
            return
            
        if task.github_issue_number:
            # Update existing GitHub issue
            update_github_issue(task, project)
        elif task.issue_key:  # Only create if it's an agile task
            # Create new GitHub issue
            create_github_issue_from_task(task, project)
    except Exception as e:
        frappe.log_error(f"Failed to sync task to GitHub: {str(e)}"[:140], "GitHub Task Sync Error")

def create_github_issue_from_task(task, project):
    """Create GitHub issue from task"""
    try:
        github_issue = frappe.call(
            'erpnext_github_integration.github_api.create_issue',
            repository=project.github_repository,
            title=f"{task.issue_key}: {task.subject}",
            body=get_github_issue_body_from_task(task),
            assignees=get_github_assignees_from_task(task),
            labels=get_github_labels_from_task(task)
        )
        
        if github_issue:
            frappe.db.set_value("Task", task.name, "github_issue_number", github_issue.get('number'))
            frappe.db.commit()
    except Exception as e:
        frappe.log_error(f"Failed to create GitHub issue from task: {str(e)}"[:140], "Create GitHub Issue Error")

def update_github_issue(task, project):
    """Update existing GitHub issue"""
    try:
        frappe.call(
            'erpnext_github_integration.github_api.update_issue',
            repository=project.github_repository,
            issue_number=task.github_issue_number,
            title=f"{task.issue_key}: {task.subject}",
            body=get_github_issue_body_from_task(task),
            state=map_task_status_to_github_state(task.status)
        )
    except Exception as e:
        frappe.log_error(f"Failed to update GitHub issue: {str(e)}"[:140], "Update GitHub Issue Error")

def get_github_issue_body_from_task(task):
    """Format task description for GitHub"""
    body = f"""
**Issue Type:** {task.issue_type or 'Task'}
**Priority:** {task.issue_priority or 'Medium'}
**Story Points:** {task.story_points or 'Not estimated'}

## Description
{task.description or 'No description provided'}

---
*Created from ERPNext Agile: {frappe.utils.get_url()}/app/task/{task.name}*
    """
    return body.strip()

def get_github_assignees_from_task(task):
    """Get GitHub usernames for task assignees"""
    if not task.assigned_to:
        return []
    
    github_username = frappe.db.get_value("User", task.assigned_to, "github_username")
    return [github_username] if github_username else []

def get_github_labels_from_task(task):
    """Convert task labels to GitHub labels"""
    labels = []
    
    # Add issue type as label
    if task.issue_type:
        labels.append(task.issue_type.lower())
    
    # Add priority as label
    if task.issue_priority:
        labels.append(f"priority-{task.issue_priority.lower()}")
    
    # Add custom labels from task
    if hasattr(task, 'labels') and task.labels:
        for label in task.labels:
            if hasattr(label, 'label_name'):
                labels.append(label.label_name)
    
    return labels

def update_sprint_progress():
    """Update sprint progress metrics"""
    try:
        active_sprints = frappe.get_all("Agile Sprint", {
            "sprint_state": "Active"
        }, ["name", "project"])
        
        for sprint in active_sprints:
            # Use Task instead of Agile Issue
            tasks = frappe.get_all("Task", {
                "current_sprint": sprint.name,
                "project": sprint.project
            }, ["story_points", "status"])
            
            total_points = sum(task.story_points or 0 for task in tasks)
            completed_points = sum(
                task.story_points or 0 
                for task in tasks 
                if task.status in ["Completed"]
            )
            
            sprint_doc = frappe.get_doc("Agile Sprint", sprint.name)
            sprint_doc.total_points = total_points
            sprint_doc.completed_points = completed_points
            sprint_doc.progress_percentage = (completed_points / total_points * 100) if total_points else 0
            sprint_doc.save()
    except Exception as e:
        frappe.log_error(f"Failed to update sprint progress: {str(e)}"[:140], "Sprint Progress Error")

def map_task_status_to_github_state(task_status):
    """Map ERPNext Task status to GitHub issue state"""
    try:
        # Map to GitHub's open/closed states
        completed_statuses = ["Completed", "Cancelled"]
        return "closed" if task_status in completed_statuses else "open"
    except Exception as e:
        frappe.log_error(f"Failed to map task status: {str(e)}"[:140], "Task Status Map Error")
        return "open"

def map_github_status_to_task_status(github_status):
    """Map GitHub issue status to Task status"""
    try:
        status_map = {
            "open": "Open",
            "closed": "Completed"
        }
        return status_map.get(github_status, "Open")
    except Exception as e:
        frappe.log_error(f"Failed to map GitHub status: {str(e)}"[:140], "GitHub Status Map Error")
        return "Open"

def sync_agile_project_changes(doc, method):
    """Sync project changes when agile settings are updated"""
    try:
        if doc.enable_agile:
            # Update all tasks in this project if project key changed
            if doc.has_value_changed('project_key'):
                update_task_issue_keys_for_project(doc)
    except Exception as e:
        frappe.log_error(f"Failed to sync project changes: {str(e)}"[:140], "Sync Project Changes Error")

def update_task_issue_keys_for_project(project_doc):
    """Update all task issue keys when project key changes"""
    try:
        if not project_doc.project_key:
            return
            
        tasks_without_keys = frappe.get_all("Task", {
            "project": project_doc.name,
            "issue_key": ["in", ["", None]]
        }, ["name"])
        
        for task in tasks_without_keys:
            new_key = generate_task_issue_key(project_doc.name)
            if new_key:
                frappe.db.set_value("Task", task.name, "issue_key", new_key)
        
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(f"Failed to update task issue keys: {str(e)}"[:140], "Update Issue Keys Error")

def is_agile_task(task_name):
    """Check if a task belongs to an agile project"""
    try:
        task = frappe.get_cached_doc("Task", task_name)
        if task.project:
            project = frappe.get_cached_doc("Project", task.project)
            return project.enable_agile
        return False
    except Exception:
        return False

def get_agile_project_stats(project_name):
    """Get agile project statistics"""
    try:
        project = frappe.get_cached_doc("Project", project_name)
        if not project.enable_agile:
            return {}
            
        return {
            "total_issues": frappe.db.count("Task", {"project": project_name}),
            "open_issues": frappe.db.count("Task", {
                "project": project_name,
                "status": ["not in", ["Completed", "Cancelled"]]
            }),
            "current_sprint_issues": get_current_sprint_issue_count(project_name),
            "velocity": calculate_project_velocity(project_name)
        }
    except Exception as e:
        frappe.log_error(f"Failed to get project stats: {str(e)}"[:140], "Project Stats Error")
        return {}

def get_current_sprint_issue_count(project_name):
    """Get current sprint issue count"""
    try:
        current_sprint = frappe.db.get_value("Agile Sprint", {
            "project": project_name,
            "sprint_state": "Active"
        }, "name")
        
        if current_sprint:
            return frappe.db.count("Task", {
                "project": project_name,
                "current_sprint": current_sprint
            })
        return 0
    except Exception:
        return 0

def calculate_project_velocity(project_name):
    """Calculate team velocity from last 3 sprints"""
    try:
        completed_sprints = frappe.get_all("Agile Sprint", {
            "project": project_name,
            "sprint_state": "Completed"
        }, ["name"], limit=3, order_by="actual_end_date desc")
        
        if not completed_sprints:
            return 0
        
        total_points = 0
        for sprint in completed_sprints:
            sprint_points = frappe.db.sql("""
                SELECT SUM(story_points) 
                FROM `tabTask` 
                WHERE project = %s 
                AND current_sprint = %s 
                AND status = 'Completed'
            """, (project_name, sprint.name))[0][0] or 0
            total_points += sprint_points
        
        return total_points / len(completed_sprints)
    except Exception:
        return 0