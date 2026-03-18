# erpnext_agile/erpnext_agile/report/project_analysis_report/project_analysis_report.py
#
# Project Analysis Report
# =======================
# Leaderboard for employee performance based on agile task completion.
#
# Performance Score = weighted_story_points × (1 + completion_rate × 0.2)
#   - weighted_story_points : story_points × (contribution% / 100)
#                             falls back to equal split if contribution% not set
#   - completion_rate        : tasks_completed ÷ total_assigned_tasks (0–1)
#   - The 0.2 multiplier gives up to a 20% bonus for fully completing tasks
#
# Columns:
#   - Total Tasks          → ALL tasks in the project/sprint (incl. unassigned)
#   - Total Assigned Tasks → tasks the specific user is assigned to

import frappe
from frappe import _
from frappe.utils import flt
from collections import defaultdict


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

def execute(filters=None):
    filters = filters or {}
    _validate_filters(filters)
    columns          = get_columns(filters)
    data, chart_data = get_data(filters)
    chart            = _build_chart(chart_data)
    summary          = _build_summary(data)
    return columns, data, None, chart, summary


# ─────────────────────────────────────────────
# VALIDATION
# ─────────────────────────────────────────────

def _validate_filters(filters):
    if filters.get("from_date") and filters.get("to_date"):
        if filters["from_date"] > filters["to_date"]:
            frappe.throw(_("From Date cannot be greater than To Date"))


# ─────────────────────────────────────────────
# COLUMNS
# ─────────────────────────────────────────────

def get_columns(filters):
    return [
        {"label": _("Rank"),                 "fieldname": "rank",                 "fieldtype": "Data",    "width": 70},
        {"label": _("Employee"),             "fieldname": "user",                 "fieldtype": "Link",    "options": "User", "width": 220},
        {"label": _("Full Name"),            "fieldname": "full_name",            "fieldtype": "Data",    "width": 160},
        {"label": _("Project(s)"),           "fieldname": "project_display",      "fieldtype": "Data",    "width": 210},
        {"label": _("Total Tasks"),          "fieldname": "project_total_tasks",  "fieldtype": "Int",     "width": 110},
        {"label": _("Total Assigned Tasks"), "fieldname": "total_assigned_tasks", "fieldtype": "Int",     "width": 140},
        {"label": _("Completed"),            "fieldname": "tasks_completed",      "fieldtype": "Int",     "width": 110},
        {"label": _("In Progress"),          "fieldname": "tasks_in_progress",    "fieldtype": "Int",     "width": 110},
        {"label": _("Raw Story Pts"),        "fieldname": "raw_story_points",     "fieldtype": "Float",   "precision": 1, "width": 130},
        {"label": _("Weighted Pts"),         "fieldname": "weighted_points",      "fieldtype": "Float",   "precision": 2, "width": 130},
        {"label": _("Avg Contribution %"),   "fieldname": "avg_contribution_pct", "fieldtype": "Percent", "width": 140},
        {"label": _("Avg Pts / Task"),       "fieldname": "avg_points_per_task",  "fieldtype": "Float",   "precision": 2, "width": 120},
        {"label": _("Completion Rate"),      "fieldname": "completion_rate",      "fieldtype": "Percent", "width": 130},
        {"label": _("Performance Score"),    "fieldname": "performance_score",    "fieldtype": "Float",   "precision": 2, "width": 150},
    ]


# ─────────────────────────────────────────────
# DATA PIPELINE
# ─────────────────────────────────────────────

def get_data(filters):
    tasks = _fetch_tasks(filters)
    if not tasks:
        return [], _empty_chart()

    task_map   = {t["task_name"]: t for t in tasks}
    task_names = list(task_map.keys())

    # Total task count per project (ALL tasks, incl. unassigned)
    project_totals = _fetch_project_task_counts(filters)

    assignees = _fetch_assignees(task_names, filters.get("employee"))
    if not assignees:
        return [], _empty_chart()

    view = filters.get("view", "Overall")

    if view == "Per Project":
        return _build_per_project(assignees, task_map, project_totals, filters)
    else:
        return _build_overall(assignees, task_map, project_totals, filters)


# ─────────────────────────────────────────────
# SQL HELPERS
# ─────────────────────────────────────────────

