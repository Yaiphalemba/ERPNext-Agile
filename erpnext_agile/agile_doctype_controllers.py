import frappe
from frappe import _
from frappe.utils import today, getdate
from frappe.share import add_docshare

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
        if doc.exp_end_date and getdate(doc.exp_end_date) < getdate(today()):
            frappe.db.set_value(doc.doctype, doc.name, 'custom_overdue', 1)
            doc.reload()
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
    add_reviewer_to_watchers(doc)
    share_doc_with_watchers(doc)
    add_bug_reporter_to_watchers(doc)
    add_owner_to_watchers(doc)
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

def add_reviewer_to_watchers(doc):
    """
    If the task has a reviewer assigned, ensure that the reviewer is also in the assignees list.
    This ensures that reviewers are always notified and have access to the task.
    """
    
    if doc.custom_reviewer and not any(watcher.user == doc.custom_reviewer for watcher in doc.watchers):
        # Add the reviewer to the assignees list
        doc.append('watchers', {
            'user': doc.custom_reviewer
        })
    
def share_doc_with_watchers(doc):
    """
    Share the document with all users listed in the watchers table.
    """
    if not getattr(doc, "watchers", None):
        return

    for watcher in doc.watchers:
        if watcher.user:
            try:
                add_docshare(
                    doctype=doc.doctype,
                    name=doc.name,
                    user=watcher.user,
                    read=1,      
                    write=1,     
                    share=0,     
                    notify=0     
                )
            except Exception as e:
                frappe.log_error(
                    title=f"Failed to share {doc.doctype} with {watcher.user}", 
                    message=str(e)
                )

def add_bug_reporter_to_watchers(doc):
    """
    If the task has a bug reporter assigned, ensure that the bug reporter is also in the watcher list.
    This ensures that bug reporter are always notified and have access to the task.
    """
    
    if doc.custom_bug_raised_by and not any(watcher.user == doc.custom_bug_raised_by for watcher in doc.watchers):
        # Add the Bug reporter to the watcher list
        doc.append('watchers', {
            'user': doc.custom_bug_raised_by
        })

def add_owner_to_watchers(doc):
    """
    If the task has an owner assigned, ensure that the owner is also in the watcher list.
    This ensures that owner are always notified and have access to the task.
    """
    
    if doc.custom_original_owner and not any(watcher.user == doc.custom_original_owner for watcher in doc.watchers):
        # Add the Owner to the watcher list
        doc.append('watchers', {
            'user': doc.custom_original_owner
        })

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