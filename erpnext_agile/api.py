# erpnext_agile/api.py (Updated)
import frappe

@frappe.whitelist()
def get_board_data(project, sprint=None):
    """Get board data for Jira-style board using Task doctype"""
    filters = {"project": project}
    if sprint:
        filters["current_sprint"] = sprint
    
    # Ensure it's an agile project
    project_doc = frappe.get_doc("Project", project)
    if not project_doc.enable_agile:
        frappe.throw("This is not an agile project")
    
    issues = frappe.get_all("Task", 
        filters=filters,
        fields=[
            "name", "issue_key", "subject as summary", "issue_type", "issue_priority as priority", 
            "status", "assigned_to as assignee", "story_points", "github_pull_request",
            "github_branch", "epic"
        ]
    )
    
    # Get status columns (using Task status)
    statuses = [
        {"name": "Open", "status_category": "To Do", "color": "#b3b3b3"},
        {"name": "Working", "status_category": "In Progress", "color": "#4a90e2"},
        {"name": "Pending Review", "status_category": "In Progress", "color": "#f79232"},
        {"name": "Completed", "status_category": "Done", "color": "#65ba43"},
        {"name": "Cancelled", "status_category": "Done", "color": "#999999"}
    ]
    
    # Get project stats
    project_stats = project_doc.get_project_stats()
    
    return {
        "issues": issues,
        "statuses": statuses,
        "project_stats": project_stats
    }

@frappe.whitelist()
def update_issue_status(task_name, new_status):
    """Update task status - for drag and drop"""
    task = frappe.get_doc("Task", task_name)
    task.status = new_status
    task.save()
    
    return {"message": f"Task {task.issue_key or task.name} moved to {new_status}"}