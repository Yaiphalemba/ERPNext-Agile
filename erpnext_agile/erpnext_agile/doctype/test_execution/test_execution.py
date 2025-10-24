# Copyright (c) 2025, Yanky and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

class TestExecution(Document):
    def autoname(self):
        """Auto-generate execution ID"""
        if not self.execution_id:
            last_exec = frappe.db.sql("""
                SELECT execution_id 
                FROM `tabTest Execution` 
                WHERE execution_id LIKE 'TEXEC-%'
                ORDER BY creation DESC 
                LIMIT 1
            """)
            
            if last_exec:
                last_num = int(last_exec[0][0].split('-')[1])
                new_num = last_num + 1
            else:
                new_num = 1
            
            self.execution_id = f"TEXEC-{new_num:05d}"
            self.name = self.execution_id
    
    def validate(self):
        """Validate test execution"""
        # Set execution date if not set
        if not self.execution_date:
            self.execution_date = now_datetime()
        
        # Set executed_by if not set
        if not self.executed_by:
            self.executed_by = frappe.session.user
        
        # Validate test cycle and test case project match
        cycle_project = frappe.db.get_value("Test Cycle", self.test_cycle, "project")
        case_project = frappe.db.get_value("Test Case", self.test_case, "project")
        
        if case_project and cycle_project != case_project:
            frappe.throw("Test Case project must match Test Cycle project")
    
    def before_submit(self):
        """Actions before submission"""
        # Load test steps into test results if not already loaded
        if not self.test_results:
            self.load_test_steps()
            
        """Auto-create bug if test fails"""
        # Update test cycle item status
        self.update_cycle_item_status()
        
        # Update test cycle metrics
        self.update_cycle_metrics()
        
        # Create bug if failed and no defects linked
        if self.status == "Fail" and not self.defects:
        # Set flag to indicate we're in submit context
            self._in_submit = True
            try:
                bug_name = self.create_bug()
                frappe.msgprint(f"Bug {bug_name} created automatically", alert=True, indicator="green")
            finally:
                # Always clear the flag
                self._in_submit = False
            
    
    def on_cancel(self):
        """Reset cycle item status on cancel"""
        self.update_cycle_item_status("Not Run")
        self.update_cycle_metrics()
        
    def before_save(self):
        if self.test_case:
            frappe.db.set_value('Test Case', self.test_case, 'last_executed', self.execution_date or frappe.utils.now())
    
    @frappe.whitelist()
    def load_test_steps(self):
        """Load test steps from test case"""
        test_case = frappe.get_doc("Test Case", self.test_case)
        
        for step in test_case.test_steps:
            self.append("test_results", {
                "step_number": step.step_number,
                "action": step.action,
                "expected_result": step.expected_result,
                "actual_result": "",
                "step_status": "Not Run"
            })
    
    def update_cycle_item_status(self, status=None):
        """Update test cycle item execution status"""
        cycle = frappe.get_doc("Test Cycle", self.test_cycle)
        
        for item in cycle.test_cases:
            if item.test_case == self.test_case:
                item.execution_status = status or self.status
                break
        
        cycle.save()
    
    def update_cycle_metrics(self):
        """Trigger cycle metrics recalculation"""
        cycle = frappe.get_doc("Test Cycle", self.test_cycle)
        cycle.calculate_metrics()
    
    @frappe.whitelist()
    def create_bug(self):
        """Create a bug task automatically - handles both manual and auto-submit calls"""
        try:
            # Get fresh document to avoid stale data issues
            if getattr(self, "_in_submit", False):
                # If called from before_submit, use self but be careful with saves
                doc = self
            else:
                # If called from button click, get fresh document
                doc = frappe.get_doc("Test Execution", self.name)
            
            # Validate required fields
            if not doc.test_cycle:
                frappe.throw("Test Cycle is required to create a bug")
            
            if not doc.test_case:
                frappe.throw("Test Case is required to create a bug")
            
            project = frappe.db.get_value("Test Cycle", doc.test_cycle, "project")
            if not project:
                frappe.throw("Project not found for the selected Test Cycle")
            
            # Check if there are any failed steps
            failed_steps = []
            for result in doc.test_results:
                if result.step_status == "Fail":
                    failed_steps.append(f"Step {result.step_number}: {result.action}")
            
            failed_steps_text = "\n".join(failed_steps) if failed_steps else "No specific failed steps recorded. Check test execution for details."
            
            # Prepare bug data
            bug_data = {
                "doctype": "Task",
                "subject": f"Bug: {doc.test_case} - Test Failed",
                "type": "Bug",
                "project": project,
                "description": f"""
                    <h3>Test Execution Failed</h3>
                    <p><strong>Test Case:</strong> {frappe.utils.strip_html(str(doc.test_case))}</p>
                    <p><strong>Test Execution:</strong> {doc.name}</p>
                    <p><strong>Environment:</strong> {doc.environment or 'N/A'}</p>
                    <p><strong>Build Version:</strong> {doc.build_version or 'N/A'}</p>
                    <p><strong>Executed By:</strong> {doc.executed_by or 'N/A'}</p>
                    <p><strong>Execution Date:</strong> {doc.execution_date or frappe.utils.nowdate()}</p>
                    
                    <h4>Failed Steps:</h4>
                    <pre>{failed_steps_text}</pre>
                    
                    <h4>Additional Comments:</h4>
                    <p>{doc.comments or 'No additional comments'}</p>
                    
                    <hr>
                    <p><em>Auto-generated from Test Execution: {doc.name}</em></p>
                """,
                "priority": doc.get_bug_priority() if hasattr(doc, 'get_bug_priority') else "High",
                "is_agile": 1,
                "status": "Open"
            }
            
            # Create bug document
            bug = frappe.get_doc(bug_data)
            
            # Set agile fields if project has agile enabled
            if frappe.db.get_value("Project", project, "enable_agile"):
                agile_status = frappe.db.get_value(
                    "Agile Issue Status", 
                    {"status_category": "To Do"}, 
                    "name"
                )
                if agile_status:
                    bug.issue_status = agile_status
                
                issue_type = frappe.db.get_value(
                    "Agile Issue Type", 
                    {"issue_type_name": "Bug"}, 
                    "name"
                )
                bug.issue_type = issue_type or "Bug"
                
                if hasattr(doc, 'get_agile_priority'):
                    bug.issue_priority = doc.get_agile_priority()
            
            # Insert the bug
            bug.insert(ignore_permissions=True)
            
            # Link bug back to execution
            doc.append("defects", {
                "bug_task": bug.name,
                "severity": doc.get_severity_from_priority() if hasattr(doc, 'get_severity_from_priority') else "Medium"
            })
            
            # Handle save differently based on context
            if getattr(doc, "_in_submit", False):
                # If in submit process, don't save - the parent submit will handle it
                # Just update the in-memory document
                pass
            else:
                # If called from button, save immediately
                doc.save(ignore_permissions=True)
                frappe.db.commit()
            
            return bug.name
            
        except Exception as e:
            frappe.db.rollback()
            frappe.log_error(
                title=f"Error creating bug for Test Execution {self.name}",
                message=frappe.get_traceback()
            )
            frappe.throw(f"Failed to create bug: {str(e)}")
    
    def get_bug_priority(self):
        """Map test priority to bug priority"""
        priority_map = {
            "Critical": "High",
            "High": "Medium",
            "Medium": "Low",
            "Low": "Low"
        }
        test_priority = frappe.db.get_value("Test Case", self.test_case, "priority")
        return priority_map.get(test_priority, "Medium")
    
    def get_agile_priority(self):
        """Get agile issue priority"""
        test_priority = frappe.db.get_value("Test Case", self.test_case, "priority")
        
        # Try to find matching agile priority
        agile_priority = frappe.db.get_value(
            "Agile Issue Priority",
            {"priority_name": test_priority},
            "name"
        )
        
        # Fallback to first available priority
        if not agile_priority:
            agile_priority = frappe.db.get_value(
                "Agile Issue Priority",
                {},
                "name",
                order_by="sort_order"
            )
        
        return agile_priority
    
    def get_severity_from_priority(self):
        """Get severity based on test case priority"""
        priority = frappe.db.get_value("Test Case", self.test_case, "priority")
        severity_map = {
            "Critical": "Critical",
            "High": "Major",
            "Medium": "Minor",
            "Low": "Minor"
        }
        return severity_map.get(priority, "Minor")