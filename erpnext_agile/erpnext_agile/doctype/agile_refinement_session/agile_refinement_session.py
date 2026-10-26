import frappe
from frappe.model.document import Document

class AgileRefinementSession(Document):
    def validate(self):
        """Validate session"""
        if not self.project:
            frappe.throw("Project is mandatory")
        
        if not self.session_date:
            self.session_date = frappe.utils.today()
        
        if not self.facilitator:
            self.facilitator = frappe.session.user