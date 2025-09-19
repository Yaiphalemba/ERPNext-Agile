import frappe

class AgileWorkflowEngine:
    """Jira-style workflow engine"""
    
    @staticmethod
    def get_available_transitions(issue_name, user=None):
        """Get available status transitions for user"""
        issue = frappe.get_doc("Agile Issue", issue_name)
        current_status = issue.status
        user = user or frappe.session.user
        
        # Get workflow scheme
        agile_project = frappe.get_doc("Agile Project", issue.agile_project)
        workflow_scheme = agile_project.workflow_scheme
        
        if not workflow_scheme:
            # Default transitions
            return get_default_transitions(current_status)
        
        # Get allowed transitions from workflow
        transitions = frappe.get_all("Agile Workflow Transition", {
            "workflow_scheme": workflow_scheme,
            "from_status": current_status
        }, ["to_status", "transition_name", "required_permission"])
        
        # Filter by user permissions
        allowed_transitions = []
        for transition in transitions:
            if has_transition_permission(user, transition.required_permission, issue):
                allowed_transitions.append(transition)
        
        return allowed_transitions
    
    @staticmethod
    def transition_issue(issue_name, to_status, comment=None):
        """Transition issue with validation"""
        issue = frappe.get_doc("Agile Issue", issue_name)
        from_status = issue.status
        
        # Validate transition is allowed
        available_transitions = AgileWorkflowEngine.get_available_transitions(issue_name)
        if to_status not in [t.to_status for t in available_transitions]:
            frappe.throw(f"Transition from {from_status} to {to_status} not allowed")
        
        # Perform transition
        issue.status = to_status
        
        # Execute post-functions
        execute_post_functions(issue, from_status, to_status)
        
        # Add comment if provided
        if comment:
            issue.add_comment("Comment", comment)
        
        issue.save()

def get_default_transitions(current_status):
    """Default workflow transitions"""
    transitions = {
        "Open": ["In Progress", "Resolved", "Closed"],
        "In Progress": ["Open", "In Review", "Resolved", "Closed"],
        "In Review": ["In Progress", "Testing", "Resolved"],
        "Testing": ["In Review", "Resolved", "Closed"],
        "Resolved": ["Closed", "Reopened"],
        "Closed": ["Reopened"]
    }
    
    return [{"to_status": status, "transition_name": f"Move to {status}"} 
            for status in transitions.get(current_status, [])]

def execute_post_functions(issue, from_status, to_status):
    """Execute post-transition functions"""
    # Auto-assign when moving to In Progress
    if to_status == "In Progress" and not issue.assignee:
        issue.assignee = frappe.session.user
    
    # Update GitHub issue status
    if issue.github_issue_number:
        sync_status_to_github(issue, to_status)
    
    # Create timesheet when resolving
    if to_status in ["Resolved", "Closed"] and issue.remaining_estimate:
        create_completion_timesheet(issue)

def sync_status_to_github(issue, status):
    """Sync status changes to GitHub"""
    # Map agile status to GitHub actions
    if status in ["Resolved", "Closed"]:
        # Close GitHub issue
        frappe.call(
            'erpnext_github_integration.github_api.close_issue',
            repository=issue.get_github_repository(),
            issue_number=issue.github_issue_number
        )

def create_completion_timesheet(issue):
    """Create ERPNext Timesheet entry when issue is resolved or closed"""
    agile_project = frappe.get_doc("Agile Project", issue.agile_project)
    
    # Get employee linked to the assignee
    employee = frappe.db.get_value("Employee", {"user_id": issue.assignee}, "name")
    
    # Convert remaining_estimate (duration in seconds) to hours
    hours = frappe.utils.time_diff_in_hours(issue.remaining_estimate, "00:00:00") if issue.remaining_estimate else 0
    
    if hours <= 0:
        return
    
    try:
        timesheet = frappe.get_doc({
            "doctype": "Timesheet",
            "employee": employee,
            "time_logs": [{
                "activity_type": "Development",
                "hours": hours,
                "project": agile_project.project,
                "task": issue.task,
                "description": f"Completed {issue.issue_key}: {issue.summary}"
            }]
        })
        timesheet.insert()
        
        # Clear remaining estimate
        issue.remaining_estimate = None
        frappe.msgprint(f"Timesheet created for {issue.issue_key} with {hours} hours")
        
    except Exception as e:
        frappe.log_error(f"Failed to create timesheet for {issue.issue_key}: {str(e)}")

def has_transition_permission(user, required_permission, issue):
    """Check if user has permission for workflow transition"""
    if not required_permission:
        return True  # No specific permission required
    
    # Get permission scheme from project
    agile_project = frappe.get_doc("Agile Project", issue.agile_project)
    permission_scheme = agile_project.permission_scheme
    
    if not permission_scheme:
        # Fallback to standard Frappe permissions
        return frappe.has_permission("Agile Issue", "write", user=user, doc=issue.name)
    
    # Check if user has the required permission role
    user_roles = frappe.get_roles(user)
    permission_roles = frappe.db.get_value(
        "Agile Permission Scheme",
        permission_scheme,
        required_permission,
        as_dict=True
    )
    
    if not permission_roles:
        return False
    
    # Check if any user role matches the required permission roles
    return any(role in user_roles for role in permission_roles.get(required_permission, []))