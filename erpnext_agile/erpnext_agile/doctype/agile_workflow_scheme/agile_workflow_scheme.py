import frappe
from frappe.model.document import Document

class AgileWorkflowScheme(Document):
    """Jira-style workflow schemes"""
    
    def get_transitions(self, from_status):
        """Get available transitions from status"""
        return frappe.get_all("Agile Workflow Transition", {
            "workflow_scheme": self.name,
            "from_status": from_status
        }, ["to_status", "transition_name", "required_permission"])
    
    def validate_transition(self, from_status, to_status, user=None):
        """Validate if transition is allowed"""
        transitions = self.get_transitions(from_status)
        allowed_statuses = [t.to_status for t in transitions]
        
        if to_status not in allowed_statuses:
            frappe.throw(f"Transition from {from_status} to {to_status} not allowed")
        
        return True