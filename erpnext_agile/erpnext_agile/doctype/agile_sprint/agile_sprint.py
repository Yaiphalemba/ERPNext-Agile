# erpnext_agile/erpnext_agile/doctype/agile_sprint/agile_sprint.py
import frappe
from frappe.model.document import Document
from frappe.utils import today, add_days

class AgileSprint(Document):
    def validate(self):
        """Validate sprint data"""
        # Validate dates
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                frappe.throw("End date cannot be before start date")
        
        # Validate no overlapping active sprints
        if self.sprint_state == 'Active':
            self.validate_no_overlap()
    
    def validate_no_overlap(self):
        """Ensure no other active sprint exists"""
        existing = frappe.db.sql("""
            SELECT name FROM `tabAgile Sprint`
            WHERE project = %s 
            AND sprint_state = 'Active'
            AND name != %s
        """, (self.project, self.name or ''))
        
        if existing:
            frappe.throw(f"Another sprint '{existing[0][0]}' is already active")
    
    def on_update(self):
        """Actions on update"""
        # Update sprint metrics
        if self.sprint_state == 'Active':
            self.calculate_metrics()
    
    def calculate_metrics(self):
        """Calculate and update sprint metrics"""
        from erpnext_agile.agile_sprint_manager import AgileSprintManager
        manager = AgileSprintManager()
        metrics = manager.calculate_sprint_metrics(self)
        
        # Update fields without triggering another save
        self.db_set('total_points', metrics['total_points'], update_modified=False)
        self.db_set('completed_points', metrics['completed_points'], update_modified=False)
        self.db_set('progress_percentage', metrics['progress_percentage'], update_modified=False)
        self.db_set('velocity', metrics['velocity'], update_modified=False)