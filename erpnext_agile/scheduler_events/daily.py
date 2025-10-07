# erpnext_agile/tasks/daily.py
import frappe
from frappe.utils import today, add_days, get_datetime

def send_sprint_digest():
    """Send daily sprint digest to team members"""
    active_sprints = frappe.get_all('Agile Sprint',
        filters={'sprint_state': 'Active'},
        fields=['name', 'project', 'sprint_name']
    )
    
    from erpnext_agile.agile_sprint_manager import AgileSprintManager
    manager = AgileSprintManager()
    
    for sprint in active_sprints:
        try:
            # Check if project has email notifications enabled
            if not frappe.db.get_value('Project', sprint.project, 'enable_email_notifications'):
                continue
            
            # Get sprint report
            report = manager.get_sprint_report(sprint.name)
            
            # Get team members
            team_members = frappe.get_all('Project User',
                filters={'parent': sprint.project},
                fields=['user'],
                pluck='user'
            )
            
            if team_members:
                # Send digest email
                frappe.sendmail(
                    recipients=team_members,
                    subject=f"Daily Sprint Digest: {sprint.sprint_name}",
                    template="agile_sprint_digest",
                    args={
                        'sprint': sprint,
                        'report': report,
                        'site_url': frappe.utils.get_url()
                    }
                )
        except Exception as e:
            frappe.log_error(f"Error sending sprint digest for {sprint.name}: {str(e)}")

def cleanup_old_timers():
    """Clean up stale work timers (running for more than 24 hours)"""
    threshold = add_days(today(), -1)
    
    stale_timers = frappe.get_all('Agile Work Timer',
        filters={
            'status': 'Running',
            'start_time': ['<', threshold]
        },
        fields=['name', 'task', 'user']
    )
    
    for timer in stale_timers:
        try:
            # Auto-stop the timer
            from erpnext_agile.agile_time_tracking import AgileTimeTracking
            tracker = AgileTimeTracking()
            
            tracker.stop_timer(timer.name, work_description="Auto-stopped after 24 hours")
            
            # Notify user
            frappe.sendmail(
                recipients=[timer.user],
                subject="Work Timer Auto-Stopped",
                message=f"Your work timer for task {timer.task} was automatically stopped after running for 24 hours.",
                delayed=False
            )
        except Exception as e:
            frappe.log_error(f"Error cleaning up timer {timer.name}: {str(e)}")