def _build_conditions(filters, table_alias="t"):
    """Shared WHERE conditions used by both task queries."""
    conditions = [f"{table_alias}.is_agile = 1"]
    values = {}

    if filters.get("project"):
        conditions.append(f"{table_alias}.project = %(project)s")
        values["project"] = filters["project"]

    if filters.get("sprint"):
        conditions.append(f"{table_alias}.current_sprint = %(sprint)s")
        values["sprint"] = filters["sprint"]

    if filters.get("from_date"):
        conditions.append(f"DATE({table_alias}.modified) >= %(from_date)s")
        values["from_date"] = filters["from_date"]

    if filters.get("to_date"):
        conditions.append(f"DATE({table_alias}.modified) <= %(to_date)s")
        values["to_date"] = filters["to_date"]

    return conditions, values


def _fetch_tasks(filters):
    """
    Returns only tasks that have at least one assignee.
    story_points is a Select field (string) → cast to UNSIGNED.
    """
    conditions, values = _build_conditions(filters)
    conditions.append(
        "EXISTS (SELECT 1 FROM `tabAssigned To Users` atu_check WHERE atu_check.parent = t.name)"
    )
    where = " AND ".join(conditions)

    return frappe.db.sql(f"""
        SELECT
            t.name                                                        AS task_name,
            t.project,
            CAST(COALESCE(NULLIF(t.story_points, ''), '0') AS UNSIGNED)  AS story_points,
            t.status                                                      AS task_status,
            COALESCE(ais.status_category, 'To Do')                       AS status_category,
            (
                SELECT COUNT(DISTINCT a2.user)
                FROM `tabAssigned To Users` a2
                WHERE a2.parent = t.name
            )                                                             AS assignee_count,
            CASE
                WHEN t.status = 'Completed'
                     OR COALESCE(ais.status_category, '') = 'Done'        THEN 'completed'
                WHEN t.status IN ('Working', 'Pending Review')            THEN 'in_progress'
                ELSE 'open'
            END                                                           AS derived_status
        FROM `tabTask` t
        LEFT JOIN `tabAgile Issue Status` ais ON ais.name = t.issue_status
        WHERE {where}
    """, values, as_dict=True)


def _fetch_project_task_counts(filters):
    """
    Count ALL agile tasks per project matching the same filters,
    regardless of whether they are assigned to anyone.
    Returns: {project: total_task_count}
    """
    conditions, values = _build_conditions(filters)
    where = " AND ".join(conditions)

    rows = frappe.db.sql(f"""
        SELECT
            t.project,
            COUNT(t.name) AS total_tasks
        FROM `tabTask` t
        WHERE {where}
        GROUP BY t.project
    """, values, as_dict=True)

    return {r["project"]: r["total_tasks"] for r in rows}


def _fetch_assignees(task_names, employee_filter=None):
    """Fetch all (task → user) pairs for the given task list."""
    if not task_names:
        return []

    placeholders = ", ".join(["%s"] * len(task_names))
    rows = frappe.db.sql(f"""
        SELECT
            atu.parent                          AS task_name,
            atu.user,
            atu.custom_percentage_              AS custom_percentage_,
            COALESCE(u.full_name, atu.user)     AS full_name
        FROM `tabAssigned To Users` atu
        INNER JOIN `tabUser` u ON u.name = atu.user
        WHERE atu.parent IN ({placeholders})
        ORDER BY atu.parent, atu.user
    """, tuple(task_names), as_dict=True)

    if employee_filter:
        rows = [r for r in rows if r["user"] == employee_filter]

    return rows


# ─────────────────────────────────────────────
# AGGREGATION
# ─────────────────────────────────────────────

