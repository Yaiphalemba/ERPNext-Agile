import frappe
from frappe.model.document import Document

class AgileSprintBurndown(Document):
    def validate(self):
        """Validate burndown entry"""
        if not self.sprint:
            frappe.throw("Sprint is mandatory")
        
        if not self.date:
            self.date = frappe.utils.today()
    
    def calculate_variance(self):
        """Calculate variance from ideal burndown"""
        if not self.ideal_remaining:
            return 0
        return self.remaining_points - self.ideal_remaining