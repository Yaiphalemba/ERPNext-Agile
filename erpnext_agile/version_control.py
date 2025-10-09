# erpnext_agile/version_control.py
"""
Version Control Integration for Agile Issues
Tracks all changes to issues and provides rollback functionality
"""

import frappe
from frappe import _
from frappe.model.document import Document
import json
from datetime import datetime

class IssueVersionControl:
    """Manage version control for agile issues"""
    
    def __init__(self, task_name):
        self.task_name = task_name
    
    def create_version(self, change_description=None):
        """Create a version snapshot of the issue"""
        task_doc = frappe.get_doc('Task', self.task_name)
        
        # Create version record
        version = frappe.get_doc({
            'doctype': 'Agile Issue Version',
            'issue': self.task_name,
            'issue_key': task_doc.issue_key,
            'version_number': self.get_next_version_number(),
            'created_by': frappe.session.user,
            'created_at': frappe.utils.now_datetime(),
            'change_description': change_description or 'Version snapshot',
            'data': json.dumps(self.get_version_data(task_doc))
        })
        version.insert(ignore_permissions=True)
        frappe.db.commit()
        task_doc.append('fix_versions', {'version': version.name})
        task_doc.save()
        frappe.db.commit()
        
        return version
    
    def get_next_version_number(self):
        """Get next version number"""
        last_version = frappe.db.get_value(
            'Agile Issue Version',
            {'issue': self.task_name},
            'version_number',
            order_by='version_number desc'
        )
        return (last_version or 0) + 1
    
    def get_version_data(self, task_doc):
        """Extract versionable data from task"""
        return {
            'subject': task_doc.subject,
            'description': task_doc.description,
            'issue_type': task_doc.issue_type,
            'issue_priority': task_doc.issue_priority,
            'issue_status': task_doc.issue_status,
            'story_points': task_doc.story_points,
            'current_sprint': task_doc.current_sprint,
            'parent_issue': task_doc.parent_issue,
            'original_estimate': task_doc.original_estimate,
            'remaining_estimate': task_doc.remaining_estimate,
            'assigned_to': [{'user': a.user} for a in task_doc.get('assigned_to_users', [])],
            'watchers': [{'user': w.user} for w in task_doc.get('watchers', [])],
            'fix_versions': [{'version': v.version} for v in task_doc.get('fix_versions', [])],
            'modified': str(task_doc.modified)
        }
    
    def get_version_history(self):
        """Get all versions for this issue"""
        return frappe.get_all('Agile Issue Version',
            filters={'issue': self.task_name},
            fields=['name', 'version_number', 'created_by', 'created_at', 'change_description'],
            order_by='version_number desc'
        )
    
    def get_version_diff(self, version1, version2):
        """Compare two versions and return differences"""
        v1_doc = frappe.get_doc('Agile Issue Version', version1)
        v2_doc = frappe.get_doc('Agile Issue Version', version2)
        
        v1_data = json.loads(v1_doc.data)
        v2_data = json.loads(v2_doc.data)
        
        diff = {}
        all_keys = set(v1_data.keys()) | set(v2_data.keys())
        
        for key in all_keys:
            v1_value = v1_data.get(key)
            v2_value = v2_data.get(key)
            
            if v1_value != v2_value:
                diff[key] = {
                    'old': v1_value,
                    'new': v2_value
                }
        
        return diff
    
    def restore_version(self, version_number):
        """Restore issue to a specific version"""
        version_doc = frappe.get_doc('Agile Issue Version', {
            'issue': self.task_name,
            'version_number': version_number
        })
        
        task_doc = frappe.get_doc('Task', self.task_name)
        version_data = json.loads(version_doc.data)
        
        # Restore simple fields
        for field in ['subject', 'description', 'issue_type', 'issue_priority', 
                      'issue_status', 'story_points', 'current_sprint', 
                      'parent_issue', 'original_estimate', 'remaining_estimate']:
            if field in version_data:
                setattr(task_doc, field, version_data[field])
        
        # Restore child tables
        if 'fix_versions' in version_data:
            task_doc.set('fix_versions', [])
            for version in version_data['fix_versions']:
                task_doc.append('fix_versions', version)
        
        if 'watchers' in version_data:
            task_doc.set('watchers', [])
            for watcher in version_data['watchers']:
                task_doc.append('watchers', watcher)
        
        if 'assigned_to' in version_data:
            task_doc.set('assigned_to_users', [])
            for assignee in version_data['assigned_to']:
                task_doc.append('assigned_to_users', assignee)
        task_doc.save()
        frappe.db.commit()
        
        # Log activity
        activity = frappe.get_doc({
            'doctype': 'Agile Issue Activity',
            'issue': self.task_name,
            'activity_type': 'version_restored',
            'user': frappe.session.user,
            'data': json.dumps({
                'version_number': version_number,
                'restored_from': str(version_doc.created_at)
            })
        })
        activity.insert(ignore_permissions=True)
        frappe.db.commit()
        
        return task_doc
    
    @frappe.whitelist()
    def compare_with_current(self, version_number):
        """Compare a version with current state"""
        if not frappe.has_permission("Task", "write", self.task_name):
            frappe.throw(_("No permission to restore this task"), frappe.PermissionError)
        version_doc = frappe.get_doc('Agile Issue Version', {
            'issue': self.task_name,
            'version_number': version_number
        })
        
        task_doc = frappe.get_doc('Task', self.task_name)
        current_data = self.get_version_data(task_doc)
        version_data = json.loads(version_doc.data)
        
        return self._compute_diff(version_data, current_data)
    
    def _compute_diff(self, old_data, new_data):
        """Compute differences between two data snapshots"""
        diff = []
        
        all_keys = set(old_data.keys()) | set(new_data.keys())
        
        for key in all_keys:
            old_value = old_data.get(key)
            new_value = new_data.get(key)
            
            if old_value != new_value:
                diff.append({
                    'field': key,
                    'old_value': self._format_value(old_value),
                    'new_value': self._format_value(new_value),
                    'change_type': self._get_change_type(old_value, new_value)
                })
        
        return diff
    
    def _format_value(self, value):
        """Format value for display"""
        if value is None:
            return 'None'
        if isinstance(value, list):
            return f"[{len(value)} items]"
        if isinstance(value, dict):
            return str(value)
        return str(value)
    
    def _get_change_type(self, old_value, new_value):
        """Determine type of change"""
        if old_value is None and new_value is not None:
            return 'added'
        elif old_value is not None and new_value is None:
            return 'removed'
        else:
            return 'modified'
    
    def get_version_details(self, version_number):
        """Get detailed information about a specific version"""
        version_doc = frappe.get_doc('Agile Issue Version', {
            'issue': self.task_name,
            'version_number': version_number
        })
        
        return {
            'name': version_doc.name,
            'version_number': version_doc.version_number,
            'created_by': version_doc.created_by,
            'created_at': version_doc.created_at,
            'change_description': version_doc.change_description,
            'data': json.loads(version_doc.data),
            'is_backup': version_doc.is_backup,
            'restored_from_version': version_doc.restored_from_version
        }
    
    def delete_version(self, version_number):
        """Delete a specific version (use with caution)"""
        version_name = frappe.db.get_value('Agile Issue Version', {
            'issue': self.task_name,
            'version_number': version_number
        }, 'name')
        
        if version_name:
            frappe.delete_doc('Agile Issue Version', version_name, ignore_permissions=True)
            frappe.db.commit()
            return True
        return False
    
    def cleanup_old_versions(self, keep_latest=10):
        """Clean up old versions, keeping only the latest N versions"""
        versions = frappe.get_all('Agile Issue Version',
            filters={'issue': self.task_name},
            fields=['name', 'version_number'],
            order_by='version_number desc'
        )
        
        if len(versions) > keep_latest:
            versions_to_delete = versions[keep_latest:]
            for version in versions_to_delete:
                frappe.delete_doc('Agile Issue Version', version.name, ignore_permissions=True)
            frappe.db.commit()
            return len(versions_to_delete)
        return 0


