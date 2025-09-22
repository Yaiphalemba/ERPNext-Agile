import frappe
from frappe.model.document import Document

class AgileProject(Document):
    def before_insert(self):
        """Auto-create ERPNext Project when Agile Project is created"""
        if not self.project:
            self.create_erpnext_project()
        
        # Validate project key format
        self.validate_project_key()
    
    def validate_project_key(self):
        """Ensure project key follows naming conventions"""
        import re
        if not re.match(r'^[A-Z]{2,10}$', self.project_key):
            frappe.throw("Project Key must be 2-10 uppercase letters")
    
    def create_erpnext_project(self):
        """Create linked ERPNext Project automatically"""
        project_doc = frappe.get_doc({
            "doctype": "Project",
            "project_name": self.project_name,
            "status": "Open",
            "is_active": "Yes",
            "project_type": "External",
            "custom_agile_project": self.name  # Link back
        })
        
        # Copy relevant fields
        if self.project_lead:
            project_doc.custom_project_lead = self.project_lead
            
        project_doc.insert()
        self.project = project_doc.name
        
        frappe.msgprint(f"ERPNext Project '{project_doc.name}' created automatically")
    
    def on_update(self):
        """Sync changes to ERPNext Project"""
        if self.project:
            self.sync_to_erpnext_project()
    
    def sync_to_erpnext_project(self):
        """Keep ERPNext Project in sync"""
        project_doc = frappe.get_doc("Project", self.project)
        project_doc.project_name = self.project_name
        project_doc.save()
    
    @frappe.whitelist()
    def create_sprint(self, sprint_name, start_date, end_date):
        """Create new sprint for this project"""
        sprint = frappe.get_doc({
            "doctype": "Agile Sprint",
            "sprint_name": sprint_name,
            "agile_project": self.name,
            "start_date": start_date,
            "end_date": end_date,
            "sprint_goal": ""
        })
        sprint.insert()
        return sprint.name
    
    @frappe.whitelist()
    def get_project_stats(self):
        """Get project statistics for dashboard"""
        return {
            "total_issues": frappe.db.count("Agile Issue", {"agile_project": self.name}),
            "open_issues": frappe.db.count("Agile Issue", {
                "agile_project": self.name, 
                "status": ["not in", ["Closed", "Resolved"]]
            }),
            "current_sprint_issues": self.get_current_sprint_issue_count(),
            "velocity": self.calculate_velocity()
        }
    
    def get_current_sprint_issue_count(self):
        """Get current sprint issue count"""
        current_sprint = frappe.db.get_value("Agile Sprint", {
            "agile_project": self.name,
            "sprint_state": "Active"
        })
        
        if current_sprint:
            return frappe.db.count("Agile Issue", {
                "agile_project": self.name,
                "current_sprint": current_sprint
            })
        return 0
    
    def calculate_velocity(self):
        """Calculate team velocity from last 3 sprints"""
        completed_sprints = frappe.get_all("Agile Sprint", {
            "agile_project": self.name,
            "sprint_state": "Completed"
        }, ["name"], limit=3, order_by="end_date desc")
        
        if not completed_sprints:
            return 0
        
        total_points = 0
        for sprint in completed_sprints:
            sprint_points = frappe.db.sql("""
                SELECT SUM(story_points) 
                FROM `tabAgile Issue` 
                WHERE agile_project = %s 
                AND current_sprint = %s 
                AND status IN ('Closed', 'Resolved')
            """, (self.name, sprint.name))[0][0] or 0
            total_points += sprint_points
        
        return total_points / len(completed_sprints)
    
    def validate(self):
        """Validate Agile Project settings"""
        if self.workflow_scheme and not frappe.db.exists("Agile Workflow Scheme", self.workflow_scheme):
            frappe.throw(f"Workflow Scheme {self.workflow_scheme} does not exist")
        if self.permission_scheme and not frappe.db.exists("Agile Permission Scheme", self.permission_scheme):
            frappe.throw(f"Permission Scheme {self.permission_scheme} does not exist")
        if self.github_repository and self.github_sync_enabled:
            if not frappe.db.exists("App", "erpnext_github_integration"):
                frappe.throw("GitHub Sync is enabled but erpnext_github_integration app is not installed")

def get_dashboard_data(data):
    """Define dashboard data for Agile Project"""
    data = frappe._dict(data)
    
    # Add cards for issue counts by status
    data.cards = [
        {
            "label": "Open Issues",
            "value": frappe.db.count("Agile Issue", {"agile_project": data.name, "status": "Open"}),
            "color": "#b3b3b3"
        },
        {
            "label": "In Progress Issues",
            "value": frappe.db.count("Agile Issue", {"agile_project": data.name, "status": "In Progress"}),
            "color": "#4a90e2"
        },
        {
            "label": "Resolved Issues",
            "value": frappe.db.count("Agile Issue", {"agile_project": data.name, "status": "Resolved"}),
            "color": "#65ba43"
        }
    ]
    
    # Add chart for issue status distribution
    statuses = frappe.get_all("Agile Issue Status", fields=["name"], order_by="sort_order")
    status_counts = [
        frappe.db.count("Agile Issue", {"agile_project": data.name, "status": status.name})
        for status in statuses
    ]
    data.charts = [
        {
            "chart_name": "Issue Status Distribution",
            "chart_type": "bar",
            "x_axis": [status.name for status in statuses],
            "data": [{"values": status_counts, "label": "Issues"}]
        }
    ]
    
    # Add heatmap for issue creation
    data.heatmap = {
        "label": "Issue Creation Activity",
        "field": "creation",
        "time_interval": "Daily",
        "doctype": "Agile Issue",
        "filters": {"agile_project": data.name}
    }
    
    return data