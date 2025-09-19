import frappe

def get_agile_issue_permission_query_conditions(user):
    """Custom permission query for agile issues"""
    if not user:
        user = frappe.session.user
    
    if user == "Administrator":
        return ""
    
    # Users can see issues in projects they have access to
    user_projects = frappe.get_all("Project", 
        filters={"custom_project_lead": user},
        pluck="name"
    )
    
    if user_projects:
        return f"`tabAgile Issue`.`agile_project` IN (SELECT name FROM `tabAgile Project` WHERE project IN ({','.join(['%s'] * len(user_projects))}))"
    
    # Fallback: only assigned issues
    return f"`tabAgile Issue`.`assignee` = '{user}' OR `tabAgile Issue`.`reporter` = '{user}'"

def has_transition_permission(user, required_permission, issue):
    """Check if user has permission for workflow transition"""
    if not required_permission:
        return True
    
    if user == "Administrator":
        return True
    
    # Check role-based permissions
    user_roles = frappe.get_roles(user)
    return required_permission in user_roles