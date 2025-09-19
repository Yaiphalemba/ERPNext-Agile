import frappe
from frappe.model.document import Document

class AgileIssueWatcher(Document):
    def validate(self):
        """Ensure valid watcher configuration"""
        if not self.user:
            frappe.throw("User is mandatory")
        if not frappe.db.exists("User", self.user):
            frappe.throw(f"Invalid User: {self.user}")