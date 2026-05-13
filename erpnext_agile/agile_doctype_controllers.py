import frappe
from frappe import _

def task_validate(doc, method):
    """Extend Task validation for agile features"""
    if doc.is_agile:
        # Validate agile fields
        if not doc.project:
            frappe.throw("Project is mandatory for agile issues")
        
        project_doc = frappe.get_doc('Project', doc.project)
        if not project_doc.enable_agile:
            frappe.throw(f"Project {doc.project} is not agile-enabled")
        
        from erpnext_agile.agile_issue_manager import AgileIssueManager
        manager = AgileIssueManager()
            
        # Auto-generate issue key if not set
        if not doc.issue_key:
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
    ## Reflection: Tasks Linked into other task's child table as dependincies were not getting updated on task update. Hence added a method to update the same.
    sync_dependent_task_details(doc)
    ## Reflection: Test Cases Linked into This task's child table will also reflect this tasks into its linked tasks child table.
    link_task_to_test_cases(doc)
    remove_unlinked_test_cases(doc)    

def sync_dependent_task_details(doc):
    """
    Updates the subject and status in the 'Task Depends On' child table 
    across all parent tasks that link to this document.
    """
    
    frappe.db.sql("""
        UPDATE `tabTask Depends On`
        SET 
            subject = %s,
            custom_task_status = %s
        WHERE 
            task = %s
    """, (doc.subject, doc.issue_status, doc.name))

def link_task_to_test_cases(doc):
    """
    For each test case linked to this task, ensure that the task is listed in the test case's linked tasks.
    This maintains bidirectional linking between tasks and test cases.
    """
    
    for entry in doc.custom_test_cases:
        test_case_doc = frappe.get_doc('Test Case', entry.test_case)
        
        # Check if the task is already linked in the test case's linked items
        if not any(link.link_doctype == 'Task' and link.link_name == doc.name for link in test_case_doc.linked_items):
            # If not linked, add it
            test_case_doc.append('linked_items', {
                'link_doctype': 'Task',
                'link_name': doc.name
            })
            test_case_doc.flags.sync_in_progress = True
            test_case_doc.save(ignore_permissions=True)

def remove_unlinked_test_cases(doc):
    """Remove this Task from Test Cases that were unlinked during this save."""
    if doc.is_new() or doc.flags.sync_in_progress:
        return

    old_doc = doc.get_doc_before_save()
    if not old_doc:
        return

    # Find which test cases were present before the save, but are missing now
    old_tcs = {row.test_case for row in old_doc.custom_test_cases if row.test_case}
    current_tcs = {row.test_case for row in doc.custom_test_cases if row.test_case}
    
    removed_tcs = old_tcs - current_tcs

    for tc_name in removed_tcs:
        tc_doc = frappe.get_doc("Test Case", tc_name)
        
        initial_count = len(tc_doc.linked_items)
        
        # Filter out this task from the Test Case's child table
        tc_doc.linked_items = [
            link for link in tc_doc.linked_items 
            if not (link.link_doctype == 'Task' and link.link_name == doc.name)
        ]
        
        if len(tc_doc.linked_items) < initial_count:
            # Set the flag to prevent the Test case from triggering another sync back
            tc_doc.flags.sync_in_progress = True
            tc_doc.save(ignore_permissions=True)

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