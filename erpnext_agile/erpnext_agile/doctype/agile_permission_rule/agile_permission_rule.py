import frappe
from frappe.model.document import Document

class AgilePermissionRule(Document):
    def validate(self):
        """Ensure valid permission rule configuration"""
        if not self.permission_type:
            frappe.throw("Permission Type is mandatory")
        if not self.roles:
            frappe.throw("At least one role must be selected")