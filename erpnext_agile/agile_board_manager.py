import frappe
from frappe import _
from frappe.model.document import Document
import json

class AgileBoardManager:
    """Core class for managing Agile Boards (Kanban/Scrum boards)"""
    
    def __init__(self, project=None, sprint=None):
        self.project = project
        self.sprint = sprint
    
    @frappe.whitelist()
    def get_board_data(self, project, sprint=None, view_type='sprint'):
        """Get board data for Kanban/Scrum board visualization"""
        
        # Get project workflow statuses
        workflow_statuses = self.get_workflow_statuses(project)
        
        # Build filters based on view type
        filters = {
            'project': project,
            'is_agile': 1,
            'status': ['!=', 'Cancelled']
        }
        
        if view_type == 'sprint' and sprint:
            filters['current_sprint'] = sprint
        elif view_type == 'backlog':
            filters['current_sprint'] = ['in', ['', None]]
        
        # Get all issues
        issues = frappe.get_all('Task',
            filters=filters,
            fields=[
                'name', 'subject', 'issue_key', 'issue_type', 'issue_priority',
                'issue_status', 'story_points', 'epic', 'assigned_to_users',
                'reporter', 'github_issue_number', 'github_pr_number'
            ]
        )
        
        # Organize issues by status (columns)
        board_columns = {}
        for status in workflow_statuses:
            board_columns[status['name']] = {
                'status': status,
                'issues': [],
                'total_points': 0
            }
        
        # Distribute issues into columns
        for issue in issues:
            status = issue.get('issue_status')
            if status and status in board_columns:
                # Get assignees
                assignees = frappe.get_all('Task Assigned To',
                    filters={'parent': issue['name']},
                    fields=['user'],
                    pluck='user'
                )
                issue['assignees'] = assignees
                
                board_columns[status]['issues'].append(issue)
                board_columns[status]['total_points'] += issue.get('story_points', 0)
        
        return {
            'columns': board_columns,
            'statuses': workflow_statuses,
            'view_type': view_type,
            'project': project,
            'sprint': sprint
        }
    
    def get_workflow_statuses(self, project):
        """Get workflow statuses for the project"""
        project_doc = frappe.get_doc('Project', project)
        workflow_scheme = project_doc.get('workflow_scheme')
        
        if workflow_scheme:
            # Get statuses from workflow scheme
            statuses = frappe.get_all('Agile Issue Status',
                fields=['name', 'status_name', 'status_category', 'color', 'sort_order'],
                order_by='sort_order'
            )
        else:
            # Use default statuses
            statuses = [
                {'name': 'Open', 'status_name': 'To Do', 'status_category': 'To Do', 'color': '#808080', 'sort_order': 1},
                {'name': 'Working', 'status_name': 'In Progress', 'status_category': 'In Progress', 'color': '#0066ff', 'sort_order': 2},
                {'name': 'Completed', 'status_name': 'Done', 'status_category': 'Done', 'color': '#00aa00', 'sort_order': 3}
            ]
        
        return statuses
    
    @frappe.whitelist()
    def move_issue(self, task_name, from_status, to_status, position=None):
        """Move issue from one column to another (drag & drop)"""
        
        task_doc = frappe.get_doc('Task', task_name)
        project_doc = frappe.get_doc('Project', task_doc.project)
        
        # Validate transition using AgileIssueManager
        from erpnext_agile.agile_issue_manager import AgileIssueManager
        manager = AgileIssueManager()
        
        if not manager.validate_transition(project_doc, from_status, to_status):
            frappe.throw(_("Invalid transition from {0} to {1}").format(from_status, to_status))
        
        # Perform transition
        manager.transition_issue(task_name, from_status, to_status, 
            comment="Moved via board")
        
        return {
            'success': True,
            'task': task_name,
            'from_status': from_status,
            'to_status': to_status
        }
    
    @frappe.whitelist()
    def quick_create_issue(self, project, status, issue_data):
        """Quick create issue from board (inline creation)"""
        
        from erpnext_agile.agile_issue_manager import AgileIssueManager
        manager = AgileIssueManager()
        
        # Set issue status
        issue_data['issue_status'] = status
        issue_data['project'] = project
        
        # If board is in sprint view, add to current sprint
        if issue_data.get('sprint'):
            issue_data['sprint'] = issue_data.get('sprint')
        
        # Create issue
        task_doc = manager.create_agile_issue(issue_data)
        
        return {
            'success': True,
            'task': task_doc.name,
            'issue_key': task_doc.issue_key
        }
    
    @frappe.whitelist()
    def filter_board(self, project, sprint=None, filters=None):
        """Filter board by various criteria"""
        
        if not filters:
            filters = {}
        
        board_data = self.get_board_data(project, sprint)
        
        # Apply filters
        if filters.get('assignee'):
            assignee = filters['assignee']
            for status, column in board_data['columns'].items():
                column['issues'] = [
                    issue for issue in column['issues']
                    if assignee in issue.get('assignees', [])
                ]
        
        if filters.get('epic'):
            epic = filters['epic']
            for status, column in board_data['columns'].items():
                column['issues'] = [
                    issue for issue in column['issues']
                    if issue.get('epic') == epic
                ]
        
        if filters.get('issue_type'):
            issue_type = filters['issue_type']
            for status, column in board_data['columns'].items():
                column['issues'] = [
                    issue for issue in column['issues']
                    if issue.get('issue_type') == issue_type
                ]
        
        if filters.get('priority'):
            priority = filters['priority']
            for status, column in board_data['columns'].items():
                column['issues'] = [
                    issue for issue in column['issues']
                    if issue.get('issue_priority') == priority
                ]
        
        return board_data
    
    @frappe.whitelist()
    def get_swimlane_data(self, project, sprint=None, swimlane_by='epic'):
        """Get board data organized by swimlanes"""
        
        board_data = self.get_board_data(project, sprint)
        
        # Organize by swimlanes
        swimlanes = {}
        
        for status, column in board_data['columns'].items():
            for issue in column['issues']:
                swimlane_key = issue.get(swimlane_by) or 'Unassigned'
                
                if swimlane_key not in swimlanes:
                    swimlanes[swimlane_key] = {}
                
                if status not in swimlanes[swimlane_key]:
                    swimlanes[swimlane_key][status] = {
                        'issues': [],
                        'total_points': 0
                    }
                
                swimlanes[swimlane_key][status]['issues'].append(issue)
                swimlanes[swimlane_key][status]['total_points'] += issue.get('story_points', 0)
        
        return {
            'swimlanes': swimlanes,
            'statuses': board_data['statuses'],
            'swimlane_by': swimlane_by
        }
    
    @frappe.whitelist()
    def get_board_metrics(self, project, sprint=None):
        """Get board metrics for visualization"""
        
        board_data = self.get_board_data(project, sprint)
        
        metrics = {
            'total_issues': 0,
            'total_points': 0,
            'by_status_category': {
                'To Do': {'count': 0, 'points': 0},
                'In Progress': {'count': 0, 'points': 0},
                'Done': {'count': 0, 'points': 0}
            },
            'by_type': {},
            'by_priority': {},
            'blocked_issues': 0,
            'unassigned_issues': 0
        }
        
        for status, column in board_data['columns'].items():
            status_category = column['status'].get('status_category', 'To Do')
            
            for issue in column['issues']:
                metrics['total_issues'] += 1
                metrics['total_points'] += issue.get('story_points', 0)
                
                # By status category
                metrics['by_status_category'][status_category]['count'] += 1
                metrics['by_status_category'][status_category]['points'] += issue.get('story_points', 0)
                
                # By type
                issue_type = issue.get('issue_type') or 'Untyped'
                if issue_type not in metrics['by_type']:
                    metrics['by_type'][issue_type] = {'count': 0, 'points': 0}
                metrics['by_type'][issue_type]['count'] += 1
                metrics['by_type'][issue_type]['points'] += issue.get('story_points', 0)
                
                # By priority
                priority = issue.get('issue_priority') or 'Unassigned'
                if priority not in metrics['by_priority']:
                    metrics['by_priority'][priority] = 0
                metrics['by_priority'][priority] += 1
                
                # Unassigned
                if not issue.get('assignees'):
                    metrics['unassigned_issues'] += 1
        
        # Calculate cycle time and throughput if sprint
        if sprint:
            metrics['cycle_time'] = self.calculate_cycle_time(sprint)
            metrics['throughput'] = self.calculate_throughput(sprint)
        
        return metrics
    
    def calculate_cycle_time(self, sprint):
        """Calculate average cycle time for sprint"""
        # Cycle time: time from "In Progress" to "Done"
        
        done_statuses = [status.name for status in frappe.get_all(
            'Agile Issue Status',
            filters={'status_category': 'Done'},
            fields=['name']
        )]
        
        # Get issues completed in sprint
        completed_issues = frappe.get_all('Task',
            filters={
                'current_sprint': sprint,
                'is_agile': 1,
                'issue_status': ['in', done_statuses]
            },
            fields=['name', 'creation', 'modified']
        )
        
        if not completed_issues:
            return {'average_days': 0, 'count': 0}
        
        # Simplified cycle time calculation
        # In real implementation, track status transition timestamps
        total_days = 0
        for issue in completed_issues:
            days = frappe.utils.date_diff(issue['modified'], issue['creation'])
            total_days += days
        
        average_days = total_days / len(completed_issues)
        
        return {
            'average_days': round(average_days, 1),
            'count': len(completed_issues)
        }
    
    def calculate_throughput(self, sprint):
        """Calculate throughput (issues completed per day)"""
        
        sprint_doc = frappe.get_doc('Agile Sprint', sprint)
        
        if sprint_doc.sprint_state != 'Active':
            return {'issues_per_day': 0, 'points_per_day': 0}
        
        days_elapsed = frappe.utils.date_diff(
            frappe.utils.today(),
            sprint_doc.actual_start_date or sprint_doc.start_date
        ) or 1
        
        done_statuses = [status.name for status in frappe.get_all(
            'Agile Issue Status',
            filters={'status_category': 'Done'},
            fields=['name']
        )]
        
        completed = frappe.get_all('Task',
            filters={
                'current_sprint': sprint,
                'is_agile': 1,
                'issue_status': ['in', done_statuses]
            },
            fields=['story_points']
        )
        
        completed_count = len(completed)
        completed_points = sum(issue.get('story_points', 0) for issue in completed)
        
        return {
            'issues_per_day': round(completed_count / days_elapsed, 2),
            'points_per_day': round(completed_points / days_elapsed, 2),
            'days_elapsed': days_elapsed
        }
    
    @frappe.whitelist()
    def bulk_move_issues(self, issue_keys, to_status):
        """Bulk move multiple issues to a status"""
        
        moved_count = 0
        errors = []
        
        for issue_key in issue_keys:
            try:
                task_name = frappe.db.get_value('Task', {'issue_key': issue_key}, 'name')
                if task_name:
                    task_doc = frappe.get_doc('Task', task_name)
                    from_status = task_doc.issue_status
                    
                    self.move_issue(task_name, from_status, to_status)
                    moved_count += 1
            except Exception as e:
                errors.append({
                    'issue_key': issue_key,
                    'error': str(e)
                })
        
        return {
            'success': True,
            'moved': moved_count,
            'errors': errors
        }
    
    @frappe.whitelist()
    def configure_board(self, project, board_config):
        """Configure board settings (columns, swimlanes, etc.)"""
        
        project_doc = frappe.get_doc('Project', project)
        
        # Store board configuration in custom field or settings
        if not frappe.db.exists('Custom Field', {'dt': 'Project', 'fieldname': 'board_config'}):
            self.create_board_config_field()
        
        project_doc.db_set('board_config', json.dumps(board_config))
        
        return {
            'success': True,
            'message': 'Board configuration saved'
        }
    
    def create_board_config_field(self):
        """Create board config custom field"""
        frappe.get_doc({
            'doctype': 'Custom Field',
            'dt': 'Project',
            'fieldname': 'board_config',
            'label': 'Board Configuration',
            'fieldtype': 'Long Text',
            'insert_after': 'enable_agile',
            'hidden': 1
        }).insert()