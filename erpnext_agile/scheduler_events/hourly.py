# erpnext_agile/tasks/hourly.py
import frappe
from frappe.utils import today, now_datetime

def update_sprint_metrics():
    """Update metrics for all active sprints"""
    active_sprints = frappe.get_all('Agile Sprint',
        filters={'sprint_state': 'Active'},
        fields=['name', 'project']
    )
    
    from erpnext_agile.agile_sprint_manager import AgileSprintManager
    manager = AgileSprintManager()
    
    for sprint in active_sprints:
        try:
            sprint_doc = frappe.get_doc('Agile Sprint', sprint.name)
            metrics = manager.calculate_sprint_metrics(sprint_doc)
            
            # Update without triggering save hooks
            sprint_doc.db_set('total_points', metrics['total_points'], update_modified=False)
            sprint_doc.db_set('completed_points', metrics['completed_points'], update_modified=False)
            sprint_doc.db_set('progress_percentage', metrics['progress_percentage'], update_modified=False)
            sprint_doc.db_set('velocity', metrics['velocity'], update_modified=False)
            
            frappe.db.commit()
        except Exception as e:
            frappe.log_error(f"Error updating sprint metrics for {sprint.name}: {str(e)}")

def create_burndown_entries():
    """Create burndown entries for active sprints"""
    active_sprints = frappe.get_all('Agile Sprint',
        filters={'sprint_state': 'Active'},
        fields=['name', 'project']
    )
    
    from erpnext_agile.agile_sprint_manager import AgileSprintManager
    manager = AgileSprintManager()
    
    for sprint in active_sprints:
        try:
            sprint_doc = frappe.get_doc('Agile Sprint', sprint.name)
            
            # Check if burndown is enabled for project
            if frappe.db.get_value('Project', sprint_doc.project, 'burndown_enabled'):
                # Check if entry already exists for today
                existing = frappe.db.exists('Agile Sprint Burndown', {
                    'sprint': sprint.name,
                    'date': today()
                })
                
                if not existing:
                    manager.create_burndown_entry(sprint_doc)
                    frappe.db.commit()
        except Exception as e:
            frappe.log_error(f"Error creating burndown entry for {sprint.name}: {str(e)}")