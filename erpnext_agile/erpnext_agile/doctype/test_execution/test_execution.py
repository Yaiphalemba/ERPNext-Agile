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
    
    def on_submit(self):
        """Auto-create bug if test fails"""
        # Update test cycle item status
        self.update_cycle_item_status()
        
        # Update test cycle metrics
        self.update_cycle_metrics()
        
        # Create bug if failed and no defects linked
        if self.status == "Fail" and not self.defects:
            self.create_bug()
    
    def on_cancel(self):
        """Reset cycle item status on cancel"""
        self.update_cycle_item_status("Not Run")
        self.update_cycle_metrics()
        
    def before_save(self):
        if self.test_case:
            frappe.db.set_value('Test Case', self.test_case, 'last_executed', self.execution_date or frappe.utils.now())
    
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
    
    def create_bug(self):
        """Create a bug task automatically"""
        project = frappe.db.get_value("Test Cycle", self.test_cycle, "project")
        
        # Get failed steps for bug description
        failed_steps = []
        for result in self.test_results:
            if result.step_status == "Fail":
                failed_steps.append(f"Step {result.step_number}: {result.action}")
        
        failed_steps_text = "\n".join(failed_steps) if failed_steps else "See test execution for details"
        
        bug = frappe.get_doc({
            "doctype": "Task",
            "subject": f"Bug: {self.test_case} - Test Failed",
            "type": "Bug",
            "project": project,
            "description": f"""
                <h3>Test Execution Failed</h3>
                <p><b>Test Case:</b> {self.test_case}</p>
                <p><b>Test Execution:</b> {self.name}</p>
                <p><b>Environment:</b> {self.environment}</p>
                <p><b>Build Version:</b> {self.build_version or 'N/A'}</p>
                <p><b>Executed By:</b> {self.executed_by}</p>
                <p><b>Execution Date:</b> {self.execution_date}</p>
                
                <h4>Failed Steps:</h4>
                <pre>{failed_steps_text}</pre>
                
                <h4>Comments:</h4>
                {self.comments or 'No comments'}
            """,
            "priority": self.get_bug_priority(),
            "is_agile": 1,
            "status": "Open"
        })
        
        # Check if project has agile enabled
        if frappe.db.get_value("Project", project, "enable_agile"):
            # Set agile fields
            bug.issue_status = frappe.db.get_value(
                "Agile Issue Status", 
                {"status_category": "To Do"}, 
                "name"
            )
            bug.issue_type = frappe.db.get_value(
                "Agile Issue Type", 
                {"issue_type_name": "Bug"}, 
                "name"
            ) or "Bug"
            bug.issue_priority = self.get_agile_priority()
        
        bug.insert(ignore_permissions=True)
        
        # Link bug back to execution
        self.append("defects", {
            "bug_task": bug.name,
            "severity": self.get_severity_from_priority()
        })
        self.save()
        
        frappe.msgprint(f"Bug {bug.name} created automatically", alert=True, indicator="red")
        return bug.name
    
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