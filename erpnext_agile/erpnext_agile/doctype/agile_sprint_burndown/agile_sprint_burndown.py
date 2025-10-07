import frappe
from frappe.model.document import Document

class AgileSprintBurndown(Document):
    def validate(self):
        """Validate burndown entry"""
        if not self.sprint:
            frappe.throw("Sprint is mandatory")
        
        if not self.date:
            self.date = frappe.utils.today()
        
        # Ensure only one entry per sprint per date
        existing = frappe.db.exists('Agile Sprint Burndown', {
            'sprint': self.sprint,
            'date': self.date,
            'name': ['!=', self.name or '']
        })
        
        if existing:
            frappe.throw(f"Burndown entry already exists for {self.sprint} on {self.date}")
    
    def calculate_variance(self):
        """Calculate variance from ideal burndown"""
        if not self.ideal_remaining:
            return 0
        return self.remaining_points - self.ideal_remaining