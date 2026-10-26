import frappe
from frappe.model.document import Document

class AgileIssuePriority(Document):
    def validate(self):
        """Validate priority configuration"""
        if not self.priority_name:
            frappe.throw("Priority Name is mandatory")