import frappe
from frappe import _
from erpnext.projects.doctype.project.project import Project


class AgileProject(Project):
    def validate(self):
        super().validate()
        if self.enable_agile:
            self.validate_agile_settings()
            
    def after_insert(self):
        super().after_insert()
        if self.enable_agile:
            if self.custom_project_manager or self.owner:
                self.add_project_manager_and_creator()
                self.reload()

    def validate_agile_settings(self):
        """Validate agile-specific settings"""
        if self.workflow_scheme and not frappe.db.exists("Agile Workflow Scheme", self.workflow_scheme):
            frappe.throw(f"Workflow Scheme {self.workflow_scheme} does not exist")
        if self.permission_scheme and not frappe.db.exists("Agile Permission Scheme", self.permission_scheme):
            frappe.throw(f"Permission Scheme {self.permission_scheme} does not exist")
            
    def add_project_manager_and_creator(self):
        """Ensure project manager and creator are added as project users"""
        
        # 1. Handle the Owner (Creator)
        user_in_project = frappe.db.exists(
            'Project User',
            {'parent': self.name, 'user': self.owner}
        )
        
        if not user_in_project:
            frappe.get_doc({
                'doctype': 'Project User',
                'parent': self.name,
                'parenttype': 'Project',    # <-- Added this
                'parentfield': 'users',     # <-- Added this
                'user': self.owner
            }).insert(ignore_permissions=True)
        
        # 2. Handle the Custom Project Manager
        if self.custom_project_manager:
            pm_in_project = frappe.db.exists(
                'Project User',
                {'parent': self.name, 'user': self.custom_project_manager}
            )
            if not pm_in_project:
                frappe.get_doc({
                    'doctype': 'Project User',
                    'parent': self.name,
                    'parenttype': 'Project',    # <-- Added this
                    'parentfield': 'users',     # <-- Added this
                    'user': self.custom_project_manager
                }).insert(ignore_permissions=True)


# ============================================
# PERMISSION QUERY CONDITIONS FOR PROJECT
# ============================================

