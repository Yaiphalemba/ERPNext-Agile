import frappe
from frappe.model.document import Document

class AgileIssueStatus(Document):
    def validate(self):
        """Ensure valid status configuration"""
        if not self.status_category:
            frappe.throw("Status Category is mandatory")