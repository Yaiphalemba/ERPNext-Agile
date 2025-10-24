# Copyright (c) 2025, Yanky and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class AgileReleaseVersion(Document):
	pass

@frappe.whitelist()
def get_branch_commit_sha(branch_name, repository):
    """Get commit SHA with proper permission handling"""
    try:
        # Check if user has permission to read Repository
        if not frappe.has_permission("Repository", "read"):
            frappe.throw("No permission to read Repository")
        
        # Get the commit SHA
        commit_sha = frappe.db.get_value("Repository Branch", 
            {"name": branch_name, "parent": repository}, 
            "commit_sha")
        
        return commit_sha
        
    except Exception as e:
        frappe.log_error(f"Error getting commit SHA: {str(e)}")
        return None