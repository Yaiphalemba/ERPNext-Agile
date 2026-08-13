# import frappe
# import json
# from collections import defaultdict


# def execute(filters=None):
#     filters = frappe._dict(filters or {})

#     columns = get_columns()

#     sprint_stats = get_project_sprints(filters)

#     if not sprint_stats:
#         return columns, []

#     task_map = get_tasks(sprint_stats)

#     populate_planned_tasks(task_map, sprint_stats)

#     populate_shifted_tasks(task_map, sprint_stats)

#     data = prepare_data(sprint_stats)

#     summary = get_summary(data)

#     chart = get_chart(data)

#     return columns, data, None, chart, summary


# # ------------------------------------------------------------------
# # Columns
# # ------------------------------------------------------------------

# def get_columns():
#     return [
#         {
#             "label": "Project",
#             "fieldname": "project",
#             "fieldtype": "Data",
#             "width": 250,
#         },
#         {
#             "label": "Sprint",
#             "fieldname": "sprint",
#             "fieldtype": "Data",
#             "width": 250,
#         },
#         {
#             "label": "Planned Tasks",
#             "fieldname": "planned_tasks",
#             "fieldtype": "Int",
#             "width": 120,
#         },
#         {
#             "label": "Planned Story Points",
#             "fieldname": "planned_story_points",
#             "fieldtype": "Float",
#             "width": 150,
#         },
#         {
#             "label": "Shifted Tasks",
#             "fieldname": "shifted_tasks",
#             "fieldtype": "Int",
#             "width": 120,
#         },
#         {
#             "label": "Shifted Story Points",
#             "fieldname": "shifted_story_points",
#             "fieldtype": "Float",
#             "width": 150,
#         },
#         {
#             "label": "Carry Forward %",
#             "fieldname": "carry_forward_percentage",
#             "fieldtype": "Percent",
#             "width": 130,
#         },
#     ]


# # ------------------------------------------------------------------
# # Fetch Project Sprints
# # ------------------------------------------------------------------

# def get_project_sprints(filters):

#     sprint_filters = {}

#     if filters.get("project"):
#         sprint_filters["project"] = filters.project

#     # Overlapping date logic
#     if filters.get("from_date"):
#         sprint_filters["end_date"] = (">=", filters.from_date)

#     if filters.get("to_date"):
#         sprint_filters["start_date"] = ("<=", filters.to_date)

#     sprints = frappe.get_all(
#         "Agile Sprint",
#         filters=sprint_filters,
#         fields=[
#             "name",
#             "project",
#             "start_date",
#             "end_date",
#         ],
#         order_by="project asc, start_date asc",
#     )

#     sprint_stats = {}

#     for sprint in sprints:

#         sprint_stats[sprint.name] = {
#             "project": sprint.project,
#             "start_date": sprint.start_date,
#             "end_date": sprint.end_date,
#             "planned_tasks": 0,
#             "planned_story_points": 0,
#             "shifted_tasks": 0,
#             "shifted_story_points": 0,
#         }

#     return sprint_stats


# # ------------------------------------------------------------------
# # Fetch Tasks
# # ------------------------------------------------------------------

# def get_tasks(sprint_stats):

#     sprint_names = list(sprint_stats.keys())

#     if not sprint_names:
#         return {}

#     tasks = frappe.get_all(
#         "Task",
#         filters={
#             "current_sprint": ["in", sprint_names]
#         },
#         fields=[
#             "name",
#             "subject",
#             "project",
#             "story_points",
#             "current_sprint",
#         ],
#     )

#     return {d.name: d for d in tasks}


# # ------------------------------------------------------------------
# # Planned Tasks
# # ------------------------------------------------------------------

# def populate_planned_tasks(task_map, sprint_stats):

#     for task in task_map.values():

#         sprint = task.current_sprint

#         if not sprint:
#             continue

#         if sprint not in sprint_stats:
#             continue

#         sprint_stats[sprint]["planned_tasks"] += 1