def _aggregate(assignees, task_map):
    """
    Returns nested dict: {user: {project: stats_dict}}

    stats_dict keys:
        full_name, tasks_completed, tasks_in_progress, total_assigned_tasks,
        raw_story_points, weighted_points, contribution_pct_sum
    """
    result = defaultdict(lambda: defaultdict(lambda: {
        "full_name":             "",
        "tasks_completed":       0,
        "tasks_in_progress":     0,
        "total_assigned_tasks":  0,
        "raw_story_points":      0.0,
        "weighted_points":       0.0,
        "contribution_pct_sum":  0.0,
    }))

    for row in assignees:
        task = task_map.get(row["task_name"])
        if not task:
            continue

        user    = row["user"]
        project = task["project"]
        s       = result[user][project]

        s["full_name"] = row["full_name"]

        sp = flt(task["story_points"]) or 0

        # Use custom_percentage_ if set, otherwise fall back to equal split
        raw_pct = flt(row.get("custom_percentage_"))
        if raw_pct and raw_pct > 0:
            contrib = raw_pct / 100.0
        else:
            n       = max(int(task["assignee_count"] or 1), 1)
            contrib = 1.0 / n

        s["total_assigned_tasks"]  += 1
        s["raw_story_points"]      += sp
        s["weighted_points"]       += sp * contrib
        s["contribution_pct_sum"]  += contrib * 100

        ds = task["derived_status"]
        if ds == "completed":
            s["tasks_completed"]   += 1
        elif ds == "in_progress":
            s["tasks_in_progress"] += 1

    return result


# ─────────────────────────────────────────────
# ROW BUILDERS
# ─────────────────────────────────────────────

def _calc_performance(s):
    """
    Performance Score = weighted_points × (1 + completion_rate × 0.2)
    Uses total_assigned_tasks as the denominator — fair per-user metric.
    """
    total = s["total_assigned_tasks"]
    tc    = s["tasks_completed"]
    wp    = flt(s["weighted_points"])

    completion_rate = tc / total if total > 0 else 0
    return round(wp * (1 + completion_rate * 0.2), 2)


def _make_row(rank, user, project_display, s, project_total_tasks=0, indent=0):
    tc     = s["tasks_completed"]
    tip    = s["tasks_in_progress"]
    total  = s["total_assigned_tasks"]
    wp     = flt(s["weighted_points"])
    rsp    = flt(s["raw_story_points"])
    csum   = flt(s["contribution_pct_sum"])

    avg_contrib = round(csum / total, 1)       if total > 0 else 0
    avg_pts     = round(wp / tc, 2)            if tc > 0    else round(wp / total, 2) if total > 0 else 0
    comp_rate   = round((tc / total) * 100, 1) if total > 0 else 0
    perf_score  = _calc_performance(s)

    return {
        "rank":                 f"#{rank}" if rank else "",
        "user":                 user,
        "full_name":            s.get("full_name", ""),
        "project_display":      project_display,
        "project_total_tasks":  project_total_tasks,
        "total_assigned_tasks": total,
        "tasks_completed":      tc,
        "tasks_in_progress":    tip,
        "raw_story_points":     round(rsp, 1),
        "weighted_points":      round(wp, 2),
        "avg_contribution_pct": avg_contrib,
        "avg_points_per_task":  avg_pts,
        "completion_rate":      comp_rate,
        "performance_score":    perf_score,
        "indent":               indent,
    }


def _section_header(label, project_display=""):
    """Bold section separator row (no data cells)."""
    return {
        "rank":                 "",
        "user":                 label,
        "full_name":            "",
        "project_display":      project_display,
        "project_total_tasks":  None,
        "total_assigned_tasks": None,
        "tasks_completed":      None,
        "tasks_in_progress":    None,
        "raw_story_points":     None,
        "weighted_points":      None,
        "avg_contribution_pct": None,
        "avg_points_per_task":  None,
        "completion_rate":      None,
        "performance_score":    None,
        "bold":                 1,
        "indent":               0,
    }


# ─────────────────────────────────────────────
# VIEW BUILDERS
# ─────────────────────────────────────────────

