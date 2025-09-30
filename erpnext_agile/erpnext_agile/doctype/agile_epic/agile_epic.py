import frappe
from frappe.model.document import Document

class AgileEpic(Document):
    def validate(self):
        """Validate epic data"""
        # Validate project exists and is agile-enabled
        if self.project:
            if not frappe.db.get_value('Project', self.project, 'enable_agile'):
                frappe.throw(f"Project {self.project} is not agile-enabled")
    
    def get_progress(self):
        """Get epic progress"""
        from erpnext_agile.agile_backlog_manager import AgileBacklogManager
        manager = AgileBacklogManager()
        return manager.get_epic_progress(self.name)