import frappe

def task_validate(doc, method):
    """Extend Task validation for agile features"""
    if doc.is_agile:
        # Validate agile fields
        if not doc.project:
            frappe.throw("Project is mandatory for agile issues")
        
        project_doc = frappe.get_doc('Project', doc.project)
        if not project_doc.enable_agile:
            frappe.throw(f"Project {doc.project} is not agile-enabled")
        
        # Auto-generate issue key if not set
        if not doc.issue_key:
            from erpnext_agile.agile_issue_manager import AgileIssueManager
            manager = AgileIssueManager()
            doc.issue_key = manager.generate_issue_key(project_doc)
        
        # Set default status if not set
        if not doc.issue_status:
            doc.issue_status = manager.get_default_status(project_doc)

def task_on_update(doc, method):
    """Actions on task update"""
    if doc.is_agile:
        # Sync to GitHub if enabled
        project_doc = frappe.get_doc('Project', doc.project)
        
        if (project_doc.get('auto_create_github_issues') and 
            project_doc.get('github_repository') and 
            not doc.github_issue_number):
            # Create GitHub issue in background
            frappe.enqueue(
                'erpnext_agile.agile_github_integration.AgileGitHubIntegration.create_github_issue',
                task_doc=doc,
                queue='short'
            )

def task_after_insert(doc, method):
    """Actions after task insert"""
    if doc.is_agile:
        # Send creation notifications
        from erpnext_agile.agile_issue_manager import AgileIssueManager
        manager = AgileIssueManager()
        manager.send_issue_notifications(doc, 'created')

def task_on_trash(doc, method):
    """Actions on task deletion"""
    if doc.is_agile:
        # Clean up related records
        frappe.db.delete('Agile Issue Activity', {'issue': doc.name})
        frappe.db.delete('Agile Work Timer', {'task': doc.name})