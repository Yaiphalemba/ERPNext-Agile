# Copyright (c) 2025, Yanky and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today

class TestCycle(Document):
    def autoname(self):
        """Auto-generate cycle ID"""
        if not self.cycle_id:
            last_cycle = frappe.db.sql("""
                SELECT cycle_id 
                FROM `tabTest Cycle` 
                WHERE cycle_id LIKE 'TCYCLE-%'
                ORDER BY creation DESC 
                LIMIT 1
            """)
            
            if last_cycle:
                last_num = int(last_cycle[0][0].split('-')[1])
                new_num = last_num + 1
            else:
                new_num = 1
            
            self.cycle_id = f"TCYCLE-{new_num:05d}"
            self.name = self.cycle_id
    
    def validate(self):
        """Validate test cycle"""
        # Validate dates
        if self.planned_end_date and self.planned_start_date:
            if self.planned_end_date < self.planned_start_date:
                frappe.throw("Planned End Date cannot be before Planned Start Date")
        
        # Validate sprint project match
        if self.sprint:
            sprint_project = frappe.db.get_value("Agile Sprint", self.sprint, "project")
            if sprint_project != self.project:
                frappe.throw("Sprint project must match Test Cycle project")
        
        # Set actual dates based on status
        if self.status == "In Progress" and not self.actual_start_date:
            self.actual_start_date = today()
        
        if self.status == "Completed" and not self.actual_end_date:
            self.actual_end_date = today()
    
    def on_update(self):
        """Calculate metrics on update"""
        self.calculate_metrics()
    
    def calculate_metrics(self):
        """Calculate and update execution metrics"""
        executions = frappe.get_all(
            "Test Execution",
            filters={"test_cycle": self.name},
            fields=["status"]
        )
        
        total = len(executions)
        passed = len([e for e in executions if e.status == "Pass"])
        failed = len([e for e in executions if e.status == "Fail"])
        blocked = len([e for e in executions if e.status == "Blocked"])
        not_run = len([e for e in executions if e.status == "Not Run"])
        
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        # Update metrics without triggering save again
        self.db_set('total_tests', total, update_modified=False)
        self.db_set('passed_tests', passed, update_modified=False)
        self.db_set('failed_tests', failed, update_modified=False)
        self.db_set('blocked_tests', blocked, update_modified=False)
        self.db_set('not_run_tests', not_run, update_modified=False)
        self.db_set('pass_rate', pass_rate, update_modified=False)
    
    def get_execution_summary(self):
        """Get detailed execution summary"""
        return {
            "total": self.total_tests or 0,
            "passed": self.passed_tests or 0,
            "failed": self.failed_tests or 0,
            "blocked": self.blocked_tests or 0,
            "not_run": self.not_run_tests or 0,
            "pass_rate": self.pass_rate or 0
        }
    
    def start_cycle(self):
        """Start the test cycle"""
        if self.status != "Not Started":
            frappe.throw("Can only start cycles that are Not Started")
        
        self.status = "In Progress"
        self.actual_start_date = today()
        self.save()
        frappe.msgprint(f"Test Cycle {self.name} started")
    
    def complete_cycle(self):
        """Complete the test cycle"""
        if self.status != "In Progress":
            frappe.throw("Can only complete cycles that are In Progress")
        
        # Check if all tests are executed
        not_run = self.not_run_tests or 0
        if not_run > 0:
            frappe.throw(f"{not_run} test(s) are still Not Run. Please execute all tests before completing.")
        
        self.status = "Completed"
        self.actual_end_date = today()
        self.save()
        frappe.msgprint(f"Test Cycle {self.name} completed with {self.pass_rate}% pass rate")
    
    def add_test_cases_bulk(self, test_cases):
        """Bulk add test cases to cycle"""
        for tc in test_cases:
            if not frappe.db.exists("Test Case", tc):
                continue
            
            # Check if already added
            exists = any(row.test_case == tc for row in self.test_cases)
            if not exists:
                self.append("test_cases", {
                    "test_case": tc,
                    "execution_status": "Not Run"
                })
        
        self.save()
        frappe.msgprint(f"{len(test_cases)} test case(s) added to cycle")