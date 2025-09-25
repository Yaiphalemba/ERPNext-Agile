# Updated github_integration.py
import frappe

def process_github_webhook(payload):
    """Enhanced webhook processing for agile tasks"""
    event_type = payload.get('action')
    
    if 'issue' in payload:
        process_github_issue_event(payload)
    elif 'pull_request' in payload:
        process_github_pr_event(payload)
    elif 'commits' in payload:
        process_github_push_event(payload)

def process_github_issue_event(payload):
    """Process GitHub issue events"""
    github_issue = payload['issue']
    issue_title = github_issue['title']
    
    # Extract issue key from title
    issue_key = extract_issue_key(issue_title)
    if not issue_key:
        return
    
    agile_task = frappe.db.get_value("Task", {"issue_key": issue_key})
    if not agile_task:
        return
    
    # Update status based on GitHub issue state
    if payload['action'] == 'closed':
        frappe.db.set_value("Task", agile_task, "status", "Resolved")
    elif payload['action'] == 'reopened':
        frappe.db.set_value("Task", agile_task, "status", "Open")

def process_github_pr_event(payload):
    """Process GitHub pull request events"""
    pr = payload['pull_request']
    pr_title = pr['title']
    
    # Extract issue key from PR title
    issue_key = extract_issue_key(pr_title)
    if not issue_key:
        return
    
    agile_task = frappe.get_doc("Task", {"issue_key": issue_key})
    if not agile_task:
        return
    
    # Update task based on PR state
    if payload['action'] == 'opened':
        agile_task.github_pull_request = pr['number']
        agile_task.status = "In Review"
    elif payload['action'] == 'merged':
        agile_task.status = "Resolved"
    elif payload['action'] == 'closed' and not pr['merged']:
        agile_task.status = "In Progress"  # PR rejected, back to work
    
    agile_task.save()

def process_github_push_event(payload):
    """Process GitHub push events to link commits"""
    commits = payload.get('commits', [])
    
    for commit in commits:
        commit_message = commit['message']
        issue_keys = extract_all_issue_keys(commit_message)
        
        for issue_key in issue_keys:
            link_commit_to_task(issue_key, commit)

def link_commit_to_task(issue_key, commit_data):
    """Link commit to agile task"""
    agile_task = frappe.db.get_value("Task", {"issue_key": issue_key})
    if not agile_task:
        return
    
    # Add commit to linked commits table (assuming child table on Task)
    task_doc = frappe.get_doc("Task", agile_task)
    task_doc.append("linked_commits", {
        "commit_hash": commit_data['id'],
        "commit_message": commit_data['message'],
        "author": commit_data['author']['name'],
        "commit_date": commit_data['timestamp']
    })
    task_doc.save()

def extract_issue_key(text):
    """Extract issue key from text (PROJ-123 format)"""
    import re
    match = re.search(r'([A-Z]{2,10}-\d+)', text)
    return match.group(1) if match else None

def extract_all_issue_keys(text):
    """Extract all issue keys from text"""
    import re
    return re.findall(r'([A-Z]{2,10}-\d+)', text)