# erpnext_agile/tasks/weekly.py
import frappe
from frappe.utils import today, add_days

def generate_team_velocity_report():
    """Generate weekly team velocity report"""
    # Get all agile projects
    projects = frappe.get_all('Project',
        filters={'enable_agile': 1},
        fields=['name', 'project_name']
    )
    
    from erpnext_agile.agile_sprint_manager import AgileSprintManager
    manager = AgileSprintManager()
    
    for project in projects:
        try:
            velocity_data = manager.calculate_team_velocity(project.name)
            
            # Store velocity data for trending
            frappe.get_doc({
                'doctype': 'Agile Team Velocity',
                'project': project.name,
                'week_start': add_days(today(), -7),
                'week_end': today(),
                'average_velocity': velocity_data['average'],
                'trend': velocity_data['trend']
            }).insert()
            
            frappe.db.commit()
        except Exception as e:
            frappe.log_error(f"Error generating velocity report for {project.name}: {str(e)}")