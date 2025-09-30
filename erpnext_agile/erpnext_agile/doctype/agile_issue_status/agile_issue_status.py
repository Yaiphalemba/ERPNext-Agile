import frappe
from frappe.model.document import Document

class AgileIssueStatus(Document):
    def validate(self):
        """Validate status configuration"""
        if not self.status_category:
            frappe.throw("Status Category is mandatory")
        
        # Ensure unique status names
        existing = frappe.db.exists('Agile Issue Status', {
            'status_name': self.status_name,
            'name': ['!=', self.name or '']
        })
        if existing:
            frappe.throw(f"Status name '{self.status_name}' already exists")
