# erpnext_agile/overrides/project.py
import frappe
from frappe import _
import re
from erpnext.projects.doctype.project.project import Project

class AgileProject(Project):
    def validate(self):
        super().validate()
        if self.enable_agile:
            self.validate_agile_settings()

    def validate_agile_settings(self):
        """Validate agile-specific settings"""
        if self.workflow_scheme and not frappe.db.exists("Agile Workflow Scheme", self.workflow_scheme):
            frappe.throw(f"Workflow Scheme {self.workflow_scheme} does not exist")
        if self.permission_scheme and not frappe.db.exists("Agile Permission Scheme", self.permission_scheme):
            frappe.throw(f"Permission Scheme {self.permission_scheme} does not exist")