import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt
import json

class AgileBacklogManager:
    """Core class for managing Product Backlog with Jira-like functionality"""
    
    def __init__(self, project=None):
        self.project = project
    
    @frappe.whitelist()
    def get_backlog(self, project, filters=None):
        """Get backlog items (issues not in any sprint)"""
        
        if not filters:
            filters = {}
        
        # Build query filters
        query_filters = {
            'project': project,
            'is_agile': 1
        }
        
        # Exclude items in sprints
        backlog_items = frappe.db.sql("""
            SELECT 
                name, subject, issue_key, issue_type, issue_priority,
                issue_status, story_points, parent_issue,
                reporter, creation, modified
            FROM `tabTask`
            WHERE project = %s 
                AND is_agile = 1
                AND (current_sprint IS NULL OR current_sprint = '')
                AND status != 'Cancelled'
            ORDER BY 
                CASE 
                    WHEN issue_priority = 'Critical' THEN 1
                    WHEN issue_priority = 'High' THEN 2
                    WHEN issue_priority = 'Medium' THEN 3
                    WHEN issue_priority = 'Low' THEN 4
                    ELSE 5
                END,
                creation DESC
        """, (project,), as_dict=True)
        
        return backlog_items
    
    @frappe.whitelist()
    def rank_backlog_item(self, task_name, new_rank):
        """Change priority/rank of backlog item"""
        task_doc = frappe.get_doc('Task', task_name)
        
        # Use a custom field for backlog rank
        if not frappe.db.exists('Custom Field', {'dt': 'Task', 'fieldname': 'backlog_rank'}):
            self.create_backlog_rank_field()
        
        task_doc.db_set('backlog_rank', new_rank)
        
        return {'success': True, 'new_rank': new_rank}
    
    def create_backlog_rank_field(self):
        """Create backlog rank custom field if it doesn't exist"""
        frappe.get_doc({
            'doctype': 'Custom Field',
            'dt': 'Task',
            'fieldname': 'backlog_rank',
            'label': 'Backlog Rank',
            'fieldtype': 'Int',
            'insert_after': 'is_agile',
            'hidden': 1
        }).insert()
    
    @frappe.whitelist()
    def estimate_backlog_item(self, task_name, story_points, estimation_method='planning_poker'):
        """Estimate story points for backlog item"""
        task_doc = frappe.get_doc('Task', task_name)
        
        old_points = task_doc.story_points or 0
        task_doc.story_points = story_points
        task_doc.save()
        
        # Log estimation activity
        self.log_estimation_activity(task_doc, old_points, story_points, estimation_method)
        
        return {
            'success': True,
            'old_points': old_points,
            'new_points': story_points
        }
    
    def log_estimation_activity(self, task_doc, old_points, new_points, method):
        """Log estimation activity"""
        try:
            activity_doc = frappe.get_doc({
                'doctype': 'Agile Issue Activity',
                'issue': task_doc.name,
                'activity_type': 'estimation_changed',
                'user': frappe.session.user,
                'data': json.dumps({
                    'old_points': old_points,
                    'new_points': new_points,
                    'method': method
                })
            })
            activity_doc.insert()
        except:
            pass  # Fail silently if activity logging fails
    
    @frappe.whitelist()
    def refine_backlog(self, project, refinement_data):
        """Backlog refinement session (Jira-style grooming)"""
        
        # Validate project
        if not frappe.db.get_value('Project', project, 'enable_agile'):
            frappe.throw(_("Project is not agile-enabled"))
        
        updated_items = []
        
        for item_data in refinement_data.get('items', []):
            task_name = item_data.get('task_name')
            
            if not task_name:
                continue
            
            task_doc = frappe.get_doc('Task', task_name)
            
            # Update story points if provided
            if 'story_points' in item_data:
                task_doc.story_points = item_data['story_points']
            
            # Update priority if provided
            if 'issue_priority' in item_data:
                task_doc.issue_priority = item_data['issue_priority']
            
            # Update description if provided
            if 'description' in item_data:
                task_doc.description = item_data['description']
            
            # Add acceptance criteria if provided
            if 'acceptance_criteria' in item_data:
                if task_doc.description:
                    task_doc.description += f"\n\n## Acceptance Criteria\n{item_data['acceptance_criteria']}"
                else:
                    task_doc.description = f"## Acceptance Criteria\n{item_data['acceptance_criteria']}"
            
            task_doc.save()
            updated_items.append(task_name)
        
        # Create refinement session record
        self.create_refinement_session(project, updated_items, refinement_data)
        
        return {
            'success': True,
            'updated_items': len(updated_items)
        }
    
    def create_refinement_session(self, project, updated_items, refinement_data):
        """Create backlog refinement session record"""
        try:
            session_doc = frappe.get_doc({
                'doctype': 'Agile Refinement Session',
                'project': project,
                'session_date': frappe.utils.today(),
                'facilitator': frappe.session.user,
                'items_refined': len(updated_items),
                'notes': refinement_data.get('notes', ''),
                'duration': refinement_data.get('duration', 0)
            })
            session_doc.insert()
        except:
            pass  # Fail silently if session creation fails
    
    @frappe.whitelist()
    def split_story(self, task_name, split_data):
        """Split a user story into multiple stories"""
        parent_task = frappe.get_doc('Task', task_name)
        
        if not parent_task.is_agile:
            frappe.throw(_("Task is not an agile issue"))
        
        # Create sub-tasks
        sub_tasks = []
        total_points = flt(parent_task.story_points or 0)
        points_distributed = 0
        
        for i, split in enumerate(split_data.get('splits', [])):
            # Create new issue using AgileIssueManager
            from erpnext_agile.agile_issue_manager import AgileIssueManager
            manager = AgileIssueManager()
            
            issue_data = {
                'project': parent_task.project,
                'summary': split.get('summary'),
                'description': split.get('description', ''),
                'issue_type': parent_task.issue_type,
                'issue_priority': parent_task.issue_priority,
                'reporter': frappe.session.user,
                'story_points': split.get('story_points', 0),
                'parent_issue': parent_task.name
            }
            
            sub_task = manager.create_agile_issue(issue_data)
            sub_tasks.append(sub_task.name)
            points_distributed += flt(split.get('story_points', 0))
        
        # Update parent task
        parent_task.story_points = 0  # Points now distributed to sub-tasks
        
        # Add note about split
        if parent_task.description:
            parent_task.description += f"\n\n---\n**Split into sub-tasks:** {', '.join([st for st in sub_tasks])}"
        
        parent_task.save()
        
        return {
            'success': True,
            'parent': parent_task.name,
            'sub_tasks': sub_tasks,
            'total_points_distributed': points_distributed
        }
    
    @frappe.whitelist()
    def get_backlog_metrics(self, project):
        """Get backlog health metrics"""
        
        backlog_items = self.get_backlog(project)
        
        metrics = {
            'total_items': len(backlog_items),
            'total_points': sum(flt(item.get('story_points', 0)) for item in backlog_items),
            'estimated_items': sum(1 for item in backlog_items if flt(item.get('story_points', 0)) > 0),
            'unestimated_items': sum(1 for item in backlog_items if not flt(item.get('story_points', 0)) or flt(item.get('story_points', 0)) == 0),
            'by_priority': {},
            'by_type': {},
            'ready_for_sprint': 0
        }
        
        # Calculate distributions
        for item in backlog_items:
            # By priority
            priority = item.get('issue_priority') or 'Unassigned'
            metrics['by_priority'][priority] = metrics['by_priority'].get(priority, 0) + 1
            
            # By type
            issue_type = item.get('issue_type') or 'Untyped'
            metrics['by_type'][issue_type] = metrics['by_type'].get(issue_type, 0) + 1
            
            # Ready for sprint (has story points and acceptance criteria)
            if item.get('story_points', 0) > 0 and item.get('description'):
                metrics['ready_for_sprint'] += 1
        
        # Calculate estimation percentage
        metrics['estimation_percentage'] = (
            (metrics['estimated_items'] / metrics['total_items'] * 100)
            if metrics['total_items'] > 0 else 0
        )
        
        # Calculate readiness percentage
        metrics['readiness_percentage'] = (
            (metrics['ready_for_sprint'] / metrics['total_items'] * 100)
            if metrics['total_items'] > 0 else 0
        )
        
        return metrics
    
    @frappe.whitelist()
    def prioritize_backlog(self, project, prioritization_method='value_effort'):
        """Auto-prioritize backlog based on various methods"""
        
        backlog_items = self.get_backlog(project)
        
        if prioritization_method == 'value_effort':
            # Sort by value (priority) to effort (story points) ratio
            scored_items = []
            
            priority_scores = {
                'Critical': 5,
                'High': 4,
                'Medium': 3,
                'Low': 2
            }
            
            for item in backlog_items:
                priority = item.get('issue_priority') or 'Low'
                value_score = priority_scores.get(priority, 1)
                effort = max(flt(item.get('story_points', 5)), 1)  # Avoid division by zero
                
                score = value_score / effort
                scored_items.append({
                    'task_name': item['name'],
                    'issue_key': item['issue_key'],
                    'score': score,
                    'value': value_score,
                    'effort': effort
                })
            
            # Sort by score descending
            scored_items.sort(key=lambda x: x['score'], reverse=True)
            
            # Update ranks
            for rank, item in enumerate(scored_items, start=1):
                self.rank_backlog_item(item['task_name'], rank)
            
            return {
                'success': True,
                'method': prioritization_method,
                'items_prioritized': len(scored_items),
                'top_items': scored_items[:10]  # Return top 10
            }
        
        return {'success': False, 'message': 'Unknown prioritization method'}
    
    @frappe.whitelist()
    def bulk_estimate_backlog(self, project, estimation_template):
        """Bulk estimate backlog items using templates"""
        
        backlog_items = self.get_backlog(project)
        
        # Filter unestimated items
        unestimated = [item for item in backlog_items if not item.get('story_points')]
        
        estimated_count = 0
        
        # Apply estimation based on issue type
        type_estimates = estimation_template.get('by_type', {})
        
        for item in unestimated:
            issue_type = item.get('issue_type')
            
            if issue_type and issue_type in type_estimates:
                default_points = type_estimates[issue_type]
                frappe.db.set_value('Task', item['name'], 'story_points', default_points)
                estimated_count += 1
        
        return {
            'success': True,
            'estimated': estimated_count,
            'remaining_unestimated': len(unestimated) - estimated_count
        }