import frappe

def get_context(context):
    """Page context for agile board"""
    context.no_cache = 1
    
    # Get user's agile projects
    user_projects = get_user_agile_projects()
    context.agile_projects = user_projects
    
    # Get current project from URL or default
    project_key = frappe.form_dict.get('project')
    if project_key:
        context.current_project = frappe.db.get_value("Agile Project", {"project_key": project_key})
    elif user_projects:
        context.current_project = user_projects[0].name
    
    return context

def get_user_agile_projects():
    """Get agile projects user has access to"""
    return frappe.get_all("Agile Project", 
        filters={}, # Add permission filters
        fields=["name", "project_name", "project_key"]
    )