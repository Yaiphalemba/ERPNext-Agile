# erpnext_agile/overrides/project.py
import frappe
from frappe import _
import re
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
    """
    Permission query for Project doctype
    
    Rules:
    - Administrators and Project Managers: See all projects
    - Others: See only projects they are part of (via users child table)
    """
    
    # Admins and System Managers see everything
    if "Administrator" in frappe.get_roles(user):
        return ""  # Empty string means no restrictions
    
    # Project Managers see all projects
    if "Projects Manager" in frappe.get_roles(user):
        return ""
    
    # Everyone else sees only projects they're in (via users table)
    # Use backticks to escape the email properly
    user_quoted = f"'{user}'"
    return f"""
        (`tabProject`.name IN (
            SELECT parent FROM `tabProject User`
            WHERE user = {user_quoted}
        ))
    """


def has_project_permission(doc, perm_type=None, user=None):
    """
    Permission validator for Project doctype
    
    Rules:
    - Administrators: Full access
    - Project Managers: Full access
    - Project Owner: Full access
    - Users in Project's users table: Read/Write access
    - Others: No access
    """
    
    if not user:
        user = frappe.session.user
    
    # Admins have full access
    if "Administrator" in frappe.get_roles(user):
        return True
    
    # Project Managers have full access
    if "Projects Manager" in frappe.get_roles(user):
        return True
    
    # Project owner has full access
    if doc.owner == user:
        return True
    
    # Check if user is in the project's users child table
    user_in_project = frappe.db.exists(
        'Project User',
        {
            'parent': doc.name,
            'user': user
        }
    )
    
    if user_in_project:
        return True
    
    # No access for others
    return False


# ============================================
# PERMISSION QUERY CONDITIONS FOR TASK
# ============================================

@frappe.whitelist()
def get_task_permission_query_conditions(user):
    """
    Permission query for Task doctype (Agile Issues)
    
    Rules:
    - Administrators: See all tasks
    - Project Managers: See all tasks
    - Others: See only tasks they are assigned to (via assigned_to_users table)
              OR tasks in projects they are part of
    """
    
    # Admins see everything
    if "Administrator" in frappe.get_roles(user):
        return ""
    
    # Project Managers see everything
    if "Projects Manager" in frappe.get_roles(user):
        return ""
    
    # Everyone else sees:
    # 1. Tasks they are assigned to
    # 2. Tasks in projects they are part of
    return f"""
        (
            `tabTask`.name IN (
                SELECT parent FROM `tabAssigned To Users`
                WHERE user = {frappe.db.escape(user)}
            )
            OR
            `tabTask`.project IN (
                SELECT parent FROM `tabProject User`
                WHERE user = {frappe.db.escape(user)}
            )
        )
    """


def has_task_permission(doc, perm_type=None, user=None):
    """
    Permission validator for Task doctype (Agile Issues)
    
    Rules:
    - Administrators: Full access
    - Project Managers: Full access
    - Task Creator/Owner: Full access
    - Assigned Users: Read/Write access
    - Users in Project.users table: Read access only
    - Others: No access
    """
    
    if not user:
        user = frappe.session.user
    
    # Admins have full access
    if "Administrator" in frappe.get_roles(user):
        return True
    
    # Project Managers have full access
    if "Projects Manager" in frappe.get_roles(user):
        return True
    
    # Task owner/creator has full access
    if doc.owner == user:
        return True
    
    # Check if user is assigned to this task
    user_assigned = frappe.db.exists(
        'Assigned To Users',
        {
            'parent': doc.name,
            'user': user
        }
    )
    
    if user_assigned:
        return True
    
    # Check if user is in the project (secondary permission)
    if doc.project:
        user_in_project = frappe.db.exists(
            'Project User',
            {
                'parent': doc.project,
                'user': user
            }
        )
        
        if user_in_project:
                return True
    
    # No access for others
    return False


# ============================================
# LIST VIEW FILTERING
# ============================================

def task_list_query_filter(filters, user):
    """
    Optional: Additional filtering for Task list view
    Ensures users only see tasks they should have access to
    """
    if "Administrator" in frappe.get_roles(user):
        return filters
    
    if "Projects Manager" in frappe.get_roles(user):
        return filters
    
    # For regular users, add filter to show only their tasks
    if not filters:
        filters = {}
    
    # This is handled by get_task_permission_query_conditions
    # but can be overridden here for additional logic
    
    return filters