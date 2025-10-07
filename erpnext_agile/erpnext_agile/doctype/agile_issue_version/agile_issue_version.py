import frappe
from frappe.model.document import Document
import json

class AgileIssueVersion(Document):
    def validate(self):
        """Validate version"""
        if not self.created_by:
            self.created_by = frappe.session.user
        
        if not self.created_at:
            self.created_at = frappe.utils.now_datetime()
        
        # Get issue key if not set
        if not self.issue_key and self.issue:
            self.issue_key = frappe.db.get_value('Task', self.issue, 'issue_key')
    
    def get_version_data_dict(self):
        """Get version data as dictionary"""
        try:
            return json.loads(self.data) if self.data else {}
        except:
            return {}
    
    def get_changes_summary(self):
        """Get summary of changes in this version"""
        data = self.get_version_data_dict()
        
        summary = []
        if data.get('subject'):
            summary.append(f"Subject: {data['subject'][:50]}...")
        if data.get('issue_status'):
            summary.append(f"Status: {data['issue_status']}")
        if data.get('story_points'):
            summary.append(f"Story Points: {data['story_points']}")
        
        return ', '.join(summary) if summary else 'No changes recorded'