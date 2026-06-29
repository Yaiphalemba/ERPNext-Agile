# Copyright (c) 2026, Yanky and contributors
# For license information, please see license.txt

import frappe
import json
from collections import defaultdict


def execute(filters=None):
    filters = frappe._dict(filters or {})

    if not filters.project:
        frappe.throw("Please select a Project.")

    columns = get_columns()

    sprint_stats = get_project_sprints(filters.project)

    if not sprint_stats:
        return columns, []

    task_map = get_project_tasks(filters.project)

    populate_planned_tasks(task_map, sprint_stats)

    populate_shifted_tasks(task_map, sprint_stats)

    data = prepare_data(sprint_stats)

    summary = get_summary(data)

    chart = get_chart(data)

    return columns, data, None, chart, summary


# --------------------------------------------------------------------
# Columns
# --------------------------------------------------------------------

def get_columns():

    return [
        {
            "label": "Sprint",
            "fieldname": "sprint",
            "fieldtype": "Link",
            "options": "Agile Sprint",
            "width": 220
        },
        {
            "label": "Planned Tasks",
            "fieldname": "planned_tasks",
            "fieldtype": "Int",
            "width": 120
        },
        {
            "label": "Planned Story Points",
            "fieldname": "planned_story_points",
            "fieldtype": "Float",
            "width": 150
        },
        {
            "label": "Shifted Tasks",
            "fieldname": "shifted_tasks",
            "fieldtype": "Int",
            "width": 120
        },
        {
            "label": "Shifted Story Points",
            "fieldname": "shifted_story_points",
            "fieldtype": "Float",
            "width": 170
        },
        {
            "label": "Carry Forward %",
            "fieldname": "carry_forward_percentage",
            "fieldtype": "Percent",
            "width": 130
        }
    ]


# --------------------------------------------------------------------
# Fetch Sprints
# --------------------------------------------------------------------

def get_project_sprints(project):

    sprints = frappe.get_all(
        "Agile Sprint",
        filters={
            "project": project
        },
        fields=[
            "name"
        ],
        order_by="start_date asc"
    )

    stats = {}

    for sprint in sprints:
        stats[sprint.name] = {
            "planned_tasks": 0,
            "planned_story_points": 0,
            "shifted_tasks": 0,
            "shifted_story_points": 0
        }

    return stats


# --------------------------------------------------------------------
# Fetch Tasks
# --------------------------------------------------------------------

def get_project_tasks(project):

    tasks = frappe.get_all(
        "Task",
        filters={
            "project": project
        },
        fields=[
            "name",
            "subject",
            "story_points",
            "current_sprint"
        ]
    )

    return {d.name: d for d in tasks}


# --------------------------------------------------------------------
# Planned Tasks
# --------------------------------------------------------------------

def populate_planned_tasks(task_map, sprint_stats):

    for task in task_map.values():

        sprint = task.current_sprint

        if not sprint:
            continue

        if sprint not in sprint_stats:
            continue

        sprint_stats[sprint]["planned_tasks"] += 1

        sprint_stats[sprint]["planned_story_points"] += (
            int(task.story_points) or 0
        )


# --------------------------------------------------------------------
# Shifted Tasks
# --------------------------------------------------------------------

def populate_shifted_tasks(task_map, sprint_stats):

    versions = frappe.get_all(
        "Version",
        filters={
            "ref_doctype": "Task"
        },
        fields=[
            "docname",
            "creation",
            "data"
        ]
    )

    for version in versions:

        if version.docname not in task_map:
            continue

        try:
            data = json.loads(version.data or "{}")
        except Exception:
            continue

        changes = data.get("changed", [])

        for change in changes:

            if len(change) < 3:
                continue

            field = change[0]

            if field != "current_sprint":
                continue

            old_sprint = change[1]
            new_sprint = change[2]

            if not old_sprint:
                continue

            if old_sprint == new_sprint:
                continue

            if old_sprint not in sprint_stats:
                continue

            story_points = task_map[version.docname].story_points or 0

            sprint_stats[old_sprint]["shifted_tasks"] += 1

            sprint_stats[old_sprint]["shifted_story_points"] += int(story_points)


# --------------------------------------------------------------------
# Data
# --------------------------------------------------------------------

def prepare_data(stats):

    data = []

    for sprint, values in stats.items():

        planned = values["planned_tasks"]

        shifted = values["shifted_tasks"]

        if planned:
            percent = (shifted / planned) * 100
        else:
            percent = 0

        data.append(
            {
                "sprint": sprint,
                "planned_tasks": planned,
                "planned_story_points": values["planned_story_points"],
                "shifted_tasks": shifted,
                "shifted_story_points": values["shifted_story_points"],
                "carry_forward_percentage": round(percent, 2)
            }
        )

    return data


# --------------------------------------------------------------------
# Summary
# --------------------------------------------------------------------

def get_summary(data):

    planned_tasks = sum(d["planned_tasks"] for d in data)

    shifted_tasks = sum(d["shifted_tasks"] for d in data)

    planned_sp = sum(d["planned_story_points"] for d in data)

    shifted_sp = sum(d["shifted_story_points"] for d in data)

    percent = 0

    if planned_tasks:
        percent = round((shifted_tasks / planned_tasks) * 100, 2)

    return [

        {
            "value": planned_tasks,
            "label": "Planned Tasks",
            "datatype": "Int"
        },

        {
            "value": shifted_tasks,
            "label": "Tasks Shifted",
            "datatype": "Int",
            "indicator": "Red"
        },

        {
            "value": planned_sp,
            "label": "Planned Story Points",
            "datatype": "Float"
        },

        {
            "value": shifted_sp,
            "label": "Story Points Shifted",
            "datatype": "Float",
            "indicator": "Orange"
        },

        {
            "value": percent,
            "label": "Carry Forward %",
            "datatype": "Percent",
            "indicator": "Red"
        }

    ]


# --------------------------------------------------------------------
# Chart
# --------------------------------------------------------------------

def get_chart(data):

    return {
        "data": {
            "labels": [d["sprint"] for d in data],
            "datasets": [
                {
                    "name": "Shifted Tasks",
                    "values": [d["shifted_tasks"] for d in data]
                }
            ]
        },
        "type": "bar",
        "height": 300
    }