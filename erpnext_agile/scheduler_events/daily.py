# erpnext_agile/tasks/daily.py
import frappe
from frappe.utils import getdate, date_diff, nowdate, get_fullname
from collections import defaultdict
from frappe.utils import today, add_days, get_datetime, getdate

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

def check_overdue_flag_in_tasks():
    """Check and update the overdue flag for tasks"""
    overdue_tasks = frappe.get_all('Task',
        filters={
            'is_agile': 1,
            'exp_end_date': ['<', today()],
            'status': ["not in", ["Cancelled", "Completed"]],
            'custom_overdue': 0
        },
        fields=['name', 'status', 'review_date']
    )            
    
    for task in overdue_tasks:
        if task.status == "Pending Review":
            if getdate(task.review_date) > getdate(today()):
                continue
        try:
            frappe.db.set_value('Task', task.name, 'custom_overdue', 1)
        except Exception as e:
            frappe.log_error(f"Error updating overdue flag for task {task.name}: {str(e)}")


def process_overdue_tasks():
    today = getdate(nowdate())
    
    # Skip if today is a weekend
    if today.weekday() >= 5:
        return
        
    is_monday = (today.weekday() == 0)
    
    # Fetch Active, Overdue Tasks
    tasks = frappe.get_all(
        "Task",
        filters={
            "status": ["not in", ["Completed", "Closed", "Resolved"]],
            "exp_end_date": ["<", today]
        },
        fields=[
            "name", "subject", "exp_end_date", "status", "project",
            "current_sprint", "custom_overdue"
        ]
    )

    if not tasks:
        return

    # Queue Structure: queues[scenario][role][email] = [tasks]
    queues = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    
    senior_mgmt_emails = get_senior_management_emails()

    for task in tasks:
        # Flag task as overdue if not already flagged
        if not task.custom_overdue:
            frappe.db.set_value("Task", task.name, "custom_overdue", 1)

        # Skip if already logged today
        if frappe.db.exists("Notification Log", {"task": task.name, "date": today}):
            continue

        overdue_days = date_diff(today, task.exp_end_date)
        sprint_end = frappe.db.get_value("Agile Sprint", task.current_sprint, "end_date") if task.current_sprint else None
        is_sprint_end = (sprint_end and today == getdate(sprint_end))

        assignees = get_task_assignees(task.name)
        reporting_managers = get_reporting_managers(assignees)
        business_analysts = get_business_analysts(task.project)

        # Determine the scenario to apply the correct email template
        if is_sprint_end:
            scenario = "SPRINT_END"
            for u in assignees: queues[scenario]["Assignee"][u].append(task)
            for u in reporting_managers: queues[scenario]["Reporting Manager"][u].append(task)
            for u in business_analysts: queues[scenario]["Business Analyst"][u].append(task)
            for u in senior_mgmt_emails: queues[scenario]["Senior Management"][u].append(task)
            
        elif is_monday:
            scenario = "MONDAY"
            for u in assignees: queues[scenario]["Assignee"][u].append(task)
            for u in reporting_managers: queues[scenario]["Reporting Manager"][u].append(task)
            for u in business_analysts: queues[scenario]["Business Analyst"][u].append(task)
            
        elif overdue_days == 1:
            scenario = "DAY_1"
            for u in assignees: queues[scenario]["Assignee"][u].append(task)

        elif overdue_days == 2:
            scenario = "DAY_2"
            for u in assignees: queues[scenario]["Assignee"][u].append(task)
            for u in reporting_managers: queues[scenario]["Reporting Manager"][u].append(task)
            
        else:
            scenario = "DAILY"
            for u in assignees: queues[scenario]["Assignee"][u].append(task)

        # Log notification
        # log_notification(task.name, today)

    # Dispatch compiled emails based on templates
    dispatch_emails(queues)
    frappe.db.commit()


# --- Email Dispatch & Templating ---

def dispatch_emails(queues):
    for scenario, roles in queues.items():
        for role, user_queues in roles.items():
            for email, tasks in user_queues.items():
                if not email: 
                    continue
                
                tasks.sort(key=lambda x: getdate(x.exp_end_date))
                
                subject, html_body = build_email_template(scenario, role, email, tasks)
                
                frappe.sendmail(
                    recipients=[email], 
                    subject=subject, 
                    message=html_body, 
                    now=False
                )