#         sprint_stats[sprint]["planned_story_points"] += (
#             int(task.story_points) or 0
#         )
    

# # ------------------------------------------------------------------
# # Shifted Tasks
# # ------------------------------------------------------------------

# def populate_shifted_tasks(task_map, sprint_stats):

#     versions = frappe.get_all(
#         "Version",
#         filters={
#             "ref_doctype": "Task"
#         },
#         fields=[
#             "docname",
#             "creation",
#             "data"
#         ]
#     )

#     # Avoid counting duplicate transfers of the same task
#     processed = set()

#     for version in versions:

#         if version.docname not in task_map:
#             continue

#         try:
#             data = json.loads(version.data or "{}")
#         except Exception:
#             continue

#         for change in data.get("changed", []):

#             if len(change) < 3:
#                 continue

#             field = change[0]

#             if field != "current_sprint":
#                 continue

#             old_sprint = change[1]
#             new_sprint = change[2]

#             if not old_sprint:
#                 continue

#             if old_sprint == new_sprint:
#                 continue

#             key = (version.docname, old_sprint)

#             if key in processed:
#                 continue

#             processed.add(key)

#             if old_sprint not in sprint_stats:
#                 continue

#             story_points = task_map[version.docname].story_points or 0

#             sprint_stats[old_sprint]["shifted_tasks"] += 1
#             sprint_stats[old_sprint]["shifted_story_points"] += int(story_points)


# # ------------------------------------------------------------------
# # Prepare Report Data
# # ------------------------------------------------------------------

# def prepare_data(sprint_stats):

#     project_map = defaultdict(list)

#     project_names = {
#         d.name: d.project_name
#         for d in frappe.get_all(
#             "Project",
#             fields=["name", "project_name"]
#         )
#     }

#     sprint_names = {
#         d.name: d.sprint_name if hasattr(d, "sprint_name") else d.name
#         for d in frappe.get_all(
#             "Agile Sprint",
#             fields=["name", "sprint_name"]
#         )
#     }

#     # Create sprint rows
#     for sprint, values in sprint_stats.items():

#         planned_tasks = values["planned_tasks"]
#         shifted_tasks = values["shifted_tasks"]

#         percentage = (
#             round((shifted_tasks / planned_tasks) * 100, 2)
#             if planned_tasks else 0
#         )

#         project_map[values["project"]].append({
#             "project": "",
#             "sprint": f"{sprint_names.get(sprint, sprint)} ({sprint})",
#             "indent": 1,
#             "planned_tasks": planned_tasks,
#             "planned_story_points": values["planned_story_points"],
#             "shifted_tasks": shifted_tasks,
#             "shifted_story_points": values["shifted_story_points"],
#             "carry_forward_percentage": percentage
#         })

#     rows = []

#     # Create project summary rows
#     for project in sorted(project_map.keys()):

#         sprint_rows = sorted(
#             project_map[project],
#             key=lambda x: x["sprint"]
#         )

#         total_planned = sum(r["planned_tasks"] for r in sprint_rows)
#         total_planned_sp = sum(r["planned_story_points"] for r in sprint_rows)
#         total_shifted = sum(r["shifted_tasks"] for r in sprint_rows)
#         total_shifted_sp = sum(r["shifted_story_points"] for r in sprint_rows)

#         percentage = (
#             round((total_shifted / total_planned) * 100, 2)
#             if total_planned else 0
#         )

#         rows.append({
#             "project": f"{project_names.get(project, project)} ({project})",
#             "sprint": "",
#             "indent": 0,
#             "planned_tasks": total_planned,
#             "planned_story_points": total_planned_sp,
#             "shifted_tasks": total_shifted,
#             "shifted_story_points": total_shifted_sp,
#             "carry_forward_percentage": percentage,
#             "bold": 1
#         })

#         rows.extend(sprint_rows)

#     return rows

# # ------------------------------------------------------------------
# # Summary
# # ------------------------------------------------------------------

# def get_summary(data):

#     # Exclude project rows from calculations
#     sprint_rows = [d for d in data if d.get("indent") == 1]

