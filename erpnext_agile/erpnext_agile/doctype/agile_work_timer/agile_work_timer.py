import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime, time_diff_in_seconds, get_datetime

class AgileWorkTimer(Document):
    def validate(self):
        """Validate timer"""
        # Check for existing running timer for same user
        if self.status == 'Running' and not self.name:
            existing = frappe.db.exists('Agile Work Timer', {
                'user': self.user,
                'status': 'Running'
            })
            if existing:
                frappe.throw(f"You already have a running timer for task {frappe.db.get_value('Agile Work Timer', existing, 'task')}")
        
        # Calculate time spent if timer is stopped
        if self.status == 'Stopped' and self.start_time and self.end_time:
            self.time_spent_seconds = time_diff_in_seconds(
                get_datetime(self.end_time),
                get_datetime(self.start_time)
            )
    
    def get_elapsed_time(self):
        """Get elapsed time for running timer"""
        if self.status != 'Running':
            return self.time_spent_seconds or 0
        
        return time_diff_in_seconds(
            now_datetime(),
            get_datetime(self.start_time)
        )
    
    def format_elapsed_time(self):
        """Format elapsed time for display"""
        seconds = self.get_elapsed_time()
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"