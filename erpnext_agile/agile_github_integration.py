import frappe
from frappe import _
from frappe.model.document import Document
import json
import re

class AgileGitHubIntegration:
    """Bridge between Agile Issues and GitHub Integration"""
    
    def __init__(self):
        pass
    
    @frappe.whitelist()
    def sync_agile_issue_to_github(self, task_name):
        """Sync an agile issue to GitHub"""
        task_doc = frappe.get_doc('Task', task_name)
        
        if not task_doc.is_agile:
            frappe.throw(_("Task is not an agile issue"))
        
        project_doc = frappe.get_doc('Project', task_doc.project)
        
        if not project_doc.get('auto_create_github_issues') or not project_doc.get('github_repository'):
            frappe.throw(_("GitHub integration not enabled for this project"))
        
        try:
            from erpnext_github_integration.github_api import create_issue
            
            # Prepare GitHub issue data
            github_data = self.prepare_github_issue_data(task_doc)
            
            # Create GitHub issue
            result = create_issue(
                repository=project_doc.github_repository,
                title=github_data['title'],
                body=github_data['body'],
                assignees=github_data.get('assignees', []),
                labels=github_data.get('labels', [])
            )
            
            if result and result.get('issue'):
                issue_data = result['issue']
                
                # Update task with GitHub information
                task_doc.db_set('github_repo', project_doc.github_repository)
                task_doc.db_set('github_issue_number', issue_data.get('number'))
                task_doc.db_set('github_issue_doc', result.get('local_doc'))
                
                # Create branch if enabled
                if project_doc.get('auto_create_branches'):
                    self.create_feature_branch(task_doc, project_doc)
                
                frappe.msgprint(_("GitHub issue #{0} created successfully").format(issue_data.get('number')))
                return result
                
        except Exception as e:
            frappe.log_error(f"Error syncing issue to GitHub: {str(e)}")
            frappe.throw(_("Failed to create GitHub issue: {0}").format(str(e)))
    
    def prepare_github_issue_data(self, task_doc):
        """Prepare GitHub issue data from agile task"""
        # Title with issue key
        title = f"[{task_doc.issue_key}] {task_doc.subject}"
        
        # Detailed body
        body = self.format_github_issue_body(task_doc)
        
        # Assignees (convert to GitHub usernames)
        assignees = []
        for assignee_row in task_doc.get('assigned_to_users', []):
            github_username = frappe.db.get_value('User', assignee_row.user, 'github_username')
            if github_username:
                assignees.append(github_username)
        
        # Labels based on issue type, priority, and components
        labels = []
        
        if task_doc.issue_type:
            type_label = task_doc.issue_type.lower().replace(' ', '-')
            labels.append(f"type:{type_label}")
        
        if task_doc.issue_priority:
            priority_label = task_doc.issue_priority.lower().replace(' ', '-')
            labels.append(f"priority:{priority_label}")
        
        if task_doc.current_sprint:
            sprint_name = frappe.db.get_value('Agile Sprint', task_doc.current_sprint, 'sprint_name')
            if sprint_name:
                sprint_label = re.sub(r'[^a-zA-Z0-9-]', '-', sprint_name.lower())
                labels.append(f"sprint:{sprint_label}")
        
        # Add component labels
        for component_row in task_doc.get('components', []):
            if component_row.component:
                comp_label = re.sub(r'[^a-zA-Z0-9-]', '-', component_row.component.lower())
                labels.append(f"component:{comp_label}")
        
        return {
            'title': title,
            'body': body,
            'assignees': assignees,
            'labels': labels
        }
    
    def format_github_issue_body(self, task_doc):
        """Format comprehensive GitHub issue body"""
        body = ""
        
        # Issue metadata
        body += "## Issue Details\n\n"
        body += f"**Issue Key:** {task_doc.issue_key}\n"
        body += f"**Type:** {task_doc.issue_type or 'Task'}\n"
        body += f"**Priority:** {task_doc.issue_priority or 'Medium'}\n"
        body += f"**Status:** {task_doc.issue_status or 'Open'}\n"
        body += f"**Reporter:** {task_doc.reporter}\n"
        
        if task_doc.story_points:
            body += f"**Story Points:** {task_doc.story_points}\n"
        
        if task_doc.current_sprint:
            sprint_name = frappe.db.get_value('Agile Sprint', task_doc.current_sprint, 'sprint_name')
            body += f"**Sprint:** {sprint_name}\n"
        
        # Components
        if task_doc.get('components'):
            components = [row.component for row in task_doc.components if row.component]
            if components:
                body += f"**Components:** {', '.join(components)}\n"
        
        # Fix Versions
        if task_doc.get('fix_versions'):
            versions = [row.version for row in task_doc.fix_versions if row.version]
            if versions:
                body += f"**Fix Version/s:** {', '.join(versions)}\n"
        
        # Description
        if task_doc.description:
            body += f"\n## Description\n\n{task_doc.description}\n"
        
        # Acceptance Criteria (if in description)
        if "acceptance criteria" in (task_doc.description or "").lower():
            body += "\n## Acceptance Criteria\n\n"
            body += "_See description above for acceptance criteria._\n"
        
        # ERPNext Link
        site_url = frappe.utils.get_url()
        body += f"\n---\n*Created from ERPNext: {site_url}/app/task/{task_doc.name}*"
        
        return body
    
    def create_feature_branch(self, task_doc, project_doc):
        """Create feature branch for the issue"""
        try:
            branch_name = self.generate_branch_name(task_doc, project_doc)
            
            # Note: This would require GitHub API integration to create branches
            # For now, we'll just store the suggested branch name
            task_doc.db_set('github_branch', branch_name)
            
            # Log the suggested branch creation
            frappe.log_error(
                f"Suggested branch name for {task_doc.issue_key}: {branch_name}",
                "GitHub Branch Creation"
            )
            
        except Exception as e:
            frappe.log_error(f"Error creating feature branch: {str(e)}")
    
    def generate_branch_name(self, task_doc, project_doc):
        """Generate branch name based on project convention"""
        convention = project_doc.get('branch_naming_convention') or "feature/{issue_key}-{summary}"
        
        # Replace placeholders
        branch_name = convention.replace('{issue_key}', task_doc.issue_key.lower())
        
        # Clean summary for branch name
        summary = re.sub(r'[^a-zA-Z0-9\s-]', '', task_doc.subject)
        summary = re.sub(r'\s+', '-', summary.strip()).lower()[:30]  # Max 30 chars
        branch_name = branch_name.replace('{summary}', summary)
        
        # Replace other possible placeholders
        branch_name = branch_name.replace('{type}', (task_doc.issue_type or 'task').lower())
        branch_name = branch_name.replace('{priority}', (task_doc.issue_priority or 'medium').lower())
        
        return branch_name
    
    @frappe.whitelist()
    def sync_github_issue_to_agile(self, repo_issue_name):
        """Sync GitHub issue to agile task"""
        try:
            repo_issue = frappe.get_doc('Repository Issue', repo_issue_name)
            repository = repo_issue.repository
            
            # Find linked project
            project = frappe.db.get_value('Project', {'github_repository': repository}, 'name')
            if not project:
                frappe.throw(_("No project linked to repository {0}").format(repository))
            
            project_doc = frappe.get_doc('Project', project)
            
            if not project_doc.get('enable_agile'):
                frappe.throw(_("Project {0} is not agile-enabled").format(project))
            
            # Check if task already exists
            existing_task = frappe.db.get_value('Task', {
                'github_repo': repository,
                'github_issue_number': repo_issue.issue_number
            }, 'name')
            
            if existing_task:
                # Update existing task
                self.update_agile_task_from_github(existing_task, repo_issue)
                return frappe.get_doc('Task', existing_task)
            else:
                # Create new agile task
                return self.create_agile_task_from_github(repo_issue, project_doc)
                
        except Exception as e:
            frappe.log_error(f"Error syncing GitHub issue to agile: {str(e)}")
            frappe.throw(_("Failed to sync GitHub issue: {0}").format(str(e)))
    
    def create_agile_task_from_github(self, repo_issue, project_doc):
        """Create new agile task from GitHub issue"""
        # Parse GitHub issue title to extract issue key if present
        issue_key_match = re.match(r'\[([A-Z]+-\d+)\]', repo_issue.title)
        issue_key = None
        subject = repo_issue.title
        
        if issue_key_match:
            issue_key = issue_key_match.group(1)
            subject = repo_issue.title[len(issue_key_match.group(0)):].strip()
        
        # Generate new issue key if not found
        if not issue_key:
            from erpnext_agile.agile_issue_manager import AgileIssueManager
            manager = AgileIssueManager()
            issue_key = manager.generate_issue_key(project_doc)
        
        # Parse labels to extract metadata
        labels = (repo_issue.labels or "").split(',')
        issue_type, issue_priority = self.parse_github_labels(labels)
        
        # Create task
        task_doc = frappe.get_doc({
            'doctype': 'Task',
            'subject': subject,
            'description': repo_issue.body or '',
            'project': project_doc.name,
            'is_agile': 1,
            'issue_key': issue_key,
            'issue_type': issue_type,
            'issue_priority': issue_priority,
            'issue_status': 'Open' if repo_issue.state == 'open' else 'Closed',
            'reporter': frappe.session.user,
            'github_repo': repo_issue.repository,
            'github_issue_number': repo_issue.issue_number,
            'github_issue_doc': repo_issue.name
        })
        
        # Add assignees
        for assignee_row in repo_issue.get('assignees_table', []):
            # Try to find ERPNext user by GitHub username
            user = frappe.db.get_value('User', {'github_username': assignee_row.user}, 'name')
            if user:
                task_doc.append('assigned_to_users', {'user': user})
        
        task_doc.insert()
        
        frappe.msgprint(_("Agile issue {0} created from GitHub issue #{1}").format(
            task_doc.issue_key, repo_issue.issue_number
        ))
        
        return task_doc
    
    def update_agile_task_from_github(self, task_name, repo_issue):
        """Update existing agile task from GitHub issue"""
        task_doc = frappe.get_doc('Task', task_name)
        
        # Update basic fields
        # Extract subject without issue key prefix
        subject = repo_issue.title
        if subject.startswith(f'[{task_doc.issue_key}]'):
            subject = subject[len(f'[{task_doc.issue_key}]'):].strip()
        
        task_doc.subject = subject
        task_doc.description = repo_issue.body or ''
        
        # Update status based on GitHub state
        if repo_issue.state == 'closed' and task_doc.issue_status not in self.get_done_statuses():
            # Find a "Done" status to use
            done_status = frappe.db.get_value('Agile Issue Status', 
                {'status_category': 'Done'}, 'name', order_by='sort_order')
            if done_status:
                task_doc.issue_status = done_status
                task_doc.status = 'Completed'
        
        # Update assignees
        task_doc.set('assigned_to_users', [])
        for assignee_row in repo_issue.get('assignees_table', []):
            user = frappe.db.get_value('User', {'github_username': assignee_row.user}, 'name')
            if user:
                task_doc.append('assigned_to_users', {'user': user})
        
        task_doc.save()
        
        frappe.msgprint(_("Agile issue {0} updated from GitHub").format(task_doc.issue_key))
    
    def parse_github_labels(self, labels):
        """Parse GitHub labels to extract issue type and priority"""
        issue_type = None
        issue_priority = None
        
        for label in labels:
            label = label.strip().lower()
            
            if label.startswith('type:'):
                type_name = label[5:].replace('-', ' ').title()
                # Try to find matching issue type
                existing_type = frappe.db.get_value('Agile Issue Type', 
                    {'issue_type_name': type_name}, 'name')
                if existing_type:
                    issue_type = existing_type
            
            elif label.startswith('priority:'):
                priority_name = label[9:].replace('-', ' ').title()
                # Try to find matching priority
                existing_priority = frappe.db.get_value('Agile Issue Priority',
                    {'priority_name': priority_name}, 'name')
                if existing_priority:
                    issue_priority = existing_priority
        
        return issue_type, issue_priority
    
    def get_done_statuses(self):
        """Get all statuses in Done category"""
        return [status.name for status in frappe.get_all(
            'Agile Issue Status',
            filters={'status_category': 'Done'},
            fields=['name']
        )]
    
    @frappe.whitelist()
    def sync_commits_to_issue(self, task_name):
        """Sync GitHub commits to agile issue"""
        task_doc = frappe.get_doc('Task', task_name)
        
        if not task_doc.github_repo or not task_doc.github_issue_number:
            return {'commits': 0}
        
        try:
            # Get commits that reference this issue
            commits = self.get_commits_for_issue(task_doc)
            
            # Clear existing commit links
            task_doc.set('linked_commits', [])
            
            # Add commit links
            for commit in commits:
                task_doc.append('linked_commits', {
                    'commit_sha': commit['sha'][:7],  # Short SHA
                    'commit_message': commit['message'][:100],  # Truncated message
                    'author': commit['author'],
                    'commit_date': commit['date'],
                    'url': commit['url']
                })
            
            task_doc.save()
            
            return {'commits': len(commits)}
            
        except Exception as e:
            frappe.log_error(f"Error syncing commits: {str(e)}")
            return {'commits': 0, 'error': str(e)}
    
    def get_commits_for_issue(self, task_doc):
        """Get commits that reference the issue"""
        # This would typically use GitHub API to search for commits
        # that mention the issue key in commit messages
        # For now, return empty list as placeholder
        return []
    
    @frappe.whitelist()
    def bulk_sync_project_issues(self, project_name):
        """Bulk sync all GitHub issues for a project"""
        project_doc = frappe.get_doc('Project', project_name)
        
        if not project_doc.get('github_repository'):
            frappe.throw(_("No GitHub repository linked to project"))
        
        repository = project_doc.github_repository
        
        # Get all GitHub issues for this repository
        repo_issues = frappe.get_all('Repository Issue',
            filters={'repository': repository},
            fields=['name', 'issue_number', 'title', 'state']
        )
        
        synced_count = 0
        created_count = 0
        updated_count = 0
        
        for repo_issue in repo_issues:
            try:
                # Check if agile task exists
                existing_task = frappe.db.get_value('Task', {
                    'github_repo': repository,
                    'github_issue_number': repo_issue.issue_number
                }, 'name')
                
                if existing_task:
                    # Update existing
                    repo_issue_doc = frappe.get_doc('Repository Issue', repo_issue.name)
                    self.update_agile_task_from_github(existing_task, repo_issue_doc)
                    updated_count += 1
                else:
                    # Create new
                    repo_issue_doc = frappe.get_doc('Repository Issue', repo_issue.name)
                    self.create_agile_task_from_github(repo_issue_doc, project_doc)
                    created_count += 1
                
                synced_count += 1
                
            except Exception as e:
                frappe.log_error(f"Error syncing issue {repo_issue.issue_number}: {str(e)}")
        
        frappe.msgprint(_(
            "Bulk sync completed: {0} issues processed, {1} created, {2} updated"
        ).format(synced_count, created_count, updated_count))
        
        return {
            'synced': synced_count,
            'created': created_count,
            'updated': updated_count
        }