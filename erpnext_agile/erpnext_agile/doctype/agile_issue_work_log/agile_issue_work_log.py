import frappe
from frappe.model.document import Document

class AgileIssueWorkLog(Document):
    def validate(self):
        """Validate work log"""
        if not self.logged_at:
            self.logged_at = frappe.utils.now_datetime()
        
        # Format display time
        if self.time_spent_seconds and not self.time_spent_display:
            self.time_spent_display = self.format_time_display(self.time_spent_seconds)
    
    def format_time_display(self, seconds):
        """Format seconds to display format"""
        if not seconds:
            return "0m"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        
        if hours > 0 and minutes > 0:
            return f"{hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h"
        else:
            return f"{minutes}m"