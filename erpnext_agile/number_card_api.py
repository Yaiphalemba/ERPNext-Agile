import frappe

def is_admin_or_system_manager(user=None):
    """Check if user has admin privileges"""
    user = user or frappe.session.user
    return user == "Administrator" or "System Manager" in frappe.get_roles(user)

@frappe.whitelist()
def get_user_projects_count():
    user = frappe.session.user
    
    if is_admin_or_system_manager(user):
        count = frappe.db.count("Project", {"status": ["!=", "Cancelled"]})
    else:
        count = frappe.db.sql("""
            SELECT COUNT(DISTINCT parent)
            FROM `tabProject User`
            WHERE user = %s
        """, user)[0][0]

    return {
        "value": count,
        "fieldtype": "Int",
        "route": ["List", "Project"],
        "route_options": {
            "status": ["!=", "Cancelled"]
        }
    }