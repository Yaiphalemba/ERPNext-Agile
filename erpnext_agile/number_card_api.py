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


@frappe.whitelist()
def get_total_task_count():
    user = frappe.session.user

    if is_admin_or_system_manager(user):
        count = frappe.db.count("Task")
    else:
        count = frappe.db.sql("""
        SELECT COUNT(DISTINCT t.name)
        FROM `tabTask` t
        LEFT JOIN `tabAssigned To Users` atu
            ON atu.parent = t.name
        WHERE
            atu.user = %s
            OR t.reporter = %s
            OR t.custom_original_owner = %s
    """, (user, user, user))[0][0]
    
    return {
        "value": count,
        "fieldtype": "Int",
        "route": ["List", "Task"],
        "route_options": {
            "status": ["not in", ["Cancelled", "Template"]]
        }
    }

        
@frappe.whitelist()
def get_total_open_task_count():
    user = frappe.session.user

    if is_admin_or_system_manager(user):
        count = frappe.db.count("Task", filters={"status":"Open"})
    else:
        count = frappe.db.sql("""
        SELECT COUNT(DISTINCT t.name)
        FROM `tabTask` t
        LEFT JOIN `tabAssigned To Users` atu
            ON atu.parent = t.name
        WHERE
            (
                atu.user = %s
                OR t.reporter = %s
                OR t.custom_original_owner = %s
            ) 
            AND t.status = 'Open'
    """, (user, user, user))[0][0]
    
    return {
        "value": count,
        "fieldtype": "Int",
        "route": ["List", "Task"],
        "route_options": {
            "status": ["=", "Open"]
        }
    }


@frappe.whitelist()
def get_total_ongoing_task_count():
    user = frappe.session.user

    if is_admin_or_system_manager(user):
        count = frappe.db.count("Task", filters=["status", "in", ["Working","Pending Review","Overdue"]])
    else:
        count = frappe.db.sql("""
        SELECT COUNT(DISTINCT t.name)
        FROM `tabTask` t
        LEFT JOIN `tabAssigned To Users` atu
            ON atu.parent = t.name
        WHERE
            (
                atu.user = %s
                OR t.reporter = %s
                OR t.custom_original_owner = %s
            ) 
            AND t.status IN ('Working', 'Pending Review', 'Overdue')
    """, (user, user, user))[0][0]
    
    return {
        "value": count,
        "fieldtype": "Int",
        "route": ["List", "Task"],
        "route_options": {
            "status": ["in", ["Working", "Pending Review", "Overdue"]]
        }
    }


@frappe.whitelist()
def get_total_complete_task_count():
    user = frappe.session.user

    if is_admin_or_system_manager(user):
        count = frappe.db.count("Task", filters={"status":"Completed"})
    else:
        count = frappe.db.sql("""
        SELECT COUNT(DISTINCT t.name)
        FROM `tabTask` t
        LEFT JOIN `tabAssigned To Users` atu
            ON atu.parent = t.name
        WHERE
            (
                atu.user = %s
                OR t.reporter = %s
                OR t.custom_original_owner = %s
            ) 
            AND t.status = 'Completed'
    """, (user, user, user))[0][0]
    
    return {
        "value": count,
        "fieldtype": "Int",
        "route": ["List", "Task"],
        "route_options": {
            "status": ["=", "Completed"]
        }
    }

        
@frappe.whitelist()
def get_total_overdue_task_count():
    user = frappe.session.user

    if is_admin_or_system_manager(user):
        count = frappe.db.count("Task", filters={"status":"Overdue"})
    else:
        count = frappe.db.sql("""
        SELECT COUNT(DISTINCT t.name)
        FROM `tabTask` t
        LEFT JOIN `tabAssigned To Users` atu
            ON atu.parent = t.name
        WHERE
            (
                atu.user = %s
                OR t.reporter = %s
                OR t.custom_original_owner = %s
            ) 
            AND t.status = 'Overdue'
    """, (user, user, user))[0][0]
    
    return {
        "value": count,
        "fieldtype": "Int",
        "route": ["List", "Task"],
        "route_options": {
            "status": ["=", "Overdue"]
        }
    }

        