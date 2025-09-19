import frappe
from frappe.model.document import Document

class AgileWorkflowTransition(Document):
    def validate(self):
        """Ensure valid transition"""
        if self.from_status == self.to_status:
            frappe.throw("From Status and To Status cannot be the same")
        
        # Ensure statuses exist
        if not frappe.db.exists("Agile Issue Status", self.from_status):
            frappe.throw(f"Invalid From Status: {self.from_status}")
        if not frappe.db.exists("Agile Issue Status", self.to_status):
            frappe.throw(f"Invalid To Status: {self.to_status}")