#     total_planned_tasks = sum(
#         d["planned_tasks"] for d in sprint_rows
#     )

#     total_shifted_tasks = sum(
#         d["shifted_tasks"] for d in sprint_rows
#     )

#     total_planned_sp = sum(
#         d["planned_story_points"] for d in sprint_rows
#     )

#     total_shifted_sp = sum(
#         d["shifted_story_points"] for d in sprint_rows
#     )

#     carry_forward = 0

#     if total_planned_tasks:
#         carry_forward = round(
#             (total_shifted_tasks / total_planned_tasks) * 100,
#             2
#         )

#     return [
#         {
#             "value": total_planned_tasks,
#             "label": "Planned Tasks",
#             "datatype": "Int",
#             "indicator": "Blue"
#         },
#         {
#             "value": total_shifted_tasks,
#             "label": "Shifted Tasks",
#             "datatype": "Int",
#             "indicator": "Red"
#         },
#         {
#             "value": total_planned_sp,
#             "label": "Planned Story Points",
#             "datatype": "Float",
#             "indicator": "Green"
#         },
#         {
#             "value": total_shifted_sp,
#             "label": "Shifted Story Points",
#             "datatype": "Float",
#             "indicator": "Orange"
#         },
#         {
#             "value": carry_forward,
#             "label": "Carry Forward %",
#             "datatype": "Percent",
#             "indicator": "Red" if carry_forward > 20 else "Orange" if carry_forward > 10 else "Green"
#         }
#     ]


# # ------------------------------------------------------------------
# # Chart
# # ------------------------------------------------------------------

# def get_chart(data):

#     sprint_rows = [d for d in data if d.get("indent") == 1]

#     return {
#         "data": {
#             "labels": [
#                 d["sprint"] for d in sprint_rows
#             ],
#             "datasets": [
#                 {
#                     "name": "Shifted Tasks",
#                     "values": [
#                         d["shifted_tasks"]
#                         for d in sprint_rows
#                     ]
#                 },
#                 {
#                     "name": "Shifted Story Points",
#                     "values": [
#                         d["shifted_story_points"]
#                         for d in sprint_rows
#                     ]
#                 }
#             ]
#         },
#         "type": "bar",
#         "height": 320
#     }






import frappe
from collections import defaultdict
from frappe.utils import flt

# ------------------------------------------------------------------
# Configuration
# Adjust these constants if your exact Doctype or fieldnames differ.
# ------------------------------------------------------------------
CHILD_TABLE_DOCTYPE = "Task Sprint History"
CHILD_SPRINT_FIELD = "sprint"


def execute(filters=None):
    filters = frappe._dict(filters or {})

    columns = get_columns()

    sprint_stats = get_project_sprints(filters)

    if not sprint_stats:
        return columns, []

    # Calculate story points dynamically from tasks & their history
    populate_story_points(sprint_stats)

    data = prepare_data(sprint_stats)

    summary = get_summary(data)

    chart = get_chart(data)

    return columns, data, None, chart, summary


# ------------------------------------------------------------------
# Columns
# ------------------------------------------------------------------

def get_columns():
    return [
        {
            "label": "Project",
            "fieldname": "project",
            "fieldtype": "Data",
            "width": 250,
        },
        {
            "label": "Sprint",
            "fieldname": "sprint",
            "fieldtype": "Data",
            "width": 250,
        },
        {
            "label": "Total Tasks",
            "fieldname": "total_tasks",
            "fieldtype": "Int",
            "width": 120,
        },
        {
            "label": "Total Story Points",
            "fieldname": "total_story_points",
            "fieldtype": "Float",
            "width": 150,
        },
        {
            "label": "Current Tasks",
            "fieldname": "current_tasks",
            "fieldtype": "Int",
            "width": 120,
        },
        {
            "label": "Current Story Points",
            "fieldname": "current_story_points",
            "fieldtype": "Float",
            "width": 150,
        },
        {
            "label": "Shifted Tasks",
            "fieldname": "shifted_tasks",
            "fieldtype": "Int",
            "width": 120,
        },
        {
            "label": "Shifted Story Points",
            "fieldname": "shifted_story_points",
            "fieldtype": "Float",
            "width": 150,
        },
        {
            "label": "Carry Forward %",
            "fieldname": "carry_forward_percentage",
            "fieldtype": "Percent",
            "width": 130,
        },
    ]


