# erpnext_agile/overrides/project.py
import frappe
from frappe import _
import re
from erpnext.projects.doctype.project.project import Project

class AgileProject(Project):
    def before_insert(self):
        """Auto-generate project key and setup agile features"""
        if self.enable_agile:
            if not self.project_key:
                self.project_key = self.generate_project_key()
            self.validate_project_key()

    def validate(self):
        super().validate()
        if self.enable_agile:
            self.validate_agile_settings()
        if self.github_repository and self.repository:
            # Ensure repository and github_repository are in sync
            self.sync_github_repository()

    # ----------------------
    # GitHub sync controller
    # ----------------------
    def sync_github_repository(self):
        """Keep github_repository and repository fields in sync"""
        if self.github_repository and not self.repository:
            self.repository = self.github_repository
        elif self.repository and not self.github_repository:
            self.github_repository = self.repository
        elif self.github_repository != self.repository:
            # If both exist but different, prefer the one that was last modified
            # We'll assume github_repository is the "Agile" source of truth
            self.repository = self.github_repository

    # ----------------------
    # Existing methods ...
    # ----------------------
    def generate_project_key(self):
        """Generate project key from project name"""
        clean_name = re.sub(r'[^a-zA-Z]', '', self.project_name)
        if len(clean_name) >= 3:
            key = clean_name[:10].upper()
        else:
            count = frappe.db.count('Project', {'enable_agile': 1})
            key = f"PROJ{count + 1}"

        # Ensure uniqueness
        counter = 1
        original_key = key
        while frappe.db.exists('Project', {'project_key': key}):
            key = f"{original_key}{counter}"
            counter += 1
        return key

    def validate_project_key(self):
        """Validate project key format"""
        if not re.match(r'^[A-Z]{2,15}$', self.project_key):
            frappe.throw(_("Project Key must be 2-15 uppercase letters"))

    def validate_agile_settings(self):
        """Validate agile-specific settings"""
        if self.workflow_scheme and not frappe.db.exists("Agile Workflow Scheme", self.workflow_scheme):
            frappe.throw(f"Workflow Scheme {self.workflow_scheme} does not exist")
        if self.permission_scheme and not frappe.db.exists("Agile Permission Scheme", self.permission_scheme):
            frappe.throw(f"Permission Scheme {self.permission_scheme} does not exist")

    @frappe.whitelist()
    def get_project_stats(self):
        """Get agile project statistics"""
        if not self.enable_agile:
            return {}
        return {
            "total_issues": frappe.db.count("Task", {"project": self.name}),
            "open_issues": frappe.db.count("Task", {
                "project": self.name,
                "status": ["not in", ["Completed", "Cancelled"]]
            }),
            "current_sprint_issues": self.get_current_sprint_issue_count(),
            "velocity": self.calculate_velocity()
        }

    def get_current_sprint_issue_count(self):
        """Get current sprint issue count"""
        current_sprint = frappe.db.get_value("Agile Sprint", {
            "project": self.name,
            "sprint_state": "Active"
        }, "name")
        if current_sprint:
            return frappe.db.count("Task", {
                "project": self.name,
                "current_sprint": current_sprint
            })
        return 0

    def calculate_velocity(self):
        """Calculate team velocity from last 3 sprints"""
        completed_sprints = frappe.get_all("Agile Sprint", {
            "project": self.name,
            "sprint_state": "Completed"
        }, ["name"], limit=3, order_by="actual_end_date desc")
        if not completed_sprints:
            return 0

        total_points = 0
        for sprint in completed_sprints:
            sprint_points = frappe.db.sql("""
                SELECT SUM(story_points) 
                FROM `tabTask` 
                WHERE project = %s 
                AND current_sprint = %s 
                AND status IN ('Completed')
            """, (self.name, sprint.name))[0][0] or 0
            total_points += sprint_points
        return total_points / len(completed_sprints)