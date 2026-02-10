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
    # if "Projects Manager" in frappe.get_roles(user):
    #     return ""

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
    Show tasks that are either:
    1. Assigned to the logged-in user
    2. Created by the logged-in user (owner)
    3. Watched by the logged-in user (Agile Issue Watcher)
    
    Admins and Project Managers can see everything.
    """
    
    user_quoted = frappe.db.escape(user)
    
    if "Administrator" in frappe.get_roles(user):
        return ""
    if "Projects Manager" in frappe.get_roles(user):
        return f"""
        (`tabTask`.name IN (
            SELECT parent
            FROM `tabAssigned To Users`
            WHERE user = {user_quoted}
            )
        OR
        `tabTask`.project IN (
            SELECT parent
            FROM `tabProject User`
            WHERE user = {user_quoted}
            )
        )
    """
    
    # Show tasks assigned to user OR created by user
    return f"""
        (
            `tabTask`.name IN (
                SELECT parent
                FROM `tabAssigned To Users`
                WHERE user = {user_quoted}
            )
            OR `tabTask`.owner = {user_quoted}
            OR `tabTask`.reporter = {user_quoted}
            OR `tabTask`.custom_original_owner = {user_quoted}
            OR `tabTask`.name IN (
                SELECT parent
                FROM `tabAgile Issue Watcher`
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
    if "Projects User" in frappe.get_roles(user):
        return True

    # Allow creation if user is in the project
    if perm_type == "create":
        if doc.project:
            return frappe.db.exists('Project User', {
                'parent': doc.project, 
                'user': user
            })
        return True  # Allow if no project specified

    # For existing tasks, check assignment
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

# ============================================
# PERMISSION QUERY CONDITIONS FOR SPRINT
# ============================================

@frappe.whitelist()
def get_agile_sprint_permission_query_conditions(user):
    """Permission query for Agile Sprint doctype"""
    if "Administrator" in frappe.get_roles(user):
        return ""
    if "Projects Manager" in frappe.get_roles(user):
        return ""

    user_quoted = f"'{user}'"
    return f"""
        (`tabAgile Sprint`.project IN (
            SELECT parent FROM `tabProject User`
            WHERE user = {user_quoted}
        ))
    """


def has_agile_sprint_permission(doc, perm_type=None, user=None):
    """Permission validator for Test Cycle doctype"""
    user = user or frappe.session.user

    if "Administrator" in frappe.get_roles(user):
        return True
    if "Projects Manager" in frappe.get_roles(user):
        return True
    if doc.owner == user:
        return True

    user_in_project_sprint = frappe.db.exists(
        'Project User',
        {'parent': doc.project, 'user': user}
    )

    return bool(user_in_project_sprint)

# ============================================
# PERMISSION QUERY CONDITIONS FOR TEST CYCLE
# ============================================

@frappe.whitelist()
def get_test_cycle_permission_query_conditions(user):
    """Permission query for Test Cycle doctype"""
    if "Administrator" in frappe.get_roles(user):
        return ""
    if "Projects Manager" in frappe.get_roles(user):
        return ""

    user_quoted = f"'{user}'"
    return f"""
        (
            `tabTest Cycle`.project IN (
                SELECT parent FROM `tabProject User`
                WHERE user = {user_quoted}
            ) 
            OR `tabTest Cycle`.owner_user = {user_quoted}   
        )

    """


def has_test_cycle_permission(doc, perm_type=None, user=None):
    """Permission validator for Test Cycle doctype"""
    user = user or frappe.session.user

    if "Administrator" in frappe.get_roles(user):
        return True
    if "Projects Manager" in frappe.get_roles(user):
        return True
    if doc.owner_user == user:
        return True

    user_in_project = frappe.db.exists(
        'Project User',
        {'parent': doc.project, 'user': user}
    )

    return bool(user_in_project)


# ============================================
# PERMISSION QUERY CONDITIONS FOR TEST CASE
# ============================================

@frappe.whitelist()
def get_test_case_permission_query_conditions(user):
    """Permission query for Test Case doctype"""
    if "Administrator" in frappe.get_roles(user):
        return ""
    if "Projects Manager" in frappe.get_roles(user):
        return ""

    user_quoted = f"'{user}'"
    return f"""
        (
            `tabTest Case`.project IN (
                SELECT parent FROM `tabProject User`
                WHERE user = {user_quoted}
            ) 
        )

    """


def has_test_case_permission(doc, perm_type=None, user=None):
    """Permission validator for Test Case doctype"""
    user = user or frappe.session.user

    if "Administrator" in frappe.get_roles(user):
        return True
    if "Projects Manager" in frappe.get_roles(user):
        return True
    if doc.owner == user:
        return True

    user_in_project = frappe.db.exists(
        'Project User',
        {'parent': doc.project, 'user': user}
    )

    return bool(user_in_project)


# =================================================
# PERMISSION QUERY CONDITIONS FOR TEST EXECUTION
# =================================================

@frappe.whitelist()
def get_test_execution_permission_query_conditions(user):
    """Permission query for Test Execution doctype"""
    if "Administrator" in frappe.get_roles(user):
        return ""
    if "Projects Manager" in frappe.get_roles(user):
        return ""

    user_quoted = f"'{user}'"
    return f"""
        (
            `tabTest Execution`.owner = {user_quoted}
            OR `tabTest Execution`.executed_by = {user_quoted}
            OR `tabTest Execution`.test_cycle IN (
                SELECT name FROM `tabTest Cycle`
                WHERE project IN (
                    SELECT parent FROM `tabProject User`
                    WHERE user = {user_quoted}
                )
                OR owner_user = {user_quoted}
            )
            
            OR `tabTest Execution`.test_case IN (
                SELECT name FROM `tabTest Case`
                WHERE project IN (
                    SELECT parent FROM `tabProject User`
                    WHERE user = {user_quoted}
                )
            )
        )
    """


def has_test_exec_permission(doc, perm_type=None, user=None):
    """
    Permission validator for Test Execution doctype.
    User must have access to the Test Case OR Test Cycle.
    """
    user = user or frappe.session.user

    if "Administrator" in frappe.get_roles(user):
        return True
    if "Projects Manager" in frappe.get_roles(user):
        return True
    
    if doc.owner == user:
        return True

    has_cycle_access = False
    if doc.test_cycle:
        test_cycle = frappe.get_doc("Test Cycle", doc.test_cycle)
        
        # User is cycle owner or in the project
        if test_cycle.owner_user == user:
            has_cycle_access = True
        elif test_cycle.project:
            has_cycle_access = frappe.db.exists(
                'Project User',
                {'parent': test_cycle.project, 'user': user}
            )
    
    # Check Test Case access
    has_case_access = False
    if doc.test_case:
        test_case = frappe.get_doc("Test Case", doc.test_case)
        
        # User is case owner or in the project
        if test_case.owner == user:
            has_case_access = True
        elif test_case.project:
            has_case_access = frappe.db.exists(
                'Project User',
                {'parent': test_case.project, 'user': user}
            )
    
    # User must have access to BOTH cycle and case (if they exist)
    if doc.test_cycle and not has_cycle_access:
        return False
    if doc.test_case and not has_case_access:
        return False
    
    # If either cycle or case exists and user has access, allow
    return has_cycle_access or has_case_access