# ------------------------------------------------------------------
# Fetch Project Sprints
# ------------------------------------------------------------------

def get_project_sprints(filters):
    sprint_filters = {}

    if filters.get("project"):
        sprint_filters["project"] = filters.project

    # Overlapping date logic
    if filters.get("from_date"):
        sprint_filters["end_date"] = (">=", filters.from_date)

    if filters.get("to_date"):
        sprint_filters["start_date"] = ("<=", filters.to_date)

    sprints = frappe.get_all(
        "Agile Sprint",
        filters=sprint_filters,
        fields=[
            "name",
            "project",
            "start_date",
            "end_date",
            "custom_total_task_count",
            "custom_current_task_count",
            "custom_transferred_task_count"
        ],
        order_by="project asc, start_date asc",
    )

    sprint_stats = {}

    for sprint in sprints:
        # Relying entirely on your new custom fields for task counts
        sprint_stats[sprint.name] = {
            "project": sprint.project,
            "start_date": sprint.start_date,
            "end_date": sprint.end_date,
            "total_tasks": sprint.custom_total_task_count or 0,
            "current_tasks": sprint.custom_current_task_count or 0,
            "shifted_tasks": sprint.custom_transferred_task_count or 0,
            "total_story_points": 0.0,
            "current_story_points": 0.0,
            "shifted_story_points": 0.0,
        }

    return sprint_stats


# ------------------------------------------------------------------
# Populate Story Points
# ------------------------------------------------------------------

def populate_story_points(sprint_stats):
    sprint_names = list(sprint_stats.keys())
    if not sprint_names:
        return

    # 1. Tally Current Story Points
    current_tasks = frappe.get_all(
        "Task",
        filters={"current_sprint": ["in", sprint_names]},
        fields=["name", "current_sprint", "story_points"]
    )

    for task in current_tasks:
        sp = flt(task.story_points)
        sprint = task.current_sprint
        
        if sprint in sprint_stats:
            sprint_stats[sprint]["current_story_points"] += sp
            sprint_stats[sprint]["total_story_points"] += sp

    # 2. Tally Shifted Story Points via Child Table
    # Using raw SQL with DISTINCT to ensure we don't duplicate story points
    # if a task somehow logged the same sprint multiple times in history.
    query = f"""
        SELECT 
            DISTINCT ch.{CHILD_SPRINT_FIELD} as sprint_name, 
            ch.parent as task_name, 
            t.story_points
        FROM 
            `tab{CHILD_TABLE_DOCTYPE}` ch
        JOIN 
            `tabTask` t ON t.name = ch.parent
        WHERE 
            ch.{CHILD_SPRINT_FIELD} IN %s
    """
    
    shifted_tasks = frappe.db.sql(query, (tuple(sprint_names),), as_dict=True)

    for task in shifted_tasks:
        sp = flt(task.story_points)
        sprint = task.sprint_name
        
        if sprint in sprint_stats:
            sprint_stats[sprint]["shifted_story_points"] += sp
            sprint_stats[sprint]["total_story_points"] += sp


# ------------------------------------------------------------------
# Prepare Report Data
# ------------------------------------------------------------------

