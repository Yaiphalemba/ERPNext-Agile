import frappe
from frappe.model.document import Document

class AgileWorkflowScheme(Document):
    """Jira-style workflow schemes"""
    
    def validate(self):
        """Validate workflow configuration"""
        # Validate transitions
        for transition in self.transitions:
            if transition.from_status == transition.to_status:
                frappe.throw("From Status and To Status cannot be the same")
    
    def get_transitions(self, from_status):
        """Get available transitions from a status"""
        transitions = []
        for t in self.transitions:
            if t.from_status == from_status:
                transitions.append({
                    'to_status': t.to_status,
                    'transition_name': t.transition_name,
                    'required_permission': t.required_permission
                })
        return transitions
    
    def validate_transition(self, from_status, to_status, user=None):
        """Validate if transition is allowed"""
        transitions = self.get_transitions(from_status)
        allowed_statuses = [t['to_status'] for t in transitions]
        
        if to_status not in allowed_statuses:
            return False
        
        # Check permissions if user provided
        if user:
            for t in transitions:
                if t['to_status'] == to_status and t.get('required_permission'):
                    # Check if user has required permission
                    return self.check_user_permission(user, t['required_permission'])
        
        return True
    
    def check_user_permission(self, user, required_permission):
        """Check if user has required permission"""
        if not required_permission or required_permission == 'All':
            return True
        
        # Check if user has the required role
        user_roles = frappe.get_roles(user)
        return required_permission in user_roles