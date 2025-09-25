# Updated permissions.py
import frappe

def get_agile_task_permission_query_conditions(user):
    """Custom permission query for agile tasks"""
    if not user:
        user = frappe.session.user
    
    if user == "Administrator":
        return ""
    
    # Users can see tasks in projects they have access to
    user_projects = frappe.get_all("Project", 
        filters={"project_lead": user, "enable_agile": 1},
        pluck="name"
    )
    
    if user_projects:
        return f"`tabTask`.`project` IN ({','.join(['%s'] * len(user_projects))})"
    
    # Fallback: only assigned tasks
    return f"`tabTask`.`assignee` = '{user}' OR `tabTask`.`reporter` = '{user}'"

def has_transition_permission(user, required_permission, task):
    """Check if user has permission for workflow transition"""
    if not required_permission:
        return True
    
    if user == "Administrator":
        return True
    
    # Check role-based permissions
    user_roles = frappe.get_roles(user)
    return required_permission in user_roles