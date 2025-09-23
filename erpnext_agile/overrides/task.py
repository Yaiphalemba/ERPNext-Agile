# erpnext_agile/overrides/task.py
import frappe
from frappe import _
import re
from erpnext.projects.doctype.task.task import Task

class AgileTask(Task):
    def before_insert(self):
        """Auto-generate issue key if agile project"""
        super().before_insert()
        if self.is_agile_task():
            if not self.issue_key:
                self.issue_key = self.generate_issue_key()
            if not self.reporter:
                self.reporter = frappe.session.user
            if not self.issue_type:
                self.issue_type = "Task"  # Default issue type
    
    def is_agile_task(self):
        """Check if this task belongs to an agile project"""
        if self.project:
            return frappe.db.get_value("Project", self.project, "enable_agile")
        return False
    
    def generate_issue_key(self):
        """Generate unique issue key like PROJ-123"""
        if not self.project:
            return None
            
        project_doc = frappe.get_doc("Project", self.project)
        if not project_doc.enable_agile or not project_doc.project_key:
            return None
        
        # Get next number for this project
        last_issue = frappe.db.sql("""
            SELECT issue_key FROM `tabTask` 
            WHERE project = %s AND issue_key IS NOT NULL
            ORDER BY creation DESC LIMIT 1
        """, self.project)
        
        if last_issue and last_issue[0][0]:
            # Extract number from last issue key
            last_number = int(last_issue[0][0].split('-')[-1])
            next_number = last_number + 1
        else:
            next_number = 1
        
        return f"{project_doc.project_key}-{next_number}"
    
    def validate(self):
        super().validate()
        if self.is_agile_task():
            self.validate_agile_fields()
        if self.github_pull_request and self.github_pr_number:
            self.sync_github_pr()

    # ----------------------
    # GitHub sync controller
    # ----------------------
    def sync_github_pr(self):
        """Keep github_repository and repository fields in sync"""
        if self.github_pull_request and not self.github_pr_number:
            self.github_pr_number = self.github_pull_request
        elif self.github_pr_number and not self.github_pull_request:
            self.github_pull_request = self.github_pr_number
        elif self.github_pull_request != self.github_pr_number:
            # If both exist but different, prefer the one that was last modified
            self.github_pr_number = self.github_pull_request
    
    def validate_agile_fields(self):
        """Validate agile-specific fields"""
        if self.issue_type and not frappe.db.exists("Agile Issue Type", self.issue_type):
            frappe.throw(f"Invalid Issue Type: {self.issue_type}")
        
        if self.issue_priority and not frappe.db.exists("Agile Issue Priority", self.issue_priority):
            frappe.throw(f"Invalid Priority: {self.issue_priority}")
    
    def on_update(self):
        super().on_update()
        if self.is_agile_task():
            self.sync_to_github()
    
    @frappe.whitelist()
    def start_work(self):
        """Start work on issue - Jira-style quick action"""
        self.status = "Working"
        
        # Create GitHub branch if enabled
        project_doc = frappe.get_doc("Project", self.project)
        if project_doc.auto_create_branches and project_doc.github_repository:
            self.create_github_branch(project_doc)
        
        self.save()
        frappe.msgprint(f"Started work on {self.issue_key}")
    
    def create_github_branch(self, project_doc):
        """Create feature branch for issue"""
        clean_summary = re.sub(r'[^a-zA-Z0-9\s]', '', self.subject)
        clean_summary = '-'.join(clean_summary.lower().split()[:4])
        
        branch_name = f"feature/{self.issue_key.lower()}-{clean_summary}"
        
        try:
            branch = frappe.call(
                'erpnext_github_integration.github_api.create_branch',
                repository=project_doc.github_repository,
                branch_name=branch_name,
                base_branch='main'
            )
            
            self.github_branch = branch_name
            frappe.db.set_value("Task", self.name, "github_branch", branch_name)
            
        except Exception as e:
            frappe.log_error(f"Failed to create GitHub branch: {str(e)}")
    
    @frappe.whitelist()
    def log_work(self, time_spent, description="", start_time=None):
        """Log work time - Jira-style work logging"""
        work_log = {
            "time_spent": time_spent,
            "description": description,
            "logged_by": frappe.session.user,
            "date_logged": start_time or frappe.utils.now()
        }
        
        if not self.work_logs:
            self.work_logs = []
        self.append("work_logs", work_log)
        
        # Update time spent
        current_time = frappe.utils.time_diff_in_seconds(self.time_spent or "00:00:00", "00:00:00")
        new_time_seconds = current_time + frappe.utils.time_diff_in_seconds(time_spent, "00:00:00")
        self.time_spent = frappe.utils.seconds_to_time(new_time_seconds)
        
        self.save()
        
        # Create ERPNext Timesheet entry
        self.create_timesheet_entry(time_spent, description)
    
    def create_timesheet_entry(self, time_spent, description):
        """Create ERPNext Timesheet entry"""
        employee = frappe.db.get_value("Employee", {"user_id": self.assigned_to})
        if not employee:
            return
        
        timesheet = frappe.get_doc({
            "doctype": "Timesheet",
            "employee": employee,
            "time_logs": [{
                "activity_type": "Development",
                "hours": frappe.utils.time_diff_in_hours(time_spent, "00:00:00"),
                "project": self.project,
                "task": self.name,
                "description": f"{self.issue_key}: {description}"
            }]
        })
        timesheet.insert()