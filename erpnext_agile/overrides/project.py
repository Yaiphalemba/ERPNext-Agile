import frappe
from frappe import _
from erpnext.projects.doctype.project.project import Project


class AgileProject(Project):
    def validate(self):
        super().validate()
        if self.enable_agile:
            self.validate_agile_settings()

    def validate_agile_settings(self):
        """Validate agile-specific settings"""
        if self.workflow_scheme and not frappe.db.exists("Agile Workflow Scheme", self.workflow_scheme):
            frappe.throw(f"Workflow Scheme {self.workflow_scheme} does not exist")
        if self.permission_scheme and not frappe.db.exists("Agile Permission Scheme", self.permission_scheme):
            frappe.throw(f"Permission Scheme {self.permission_scheme} does not exist")


# ============================================
# PERMISSION QUERY CONDITIONS FOR PROJECT
# ============================================

@frappe.whitelist()
def get_project_permission_query_conditions(user):
    """Permission query for Project doctype"""
    if "Administrator" in frappe.get_roles(user):
        return ""
    if "Projects Manager" in frappe.get_roles(user):
        return ""

    user_quoted = f"'{user}'"
    return f"""
        (`tabProject`.name IN (
            SELECT parent FROM `tabProject User`
            WHERE user = {user_quoted}
        ))
    """


def has_project_permission(doc, perm_type=None, user=None):
    """Permission validator for Project doctype"""
    user = user or frappe.session.user

    if "Administrator" in frappe.get_roles(user):
        return True
    if "Projects Manager" in frappe.get_roles(user):
        return True
    if doc.owner == user:
        return True

    user_in_project = frappe.db.exists(
        'Project User',
        {'parent': doc.name, 'user': user}
    )

    return bool(user_in_project)


# ============================================
# PERMISSION QUERY CONDITIONS FOR TASK
# ============================================

@frappe.whitelist()
def get_task_permission_query_conditions(user):
    """
    Only show tasks assigned to the logged-in user.
    Admins and Project Managers can see everything.
    """
    if "Administrator" in frappe.get_roles(user):
        return ""
    if "Projects Manager" in frappe.get_roles(user):
        return ""

    user_quoted = frappe.db.escape(user)
    """Show only tasks assigned to the user"""
    return f"""
        (`tabTask`.name IN (
            SELECT parent
            FROM `tabAssigned To Users`
            WHERE user = {user_quoted}
            )
        )
    """
    
    """Alternatively, to show tasks assigned to the user or tasks in projects where the user is a project user:"""
    # return f"""
    #     (`tabTask`.name IN (
    #         SELECT parent
    #         FROM `tabAssigned To Users`
    #         WHERE user = {user_quoted}
    #         )
    #     OR
    #     `tabTask`.project IN (
    #         SELECT parent
    #         FROM `tabProject User`
    #         WHERE user = {user_quoted}
    #         )
    #     )
    # """


def has_task_permission(doc, perm_type=None, user=None):
    """
    Restrict access to only assigned users.
    Admins and Project Managers have full access.
    """
    user = user or frappe.session.user

    if "Administrator" in frappe.get_roles(user):
        return True
    if "Projects Manager" in frappe.get_roles(user):
        return True

    # Allow if user is assigned
    if frappe.db.exists('Assigned To Users', {'parent': doc.name, 'user': user}):
        return True

    return False


# ============================================
# LIST VIEW FILTERING
# ============================================

def task_list_query_filter(filters, user):
    """
    Optional: Additional filtering for Task list view.
    - All users can see all tasks (handled by permission query above)
    - Custom logic can be added here if you want to further narrow list results
    """
    return filters