@frappe.whitelist()
def get_project_permission_query_conditions(user):
    """Permission query for Project doctype"""
    if "Administrator" in frappe.get_roles(user):
        return ""
    if "Management" in frappe.get_roles(user):
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
    Dynamically route permission logic based on the Task's parent Project settings.
    """
    
    roles = frappe.get_roles(user)
    user_quoted = frappe.db.escape(user)
    
    # 1. System Admins get a free pass.
    if "Administrator" in roles:
        return ""
    
    if "Management" in roles:
        return ""
        
    # 2. Project Managers get standard visibility across their projects.
    if "Projects Manager" in roles:
        return f"""
            (`tabTask`.name IN (
                SELECT parent FROM `tabAssigned To Users` WHERE user = {user_quoted}
            )
            OR `tabTask`.project IN (
                SELECT parent FROM `tabProject User` WHERE user = {user_quoted}
            ))
        """

    # 3. Standard Users: Let SQL do the thinking based on the Project Master.
    # We use a combined OR statement to apply the right rule based on the project's flag.
    return f"""
        (
            -- SCENARIO A: Project has strict assignment visibility enabled (= 1)
            `tabTask`.project IN (
                SELECT name FROM `tabProject` 
                WHERE custom_enable_assignment_based_visibility = 1
            )
            AND (
                `tabTask`.name IN (SELECT parent FROM `tabAssigned To Users` WHERE user = {user_quoted})
                OR `tabTask`.owner = {user_quoted}
                OR `tabTask`.reporter = {user_quoted}
                OR `tabTask`.custom_original_owner = {user_quoted}
                OR `tabTask`.name IN (SELECT parent FROM `tabAgile Issue Watcher` WHERE user = {user_quoted})
            )
        )
        OR
        (
            -- SCENARIO B: Project has it disabled (= 0), OR the Task has no project at all
            (
                `tabTask`.project IS NULL 
                OR `tabTask`.project IN (
                    SELECT name FROM `tabProject` 
                    WHERE IFNULL(custom_enable_assignment_based_visibility, 0) = 0
                )
            )
            AND (
                `tabTask`.name IN (SELECT parent FROM `tabAssigned To Users` WHERE user = {user_quoted})
                OR `tabTask`.project IN (SELECT parent FROM `tabProject User` WHERE user = {user_quoted})
            )
        )
    """


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
    if doc.owner == user:
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
    if "Management" in frappe.get_roles(user):
        return ""
    # if "Projects Manager" in frappe.get_roles(user):
    #     return ""

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
    if "Projects User" in frappe.get_roles(user):
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
    
    if "Management" in frappe.get_roles(user):
        return ""
    # if "Projects Manager" in frappe.get_roles(user):
    #     return ""

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
    if "Projects User" in frappe.get_roles(user):
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
    """
    Dynamically route permission logic based on the Test Case's parent Project settings.
    Matches the Task permission logic perfectly.
    """
    roles = frappe.get_roles(user)
    user_quoted = frappe.db.escape(user)
    # if "Administrator" in frappe.get_roles(user):
    #     return ""
    # if "Management" in frappe.get_roles(user):
    #     return ""
    # if "Projects Manager" in frappe.get_roles(user):
    #     return ""

    # 1. System Admins get a free pass.
    if "Administrator" in roles:
        return ""
        
    if "Management" in roles:
        return ""
    # 2. Project Managers get standard visibility across their projects.
    if "Projects Manager" in roles:
        return f"""
            (`tabTest Case`.name IN (
                SELECT parent FROM `tabAssigned To Users` WHERE user = {user_quoted}
            )
            OR `tabTest Case`.project IN (
                SELECT parent FROM `tabProject User` WHERE user = {user_quoted}
            ))
        """

    # 3. Standard Users: Let SQL do the thinking based on the Project Master.
    return f"""
        (
            -- SCENARIO A: Project has strict assignment visibility enabled (= 1)
            `tabTest Case`.project IN (
                SELECT name FROM `tabProject` 
                WHERE custom_enable_assignment_based_visibility = 1
            )
            AND (
                `tabTest Case`.name IN (SELECT parent FROM `tabAssigned To Users` WHERE user = {user_quoted})
                OR `tabTest Case`.owner = {user_quoted}
            )
        )
        OR
        (
            -- SCENARIO B: Project has it disabled (= 0), OR the Test Case has no project at all
            (
                `tabTest Case`.project IS NULL 
                OR `tabTest Case`.project IN (
                    SELECT name FROM `tabProject` 
                    WHERE IFNULL(custom_enable_assignment_based_visibility, 0) = 0
                )
            )
            AND (
                `tabTest Case`.name IN (SELECT parent FROM `tabAssigned To Users` WHERE user = {user_quoted})
                OR `tabTest Case`.project IN (SELECT parent FROM `tabProject User` WHERE user = {user_quoted})
            )
        )
    """


def has_test_case_permission(doc, perm_type=None, user=None):
    """
    Permission validator for Test Case doctype.
    Follows the exact same structure as has_task_permission.
    """
    user = user or frappe.session.user
    roles = frappe.get_roles(user)

    if "Administrator" in roles:
        return True
    if "Projects Manager" in roles:
        return True
    if "Projects User" in roles:
        return True

    # Allow creation if user is in the project
    if perm_type == "create":
        if doc.project:
            return bool(frappe.db.exists('Project User', {
                'parent': doc.project, 
                'user': user
            }))
        return True  # Allow if no project specified

    # For existing docs, check assignment or ownership
    if doc.owner == user:
        return True
        
    if frappe.db.exists('Assigned To Users', {'parent': doc.name, 'user': user}):
        return True

    return False


# =================================================
# PERMISSION QUERY CONDITIONS FOR TEST EXECUTION
# =================================================

@frappe.whitelist()
def get_test_execution_permission_query_conditions(user):
    """
    Dynamically route permission logic based on the parent project of the Test Case/Cycle.
    Matches the strict vs standard logic of Tasks.
    """
    roles = frappe.get_roles(user)
    user_quoted = frappe.db.escape(user)

    # 1. System Admins get a free pass.
    if "Administrator" in roles:
        return ""
    if "Management" in roles:
        return ""

    # 2. Project Managers get standard visibility.
    if "Projects Manager" in roles:
        return f"""
            (`tabTest Execution`.name IN (
                SELECT parent FROM `tabAssigned To Users` WHERE user = {user_quoted}
            )
            OR `tabTest Execution`.test_cycle IN (
                SELECT name FROM `tabTest Cycle` WHERE project IN (SELECT parent FROM `tabProject User` WHERE user = {user_quoted})
            )
            OR `tabTest Execution`.test_case IN (
                SELECT name FROM `tabTest Case` WHERE project IN (SELECT parent FROM `tabProject User` WHERE user = {user_quoted})
            ))
        """

    # 3. Standard Users: Evaluate through the parent doc's Project flag.
    return f"""
        (
            -- SCENARIO A: Parent Project has strict assignment visibility enabled (= 1)
            (
                `tabTest Execution`.test_case IN (
                    SELECT name FROM `tabTest Case` WHERE project IN (
                        SELECT name FROM `tabProject` WHERE custom_enable_assignment_based_visibility = 1
                    )
                )
                OR `tabTest Execution`.test_cycle IN (
                    SELECT name FROM `tabTest Cycle` WHERE project IN (
                        SELECT name FROM `tabProject` WHERE custom_enable_assignment_based_visibility = 1
                    )
                )
            )
            AND (
                `tabTest Execution`.name IN (SELECT parent FROM `tabAssigned To Users` WHERE user = {user_quoted})
                OR `tabTest Execution`.owner = {user_quoted}
                OR `tabTest Execution`.executed_by = {user_quoted}
            )
        )
        OR
        (
            -- SCENARIO B: Parent Project has it disabled (= 0), OR no project linkage
            (
                (`tabTest Execution`.test_case IS NULL AND `tabTest Execution`.test_cycle IS NULL)
                OR `tabTest Execution`.test_case IN (
                    SELECT name FROM `tabTest Case` WHERE project IS NULL OR project IN (
                        SELECT name FROM `tabProject` WHERE IFNULL(custom_enable_assignment_based_visibility, 0) = 0
                    )
                )
                OR `tabTest Execution`.test_cycle IN (
                    SELECT name FROM `tabTest Cycle` WHERE project IS NULL OR project IN (
                        SELECT name FROM `tabProject` WHERE IFNULL(custom_enable_assignment_based_visibility, 0) = 0
                    )
                )
            )
            AND (
                `tabTest Execution`.name IN (SELECT parent FROM `tabAssigned To Users` WHERE user = {user_quoted})
                OR `tabTest Execution`.owner = {user_quoted}
                OR `tabTest Execution`.executed_by = {user_quoted}
                OR `tabTest Execution`.test_cycle IN (
                    SELECT name FROM `tabTest Cycle`
                    WHERE project IN (SELECT parent FROM `tabProject User` WHERE user = {user_quoted})
                    OR owner_user = {user_quoted}
                )
                OR `tabTest Execution`.test_case IN (
                    SELECT name FROM `tabTest Case`
                    WHERE project IN (SELECT parent FROM `tabProject User` WHERE user = {user_quoted})
                )
            )
        )
    """


def has_test_exec_permission(doc, perm_type=None, user=None):
    """
    Permission validator for Test Execution doctype.
    Follows the exact same structural rules as has_task_permission.
    """
    user = user or frappe.session.user
    roles = frappe.get_roles(user)

    if "Administrator" in roles:
        return True
    if "Projects Manager" in roles:
        return True
    if "Projects User" in roles:
        return True
    if doc.owner == user:
        return True

    # For creation, allow if user is in the project (derived from case or cycle)
    if perm_type == "create":
        project = None
        if doc.test_cycle:
            project = frappe.db.get_value("Test Cycle", doc.test_cycle, "project")
        if not project and doc.test_case:
            project = frappe.db.get_value("Test Case", doc.test_case, "project")
            
        if project:
            return bool(frappe.db.exists('Project User', {
                'parent': project, 
                'user': user
            }))
        return True  # Allow if no project specified

    # For existing docs, check assignment, ownership, or executed_by
    if doc.owner == user or doc.get("executed_by") == user:
        return True
        
    if frappe.db.exists('Assigned To Users', {'parent': doc.name, 'user': user}):
        return True

    return False