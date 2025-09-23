import frappe
import re
from frappe.model.document import Document

class AgileProject(Document):
    def before_insert(self):
        """Auto-create ERPNext Project and validate key before inserting"""
        try:
            if not self.custom_erpnext_project:
                self.create_erpnext_project()
            self.validate_project_key()
        except Exception as e:
            frappe.log_error(f"Agile Project before_insert failed: {str(e)}"[:140], "Agile Project Before Insert Error")
            raise
    
    def validate_project_key(self):
        """Ensure project key follows naming conventions"""
        try:
            if not self.project_key:
                frappe.throw("Project Key is mandatory")
            if not isinstance(self.project_key, str):
                frappe.throw("Project Key must be a string")
            if not re.match(r'^[A-Z]{2,10}$', self.project_key):
                frappe.throw("Project Key must be 2-10 uppercase letters (e.g., SAMPLE)")
        except Exception as e:
            frappe.log_error(f"Project Key validation failed: {str(e)}"[:140], "Project Key Validation Error")
            raise
    
    def create_erpnext_project(self):
        """Create linked ERPNext Project automatically"""
        try:
            project_doc = frappe.get_doc({
                "doctype": "Project",
                "project_name": self.project_name,
                "status": "Open",
                "is_active": "Yes",
                "project_type": "External",
                "custom_agile_project": self.name,
                "custom_enable_agile": 1
            })
            
            # if self.project_lead:
            #     project_doc.custom_project_lead = self.project_lead
            
            project_doc.flags.ignore_agile_hook = True  # Prevent recursive hook
            project_doc.insert()
            self.custom_erpnext_project = project_doc.name
            
            frappe.msgprint(f"ERPNext Project '{project_doc.name}' created automatically")
        except Exception as e:
            frappe.log_error(f"Failed to create ERPNext Project: {str(e)}"[:140], "ERPNext Project Creation Error")
            raise
    
    def on_update(self):
        """Sync changes to ERPNext Project"""
        try:
            if self.custom_erpnext_project:
                self.sync_to_erpnext_project()
        except Exception as e:
            frappe.log_error(f"Sync to ERPNext Project failed: {str(e)}"[:140], "Sync ERPNext Project Error")
            raise
    
    def sync_to_erpnext_project(self):
        """Keep ERPNext Project in sync"""
        try:
            project_doc = frappe.get_doc("Project", self.custom_erpnext_project)
            project_doc.project_name = self.project_name
            project_doc.save()
        except Exception as e:
            frappe.log_error(f"Failed to sync ERPNext Project: {str(e)}"[:140], "Sync ERPNext Project Error")
            raise
    
    @frappe.whitelist()
    def create_sprint(self, sprint_name, start_date, end_date):
        """Create new sprint for this project"""
        try:
            sprint = frappe.get_doc({
                "doctype": "Agile Sprint",
                "sprint_name": sprint_name,
                "agile_project": self.name,
                "start_date": start_date,
                "end_date": end_date,
                "sprint_goal": "",
                "status": "Active"
            })
            sprint.insert()
            frappe.msgprint(f"Sprint '{sprint.name}' created successfully")
            return sprint.name
        except Exception as e:
            frappe.log_error(f"Failed to create sprint: {str(e)}"[:140], "Sprint Creation Error")
            raise
    
    @frappe.whitelist()
    def get_project_stats(self):
        """Get project statistics for dashboard"""
        try:
            return {
                "total_issues": frappe.db.count("Agile Issue", {"agile_project": self.name}),
                "open_issues": frappe.db.count("Agile Issue", {
                    "agile_project": self.name, 
                    "status": ["not in", ["Closed", "Resolved"]]
                }),
                "current_sprint_issues": self.get_current_sprint_issue_count(),
                "velocity": self.calculate_velocity()
            }
        except Exception as e:
            frappe.log_error(f"Failed to get project stats: {str(e)}"[:140], "Project Stats Error")
            return {
                "total_issues": 0,
                "open_issues": 0,
                "current_sprint_issues": 0,
                "velocity": 0
            }
    
    def get_current_sprint_issue_count(self):
        """Get current sprint issue count"""
        try:
            current_sprint = frappe.db.get_value("Agile Sprint", {
                "agile_project": self.name,
                "status": "Active"
            }, "name")
            
            if current_sprint:
                return frappe.db.count("Agile Issue", {
                    "agile_project": self.name,
                    "current_sprint": current_sprint
                })
            return 0
        except Exception as e:
            frappe.log_error(f"Failed to get current sprint issue count: {str(e)}"[:140], "Sprint Issue Count Error")
            return 0
    
    def calculate_velocity(self):
        """Calculate team velocity from last 3 sprints"""
        try:
            completed_sprints = frappe.get_all("Agile Sprint", {
                "agile_project": self.name,
                "status": "Completed"
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
        except Exception as e:
            frappe.log_error(f"Failed to calculate velocity: {str(e)}"[:140], "Velocity Calculation Error")
            return 0
    
    def validate(self):
        """Validate Agile Project settings"""
        try:
            if self.workflow_scheme and not frappe.db.exists("Agile Workflow Scheme", self.workflow_scheme):
                frappe.throw(f"Workflow Scheme {self.workflow_scheme} does not exist")
            if self.permission_scheme and not frappe.db.exists("Agile Permission Scheme", self.permission_scheme):
                frappe.throw(f"Permission Scheme {self.permission_scheme} does not exist")
            if self.github_repository and self.github_sync_enabled:
                if not frappe.db.exists("App", "erpnext_github_integration"):
                    frappe.throw("GitHub Sync is enabled but erpnext_github_integration app is not installed")
        except Exception as e:
            frappe.log_error(f"Agile Project validation failed: {str(e)}"[:140], "Agile Project Validation Error")
            raise

def get_dashboard_data(data):
    """Define dashboard data for Agile Project"""
    try:
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
            "type": "bar",
            "data": {
                "labels": [status.name for status in statuses],
                "datasets": [
                    {
                        "label": "Issues",
                        "data": status_counts,
                        "backgroundColor": "#4a90e2",
                        "borderColor": "#2a6eb2",
                        "borderWidth": 1
                    }
                ]
            },
            "options": {
                "scales": {
                    "y": {
                        "beginAtZero": True,
                        "title": {
                            "display": True,
                            "text": "Number of Issues"
                        }
                    },
                    "x": {
                        "title": {
                            "display": True,
                            "text": "Status"
                        }
                    }
                },
                "plugins": {
                    "legend": {
                        "display": True
                    },
                    "title": {
                        "display": True,
                        "text": "Issue Status Distribution"
                    }
                }
            }
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
    except Exception as e:
        frappe.log_error(f"Failed to generate dashboard data: {str(e)}"[:140], "Dashboard Data Error")
        return frappe._dict({
            "cards": [],
            "charts": [],
            "heatmap": {}
        })