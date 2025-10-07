import frappe
from frappe.model.document import Document

class AgileIssueType(Document):
    def validate(self):
        """Validate issue type configuration"""
        if not self.issue_type_name:
            frappe.throw("Issue Type Name is mandatory")