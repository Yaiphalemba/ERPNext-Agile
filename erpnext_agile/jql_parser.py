# Updated jql_parser.py
import frappe
import re

class AgileQueryLanguage:
    """Jira Query Language (JQL) equivalent for agile tasks"""
    
    def __init__(self):
        self.operators = {
            '=': '=',
            '!=': '!=', 
            'IN': 'IN',
            'NOT IN': 'NOT IN',
            '~': 'LIKE',
            '!~': 'NOT LIKE'
        }
        
        self.field_mapping = {
            'project': 'project',
            'assignee': 'assignee',
            'reporter': 'reporter', 
            'status': 'status',
            'type': 'issue_type',
            'priority': 'priority',
            'key': 'issue_key',
            'summary': 'subject',
            'sprint': 'current_sprint',
            'epic': 'epic'
        }
    
    def parse_jql(self, jql_query):
        """Parse JQL-like query into Frappe filters"""
        # Simple JQL parser - can be enhanced
        # Example: "project = PROJ AND assignee = currentUser() AND status != Closed"
        
        filters = {"project.enable_agile": 1}
        
        # Split by AND/OR (simplified - only AND for now)
        conditions = jql_query.split(' AND ')
        
        for condition in conditions:
            condition = condition.strip()
            field, operator, value = self.parse_condition(condition)
            
            if field in self.field_mapping:
                mapped_field = self.field_mapping[field]
                filters[mapped_field] = self.format_filter_value(operator, value)
        
        return filters
    
    def parse_condition(self, condition):
        """Parse individual condition"""
        # Match patterns like: field operator value
        match = re.match(r'(\w+)\s*(=|!=|IN|NOT IN|~|!~)\s*(.+)', condition)
        
        if match:
            field, operator, value = match.groups()
            return field.lower(), operator, value.strip().strip('"\'')
        
        return None, None, None
    
    def format_filter_value(self, operator, value):
        """Format value for Frappe filters"""
        if operator == '=':
            return value
        elif operator == '!=':
            return ['!=', value]
        elif operator == 'IN':
            return ['IN', value.split(',')]
        elif operator == 'NOT IN':
            return ['NOT IN', value.split(',')]
        elif operator == '~':
            return ['LIKE', f'%{value}%']
        elif operator == '!~':
            return ['NOT LIKE', f'%{value}%']
        
        return value

@frappe.whitelist()
def search_tasks_jql(jql_query, project=None):
    """Search tasks using JQL-like syntax"""
    parser = AgileQueryLanguage()
    filters = parser.parse_jql(jql_query)
    
    if project:
        filters['project'] = project
    
    tasks = frappe.get_all("Task",
        filters=filters,
        fields=["name", "issue_key", "subject", "status", "assignee", "priority", "issue_type"],
        limit=50
    )
    
    return tasks