import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import today, add_days, get_datetime, now_datetime, date_diff, flt
import json

class AgileSprintManager:
    """Core class for managing Agile Sprints with Jira-like functionality"""
    
    def __init__(self, project=None):
        self.project = project
    
    @frappe.whitelist()
    def create_sprint(self, sprint_data):
        """Create a new sprint with validation"""
        
        # Validate project is agile-enabled
        if not self.is_agile_project(sprint_data.get('project')):
            frappe.throw(_("Project {0} is not agile-enabled").format(sprint_data.get('project')))
        
        # Validate no overlapping active sprints
        self.validate_sprint_dates(sprint_data)
        
        sprint_doc = frappe.get_doc({
            'doctype': 'Agile Sprint',
            'sprint_name': sprint_data.get('sprint_name'),
            'project': sprint_data.get('project'),
            'sprint_goal': sprint_data.get('sprint_goal', ''),
            'start_date': sprint_data.get('start_date'),
            'end_date': sprint_data.get('end_date'),
            'sprint_state': 'Future'
        })
        
        sprint_doc.insert()
        return sprint_doc
    
    def validate_sprint_dates(self, sprint_data):
        """Validate sprint dates don't overlap with active sprints"""
        overlapping = frappe.db.sql("""
            SELECT name FROM `tabAgile Sprint`
            WHERE project = %s 
            AND sprint_state = 'Active'
            AND (
                (%s BETWEEN start_date AND end_date) OR
                (%s BETWEEN start_date AND end_date) OR
                (start_date BETWEEN %s AND %s)
            )
        """, (
            sprint_data.get('project'),
            sprint_data.get('start_date'),
            sprint_data.get('end_date'),
            sprint_data.get('start_date'),
            sprint_data.get('end_date')
        ))
        
        if overlapping:
            frappe.throw(_("Sprint dates overlap with active sprint: {0}").format(overlapping[0][0]))
    
    @frappe.whitelist()
    def start_sprint(self, sprint_name):
        """Start a sprint (Jira-style sprint activation)"""
        sprint_doc = frappe.get_doc('Agile Sprint', sprint_name)
        
        if sprint_doc.sprint_state != 'Future':
            frappe.throw(_("Only future sprints can be started"))
        
        # Close any other active sprints in this project
        self.complete_active_sprints(sprint_doc.project)
        
        # Start the sprint
        sprint_doc.sprint_state = 'Active'
        sprint_doc.actual_start_date = today()
        
        # Calculate initial metrics
        self.calculate_sprint_metrics(sprint_doc)
        
        sprint_doc.save()
        
        # Create sprint burndown baseline
        self.create_burndown_entry(sprint_doc)
        
        # Send notifications
        self.send_sprint_notifications(sprint_doc, 'started')
        
        frappe.msgprint(_("Sprint '{0}' started successfully!").format(sprint_doc.sprint_name))
        return sprint_doc
    
    def complete_active_sprints(self, project):
        """Complete any active sprints in the project"""
        active_sprints = frappe.get_all('Agile Sprint', 
            filters={'project': project, 'sprint_state': 'Active'},
            fields=['name']
        )
        
        for sprint in active_sprints:
            self.complete_sprint(sprint.name, auto_complete=True)
    
    @frappe.whitelist()
    def complete_sprint(self, sprint_name, auto_complete=False):
        """Complete a sprint with issue handling"""
        sprint_doc = frappe.get_doc('Agile Sprint', sprint_name)
        
        if sprint_doc.sprint_state != 'Active':
            frappe.throw(_("Only active sprints can be completed"))
        
        # Complete the sprint
        sprint_doc.sprint_state = 'Completed'
        sprint_doc.actual_end_date = today()
        
        # Calculate final metrics
        self.calculate_sprint_metrics(sprint_doc)
        
        # Handle incomplete issues
        incomplete_issues = self.get_incomplete_sprint_issues(sprint_name)
        moved_count = 0
        
        for issue in incomplete_issues:
            # Move to backlog (remove from sprint)
            frappe.db.set_value('Task', issue.name, 'current_sprint', '')
            moved_count += 1
        
        sprint_doc.save()
        
        # Create final burndown entry
        self.update_burndown_entry(sprint_doc, is_final=True)
        
        # Send notifications
        self.send_sprint_notifications(sprint_doc, 'completed', {
            'incomplete_issues': moved_count
        })
        
        if not auto_complete:
            frappe.msgprint(_(
                "Sprint completed! {0} incomplete issues moved to backlog"
            ).format(moved_count))
        
        return sprint_doc
    
    def get_incomplete_sprint_issues(self, sprint_name):
        """Get incomplete issues in sprint"""
        return frappe.get_all('Task',
            filters={
                'current_sprint': sprint_name,
                'is_agile': 1,
                'issue_status': ['not in', self.get_done_statuses()]
            },
            fields=['name', 'subject', 'issue_key']
        )
    
    def get_done_statuses(self):
        """Get all statuses in Done category"""
        return [status.name for status in frappe.get_all(
            'Agile Issue Status',
            filters={'status_category': 'Done'},
            fields=['name']
        )]
    
    def calculate_sprint_metrics(self, sprint_doc):
        """Calculate sprint metrics (points, velocity, progress)"""
        sprint_issues = frappe.get_all('Task',
            filters={'current_sprint': sprint_doc.name, 'is_agile': 1},
            fields=['story_points', 'issue_status']
        )
        
        total_points = sum(int(issue.get('story_points', 0)) for issue in sprint_issues)
        
        done_statuses = self.get_done_statuses()
        completed_points = sum(
            float(issue.get('story_points', 0)) 
            for issue in sprint_issues 
            if issue.get('issue_status') in done_statuses
        )
        
        progress_percentage = (completed_points / total_points * 100) if total_points > 0 else 0
        
        # Calculate velocity (for active/completed sprints)
        velocity = 0
        if sprint_doc.sprint_state in ['Active', 'Completed']:
            sprint_days = date_diff(sprint_doc.end_date, sprint_doc.start_date) or 1
            velocity = completed_points / sprint_days if sprint_days > 0 else 0
        
        # Update sprint metrics
        sprint_doc.total_points = total_points
        sprint_doc.completed_points = completed_points
        sprint_doc.progress_percentage = progress_percentage
        sprint_doc.velocity = velocity
        
        return {
            'total_points': total_points,
            'completed_points': completed_points,
            'progress_percentage': progress_percentage,
            'velocity': velocity
        }
    
    @frappe.whitelist()
    def add_issues_to_sprint(self, sprint_name, issue_keys):
        """Add issues to sprint (sprint planning)"""
        sprint_doc = frappe.get_doc('Agile Sprint', sprint_name)
        
        if sprint_doc.sprint_state not in ['Future', 'Active']:
            frappe.throw(_("Can only add issues to future or active sprints"))
        
        added_count = 0
        
        for issue_key in issue_keys:
            # Find task by issue key
            task = frappe.db.get_value('Task', 
                {'issue_key': issue_key, 'is_agile': 1}, 
                ['name', 'current_sprint'])
            
            if task:
                task_name = task[0]
                current_sprint = task[1]
                
                if current_sprint and current_sprint != sprint_name:
                    frappe.throw(_(
                        "Issue {0} is already in sprint {1}"
                    ).format(issue_key, current_sprint))
                
                if not current_sprint:
                    frappe.db.set_value('Task', task_name, 'current_sprint', sprint_name)
                    added_count += 1
        
        # Recalculate sprint metrics
        self.calculate_sprint_metrics(sprint_doc)
        sprint_doc.save()
        
        return {'added': added_count}
    
    @frappe.whitelist()
    def remove_issues_from_sprint(self, sprint_name, issue_keys):
        """Remove issues from sprint"""
        sprint_doc = frappe.get_doc('Agile Sprint', sprint_name)
        
        if sprint_doc.sprint_state == 'Completed':
            frappe.throw(_("Cannot modify completed sprints"))
        
        removed_count = 0
        
        for issue_key in issue_keys:
            task_name = frappe.db.get_value('Task', 
                {'issue_key': issue_key, 'current_sprint': sprint_name}, 
                'name')
            
            if task_name:
                frappe.db.set_value('Task', task_name, 'current_sprint', '')
                removed_count += 1
        
        # Recalculate sprint metrics
        self.calculate_sprint_metrics(sprint_doc)
        sprint_doc.save()
        
        return {'removed': removed_count}
    
    def create_burndown_entry(self, sprint_doc, is_final=False):
        """Create burndown chart entry"""
        if not frappe.db.get_value('Project', sprint_doc.project, 'burndown_enabled'):
            return
        
        metrics = self.calculate_sprint_metrics(sprint_doc)
        
        # Calculate remaining work
        remaining_points = metrics['total_points'] - metrics['completed_points']
        
        # Calculate ideal burndown
        if sprint_doc.sprint_state == 'Active':
            total_days = date_diff(sprint_doc.end_date, sprint_doc.start_date) or 1
            days_passed = date_diff(today(), sprint_doc.actual_start_date or sprint_doc.start_date)
            days_remaining = total_days - days_passed
            ideal_remaining = (days_remaining / total_days) * metrics['total_points'] if total_days > 0 else 0
        else:
            ideal_remaining = 0 if is_final else metrics['total_points']
        
        burndown_doc = frappe.get_doc({
            'doctype': 'Agile Sprint Burndown',
            'sprint': sprint_doc.name,
            'date': today(),
            'remaining_points': remaining_points,
            'ideal_remaining': max(0, ideal_remaining),
            'completed_points': metrics['completed_points'],
            'added_points': 0  # Track scope changes
        })
        
        burndown_doc.insert()
        
    def update_burndown_entry(self, sprint_doc, is_final=False):
        """Update today's burndown chart entry or create if missing"""
        if not frappe.db.get_value('Project', sprint_doc.project, 'burndown_enabled'):
            return

        # Recalculate metrics
        metrics = self.calculate_sprint_metrics(sprint_doc)

        # Compute remaining and ideal work
        remaining_points = metrics['total_points'] - metrics['completed_points']

        if sprint_doc.sprint_state == 'Active':
            total_days = date_diff(sprint_doc.end_date, sprint_doc.start_date) or 1
            days_passed = date_diff(today(), sprint_doc.actual_start_date or sprint_doc.start_date)
            days_remaining = total_days - days_passed
            ideal_remaining = (days_remaining / total_days) * metrics['total_points'] if total_days > 0 else 0
        else:
            ideal_remaining = 0 if is_final else metrics['total_points']

        # Check if today's burndown entry already exists
        existing_entry = frappe.db.get_value(
            'Agile Sprint Burndown',
            {
                'sprint': sprint_doc.name,
                'date': today()
            },
            'name'  # Get the actual document name
        )

        if existing_entry:
            # Update existing entry
            burndown_doc = frappe.get_doc('Agile Sprint Burndown', existing_entry)
            burndown_doc.remaining_points = remaining_points
            burndown_doc.ideal_remaining = max(0, ideal_remaining)
            burndown_doc.completed_points = metrics['completed_points']
            burndown_doc.save()
            frappe.logger().info(f"Updated burndown entry for sprint {sprint_doc.name} on {today()}")
        else:
            # Create a new one if missing (safety fallback)
            burndown_doc = frappe.get_doc({
                'doctype': 'Agile Sprint Burndown',
                'sprint': sprint_doc.name,
                'date': today(),
                'remaining_points': remaining_points,
                'ideal_remaining': max(0, ideal_remaining),
                'completed_points': metrics['completed_points'],
                'added_points': 0
            })
            burndown_doc.insert()
            frappe.logger().info(f"Created new burndown entry for sprint {sprint_doc.name} on {today()}")
        
    @frappe.whitelist()
    def get_sprint_burndown(self, sprint_name):
        """Get burndown data for charts"""
        burndown_data = frappe.get_all('Agile Sprint Burndown',
            filters={'sprint': sprint_name},
            fields=['date', 'remaining_points', 'ideal_remaining', 'completed_points'],
            order_by='date'
        )
        
        return burndown_data
    
    @frappe.whitelist()
    def get_sprint_report(self, sprint_name):
        """Generate comprehensive sprint report"""
        sprint_doc = frappe.get_doc('Agile Sprint', sprint_name)
        
        # Get all sprint issues
        issues = frappe.get_all('Task',
            filters={'current_sprint': sprint_name, 'is_agile': 1},
            fields=[
                'name', 'subject', 'issue_key', 'issue_type', 'issue_priority',
                'issue_status', 'story_points', 'reporter'
            ]
        )
        
        # Categorize issues
        issue_stats = {
            'total': len(issues),
            'completed': 0,
            'in_progress': 0,
            'todo': 0,
            'by_type': {},
            'by_priority': {},
            'by_assignee': {}
        }
        
        done_statuses = self.get_done_statuses()
        in_progress_statuses = [status.name for status in frappe.get_all(
            'Agile Issue Status',
            filters={'status_category': 'In Progress'},
            fields=['name']
        )]
        
        for issue in issues:
            status = issue.get('issue_status')
            
            if status in done_statuses:
                issue_stats['completed'] += 1
            elif status in in_progress_statuses:
                issue_stats['in_progress'] += 1
            else:
                issue_stats['todo'] += 1
            
            # Count by type
            issue_type = issue.get('issue_type') or 'Untyped'
            issue_stats['by_type'][issue_type] = issue_stats['by_type'].get(issue_type, 0) + 1
            
            # Count by priority
            priority = issue.get('issue_priority') or 'Unassigned'
            issue_stats['by_priority'][priority] = issue_stats['by_priority'].get(priority, 0) + 1
        
        # Get burndown data
        burndown_data = self.get_sprint_burndown(sprint_name)
        
        # Calculate team velocity
        team_velocity = self.calculate_team_velocity(sprint_doc.project)
        
        report = {
            'sprint': sprint_doc,
            'metrics': self.calculate_sprint_metrics(sprint_doc),
            'issues': issues,
            'issue_stats': issue_stats,
            'burndown_data': burndown_data,
            'team_velocity': team_velocity
        }
        
        return report
    
    def calculate_team_velocity(self, project):
        """Calculate team velocity based on last N completed sprints"""
        completed_sprints = frappe.get_all('Agile Sprint',
            filters={'project': project, 'sprint_state': 'Completed'},
            fields=['name', 'completed_points', 'start_date', 'end_date'],
            order_by='end_date desc',
            limit=5  # Last 5 sprints
        )
        
        if not completed_sprints:
            return {'average': 0, 'trend': 'stable', 'sprints_analyzed': 0}
        
        velocities = [sprint.get('completed_points', 0) for sprint in completed_sprints]
        average_velocity = sum(velocities) / len(velocities) if velocities else 0
        
        # Determine trend
        trend = 'stable'
        if len(velocities) >= 2:
            recent_avg = sum(velocities[:2]) / 2
            older_avg = sum(velocities[2:]) / len(velocities[2:]) if len(velocities) > 2 else recent_avg
            
            if recent_avg > older_avg * 1.1:
                trend = 'improving'
            elif recent_avg < older_avg * 0.9:
                trend = 'declining'
        
        return {
            'average': round(average_velocity, 1),
            'trend': trend,
            'sprints_analyzed': len(completed_sprints),
            'last_sprint_velocity': velocities[0] if velocities else 0
        }
    
    def send_sprint_notifications(self, sprint_doc, event_type, data=None):
        """Send sprint notifications to team members"""
        if not frappe.db.get_value('Project', sprint_doc.project, 'enable_email_notifications'):
            return
        
        # Get project team members
        team_members = frappe.get_all('Project User',
            filters={'parent': sprint_doc.project},
            fields=['user'],
            pluck='user'
        )
        
        if team_members:
            self._send_sprint_email_notification(sprint_doc, event_type, team_members, data)
    
    def _send_sprint_email_notification(self, sprint_doc, event_type, recipients, data):
        """Send sprint email notification"""
        try:
            subject_map = {
                'started': f"Sprint Started: {sprint_doc.sprint_name}",
                'completed': f"Sprint Completed: {sprint_doc.sprint_name}",
                'updated': f"Sprint Updated: {sprint_doc.sprint_name}"
            }
            
            subject = subject_map.get(event_type, f"Sprint Notification: {sprint_doc.sprint_name}")
            
            frappe.sendmail(
                recipients=recipients,
                subject=subject,
                template="agile_sprint_notification",
                args={
                    'sprint': sprint_doc,
                    'event_type': event_type,
                    'data': data,
                    'site_url': frappe.utils.get_url()
                }
            )
        except Exception as e:
            frappe.log_error(f"Failed to send sprint notification: {str(e)}")
    
    def is_agile_project(self, project_name):
        """Check if project is agile-enabled"""
        return frappe.db.get_value('Project', project_name, 'enable_agile') == 1