def build_email_template(scenario, role, email, tasks):
    user_name = get_fullname(email) or role
    
    # Defaults
    subject = "Overdue Task Reminder"
    intro = "This is to inform you that the following task is overdue."
    footer = "The above task is still incomplete. Please review the task and take the necessary action.<br>Regards,<br>ERP System"

    # Template matching image_e1b44b.png (Sprint End Escalation)
    if scenario == "SPRINT_END":
        subject = "Overdue Task Escalation – Sprint End Date Reached"
        intro = "This is to inform you that the following task is overdue."

    # Template matching image_e1b40b.png (Monday RM/BA Reminder)
    elif scenario == "MONDAY" and role in ["Reporting Manager", "Business Analyst"]:
        subject = "Overdue Task Reminder"
        # Using exact text from your wireframe
        intro = "This is to inform you that the following task is overdue and has reached its Sprint End Date."

    # Template matching image_e2067d.png (Day 2 RM Reminder)
    elif scenario == "DAY_2" and role == "Reporting Manager":
        subject = "Overdue Task Reminder"
        intro = "This is to inform you that the following task assigned is overdue."

    elif scenario == "DAY_1" and role == "Assignee":
        subject = "Overdue Task Reminder"
        intro = "This is a reminder that the following task assigned is overdue as its expected end date has passed."

    # Template matching image_e20645.png (Assignee Reminder)
    elif role == "Assignee":
        subject = "Overdue Task Reminder"
        intro = "This is a reminder that the following task is overdue as its Expected End Date has passed:"
        footer = "Please review and complete the task at the earliest.<br>Regards,<br>ERP System"

    # Constructing the Email Body
    html = f"""
    <div style="font-family: Arial, sans-serif; font-size: 14px;">
        <p>Dear {user_name},</p>
        <p>{intro}</p>
        <br>
        <table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; width: 100%; text-align: left;">
            <tr style="background-color: #f2f2f2;">
                <th>Task_ID</th>
                <th>Task_Name</th>
                <th>Assignee</th>
                <th>Expected End Date</th>
                <th>Overdue(days)</th>
            </tr>
    """
    
    for t in tasks:
        overdue_days = date_diff(nowdate(), t.exp_end_date)
        assignees = ", ".join(get_task_assignees(t.name))
        
        # Adding Project/Sprint data as shown in wireframes above the table logic
        html_project_sprint = f"<b>Project/Sprint:</b> {t.project or ''} / {t.custom_sprint or ''}<br>"
        sprint_end = frappe.db.get_value("Agile Sprint", t.custom_sprint, "end_date") if t.custom_sprint else '-'
        html_sprint_end = f"<b>Sprint End Date:</b> {sprint_end}<br><br>"
        
        html += f"""
            <tr>
                <td><a href="{frappe.utils.get_url_to_form('Task', t.name)}">{t.name}</a></td>
                <td>{t.subject}</td>
                <td>{assignees}</td>
                <td>{t.exp_end_date}</td>
                <td style="color: red;">{overdue_days}</td>
            </tr>
        """
        
    html += f"""
        </table>
        <br>
        <p>{footer}</p>
    </div>
    """
    
    # Injecting Project/Sprint context at the top based on the first task in the list
    if tasks:
        t_first = tasks[0]
        sprint_end_val = frappe.db.get_value("Agile Sprint", t_first.custom_sprint, "end_date") if t_first.custom_sprint else '-'
        context_header = f"<b>Project/Sprint:</b> {t_first.project or '-'} / {t_first.custom_sprint or '-'}<br>"
        context_header += f"<b>Sprint End Date:</b> {sprint_end_val}<br><br>"
        
        # Insert context right after intro paragraph
        html = html.replace(f"<p>{intro}</p>", f"<p>{intro}</p>{context_header}")

    return subject, html


# --- Data Lookups ---

def get_task_assignees(task_name):
    todos = frappe.get_all("ToDo", filters={"reference_type": "Task", "reference_name": task_name, "status": "Open"}, fields=["allocated_to"])
    return [todo.allocated_to for todo in todos if todo.allocated_to]

def get_reporting_managers(assignees):
    rms = set()
    for user in assignees:
        emp = frappe.db.get_value("Employee", {"user_id": user}, ["leave_approver"], as_dict=True)
        if emp and emp.leave_approver:
            rms.add(emp.leave_approver)
    return list(rms)

def get_business_analysts(project_name):
    bas = set()
    if not project_name: return []
    project_users = frappe.get_all("Project User", filters={"parent": project_name}, fields=["user"])
    for p_user in project_users:
        if "Business Analyst" in frappe.get_roles(p_user.user):
            bas.add(p_user.user)
    return list(bas)

def get_senior_management_emails():
    users = frappe.get_all("Has Role", filters={"role": "Senior Management"}, fields=["parent"])
    return [u.parent for u in users]

# def log_notification(task_name, date):
#     if frappe.get_meta("Notification Log"):
#         doc = frappe.get_doc({"doctype": "Notification Log", "task": task_name, "date": date})
#         doc.insert(ignore_permissions=True)