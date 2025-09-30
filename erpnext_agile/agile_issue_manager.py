import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import today, add_days, get_datetime, now_datetime
import json

class AgileIssueManager:
    """Core class for managing Agile Issues (Tasks with Agile functionality)"""
    
    def __init__(self, project=None):
        self.project = project
        
    @frappe.whitelist()
    def create_agile_issue(self, issue_data):
        """Create a new agile issue with full Jira-like functionality"""
        
        # Validate project is agile-enabled
        if not self.is_agile_project(issue_data.get('project')):
            frappe.throw(_("Project {0} is not agile-enabled").format(issue_data.get('project')))
        
        project_doc = frappe.get_doc('Project', issue_data.get('project'))
        
        # Generate issue key (Jira-style)
        issue_key = self.generate_issue_key(project_doc)
        
        # Create the Task with agile fields
        task_doc = frappe.get_doc({
            'doctype': 'Task',
            'subject': issue_data.get('summary'),
            'description': issue_data.get('description', ''),
            'project': issue_data.get('project'),
            'is_agile': 1,
            
            # Agile-specific fields
            'issue_key': issue_key,
            'issue_type': issue_data.get('issue_type'),
            'issue_priority': issue_data.get('issue_priority'),
            'issue_status': issue_data.get('issue_status') or self.get_default_status(project_doc),
            'reporter': issue_data.get('reporter') or frappe.session.user,
            'story_points': issue_data.get('story_points', 0),
            'epic': issue_data.get('epic'),
            'current_sprint': issue_data.get('sprint'),
            'parent_issue': issue_data.get('parent_issue'),
            
            # Time tracking
            'original_estimate': issue_data.get('original_estimate'),
            'remaining_estimate': issue_data.get('remaining_estimate'),
            
            # GitHub integration
            'github_repo': project_doc.get('github_repository'),
        })
        
        # Add components
        if issue_data.get('components'):
            for component in issue_data.get('components', []):
                task_doc.append('components', {'component': component})
        
        # Add fix versions
        if issue_data.get('fix_versions'):
            for version in issue_data.get('fix_versions', []):
                task_doc.append('fix_versions', {'version': version})
        
        # Add watchers
        if issue_data.get('watchers'):
            for watcher in issue_data.get('watchers', []):
                task_doc.append('watchers', {'user': watcher})
        
        task_doc.insert()
        
        # Create GitHub issue if auto-sync is enabled
        if project_doc.get('auto_create_github_issues') and project_doc.get('github_repository'):
            self.create_github_issue(task_doc)
        
        # Send notifications
        self.send_issue_notifications(task_doc, 'created')
        
        return task_doc
    
    def generate_issue_key(self, project_doc):
        """Generate Jira-style issue key (e.g., PROJ-123)"""
        project_key = project_doc.get('project_key')
        if not project_key:
            frappe.throw(_("Project key is required for agile projects"))
        
        # Get the next issue number for this project
        last_issue = frappe.db.sql("""
            SELECT MAX(CAST(SUBSTRING(issue_key, LENGTH(%s) + 2) AS UNSIGNED)) as last_num
            FROM `tabTask` 
            WHERE project = %s AND issue_key LIKE %s AND is_agile = 1
        """, (project_key, project_doc.name, f"{project_key}-%"), as_dict=True)
        
        next_num = (last_issue[0].get('last_num') or 0) + 1
        return f"{project_key}-{next_num}"
    
    def is_agile_project(self, project_name):
        """Check if project is agile-enabled"""
        return frappe.db.get_value('Project', project_name, 'enable_agile') == 1
    
    def get_default_status(self, project_doc):
        """Get the default status for new issues"""
        workflow_scheme = project_doc.get('workflow_scheme')
        if workflow_scheme:
            # Get the first "To Do" category status
            default_status = frappe.db.get_value(
                'Agile Issue Status', 
                {'status_category': 'To Do'}, 
                'name',
                order_by='sort_order'
            )
            return default_status
        return 'Open'  # Fallback to standard Task status
    
    @frappe.whitelist()
    def transition_issue(self, task_name, from_status, to_status, comment=None):
        """Transition issue from one status to another with workflow validation"""
        
        task_doc = frappe.get_doc('Task', task_name)
        project_doc = frappe.get_doc('Project', task_doc.project)
        
        # Validate workflow transition
        if not self.validate_transition(project_doc, from_status, to_status):
            frappe.throw(_("Invalid transition from {0} to {1}").format(from_status, to_status))
        
        # Update status
        task_doc.issue_status = to_status
        
        # Auto-update remaining estimate based on status
        if self.is_done_status(to_status):
            task_doc.remaining_estimate = 0
            task_doc.status = 'Completed'
        elif self.is_in_progress_status(to_status):
            task_doc.status = 'Working'
        else:
            task_doc.status = 'Open'
        
        task_doc.save()
        
        # Log the transition
        self.log_issue_activity(task_doc, 'status_changed', {
            'from_status': from_status,
            'to_status': to_status,
            'comment': comment
        })
        
        # Update GitHub issue status if linked
        if task_doc.get('github_issue_doc'):
            self.sync_status_to_github(task_doc)
        
        # Send notifications
        self.send_issue_notifications(task_doc, 'transitioned', {
            'from_status': from_status,
            'to_status': to_status
        })
        
        return task_doc
    
    def validate_transition(self, project_doc, from_status, to_status):
        """Validate if transition is allowed based on workflow scheme"""
        workflow_scheme = project_doc.get('workflow_scheme')
        if not workflow_scheme:
            return True  # Allow all transitions if no workflow
        
        scheme_doc = frappe.get_doc('Agile Workflow Scheme', workflow_scheme)
        return scheme_doc.validate_transition(from_status, to_status)
    
    def is_done_status(self, status):
        """Check if status is in Done category"""
        return frappe.db.get_value('Agile Issue Status', status, 'status_category') == 'Done'
    
    def is_in_progress_status(self, status):
        """Check if status is In Progress category"""
        return frappe.db.get_value('Agile Issue Status', status, 'status_category') == 'In Progress'
    
    @frappe.whitelist()
    def assign_issue(self, task_name, assignees, notify=True):
        """Assign issue to users (Jira-style multi-assignment)"""
        task_doc = frappe.get_doc('Task', task_name)
        
        # Clear existing assignments
        frappe.db.sql("DELETE FROM `tabTask Assigned To` WHERE parent = %s", task_name)
        
        # Add new assignments
        for assignee in assignees:
            task_doc.append('assigned_to_users', {'user': assignee})
        
        task_doc.save()
        
        # Update GitHub issue assignees if linked
        if task_doc.get('github_repo') and task_doc.get('github_issue_number'):
            self.sync_assignees_to_github(task_doc, assignees)
        
        if notify:
            self.send_assignment_notifications(task_doc, assignees)
        
        return task_doc
    
    def create_github_issue(self, task_doc):
        """Create corresponding GitHub issue"""
        try:
            from erpnext_github_integration.github_api import create_issue
            
            # Map assignees to GitHub usernames
            github_assignees = []
            for assignee_row in task_doc.get('assigned_to_users', []):
                github_username = frappe.db.get_value('User', assignee_row.user, 'github_username')
                if github_username:
                    github_assignees.append(github_username)
            
            # Create labels based on issue type and priority
            labels = []
            if task_doc.issue_type:
                labels.append(task_doc.issue_type.lower())
            if task_doc.issue_priority:
                labels.append(f"priority:{task_doc.issue_priority.lower()}")
            
            github_issue = create_issue(
                repository=task_doc.github_repo,
                title=f"[{task_doc.issue_key}] {task_doc.subject}",
                body=self.format_github_description(task_doc),
                assignees=github_assignees,
                labels=labels
            )
            
            if github_issue and github_issue.get('issue'):
                issue_data = github_issue['issue']
                task_doc.db_set('github_issue_number', issue_data.get('number'))
                task_doc.db_set('github_issue_doc', github_issue.get('local_doc'))
                
        except Exception as e:
            frappe.log_error(f"Failed to create GitHub issue: {str(e)}")
    
    def format_github_description(self, task_doc):
        """Format task description for GitHub"""
        description = f"**Issue Type:** {task_doc.issue_type or 'Task'}\n"
        description += f"**Priority:** {task_doc.issue_priority or 'Medium'}\n"
        description += f"**Reporter:** {task_doc.reporter}\n"
        if task_doc.story_points:
            description += f"**Story Points:** {task_doc.story_points}\n"
        if task_doc.epic:
            description += f"**Epic:** {task_doc.epic}\n"
        description += f"\n---\n\n{task_doc.description or ''}"
        return description
    
    def sync_assignees_to_github(self, task_doc, assignees):
        """Sync assignees to GitHub issue"""
        try:
            from erpnext_github_integration.github_api import assign_issue
            
            github_usernames = []
            for assignee in assignees:
                github_username = frappe.db.get_value('User', assignee, 'github_username')
                if github_username:
                    github_usernames.append(github_username)
            
            if github_usernames:
                assign_issue(
                    repo_full_name=task_doc.github_repo,
                    issue_number=task_doc.github_issue_number,
                    assignees=github_usernames
                )
        except Exception as e:
            frappe.log_error(f"Failed to sync assignees to GitHub: {str(e)}")
    
    def log_issue_activity(self, task_doc, activity_type, data):
        """Log issue activity for audit trail"""
        activity_doc = frappe.get_doc({
            'doctype': 'Agile Issue Activity',
            'issue': task_doc.name,
            'activity_type': activity_type,
            'user': frappe.session.user,
            'timestamp': now_datetime(),
            'data': json.dumps(data)
        })
        activity_doc.insert()
    
    def send_issue_notifications(self, task_doc, event_type, data=None):
        """Send notifications for issue events"""
        if not frappe.db.get_value('Project', task_doc.project, 'enable_email_notifications'):
            return
        
        recipients = set()
        
        # Add reporter
        if task_doc.reporter:
            recipients.add(task_doc.reporter)
        
        # Add assignees
        for assignee_row in task_doc.get('assigned_to_users', []):
            recipients.add(assignee_row.user)
        
        # Add watchers
        for watcher_row in task_doc.get('watchers', []):
            recipients.add(watcher_row.user)
        
        # Remove current user from notifications
        recipients.discard(frappe.session.user)
        
        if recipients:
            self._send_email_notification(task_doc, event_type, list(recipients), data)
    
    def _send_email_notification(self, task_doc, event_type, recipients, data):
        """Send email notification"""
        try:
            subject_map = {
                'created': f"[{task_doc.issue_key}] Issue Created: {task_doc.subject}",
                'transitioned': f"[{task_doc.issue_key}] Status Changed: {task_doc.subject}",
                'assigned': f"[{task_doc.issue_key}] Issue Assigned: {task_doc.subject}",
                'commented': f"[{task_doc.issue_key}] New Comment: {task_doc.subject}"
            }
            
            subject = subject_map.get(event_type, f"[{task_doc.issue_key}] Updated: {task_doc.subject}")
            
            frappe.sendmail(
                recipients=recipients,
                subject=subject,
                template="agile_issue_notification",
                args={
                    'task': task_doc,
                    'event_type': event_type,
                    'data': data,
                    'site_url': frappe.utils.get_url()
                }
            )
        except Exception as e:
            frappe.log_error(f"Failed to send notification: {str(e)}")
    
    def send_assignment_notifications(self, task_doc, assignees):
        """Send assignment notifications"""
        self.send_issue_notifications(task_doc, 'assigned', {'assignees': assignees})