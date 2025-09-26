# Updated workflow_engine.py
import frappe

class AgileWorkflowEngine:
    """Jira-style workflow engine"""
    
    @staticmethod
    def get_available_transitions(task_name, user=None):
        """Get available status transitions for user"""
        task = frappe.get_doc("Task", task_name)
        current_status = task.status
        user = user or frappe.session.user
        
        # Get workflow scheme
        project = frappe.get_doc("Project", task.project)
        if not project.enable_agile:
            return []
        
        workflow_scheme = project.workflow_scheme
        
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
            if has_transition_permission(user, transition.required_permission, task):
                allowed_transitions.append(transition)
        
        return allowed_transitions
    
    @staticmethod
    def transition_task(task_name, to_status, comment=None):
        """Transition task with validation"""
        task = frappe.get_doc("Task", task_name)
        from_status = task.status
        
        # Validate transition is allowed
        available_transitions = AgileWorkflowEngine.get_available_transitions(task_name)
        if to_status not in [t.to_status for t in available_transitions]:
            frappe.throw(f"Transition from {from_status} to {to_status} not allowed")
        
        # Perform transition
        task.status = to_status
        
        # Execute post-functions
        execute_post_functions(task, from_status, to_status)
        
        # Add comment if provided
        if comment:
            task.add_comment("Comment", comment)
        
        task.save()

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

def execute_post_functions(task, from_status, to_status):
    """Execute post-transition functions"""
    # Auto-assign when moving to In Progress
    if to_status == "In Progress" and not task.assignee:
        task.assignee = frappe.session.user
    
    # Update GitHub issue status
    if task.github_issue_number:
        sync_status_to_github(task, to_status)
    
    # Create timesheet when resolving
    if to_status in ["Resolved", "Closed"] and task.remaining_estimate:
        create_completion_timesheet(task)

def sync_status_to_github(task, status):
    """Sync status changes to GitHub"""
    # Map agile status to GitHub actions
    if status in ["Resolved", "Closed"]:
        # Close GitHub issue
        frappe.call(
            'erpnext_github_integration.github_api.close_issue',
            repository=task.github_repo,
            issue_number=task.github_issue_number
        )

def create_completion_timesheet(task):
    """Create ERPNext Timesheet entry when task is resolved or closed"""
    project = frappe.get_doc("Project", task.project)
    
    # Get assignees using the get_document_assignees function
    assignees = get_document_assignees("Task", task.name)
    
    if not assignees:
        frappe.msgprint(f"No assignees found for task {task.name}")
        return
    
    # Convert remaining_estimate (duration in seconds) to hours
    hours = frappe.utils.time_diff_in_hours(task.remaining_estimate, "00:00:00") if task.remaining_estimate else 0
    
    if hours <= 0:
        return
    
    try:
        # Create timesheet for each assignee
        for assignee in assignees:
            # Get employee linked to the assignee
            employee = frappe.db.get_value("Employee", {"user": assignee}, "name")
            
            if not employee:
                frappe.msgprint(f"No employee found for user {assignee}")
                continue
            
            timesheet = frappe.get_doc({
                "doctype": "Timesheet",
                "employee": employee,
                "time_logs": [{
                    "activity_type": "Development",
                    "hours": hours,
                    "project": project.name,
                    "task": task.name,
                    "description": f"Completed {task.issue_key}: {task.subject}"
                }]
            })
            timesheet.insert()
        
        # Clear remaining estimate
        task.remaining_estimate = None
        frappe.msgprint(f"Timesheet created for {task.issue_key} with {hours} hours for {len(assignees)} assignee(s)")
        
    except Exception as e:
        frappe.log_error(f"Failed to create timesheet for {task.issue_key}: {str(e)}")

def has_transition_permission(user, required_permission, task):
    """Check if user has permission for workflow transition"""
    if not required_permission:
        return True  # No specific permission required
    
    # Get permission scheme from project
    project = frappe.get_doc("Project", task.project)
    permission_scheme = project.permission_scheme
    
    if not permission_scheme:
        # Fallback to standard Frappe permissions
        return frappe.has_permission("Task", "write", user=user, doc=task.name)
    
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

def get_document_assignees(doctype, name):
    # Query the ToDo doctype to find assignments for the given document
    assignees = frappe.get_list(
        "ToDo",
        filters={
            "reference_type": doctype,
            "reference_name": name,
            "status":"Open"
        },
        fields=["allocated_to"]
    )
    return [d.allocated_to for d in assignees]