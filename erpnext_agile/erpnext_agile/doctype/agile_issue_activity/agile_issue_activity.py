import frappe
from frappe.model.document import Document
import json

class AgileIssueActivity(Document):
    def before_insert(self):
        """Set timestamp and user"""
        if not self.timestamp:
            self.timestamp = frappe.utils.now_datetime()
        if not self.user:
            self.user = frappe.session.user
    
    def get_formatted_data(self):
        """Get formatted activity data"""
        try:
            return json.loads(self.data) if self.data else {}
        except:
            return {}
    
    def get_activity_description(self):
        """Get human-readable activity description"""
        data = self.get_formatted_data()
        
        descriptions = {
            'created': 'Issue created',
            'transitioned': f"Status changed from {data.get('from_status')} to {data.get('to_status')}",
            'status_changed': f"Status changed from {data.get('from_status')} to {data.get('to_status')}",
            'assigned': f"Assigned to {', '.join(data.get('assignees', []))}",
            'unassigned': 'Unassigned',
            'commented': 'Added comment',
            'work_logged': f"Logged {data.get('time_spent')} of work",
            'estimation_changed': f"Estimate changed from {data.get('old_value')} to {data.get('new_value')}",
            'sprint_added': f"Added to sprint {data.get('sprint')}",
            'sprint_removed': 'Removed from sprint',
            'epic_linked': f"Linked to epic {data.get('epic')}",
            'epic_unlinked': 'Unlinked from epic',
            'attachment_added': 'Added attachment',
            'watcher_added': 'Added watcher',
            'watcher_removed': 'Removed watcher',
            'github_synced': 'Synced with GitHub'
        }
        
        return descriptions.get(self.activity_type, self.activity_type)