# API Methods for Version Control
@frappe.whitelist()
def create_issue_version(task_name, change_description=None):
    """API method to create version"""
    if not frappe.has_permission("Task", "write", task_name):
        frappe.throw(_("No permission to restore this task"), frappe.PermissionError)
    vc = IssueVersionControl(task_name)
    version = vc.create_version(change_description)
    return version.as_dict()

@frappe.whitelist()
def get_version_history(task_name):
    """API method to get version history"""
    if not frappe.has_permission("Task", "write", task_name):
        frappe.throw(_("No permission to restore this task"), frappe.PermissionError)
    vc = IssueVersionControl(task_name)
    return vc.get_version_history()

@frappe.whitelist()
def restore_issue_version(task_name, version_number):
    """API method to restore version"""
    if not frappe.has_permission("Task", "write", task_name):
        frappe.throw(_("No permission to restore this task"), frappe.PermissionError)
    vc = IssueVersionControl(task_name)
    task_doc = vc.restore_version(int(version_number))
    return task_doc.as_dict()

@frappe.whitelist()
def compare_versions(task_name, version1, version2):
    """API method to compare versions"""
    if not frappe.has_permission("Task", "write", task_name):
        frappe.throw(_("No permission to restore this task"), frappe.PermissionError)
    vc = IssueVersionControl(task_name)
    return vc.get_version_diff(version1, version2)

@frappe.whitelist()
def compare_with_current(task_name, version_number):
    """API method to compare version with current state"""
    if not frappe.has_permission("Task", "write", task_name):
        frappe.throw(_("No permission to restore this task"), frappe.PermissionError)
    vc = IssueVersionControl(task_name)
    return vc.compare_with_current(int(version_number))

@frappe.whitelist()
def get_version_details(task_name, version_number):
    """API method to get version details"""
    if not frappe.has_permission("Task", "write", task_name):
        frappe.throw(_("No permission to restore this task"), frappe.PermissionError)
    vc = IssueVersionControl(task_name)
    return vc.get_version_details(int(version_number))

