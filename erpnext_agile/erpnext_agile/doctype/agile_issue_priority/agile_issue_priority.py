import frappe
from frappe.model.document import Document

class AgileIssuePriority(Document):
    def validate(self):
        """Ensure valid priority configuration"""
        if not self.name:
            frappe.throw("Priority Name is mandatory")