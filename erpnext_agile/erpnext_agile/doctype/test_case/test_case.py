# Copyright (c) 2025, Yanky and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class TestCase(Document):
    def autoname(self):
        """Auto-generate test case ID"""
        if not self.test_case_id:
            # Get the last test case number
            last_case = frappe.db.sql("""
                SELECT test_case_id 
                FROM `tabTest Case` 
                WHERE test_case_id LIKE 'TC-%'
                ORDER BY creation DESC 
                LIMIT 1
            """)
            
            if last_case:
                last_num = int(last_case[0][0].split('-')[1])
                new_num = last_num + 1
            else:
                new_num = 1
            
            self.test_case_id = f"TC-{new_num:05d}"
            self.name = self.test_case_id
    
    def validate(self):
        """Validate test case"""
        # Ensure at least one test step
        if not self.test_steps:
            frappe.throw("At least one test step is required")
        
        # Auto-number test steps
        for idx, step in enumerate(self.test_steps, 1):
            step.step_number = idx
        
        # Validate linked items
        self.validate_linked_items()
    
    def validate_linked_items(self):
        """Validate linked tasks/projects"""
        for link in self.linked_items:
            if not frappe.db.exists(link.link_doctype, link.link_name):
                frappe.throw(f"Invalid link: {link.link_doctype} - {link.link_name}")
    
    @frappe.whitelist()
    def get_execution_count(self):
        """Get total number of executions for this test case"""
        return frappe.db.count("Test Execution", {"test_case": self.name})
    
    @frappe.whitelist()
    def get_last_execution_status(self):
        """Get the status of the last execution"""
        last_execution = frappe.db.get_value(
            "Test Execution",
            {"test_case": self.name},
            ["status", "execution_date"],
            order_by="execution_date DESC"
        )
        return last_execution if last_execution else ("Not Run", None)
    
    @frappe.whitelist()
    def get_pass_rate(self):
        """Calculate pass rate for this test case"""
        executions = frappe.get_all(
            "Test Execution",
            filters={"test_case": self.name},
            fields=["status"]
        )
        
        if not executions:
            return 0
        
        passed = len([e for e in executions if e.status == "Pass"])
        total = len(executions)
        
        return (passed / total * 100) if total > 0 else 0
    
    @frappe.whitelist()
    def clone_test_case(self):
        """Create a copy of this test case"""
        new_case = frappe.copy_doc(self)
        new_case.title = f"{self.title} (Copy)"
        new_case.status = "Draft"
        new_case.insert()
        return new_case.name