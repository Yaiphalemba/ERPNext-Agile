# erpnext_agile/overrides/task.py
import frappe
from frappe import _
import re
from erpnext.projects.doctype.task.task import Task

class AgileTask(Task):
    def validate(self):
        super().validate()
        if self.is_agile:
            self.validate_agile_fields()
        if self.parent_issue:
            self.sync_parent_task()
        # sync original_estimate → expected_time
        if self.original_estimate:
            self.sync_expected_time()
        # sync agile status → task status
        if self.issue_status:
            self.status = map_agile_status_to_task_status(self.issue_status)
        
        # sync agile priority → task priority
        if self.issue_priority:
            self.priority = map_agile_priority_to_task_priority(self.issue_priority)

    def sync_parent_task(self):
        """Keep parent_task and parent_issue in sync"""
        if self.parent_issue and not self.parent_task:
            self.parent_task = self.parent_issue
            
    def sync_expected_time(self):
        """Sync original_estimate to expected_time"""
        if self.original_estimate:
            self.expected_time = self.original_estimate/3600  # convert seconds to hours
            
        if self.expected_time:
            self.original_estimate = self.expected_time*3600  # convert hours to seconds
    
    def validate_agile_fields(self):
        """Validate agile-specific fields"""
        if self.issue_type and not frappe.db.exists("Agile Issue Type", self.issue_type):
            frappe.throw(f"Invalid Issue Type: {self.issue_type}")
        
        if self.issue_priority and not frappe.db.exists("Agile Issue Priority", self.issue_priority):
            frappe.throw(f"Invalid Priority: {self.issue_priority}")
        
def map_agile_status_to_task_status(agile_status):
    """Map agile status to ERPNext task status"""
    status_mapping = {
        "Open": "Open",
        "In Progress": "Working", 
        "In Review": "Pending Review",
        "Testing": "Pending Review",
        "Resolved": "Completed",
        "Closed": "Completed",
        "Reopened": "Open",
        "Blocked": "Open",
        "To Do": "Open",
        "Done": "Completed"
    }
    return status_mapping.get(agile_status, "Open")

def map_agile_priority_to_task_priority(agile_priority: str) -> str:
    """Map agile priority scale to ERPNext Task priority."""
    priority_mapping = {
        "Lowest": "Low",
        "Low": "Low",
        "Medium": "Medium",
        "High": "High",
        "Critical": "Urgent"
    }
    return priority_mapping.get(agile_priority, "Medium")