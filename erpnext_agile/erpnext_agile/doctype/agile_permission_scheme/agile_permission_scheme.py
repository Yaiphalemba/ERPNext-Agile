import frappe
from frappe.model.document import Document

class AgilePermissionScheme(Document):
    """Jira-style permission schemes"""
    
    def validate(self):
        """Validate permission scheme"""
        if not self.scheme_name:
            frappe.throw("Scheme Name is mandatory")
    
    def has_permission(self, permtype=None, user=None):
        """Custom permission logic"""
        if not user:
            user = frappe.session.user

        user_roles = frappe.get_roles(user)
        for perm in self.permissions:
            if perm.permission_type in [permtype, "All"]:
                if perm.role in user_roles:
                    return True
        return False