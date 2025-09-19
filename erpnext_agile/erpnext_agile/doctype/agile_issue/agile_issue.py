import frappe
from frappe.model.document import Document
from frappe.utils import now, add_days

class AgileIssue(Document):
    def before_insert(self):
        """Auto-generate issue key and create linked entities"""
        if not self.issue_key:
            self.issue_key = self.generate_issue_key()
        
        if not self.task:
            self.create_erpnext_task()
        
        # Set default reporter
        if not self.reporter:
            self.reporter = frappe.session.user
    
    def generate_issue_key(self):
        """Generate unique issue key like PROJ-123"""
        agile_project = frappe.get_doc("Agile Project", self.agile_project)
        
        # Get next number for this project
        last_issue = frappe.db.sql("""
            SELECT issue_key FROM `tabAgile Issue` 
            WHERE agile_project = %s 
            ORDER BY creation DESC LIMIT 1
        """, self.agile_project)
        
        if last_issue:
            # Extract number from last issue key
            last_number = int(last_issue[0][0].split('-')[-1])
            next_number = last_number + 1
        else:
            next_number = 1
        
        return f"{agile_project.project_key}-{next_number}"
    
    def create_erpnext_task(self):
        """Create linked ERPNext Task automatically"""
        agile_project = frappe.get_doc("Agile Project", self.agile_project)
        
        task_doc = frappe.get_doc({
            "doctype": "Task",
            "subject": f"{self.issue_key}: {self.summary}",
            "description": self.description,
            "project": agile_project.project,
            "status": self.map_status_to_task(),
            "priority": self.priority,
            "custom_agile_issue": self.name,
            "custom_issue_key": self.issue_key
        })
        
        if self.assignee:
            task_doc.custom_assigned_to = self.assignee
        
        task_doc.insert()
        self.task = task_doc.name
    
    def map_status_to_task(self):
        """Map agile status to ERPNext task status"""
        status_mapping = {
            "Open": "Open",
            "In Progress": "Working",
            "In Review": "Pending Review", 
            "Testing": "Pending Review",
            "Resolved": "Completed",
            "Closed": "Completed"
        }
        return status_mapping.get(self.status, "Open")
    
    def on_update(self):
        """Sync changes to ERPNext Task and GitHub"""
        if self.task:
            self.sync_to_erpnext_task()
        
        # Sync to GitHub if enabled
        if self.should_sync_to_github():
            self.sync_to_github()
    
    def sync_to_erpnext_task(self):
        """Keep ERPNext Task in sync"""
        task_doc = frappe.get_doc("Task", self.task)
        task_doc.subject = f"{self.issue_key}: {self.summary}"
        task_doc.description = self.description
        task_doc.status = self.map_status_to_task()
        task_doc.save()
    
    def should_sync_to_github(self):
        """Check if GitHub sync is enabled for this project"""
        agile_project = frappe.get_doc("Agile Project", self.agile_project)
        return agile_project.auto_create_github_issues and agile_project.github_repository
    
    def sync_to_github(self):
        """Sync issue to GitHub using existing integration"""
        agile_project = frappe.get_doc("Agile Project", self.agile_project)
        
        if not self.github_issue_number:
            # Create new GitHub issue
            self.create_github_issue(agile_project)
        else:
            # Update existing GitHub issue
            self.update_github_issue(agile_project)
    
    def create_github_issue(self, agile_project):
        """Create GitHub issue using existing integration"""
        try:
            github_issue = frappe.call(
                'erpnext_github_integration.github_api.create_issue',
                repository=agile_project.github_repository,
                title=f"{self.issue_key}: {self.summary}",
                body=self.get_github_issue_body(),
                assignees=self.get_github_assignees(),
                labels=self.get_github_labels()
            )
            
            self.github_issue_number = github_issue.get('number')
            frappe.db.set_value("Agile Issue", self.name, "github_issue_number", self.github_issue_number)
            
        except Exception as e:
            frappe.log_error(f"Failed to create GitHub issue: {str(e)}")
    
    def get_github_issue_body(self):
        """Format issue body for GitHub"""
        body = f"""
**Issue Type:** {self.issue_type}
**Priority:** {self.priority}
**Story Points:** {self.story_points or 'Not estimated'}

## Description
{self.description or 'No description provided'}

---
*Created from ERPNext Agile: {frappe.utils.get_url()}/app/agile-issue/{self.name}*
        """
        return body.strip()
    
    def get_github_assignees(self):
        """Get GitHub usernames for assignees"""
        if not self.assignee:
            return []
        
        # Get GitHub username from user profile
        github_username = frappe.db.get_value("User", self.assignee, "github_username")
        return [github_username] if github_username else []
    
    def get_github_labels(self):
        """Convert agile labels to GitHub labels"""
        labels = []
        
        # Add issue type as label
        if self.issue_type:
            labels.append(self.issue_type.lower())
        
        # Add priority as label
        if self.priority:
            labels.append(f"priority-{self.priority.lower()}")
        
        # Add custom labels
        for label in self.labels:
            labels.append(label.label_name)
        
        return labels
    
    @frappe.whitelist()
    def start_work(self):
        """Start work on issue - Jira-style quick action"""
        self.status = "In Progress"
        
        # Create GitHub branch if enabled
        agile_project = frappe.get_doc("Agile Project", self.agile_project)
        if agile_project.auto_create_branches:
            self.create_github_branch(agile_project)
        
        self.save()
        frappe.msgprint(f"Started work on {self.issue_key}")
    
    def create_github_branch(self, agile_project):
        """Create feature branch for issue"""
        import re
        
        # Clean summary for branch name
        clean_summary = re.sub(r'[^a-zA-Z0-9\s]', '', self.summary)
        clean_summary = '-'.join(clean_summary.lower().split()[:4])
        
        branch_name = f"feature/{self.issue_key.lower()}-{clean_summary}"
        
        try:
            branch = frappe.call(
                'erpnext_github_integration.github_api.create_branch',
                repository=agile_project.github_repository,
                branch_name=branch_name,
                base_branch='main'
            )
            
            self.github_branch = branch_name
            frappe.db.set_value("Agile Issue", self.name, "github_branch", branch_name)
            
        except Exception as e:
            frappe.log_error(f"Failed to create GitHub branch: {str(e)}")
    
    @frappe.whitelist()
    def create_pull_request(self, head_branch, base_branch='main', pr_title=None):
        """Create pull request for issue"""
        agile_project = frappe.get_doc("Agile Project", self.agile_project)
        
        if not pr_title:
            pr_title = f"{self.issue_key}: {self.summary}"
        
        pr_body = f"""
Fixes #{self.github_issue_number}

## Changes
<!-- Describe your changes here -->

## Testing
<!-- Describe how to test your changes -->

---
**Agile Issue:** {self.issue_key}
**Story Points:** {self.story_points or 'Not estimated'}
        """
        
        try:
            pr = frappe.call(
                'erpnext_github_integration.github_api.create_pull_request',
                repository=agile_project.github_repository,
                title=pr_title,
                head=head_branch,
                base=base_branch,
                body=pr_body.strip()
            )
            
            self.github_pull_request = pr.get('number')
            self.status = "In Review"
            self.save()
            
            frappe.msgprint(f"Pull Request #{pr.get('number')} created")
            return pr
            
        except Exception as e:
            frappe.throw(f"Failed to create pull request: {str(e)}")
    
    @frappe.whitelist()
    def log_work(self, time_spent, description="", start_time=None):
        """Log work time - Jira-style work logging"""
        work_log = frappe.get_doc({
            "doctype": "Agile Issue Work Log",
            "parent": self.name,
            "parenttype": "Agile Issue",
            "parentfield": "work_logs",
            "time_spent": time_spent,
            "description": description,
            "logged_by": frappe.session.user,
            "date_logged": start_time or now()
        })
        
        # Update time spent
        current_time = frappe.utils.time_diff_in_seconds(self.time_spent or "00:00:00", "00:00:00")
        new_time_seconds = current_time + frappe.utils.time_diff_in_seconds(time_spent, "00:00:00")
        self.time_spent = frappe.utils.seconds_to_time(new_time_seconds)
        
        # Create ERPNext Timesheet entry
        self.create_timesheet_entry(time_spent, description)
        
        self.save()
    
    def create_timesheet_entry(self, time_spent, description):
        """Create ERPNext Timesheet entry for billing/tracking"""
        agile_project = frappe.get_doc("Agile Project", self.agile_project)
        
        timesheet = frappe.get_doc({
            "doctype": "Timesheet",
            "employee": frappe.db.get_value("Employee", {"user_id": self.assignee}),
            "time_logs": [{
                "activity_type": "Development",
                "hours": frappe.utils.time_diff_in_hours(time_spent, "00:00:00"),
                "project": agile_project.project,
                "task": self.task,
                "description": f"{self.issue_key}: {description}"
            }]
        })
        timesheet.insert()