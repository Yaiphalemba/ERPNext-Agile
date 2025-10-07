import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, time_diff_in_seconds, get_datetime
import json

class AgileTimeTracking:
    """Core class for Jira-style time tracking and work logs"""
    
    def __init__(self):
        pass
    
    @frappe.whitelist()
    def log_work(self, task_name, time_spent, work_description, work_date=None):
        """Log work on an issue (Jira-style work log)"""
        
        task_doc = frappe.get_doc('Task', task_name)
        
        if not work_date:
            work_date = frappe.utils.today()
        
        # Convert time_spent to seconds (supports formats like "2h 30m", "1.5h", "90m")
        time_seconds = self.parse_time_spent(time_spent)
        
        # Create work log entry
        work_log = {
            'user': frappe.session.user,
            'time_spent_seconds': time_seconds,
            'time_spent_display': self.format_time_display(time_seconds),
            'work_date': work_date,
            'description': work_description,
            'logged_at': now_datetime()
        }
        
        task_doc.append('work_logs', work_log)
        
        # Update time tracking fields
        self.update_time_tracking(task_doc)
        
        task_doc.save()
        
        # Log activity
        self.log_time_tracking_activity(task_doc, 'work_logged', {
            'time_spent': time_spent,
            'description': work_description
        })
        
        return {
            'success': True,
            'time_logged': self.format_time_display(time_seconds),
            'total_time_spent': task_doc.time_spent
        }
    
    def parse_time_spent(self, time_str):
        """Parse time string to seconds"""
        # Supported formats: "2h 30m", "1.5h", "90m", "2h", "30m"
        
        total_seconds = 0
        time_str = time_str.lower().strip()
        
        # Pattern: "2h 30m"
        import re
        hours_match = re.search(r'(\d+\.?\d*)\s*h', time_str)
        minutes_match = re.search(r'(\d+\.?\d*)\s*m', time_str)
        
        if hours_match:
            hours = float(hours_match.group(1))
            total_seconds += hours * 3600
        
        if minutes_match:
            minutes = float(minutes_match.group(1))
            total_seconds += minutes * 60
        
        # If no pattern matched, try to parse as decimal hours
        if total_seconds == 0:
            try:
                hours = float(time_str.replace('h', '').replace('m', '').strip())
                total_seconds = hours * 3600
            except:
                frappe.throw(_("Invalid time format. Use formats like '2h 30m', '1.5h', or '90m'"))
        
        return int(total_seconds)
    
    def format_time_display(self, seconds):
        """Format seconds to display format (e.g., "2h 30m")"""
        if not seconds:
            return "0m"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        
        if hours > 0 and minutes > 0:
            return f"{hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h"
        else:
            return f"{minutes}m"
    
    def update_time_tracking(self, task_doc):
        """Update time tracking summary fields"""
        
        # Calculate total time spent from work logs
        total_seconds = 0
        for log in task_doc.get('work_logs', []):
            total_seconds += log.get('time_spent_seconds', 0)
        
        task_doc.time_spent = total_seconds
        
        # Update remaining estimate
        if task_doc.original_estimate:
            original_seconds = task_doc.original_estimate
            remaining = max(0, original_seconds - total_seconds)
            task_doc.remaining_estimate = remaining
    
    @frappe.whitelist()
    def update_estimate(self, task_name, estimate_type, time_value):
        """Update time estimates (original or remaining)"""
        
        task_doc = frappe.get_doc('Task', task_name)
        
        time_seconds = self.parse_time_spent(time_value)
        
        old_value = None
        if estimate_type == 'original':
            old_value = task_doc.original_estimate
            task_doc.original_estimate = time_seconds
            # Also set remaining if not set
            if not task_doc.remaining_estimate:
                task_doc.remaining_estimate = time_seconds
        elif estimate_type == 'remaining':
            old_value = task_doc.remaining_estimate
            task_doc.remaining_estimate = time_seconds
        
        task_doc.save()
        
        # Log activity
        self.log_time_tracking_activity(task_doc, 'estimate_updated', {
            'estimate_type': estimate_type,
            'old_value': self.format_time_display(old_value) if old_value else '0m',
            'new_value': self.format_time_display(time_seconds)
        })
        
        return {
            'success': True,
            'estimate_type': estimate_type,
            'new_value': self.format_time_display(time_seconds)
        }
    
    @frappe.whitelist()
    def get_time_tracking_report(self, task_name):
        """Get comprehensive time tracking report for an issue"""
        
        task_doc = frappe.get_doc('Task', task_name)
        
        # Get all work logs
        work_logs = []
        for log in task_doc.get('work_logs', []):
            work_logs.append({
                'user': log.get('user'),
                'user_fullname': frappe.db.get_value('User', log.get('user'), 'full_name'),
                'time_spent': self.format_time_display(log.get('time_spent_seconds', 0)),
                'time_spent_seconds': log.get('time_spent_seconds', 0),
                'work_date': log.get('work_date'),
                'description': log.get('description'),
                'logged_at': log.get('logged_at')
            })
        
        # Calculate summary
        total_time_spent = task_doc.time_spent or 0
        original_estimate = task_doc.original_estimate or 0
        remaining_estimate = task_doc.remaining_estimate or 0
        
        # Calculate variance
        if original_estimate > 0:
            variance = total_time_spent - original_estimate
            variance_percentage = (variance / original_estimate) * 100
        else:
            variance = 0
            variance_percentage = 0
        
        report = {
            'task': task_doc.name,
            'issue_key': task_doc.issue_key,
            'subject': task_doc.subject,
            'summary': {
                'original_estimate': self.format_time_display(original_estimate),
                'original_estimate_seconds': original_estimate,
                'time_spent': self.format_time_display(total_time_spent),
                'time_spent_seconds': total_time_spent,
                'remaining_estimate': self.format_time_display(remaining_estimate),
                'remaining_estimate_seconds': remaining_estimate,
                'variance': self.format_time_display(abs(variance)),
                'variance_seconds': variance,
                'variance_percentage': round(variance_percentage, 1),
                'is_over_estimate': variance > 0,
                'progress_percentage': (
                    (total_time_spent / original_estimate * 100) 
                    if original_estimate > 0 else 0
                )
            },
            'work_logs': work_logs,
            'total_logs': len(work_logs)
        }
        
        return report
    
    @frappe.whitelist()
    def get_team_time_report(self, project, start_date=None, end_date=None):
        """Get team time tracking report"""
        
        if not start_date:
            start_date = frappe.utils.add_days(frappe.utils.today(), -30)
        if not end_date:
            end_date = frappe.utils.today()
        
        # Get all work logs for project
        work_logs = frappe.db.sql("""
            SELECT 
                wl.user,
                wl.work_date,
                wl.time_spent_seconds,
                wl.description,
                t.name as task_name,
                t.issue_key,
                t.subject
            FROM `tabAgile Issue Work Log` wl
            INNER JOIN `tabTask` t ON wl.parent = t.name
            WHERE t.project = %s
                AND t.is_agile = 1
                AND wl.work_date BETWEEN %s AND %s
            ORDER BY wl.work_date DESC, wl.user
        """, (project, start_date, end_date), as_dict=True)
        
        # Aggregate by user
        user_summary = {}
        for log in work_logs:
            user = log['user']
            if user not in user_summary:
                user_summary[user] = {
                    'user': user,
                    'user_fullname': frappe.db.get_value('User', user, 'full_name'),
                    'total_time_seconds': 0,
                    'total_logs': 0,
                    'issues_worked_on': set()
                }
            
            user_summary[user]['total_time_seconds'] += log['time_spent_seconds']
            user_summary[user]['total_logs'] += 1
            user_summary[user]['issues_worked_on'].add(log['issue_key'])
        
        # Format user summary
        team_report = []
        for user, summary in user_summary.items():
            team_report.append({
                'user': summary['user'],
                'user_fullname': summary['user_fullname'],
                'total_time': self.format_time_display(summary['total_time_seconds']),
                'total_time_seconds': summary['total_time_seconds'],
                'total_logs': summary['total_logs'],
                'issues_count': len(summary['issues_worked_on'])
            })
        
        # Sort by total time descending
        team_report.sort(key=lambda x: x['total_time_seconds'], reverse=True)
        
        # Calculate team totals
        team_total_seconds = sum(r['total_time_seconds'] for r in team_report)
        
        return {
            'project': project,
            'start_date': start_date,
            'end_date': end_date,
            'team_members': team_report,
            'team_total': self.format_time_display(team_total_seconds),
            'team_total_seconds': team_total_seconds,
            'total_logs': sum(r['total_logs'] for r in team_report)
        }
    
    @frappe.whitelist()
    def delete_work_log(self, task_name, work_log_idx):
        """Delete a work log entry"""
        
        task_doc = frappe.get_doc('Task', task_name)
        
        # Find and remove work log
        work_logs = task_doc.get('work_logs', [])
        if work_log_idx < len(work_logs):
            deleted_log = work_logs[work_log_idx]
            task_doc.remove(deleted_log)
            
            # Update time tracking
            self.update_time_tracking(task_doc)
            task_doc.save()
            
            return {
                'success': True,
                'message': 'Work log deleted'
            }
        
        frappe.throw(_("Work log not found"))
    
    @frappe.whitelist()
    def start_timer(self, task_name):
        """Start work timer for an issue"""
        
        # Check if user already has an active timer
        active_timer = frappe.db.get_value('Agile Work Timer',
            {'user': frappe.session.user, 'status': 'Running'},
            ['name', 'task']
        )
        
        if active_timer:
            frappe.throw(_(
                "You already have an active timer running for {0}"
            ).format(active_timer[1]))
        
        # Create timer
        timer_doc = frappe.get_doc({
            'doctype': 'Agile Work Timer',
            'task': task_name,
            'user': frappe.session.user,
            'start_time': now_datetime(),
            'status': 'Running'
        })
        timer_doc.insert()
        
        return {
            'success': True,
            'timer': timer_doc.name,
            'start_time': timer_doc.start_time
        }
    
    @frappe.whitelist()
    def stop_timer(self, timer_name, work_description=''):
        """Stop work timer and log work"""
        
        timer_doc = frappe.get_doc('Agile Work Timer', timer_name)
        task_doc = frappe.get_doc('Task', timer_doc.task)
        
        if timer_doc.status != 'Running':
            frappe.throw(_("Timer is not running"))
            
        task_doc.custom_timer_status = 0
        task_doc.save()
        
        # Calculate time spent
        end_time = now_datetime()
        time_seconds = time_diff_in_seconds(end_time, get_datetime(timer_doc.start_time))
        
        # Update timer
        timer_doc.end_time = end_time
        timer_doc.time_spent_seconds = time_seconds
        timer_doc.status = 'Stopped'
        timer_doc.save()
        
        # Log work
        self.log_work(
            timer_doc.task,
            self.format_time_display(time_seconds),
            work_description or f"Work logged via timer",
            frappe.utils.today()
        )
        
        return {
            'success': True,
            'time_spent': self.format_time_display(time_seconds),
            'time_spent_seconds': time_seconds
        }
    
    def log_time_tracking_activity(self, task_doc, activity_type, data):
        """Log time tracking activity"""
        try:
            activity_doc = frappe.get_doc({
                'doctype': 'Agile Issue Activity',
                'issue': task_doc.name,
                'activity_type': activity_type,
                'user': frappe.session.user,
                'data': json.dumps(data)
            })
            activity_doc.insert()
        except:
            pass  # Fail silently