@frappe.whitelist()
def delete_version(task_name, version_number):
    """API method to delete version"""
    if not frappe.has_permission("Task", "write", task_name):
        frappe.throw(_("No permission to restore this task"), frappe.PermissionError)
    vc = IssueVersionControl(task_name)
    return vc.delete_version(int(version_number))

@frappe.whitelist()
def cleanup_old_versions(task_name, keep_latest=10):
    """API method to cleanup old versions"""
    if not frappe.has_permission("Task", "write", task_name):
        frappe.throw(_("No permission to restore this task"), frappe.PermissionError)
    vc = IssueVersionControl(task_name)
    return vc.cleanup_old_versions(int(keep_latest))


# Hook into Task save to auto-create versions on significant changes
def task_on_update_version_control(doc, method):
    """Create version snapshot after significant changes"""
    if not doc.is_agile:
        return
    
    # Skip if this is a new document
    if doc.is_new():
        return
    
    # Check if significant fields changed
    significant_fields = [
        'subject', 'description', 'issue_type', 'issue_priority',
        'issue_status', 'story_points', 'current_sprint'
    ]
    
    changed_fields = []
    for field in significant_fields:
        if doc.has_value_changed(field):
            changed_fields.append(field)
    
    if changed_fields:
        try:
            vc = IssueVersionControl(doc.name)
            description = f"Auto-save: Changed {', '.join(changed_fields)}"
            vc.create_version(description)
        except Exception as e:
            frappe.log_error(f"Error creating version: {str(e)}", "Version Control")


def task_after_insert_version_control(doc, method):
    """Create initial version after task creation"""
    if not doc.is_agile:
        return
    
    try:
        vc = IssueVersionControl(doc.name)
        vc.create_version("Initial version")
    except Exception as e:
        frappe.log_error(f"Error creating initial version: {str(e)}", "Version Control")


# Utility function to get version statistics
@frappe.whitelist()
def get_version_statistics(task_name):
    """Get version control statistics for an issue"""
    vc = IssueVersionControl(task_name)
    history = vc.get_version_history()
    
    stats = {
        'total_versions': len(history),
        'first_version_date': history[-1]['created_at'] if history else None,
        'latest_version_date': history[0]['created_at'] if history else None,
        'unique_contributors': len(set(v['created_by'] for v in history)),
        'versions': history[:10]  # Return latest 10 versions
    }
    
    return stats


# Batch operations
@frappe.whitelist()
def batch_create_versions(task_names, change_description=None):
    """Create versions for multiple issues at once"""
    if not frappe.has_permission("Task", "write", task_name):
        frappe.throw(_("No permission to restore this task"), frappe.PermissionError)
    if isinstance(task_names, str):
        task_names = json.loads(task_names)
    
    results = {
        'success': [],
        'failed': []
    }
    
    for task_name in task_names:
        try:
            vc = IssueVersionControl(task_name)
            version = vc.create_version(change_description)
            results['success'].append({
                'task': task_name,
                'version': version.name
            })
        except Exception as e:
            results['failed'].append({
                'task': task_name,
                'error': str(e)
            })
    
    return results


@frappe.whitelist()
def export_version_history(task_name, format='json'):
    """Export version history in different formats"""
    if not frappe.has_permission("Task", "write", task_name):
        frappe.throw(_("No permission to restore this task"), frappe.PermissionError)
    vc = IssueVersionControl(task_name)
    history = vc.get_version_history()
    
    if format == 'json':
        return json.dumps(history, indent=2, default=str)
    elif format == 'csv':
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=['version_number', 'created_by', 'created_at', 'change_description'])
        writer.writeheader()
        writer.writerows(history)
        return output.getvalue()
    else:
        return history


# Scheduled task to cleanup old versions
def cleanup_all_old_versions(days_to_keep=90):
    """Scheduled task to cleanup old versions across all issues"""
    cutoff_date = frappe.utils.add_days(frappe.utils.today(), -days_to_keep)
    
    old_versions = frappe.get_all('Agile Issue Version',
        filters={'created_at': ['<', cutoff_date]},
        fields=['name', 'issue']
    )
    
    deleted_count = 0
    for version in old_versions:
        try:
            # Keep at least 5 versions per issue
            issue_versions = frappe.db.count('Agile Issue Version', {'issue': version['issue']})
            if issue_versions > 5:
                frappe.delete_doc('Agile Issue Version', version['name'], ignore_permissions=True)
                deleted_count += 1
        except Exception as e:
            frappe.log_error(f"Error deleting version {version['name']}: {str(e)}")
    
    frappe.db.commit()
    return deleted_count

@frappe.whitelist()
def get_allocated_to(task_name):
    todos = frappe.get_all("ToDo",
        filters={
            "reference_type": "Task",
            "reference_name": task_name
        },
        fields=["allocated_to"]
    )
    return [todo.allocated_to for todo in todos]