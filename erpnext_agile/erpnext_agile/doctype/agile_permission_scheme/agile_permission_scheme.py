import frappe
from frappe.model.document import Document

class AgilePermissionScheme(Document):
    def validate(self):
        """Ensure valid permission scheme configuration"""
        if not self.scheme_name:
            frappe.throw("Scheme Name is mandatory")