def prepare_data(sprint_stats):
    project_map = defaultdict(list)

    project_names = {
        d.name: d.project_name
        for d in frappe.get_all("Project", fields=["name", "project_name"])
    }

    sprint_names_map = {
        d.name: d.sprint_name if hasattr(d, "sprint_name") else d.name
        for d in frappe.get_all("Agile Sprint", fields=["name", "sprint_name"])
    }

    # Create sprint rows
    for sprint, values in sprint_stats.items():
        total_tasks = values["total_tasks"]
        shifted_tasks = values["shifted_tasks"]

        percentage = round((shifted_tasks / total_tasks) * 100, 2) if total_tasks else 0

        project_map[values["project"]].append({
            "project": "",
            "sprint": f"{sprint_names_map.get(sprint, sprint)} ({sprint})",
            "indent": 1,
            "total_tasks": total_tasks,
            "total_story_points": values["total_story_points"],
            "current_tasks": values["current_tasks"],
            "current_story_points": values["current_story_points"],
            "shifted_tasks": shifted_tasks,
            "shifted_story_points": values["shifted_story_points"],
            "carry_forward_percentage": percentage
        })

    rows = []

    # Create project summary rows
    for project in sorted(project_map.keys()):
        sprint_rows = sorted(project_map[project], key=lambda x: x["sprint"])

        total_tasks_sum = sum(r["total_tasks"] for r in sprint_rows)
        total_sp_sum = sum(r["total_story_points"] for r in sprint_rows)
        current_tasks_sum = sum(r["current_tasks"] for r in sprint_rows)
        current_sp_sum = sum(r["current_story_points"] for r in sprint_rows)
        shifted_tasks_sum = sum(r["shifted_tasks"] for r in sprint_rows)
        shifted_sp_sum = sum(r["shifted_story_points"] for r in sprint_rows)

        percentage = round((shifted_tasks_sum / total_tasks_sum) * 100, 2) if total_tasks_sum else 0

        rows.append({
            "project": f"{project_names.get(project, project)} ({project})",
            "sprint": "",
            "indent": 0,
            "total_tasks": total_tasks_sum,
            "total_story_points": total_sp_sum,
            "current_tasks": current_tasks_sum,
            "current_story_points": current_sp_sum,
            "shifted_tasks": shifted_tasks_sum,
            "shifted_story_points": shifted_sp_sum,
            "carry_forward_percentage": percentage,
            "bold": 1
        })

        rows.extend(sprint_rows)

    return rows


# ------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------

def get_summary(data):
    # Exclude project (summary) rows from calculations
    sprint_rows = [d for d in data if d.get("indent") == 1]

    total_tasks_sum = sum(d["total_tasks"] for d in sprint_rows)
    total_shifted_tasks = sum(d["shifted_tasks"] for d in sprint_rows)
    total_sp_sum = sum(d["total_story_points"] for d in sprint_rows)
    total_shifted_sp = sum(d["shifted_story_points"] for d in sprint_rows)

    carry_forward = 0
    if total_tasks_sum:
        carry_forward = round((total_shifted_tasks / total_tasks_sum) * 100, 2)

    return [
        {
            "value": total_tasks_sum,
            "label": "Total Tasks",
            "datatype": "Int",
            "indicator": "Blue"
        },
        {
            "value": total_shifted_tasks,
            "label": "Shifted Tasks",
            "datatype": "Int",
            "indicator": "Red"
        },
        {
            "value": total_sp_sum,
            "label": "Total Story Points",
            "datatype": "Float",
            "indicator": "Green"
        },
        {
            "value": total_shifted_sp,
            "label": "Shifted Story Points",
            "datatype": "Float",
            "indicator": "Orange"
        },
        {
            "value": carry_forward,
            "label": "Carry Forward %",
            "datatype": "Percent",
            "indicator": "Red" if carry_forward > 20 else "Orange" if carry_forward > 10 else "Green"
        }
    ]


# ------------------------------------------------------------------
# Chart
# ------------------------------------------------------------------

def get_chart(data):
    sprint_rows = [d for d in data if d.get("indent") == 1]

    return {
        "data": {
            "labels": [d["sprint"] for d in sprint_rows],
            "datasets": [
                {
                    "name": "Shifted Tasks",
                    "values": [d["shifted_tasks"] for d in sprint_rows]
                },
                {
                    "name": "Shifted Story Points",
                    "values": [d["shifted_story_points"] for d in sprint_rows]
                }
            ]
        },
        "type": "bar",
        "height": 320
    }