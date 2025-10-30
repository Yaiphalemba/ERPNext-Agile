# Copyright (c) 2025, Yanky and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _

class AgileWorkflowScheme(Document):
    """Jira-style workflow schemes with conditional transitions"""
    
    def validate(self):
        """Validate workflow configuration"""
        # Validate transitions
        for transition in self.transitions:
            if transition.from_status == transition.to_status:
                frappe.throw(_("From Status and To Status cannot be the same"))
            
            # Validate condition syntax if provided
            if transition.condition:
                self.validate_condition_syntax(transition.condition, transition.transition_name)
    
    def validate_condition_syntax(self, condition, transition_name):
        """Validate Python condition syntax"""
        if not condition.strip():
            return
        
        try:
            # Try to compile the condition to check syntax
            compile(condition, '<string>', 'eval')
        except SyntaxError as e:
            frappe.throw(
                _("Invalid Python syntax in transition '{0}': {1}").format(
                    transition_name, str(e)
                )
            )
    
    def get_transitions(self, from_status, doc=None):
        """
        Get available transitions from a status
        
        Args:
            from_status: Current status
            doc: Document object for condition evaluation
        """
        transitions = []
        for t in self.transitions:
            if t.from_status == from_status:
                # Check if condition is met
                if t.condition and doc:
                    if not self.evaluate_condition(t.condition, doc):
                        continue  # Skip this transition
                
                transitions.append({
                    'to_status': t.to_status,
                    'transition_name': t.transition_name,
                    'required_permission': t.required_permission,
                    'condition': t.condition
                })
        return transitions
    
    def validate_transition(self, from_status, to_status, doc=None, user=None):
        """
        Validate if transition is allowed
        
        Args:
            from_status: Current status
            to_status: Target status
            doc: Document object for condition evaluation
            user: User attempting the transition
        """
        # Get all transitions from current status
        transitions = [t for t in self.transitions if t.from_status == from_status]
        
        # Find matching transition
        matching_transition = None
        for t in transitions:
            if t.to_status == to_status:
                matching_transition = t
                break
        
        if not matching_transition:
            return False, _("No transition defined from '{0}' to '{1}'").format(
                from_status, to_status
            )
        
        # Check condition if provided
        if matching_transition.condition and doc:
            if not self.evaluate_condition(matching_transition.condition, doc):
                return False, _("Transition condition not met: {0}").format(
                    matching_transition.condition
                )
        
        # Check permissions if user provided
        if user and matching_transition.required_permission:
            if not self.check_user_permission(user, matching_transition.required_permission):
                return False, _("User does not have required permission: {0}").format(
                    matching_transition.required_permission
                )
        
        return True, None
    
    def evaluate_condition(self, condition, doc):
        """
        Evaluate Python condition against document
        
        Args:
            condition: Python expression string
            doc: Document object
        
        Returns:
            Boolean result of condition evaluation
        """
        if not condition or not condition.strip():
            return True
        
        try:
            # Create safe evaluation context
            eval_context = {
                'doc': doc,
                'frappe': frappe,
                '_': _,
                # Add commonly used functions
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
                'list': list,
                'dict': dict,
                'today': frappe.utils.today,
                'now': frappe.utils.now,
                'get_value': frappe.db.get_value,
                'exists': frappe.db.exists,
            }
            
            # Evaluate condition
            result = eval(condition, {"__builtins__": {}}, eval_context)
            return bool(result)
            
        except Exception as e:
            frappe.log_error(
                f"Error evaluating workflow condition: {condition}\nError: {str(e)}",
                "Workflow Condition Error"
            )
            # If condition evaluation fails, deny transition for safety
            frappe.throw(
                _("Failed to evaluate transition condition: {0}").format(str(e))
            )
            return False
    
    def check_user_permission(self, user, required_permission):
        """Check if user has required permission"""
        if not required_permission or required_permission == 'All':
            return True
        
        # Check if user has the required role
        user_roles = frappe.get_roles(user)
        return required_permission in user_roles
    
    def get_transition_map(self, doc=None):
        """
        Get complete transition map for visualization
        
        Returns:
            Dict mapping each status to its possible next statuses
        """
        transition_map = {}
        
        for t in self.transitions:
            if t.from_status not in transition_map:
                transition_map[t.from_status] = []
            
            # Check condition if doc provided
            if doc and t.condition:
                if not self.evaluate_condition(t.condition, doc):
                    continue
            
            transition_map[t.from_status].append({
                'to_status': t.to_status,
                'transition_name': t.transition_name,
                'required_permission': t.required_permission,
                'has_condition': bool(t.condition)
            })
        
        return transition_map


# Whitelisted API methods
@frappe.whitelist()
def get_available_transitions(workflow_scheme, from_status, task_name=None):
    """
    Get available transitions for a task
    
    Args:
        workflow_scheme: Name of Agile Workflow Scheme
        from_status: Current status
        task_name: Task document name (optional)
    """
    if not frappe.db.exists("Agile Workflow Scheme", workflow_scheme):
        frappe.throw(_("Invalid Workflow Scheme"))
    
    scheme = frappe.get_doc("Agile Workflow Scheme", workflow_scheme)
    
    # Get task document if provided
    doc = None
    if task_name:
        doc = frappe.get_doc("Task", task_name)
    
    transitions = scheme.get_transitions(from_status, doc)
    
    # Filter by user permissions
    user = frappe.session.user
    filtered_transitions = []
    
    for t in transitions:
        if t['required_permission']:
            if scheme.check_user_permission(user, t['required_permission']):
                filtered_transitions.append(t)
        else:
            filtered_transitions.append(t)
    
    return filtered_transitions


@frappe.whitelist()
def validate_transition(workflow_scheme, from_status, to_status, task_name):
    """
    Validate if a transition is allowed
    
    Args:
        workflow_scheme: Name of Agile Workflow Scheme
        from_status: Current status
        to_status: Target status
        task_name: Task document name
    """
    if not frappe.db.exists("Agile Workflow Scheme", workflow_scheme):
        frappe.throw(_("Invalid Workflow Scheme"))
    
    scheme = frappe.get_doc("Agile Workflow Scheme", workflow_scheme)
    doc = frappe.get_doc("Task", task_name)
    user = frappe.session.user
    
    is_valid, error_message = scheme.validate_transition(
        from_status, to_status, doc, user
    )
    
    if not is_valid:
        frappe.throw(error_message)
    
    return {"valid": True}


@frappe.whitelist()
def get_workflow_diagram(workflow_scheme, task_name=None):
    """
    Get workflow diagram data for visualization
    
    Args:
        workflow_scheme: Name of Agile Workflow Scheme
        task_name: Task document name (optional)
    """
    if not frappe.db.exists("Agile Workflow Scheme", workflow_scheme):
        frappe.throw(_("Invalid Workflow Scheme"))
    
    scheme = frappe.get_doc("Agile Workflow Scheme", workflow_scheme)
    
    # Get task document if provided
    doc = None
    if task_name:
        doc = frappe.get_doc("Task", task_name)
    
    transition_map = scheme.get_transition_map(doc)
    
    # Get all unique statuses
    all_statuses = set()
    for from_status, transitions in transition_map.items():
        all_statuses.add(from_status)
        for t in transitions:
            all_statuses.add(t['to_status'])
    
    # Get status details
    status_details = {}
    for status in all_statuses:
        status_doc = frappe.get_doc("Agile Issue Status", status)
        status_details[status] = {
            'name': status_doc.status_name,
            'category': status_doc.status_category,
            'color': status_doc.color
        }
    
    return {
        'transitions': transition_map,
        'statuses': status_details
    }