def _build_overall(assignees, task_map, project_totals, filters):
    """Single ranked list, aggregated across all projects."""
    user_proj_stats = _aggregate(assignees, task_map)

    # Collapse projects → per-user totals
    overall = {}
    for user, proj_map in user_proj_stats.items():
        agg = {
            "full_name":             "",
            "tasks_completed":       0,
            "tasks_in_progress":     0,
            "total_assigned_tasks":  0,
            "raw_story_points":      0.0,
            "weighted_points":       0.0,
            "contribution_pct_sum":  0.0,
            "projects":              set(),
        }
        for project, s in proj_map.items():
            agg["full_name"]             = s["full_name"] or agg["full_name"]
            agg["tasks_completed"]       += s["tasks_completed"]
            agg["tasks_in_progress"]     += s["tasks_in_progress"]
            agg["total_assigned_tasks"]  += s["total_assigned_tasks"]
            agg["raw_story_points"]      += s["raw_story_points"]
            agg["weighted_points"]       += s["weighted_points"]
            agg["contribution_pct_sum"]  += s["contribution_pct_sum"]
            agg["projects"].add(project)
        overall[user] = agg

    sorted_users = sorted(
        overall.items(),
        key=lambda x: _calc_performance(x[1]),
        reverse=True,
    )

    data, labels, values = [], [], []

    for rank, (user, agg) in enumerate(sorted_users, 1):
        projects        = agg["projects"]
        project_display = filters.get("project") or ", ".join(sorted(projects))

        # Sum total tasks across all projects this user belongs to
        proj_total = sum(project_totals.get(p, 0) for p in projects)

        row = _make_row(rank, user, project_display, agg, project_total_tasks=proj_total)
        data.append(row)

        if rank <= 10:
            labels.append(agg["full_name"] or user)
            values.append(row["performance_score"])

    chart_data = {
        "labels":   labels,
        "datasets": [{"name": _("Performance Score"), "values": values}],
    }
    return data, chart_data


def _build_per_project(assignees, task_map, project_totals, filters):
    """
    Grouped view: one section per project, ranked within each project.
    Chart shows top performer score per project.
    """
    user_proj_stats = _aggregate(assignees, task_map)

    # Pivot to {project: {user: stats}}
    proj_users = defaultdict(dict)
    for user, proj_map in user_proj_stats.items():
        for project, s in proj_map.items():
            proj_users[project][user] = s

    data, labels, values = [], [], []

    for project in sorted(proj_users.keys()):
        users       = proj_users[project]
        proj_total  = project_totals.get(project, 0)

        ranked = sorted(
            users.items(),
            key=lambda x: _calc_performance(x[1]),
            reverse=True,
        )

        total_assigned  = sum(s["total_assigned_tasks"] for _, s in ranked)
        total_completed = sum(s["tasks_completed"] for _, s in ranked)
        total_wp        = sum(flt(s["weighted_points"]) for _, s in ranked)

        data.append(_section_header(
            f"📁  {project}  "
            f"({proj_total} total tasks · {total_assigned} assigned · "
            f"{total_completed} completed · {round(total_wp, 1)} pts)",
            project,
        ))

        for rank, (user, s) in enumerate(ranked, 1):
            row = _make_row(rank, user, project, s, project_total_tasks=proj_total, indent=1)
            data.append(row)

            if rank == 1:
                labels.append(f"{s['full_name'] or user}\n({project})")
                values.append(row["performance_score"])

    chart_data = {
        "labels":   labels,
        "datasets": [{"name": _("Top Performer Score per Project"), "values": values}],
    }
    return data, chart_data


# ─────────────────────────────────────────────
# CHART & SUMMARY
# ─────────────────────────────────────────────

def _empty_chart():
    return {
        "labels":   [],
        "datasets": [{"name": _("Performance Score"), "values": []}],
    }


def _build_chart(chart_data):
    if not chart_data.get("labels"):
        return None
    return {
        "data":        chart_data,
        "type":        "bar",
        "title":       _("Performance Score Leaderboard"),
        "colors":      ["#5E64FF"],
        "height":      280,
        "barOptions":  {"spaceRatio": 0.4},
        "axisOptions": {"xAxisMode": "tick", "yAxisMode": "tick"},
    }


def _build_summary(data):
    rows = [r for r in data if r.get("user") and not r.get("bold") and r.get("performance_score") is not None]
    if not rows:
        return []

    total_completed = sum(r.get("tasks_completed") or 0 for r in rows)
    total_wp        = sum(flt(r.get("weighted_points")) for r in rows)
    top             = max(rows, key=lambda x: flt(x.get("performance_score")))

    return [
        {
            "value":     len(rows),
            "label":     _("Total Contributors"),
            "datatype":  "Int",
            "indicator": "blue",
        },
        {
            "value":     total_completed,
            "label":     _("Tasks Completed"),
            "datatype":  "Int",
            "indicator": "green",
        },
        {
            "value":     round(total_wp, 1),
            "label":     _("Total Weighted Points"),
            "datatype":  "Float",
            "indicator": "purple",
        },
        {
            "value":     top.get("full_name") or top.get("user", ""),
            "label":     _("Top Performer"),
            "datatype":  "Data",
            "indicator": "orange",
        },
    ]