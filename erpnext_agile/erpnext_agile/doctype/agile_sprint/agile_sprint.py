import frappe
from frappe.model.document import Document

class AgileSprint(Document):
    def before_insert(self):
        """Set default values"""
        if not self.sprint_state:
            self.sprint_state = "Future"
    
    @frappe.whitelist()
    def start_sprint(self):
        """Start the sprint - Jira-style"""
        self.sprint_state = "Active"
        self.actual_start_date = frappe.utils.today()
        
        # Close any other active sprints in this project
        frappe.db.sql("""
            UPDATE `tabAgile Sprint` 
            SET sprint_state = 'Completed' 
            WHERE agile_project = %s AND sprint_state = 'Active' AND name != %s
        """, (self.agile_project, self.name))
        
        self.save()
        frappe.msgprint(f"Sprint '{self.sprint_name}' started!")
    
    @frappe.whitelist()
    def complete_sprint(self):
        """Complete the sprint"""
        self.sprint_state = "Completed"
        self.actual_end_date = frappe.utils.today()
        
        # Move incomplete issues to backlog
        incomplete_issues = frappe.get_all("Task", {
            "current_sprint": self.name,
            "status": ["not in", ["Resolved", "Closed"]]
        })
        
        for issue in incomplete_issues:
            frappe.db.set_value("Task", issue.name, "current_sprint", "")
        
        self.save()
        frappe.msgprint(f"Sprint completed! {len(incomplete_issues)} issues moved to backlog")
    
    def get_sprint_progress(self):
        """Calculate sprint progress"""
        total_points = frappe.db.sql("""
            SELECT SUM(story_points) FROM `tabAgile Issue` 
            WHERE current_sprint = %s
        """, self.name)[0][0] or 0
        
        completed_points = frappe.db.sql("""
            SELECT SUM(story_points) FROM `tabAgile Issue` 
            WHERE current_sprint = %s AND status IN ('Resolved', 'Closed')
        """, self.name)[0][0] or 0
        
        return {
            "total_points": total_points,
            "completed_points": completed_points,
            "progress_percentage": (completed_points / total_points * 100) if total_points > 0 else 0
        }