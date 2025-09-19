import frappe

def setup_github_agile_integration():
    """Setup integration with existing GitHub integration app"""
    
    # Extend Repository doctype with agile project link
    if not frappe.db.exists("Custom Field", {"dt": "Repository", "fieldname": "custom_agile_project"}):
        custom_field = frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "Repository",
            "fieldname": "custom_agile_project",
            "fieldtype": "Link",
            "label": "Agile Project",
            "options": "Agile Project",
            "insert_after": "repository_name"
        })
        custom_field.insert()
    
    # Extend Repository Issue with agile issue link
    if not frappe.db.exists("Custom Field", {"dt": "Repository Issue", "fieldname": "custom_agile_issue"}):
        custom_field = frappe.get_doc({
            "doctype": "Custom Field", 
            "dt": "Repository Issue",
            "fieldname": "custom_agile_issue",
            "fieldtype": "Link",
            "label": "Agile Issue",
            "options": "Agile Issue",
            "insert_after": "issue_title"
        })
        custom_field.insert()

def sync_github_repositories_to_agile():
    """Sync existing GitHub repositories to agile projects"""
    repositories = frappe.get_all("Repository", 
        fields=["name", "repository_name", "repository_owner"]
    )
    
    for repo in repositories:
        # Check if agile project exists for this repo
        agile_project = frappe.db.get_value("Agile Project", {"github_repository": repo.name})
        
        if not agile_project:
            # Create agile project for this repository
            project_key = generate_project_key(repo.repository_name)
            
            agile_project = frappe.get_doc({
                "doctype": "Agile Project",
                "project_name": f"{repo.repository_owner}/{repo.repository_name}",
                "project_key": project_key,
                "github_repository": repo.name,
                "project_type": "Scrum"
            })
            agile_project.insert()

def generate_project_key(repo_name):
    """Generate project key from repository name"""
    import re
    
    # Extract meaningful parts and create key
    clean_name = re.sub(r'[^a-zA-Z]', '', repo_name)
    
    if len(clean_name) >= 3:
        return clean_name[:10].upper()
    else:
        return f"PROJ{frappe.db.count('Agile Project') + 1}"