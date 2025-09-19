import frappe
from frappe.model.document import Document

class AgileIssueType(Document):
    def validate(self):
        """Ensure valid issue type configuration"""
        if not self.name:
            frappe.throw("Issue Type Name is mandatory")