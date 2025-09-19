import frappe

@frappe.whitelist()
def get_board_data(agile_project, sprint=None):
    """Get board data for Jira-style board"""
    filters = {"agile_project": agile_project}
    if sprint:
        filters["current_sprint"] = sprint
    
    issues = frappe.get_all("Agile Issue", 
        filters=filters,
        fields=[
            "name", "issue_key", "summary", "issue_type", "priority", 
            "status", "assignee", "story_points", "github_pull_request",
            "github_branch", "epic"
        ]
    )
    
    # Get status columns
    statuses = frappe.get_all("Agile Issue Status", 
        fields=["name", "status_category", "color"],
        order_by="sort_order"
    )
    
    # Get project stats using AgileProject class
    project_doc = frappe.get_doc("Agile Project", agile_project)
    project_stats = project_doc.get_project_stats()
    
    return {
        "issues": issues,
        "statuses": statuses,
        "project_stats": project_stats
    }

@frappe.whitelist()
def update_issue_status(issue_name, new_status):
    """Update issue status - for drag and drop"""
    issue = frappe.get_doc("Agile Issue", issue_name)
    issue.status = new_status
    issue.save()
    
    return {"message": f"Issue {issue.issue_key} moved to {new_status}"}

@frappe.whitelist()
def create_github_branch(issue_name):
    """Create GitHub branch for issue"""
    issue = frappe.get_doc("Agile Issue", issue_name)
    issue.start_work()
    
    return {"branch_name": issue.github_branch}

@frappe.whitelist()
def bulk_assign_issues(issue_names, assignee):
    """Bulk assign issues - Jira-style bulk operations"""
    for issue_name in issue_names:
        frappe.db.set_value("Agile Issue", issue_name, "assignee", assignee)
    
    frappe.db.commit()
    return {"message": f"Assigned {len(issue_names)} issues to {assignee}"}

@frappe.whitelist()
def get_issue_suggestions(query, agile_project):
    """Quick search suggestions for issue navigator"""
    issues = frappe.db.sql("""
        SELECT issue_key, summary, status, assignee
        FROM `tabAgile Issue`
        WHERE agile_project = %s 
        AND (issue_key LIKE %s OR summary LIKE %s)
        LIMIT 10
    """, (agile_project, f"%{query}%", f"%{query}%"), as_dict=True)
    
    return issues

@frappe.whitelist()
def create_subtask(parent_issue, summary, assignee=None):
    """Create subtask - Jira-style"""
    parent = frappe.get_doc("Agile Issue", parent_issue)
    
    subtask = frappe.get_doc({
        "doctype": "Agile Issue",
        "summary": summary,
        "agile_project": parent.agile_project,
        "parent_issue": parent_issue,
        "issue_type": "Sub-task",
        "priority": parent.priority,
        "assignee": assignee or parent.assignee,
        "reporter": frappe.session.user
    })
    
    subtask.insert()
    return subtask.name