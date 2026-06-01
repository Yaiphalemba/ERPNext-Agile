import frappe
import requests
import json
import time
import re
from frappe.utils import getdate, now_datetime, get_datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from frappe.utils.nestedset import rebuild_tree

try:
    from rq import get_current_job as _rq_get_current_job
except ImportError:
    _rq_get_current_job = None


CHILD_TABLE_FIELDS = {
    "assigned_to_users": "user",
    "watchers": "user",
    "custom_components": "component",
    "custom_labels": "label",
    "custom_fix_versions": "version",
    "custom_affect_versions": "version",
    "depends_on": "task",
}

def _table_signature(rows, key):
    sig = []
    for row in rows or []:
        if isinstance(row, dict):
            val = row.get(key)
        else:
            val = getattr(row, key, None)
        if val:
            sig.append(str(val).strip())
    return sorted(set(sig))

def _get_changes(doc, incoming):
    changes = {}
    for field, value in incoming.items():
        current = doc.get(field)
        if field in CHILD_TABLE_FIELDS:
            key = CHILD_TABLE_FIELDS[field]
            if _table_signature(current, key) != _table_signature(value, key):
                changes[field] = value
        else:
            if json.dumps(current, sort_keys=True, default=str) != json.dumps(value, sort_keys=True, default=str):
                changes[field] = value
    return changes


# ──────────────────────────────────────────────
# RQ JOB PROGRESS HELPERS
# ──────────────────────────────────────────────

def _get_rq_job():
    """Safely retrieve the current RQ job (None outside worker context)."""
    if not _rq_get_current_job:
        return None
    try:
        return _rq_get_current_job()
    except Exception:
        return None

def _fetch_rq_job_by_id(job_id):
    """Fetch a stored RQ job by ID for read-only progress inspection."""
    try:
        from rq.job import Job
        try:
            from frappe.utils.background_jobs import get_redis_conn
        except ImportError:
            from frappe.utils.background_jobs import get_redis_connection as get_redis_conn
        return Job.fetch(job_id, connection=get_redis_conn())
    except Exception:
        return None


# ──────────────────────────────────────────────
# CONNECTION
# ──────────────────────────────────────────────

@frappe.whitelist()
def verify_connection():
    settings = frappe.get_single("Jira Data Migration Tool")
    domain = settings.jira_domain
    email  = settings.jira_email
    token  = settings.jira_api_token
    url    = f"{domain}/rest/api/2/myself"

    base_headers = {"Accept": "application/json", "Content-Type": "application/json"}

    def parse_response(res):
        if not res.text.strip():
            raise Exception("Empty response from Jira")
        if "html" in res.text.lower():
            raise Exception("Got HTML → SSO or auth issue")
        data = res.json()
        if isinstance(data, str):
            data = json.loads(data)
        return data

    def extract_user(data):
        return (
            data.get("displayName") or data.get("emailAddress")
            or data.get("name")    or data.get("accountId")
            or "Unknown User"
        )

    try:
        res = None
        if "atlassian.net" in domain:
            res = requests.get(url, headers=base_headers, auth=(email, token))
        else:
            headers = {**base_headers, "Authorization": f"Bearer {token}"}
            res = requests.get(url, headers=headers)
            if res.status_code == 401:
                res = requests.get(url, headers=base_headers, auth=(email, token))

        if res.status_code == 401:
            frappe.throw("❌ 401 Unauthorized → Invalid credentials or SSO blocking API")

        user = extract_user(parse_response(res))
        settings.is_active     = 1
        settings.connected_user = user
        settings.save(ignore_permissions=True)
        return f"✅ Connected as {user}"

    except Exception as e:
        frappe.log_error(
            f"URL: {url}\nSTATUS: {res.status_code if res else 'N/A'}\nERROR: {str(e)}",
            "Jira Connection Debug"
        )
        settings.is_active = 0
        settings.save(ignore_permissions=True)
        frappe.throw(f"❌ Connection failed: {str(e)}")


# ──────────────────────────────────────────────
# MIGRATION ENTRY POINTS
# ──────────────────────────────────────────────

@frappe.whitelist()
def start_migration(project_key):
    # Reset control state
    frappe.cache().hset(f"jira_migration_control_{project_key}", "state", "running")

    # Initialize the reliable cache state manually before the worker even starts
    initial_state = {
        "project_key": project_key,
        "status": "running",
        "phase": "Queued in Background...",
        "percent": 0.0,
        "processed": 0,
        "failed": 0,
        "total": 0,
        "start_time": str(now_datetime()),
        "last_heartbeat": str(now_datetime())
    }
    frappe.cache().set_value(f"jira_migration_state_{project_key}", initial_state, expires_in_sec=86400)

    frappe.enqueue(
        'erpnext_agile.jira_sync.run_migration_engine',
        queue='long', timeout=7200,
        project_key=project_key
    )
    
    return "Migration started in background"


# ──────────────────────────────────────────────
# FIELD HELPERS
# ──────────────────────────────────────────────

def resolve_dynamic_fields(fields, names_map):
    rev_map = {str(v).lower().strip(): k for k, v in names_map.items()}
    
    epic_field_key = rev_map.get("epic link", "")
    epic_val = fields.get("customfield_10110") or (fields.get(epic_field_key) if epic_field_key else None)
    
    if isinstance(epic_val, dict):
        epic_val = epic_val.get("key") or epic_val.get("value")
        
    parent_field_key = rev_map.get("parent link", "")
    parent_val = fields.get(parent_field_key) if parent_field_key else None
    
    if isinstance(parent_val, dict):
        parent_val = parent_val.get("key")

    return {
        "sprint_data":  fields.get(rev_map.get("sprint", "")),
        "story_points": fields.get(
            rev_map.get("story points", "")
            or rev_map.get("original story points", "")
            or rev_map.get("story point estimate", "")
        ),
        "epic_link":    epic_val,
        "parent_link":  parent_val,
        "target_start": fields.get(rev_map.get("target start", "")),
        "target_end":   fields.get(rev_map.get("target end", "")),
    }


def format_time(secs):
    if not secs:
        return None
    try:
        secs = int(secs)
        h, m = secs // 3600, (secs % 3600) // 60
        return f"{h}h {m}m" if m else f"{h}h"
    except Exception:
        return None


def extract_description(desc):
    if not desc:
        return ""
    if isinstance(desc, str):
        return desc
    if isinstance(desc, dict) and desc.get("type") == "doc":
        return _adf_to_html(desc)
    return str(desc)


def _adf_to_html(node):
    if not node:
        return ""
    node_type  = node.get("type", "")
    content    = node.get("content", [])
    text       = node.get("text", "")
    attrs      = node.get("attrs", {})
    child_html = "".join(_adf_to_html(c) for c in content)

    mapping = {
        "doc":        child_html,
        "paragraph":  f"<p>{child_html}</p>",
        "text":       _apply_adf_marks(text, node.get("marks", [])),
        "bulletList": f"<ul>{child_html}</ul>",
        "orderedList":f"<ol>{child_html}</ol>",
        "listItem":   f"<li>{child_html}</li>",
        "heading":    f"<h{attrs.get('level', 2)}>{child_html}</h{attrs.get('level', 2)}>",
        "codeBlock":  f"<pre><code>{child_html}</code></pre>",
        "blockquote": f"<blockquote>{child_html}</blockquote>",
        "hardBreak":  "<br>",
        "rule":       "<hr>",
        "mention":    f"@{attrs.get('text', attrs.get('id', ''))}",
        "inlineCard": f'<a href="{attrs.get("url", "")}">{attrs.get("url", "")}</a>',
    }
    return mapping.get(node_type, child_html or text)


def _apply_adf_marks(text, marks):
    for mark in marks:
        t = mark.get("type", "")
        if   t == "strong":    text = f"<strong>{text}</strong>"
        elif t == "em":        text = f"<em>{text}</em>"
        elif t == "code":      text = f"<code>{text}</code>"
        elif t == "underline": text = f"<u>{text}</u>"
        elif t == "strike":    text = f"<s>{text}</s>"
        elif t == "link":
            href = mark.get("attrs", {}).get("href", "")
            text = f'<a href="{href}">{text}</a>'
    return text


# ──────────────────────────────────────────────
# TASK BUILDER
# ──────────────────────────────────────────────

def build_task_dict_from_jira(issue, domain, auth, names_map):
    fields   = issue.get("fields", {})
    jira_key = issue.get("key")

    proj_name   = resolve_project(fields.get("project"))
    dyn         = resolve_dynamic_fields(fields, names_map)
    sprint_name = resolve_sprint(dyn["sprint_data"], proj_name)

    fix_versions_table    = resolve_version_table(fields.get("fixVersions"), proj_name)
    affect_versions_table = resolve_version_table(fields.get("versions"),    proj_name)
    components_table      = resolve_components(fields.get("components"))
    labels_table          = resolve_labels(fields.get("labels"))

    creator_email  = (fields.get("creator")  or {}).get("emailAddress", "Administrator")
    assignee_email = (fields.get("assignee") or {}).get("emailAddress")

    issue_type   = (fields.get("issuetype") or {}).get("name", "Task")
    is_parent    = 1 if issue_type == "Epic" else 0
    resolution_val = (fields.get("resolution") or {}).get("name", "Unresolved")

    jira_status_raw = (fields.get("status") or {}).get("name", "Open")
    mapped_status   = _map_jira_status(jira_status_raw)

    completed_on = completed_by = None
    if mapped_status == "Completed":
        res_date = fields.get("resolutiondate")
        if res_date:
            completed_on = getdate(res_date[:10])
            completed_by = resolve_user(assignee_email or creator_email)

    t_start = dyn.get("target_start")
    t_end   = dyn.get("target_end")
    final_start = getdate(t_start[:10]) if t_start else (
        getdate(fields.get("created")[:10]) if fields.get("created") else None
    )
    final_end = getdate(t_end[:10]) if t_end else (
        getdate(fields.get("duedate")[:10]) if fields.get("duedate") else None
    )

    orig_est       = fields.get("timeoriginalestimate") or 0
    rem_est        = fields.get("timeestimate")         or 0
    time_spent     = fields.get("timespent")            or 0
    agg_time_spent = fields.get("aggregatetimespent")   or 0

    depends_on = resolve_issue_links(fields.get("issuelinks", []), jira_key)

    task_payload = {
        "doctype":   "Task",
        "is_agile":  1,
        "issue_key": jira_key,
        "subject":   str(fields.get("summary") or "Untitled")[:140],
        "status":    mapped_status,
        "description": extract_description(fields.get("description")),
        "project":     proj_name,
        "current_sprint": sprint_name,

        "custom_fix_version":    fix_versions_table[0]["version"] if fix_versions_table else None,
        "custom_affect_version": affect_versions_table[0]["version"] if affect_versions_table else None,
        "custom_fix_versions":    fix_versions_table,
        "custom_affect_versions": affect_versions_table,
        "custom_components":      components_table,
        "custom_labels":          labels_table,

        "assigned_to_users": [{"user": resolve_user(assignee_email)}] if assignee_email else [],
        "watchers":          [],

        "custom_original_owner": resolve_user(creator_email),
        "story_points":          parse_story_points(dyn.get("story_points")),

        "original_estimate":              orig_est,
        "custom_original_estimated_time": format_time(orig_est),
        "remaining_estimate":             rem_est,
        "custom_remaining_estimated_time":format_time(rem_est),
        "time_spent":                     time_spent,
        "custom_total_time_spent":        format_time(agg_time_spent),

        "exp_start_date":         final_start,
        "custom_actual_start_date": getdate(fields.get("created")[:10]) if fields.get("created") else None,
        "exp_end_date":           final_end,

        "completed_on":   completed_on,
        "completed_by":   completed_by,
        "is_group":       is_parent,
        "issue_type":     issue_type,
        "issue_priority": (fields.get("priority") or {}).get("name", "Medium"),
        "issue_status":   jira_status_raw,
        "custom_resolution": map_resolution(resolution_val),

        "depends_on": depends_on,
    }

    attachments = fields.get("attachment", [])
    worklogs    = fields.get("worklog", {}).get("worklogs", [])

    return task_payload, dyn, attachments, worklogs


def _map_jira_status(raw):
    s = raw.lower()
    if s in ["done", "completed", "resolved", "closed", "verified"]:
        return "Completed"
    if s in ["in progress", "working", "in review", "active"]:
        return "Working"
    if s in ["cancelled", "won't do", "duplicate", "rejected"]:
        return "Cancelled"
    return "Open"


# ──────────────────────────────────────────────
# THE MIGRATION ENGINE (STATE MACHINE)
# ──────────────────────────────────────────────
def pulse_worker(project_key, phase_text=None, percent=None):
    """Pings the cache to keep the heartbeat alive and update the UI phase dynamically."""
    if not project_key:
        return
    state_key = f"jira_migration_state_{project_key}"
    state = frappe.cache().get_value(state_key)
    if state:
        state["last_heartbeat"] = str(now_datetime())
        if phase_text:
            state["phase"] = phase_text
        if percent is not None:
            state["percent"] = percent
        frappe.cache().set_value(state_key, state, expires_in_sec=86400)


def run_migration_engine(project_key):
    settings = frappe.get_single("Jira Data Migration Tool")
    if not settings.is_active:
        frappe.throw("Jira integration is not active.")

    jira_domain = settings.jira_domain
    auth        = (settings.jira_email, settings.jira_api_token)
    headers     = {"Accept": "application/json"}

    redis_hierarchy_key = f"jira_hierarchy_{project_key}"
    failure_key         = f"jira_migration_failures_{project_key}"

    frappe.cache().delete_value(redis_hierarchy_key)
    frappe.cache().delete_value(failure_key)

    # ── Local counters ──
    processed  = 0
    failed     = 0
    total      = 0
    start_time = str(now_datetime())

    def save_progress(status="running", phase="Initializing...", percent=0.0):
        """Write precise states directly to Frappe Cache, skipping RQ meta."""
        state = {
            "project_key":    project_key,
            "processed":      processed,
            "failed":         failed,
            "total":          total,
            "status":         status,
            "phase":          phase,
            "percent":        percent,
            "start_time":     start_time,
            "last_heartbeat": str(now_datetime()),
        }
        # Dump it straight to Redis where it can't be touched by the worker crashing
        frappe.cache().set_value(f"jira_migration_state_{project_key}", state, expires_in_sec=86400)

    save_progress("running", "Preparing Migration...", 0)

    existing_tasks = {
        d.issue_key: d.name
        for d in frappe.db.get_all("Task", fields=["issue_key", "name"])
    }

    start_at         = 0
    max_results      = 100
    BATCH_SIZE       = 150
    tasks_insert_buf = []
    tasks_update_buf = []
    attachments_buf  = []
    worklogs_buf     = []
    comments_buf     = []

    try:
        # ──────────────────────────────────────────────
        # PHASE 1: FETCH & CREATE TASKS (0% - 70%)
        # ──────────────────────────────────────────────
        while True:
            if check_control(project_key) == "stopped":
                save_progress("stopped", "Migration Halted by User", 0)
                _flush_inserts(tasks_insert_buf)
                _flush_updates(tasks_update_buf)
                frappe.db.commit()
                return

            payload = {
                "jql":        f"project = '{project_key}' ORDER BY created ASC",
                "expand":     ["names"],
                "fields":     ["*all"],
                "startAt":    start_at,
                "maxResults": max_results,
            }
            try:
                res = requests.post(
                    f"{jira_domain}/rest/api/2/search",
                    json=payload, auth=auth, headers=headers
                )
                res.raise_for_status()
                data = res.json()
            except Exception:
                frappe.log_error(frappe.get_traceback(), "Jira Fetch Failed")
                break

            issues    = data.get("issues", [])
            names_map = data.get("names", {})
            total     = data.get("total", 0)

            if not issues:
                break

            raw_watcher_emails_map = batch_fetch_watcher_emails(
                [i.get("key") for i in issues], jira_domain, auth
            )

            for issue in issues:
                if check_control(project_key) == "stopped":
                    save_progress("stopped", "Migration Halted by User", 0)
                    _flush_inserts(tasks_insert_buf)
                    _flush_updates(tasks_update_buf)
                    frappe.db.commit()
                    return

                jira_key = issue.get("key")
                try:
                    task_dict, dyn_fields, attachments, worklogs = build_task_dict_from_jira(
                        issue, jira_domain, auth, names_map
                    )

                    task_dict["watchers"] = [
                        {"user": resolve_user(email)}
                        for email in raw_watcher_emails_map.get(jira_key, [])
                    ]

                    if jira_key in existing_tasks:
                        tasks_update_buf.append({"name": existing_tasks[jira_key], "data": task_dict})
                    else:
                        tasks_insert_buf.append(task_dict)

                    if attachments:
                        attachments_buf.append({"jira_key": jira_key, "attachments": attachments})
                    if worklogs:
                        worklogs_buf.append({"jira_key": jira_key, "worklogs": worklogs})

                    comments_buf.append({"jira_key": jira_key})

                    fields     = issue.get("fields", {})
                    parent_data = fields.get("parent")
                    std_parent = parent_data if isinstance(parent_data, str) else (parent_data or {}).get("key")
                    
                    target_parent = std_parent or dyn_fields.get("epic_link") or dyn_fields.get("parent_link")
                    if target_parent:
                        frappe.cache().hset(redis_hierarchy_key, jira_key, target_parent)

                    processed += 1

                except Exception:
                    frappe.log_error(frappe.get_traceback(), f"Issue Processing Failed: {jira_key}")
                    failed += 1
                    frappe.cache().rpush(failure_key, jira_key)

                # Dynamic progress scaling for Phase 1 (caps at 70%)
                if (processed + failed) % 5 == 0:
                    current_percent = min(round((processed / total) * 70, 2), 70) if total else 0
                    save_progress("running", "Fetching & Creating Tasks", current_percent)

            # Batch flush
            if len(tasks_insert_buf) >= BATCH_SIZE:
                failed += _flush_inserts(tasks_insert_buf)
                tasks_insert_buf = []

            if len(tasks_update_buf) >= BATCH_SIZE:
                failed += _flush_updates(tasks_update_buf)
                tasks_update_buf = []

            start_at += len(issues)
            if start_at >= total:
                break

        # Final flush for tasks
        failed += _flush_inserts(tasks_insert_buf)
        failed += _flush_updates(tasks_update_buf)
        frappe.db.commit()

        # ──────────────────────────────────────────────
        # SECONDARY PHASES (Run Sequentially with Pulses)
        # ──────────────────────────────────────────────
        
        if attachments_buf:
            save_progress("running", "Starting Attachment Sync...", 75.0)
            process_attachments_queue(attachments_buf, auth, project_key)
            
        if worklogs_buf:
            save_progress("running", "Starting Worklog Sync...", 80.0)
            process_worklogs_queue(worklogs_buf, project_key)
            
        if comments_buf:
            save_progress("running", "Starting Comment Sync...", 85.0)
            process_comments_queue(comments_buf, jira_domain, auth, project_key)

        save_progress("running", "Building Task Hierarchy...", 90.0)
        weave_hierarchies(redis_hierarchy_key, project_key)
        build_hierarchy_from_dependencies(project_key)
        update_parent_end_dates()

        save_progress("running", "Rebuilding Tree Structure...", 95.0)
        frappe.log_error("Rebuilding Task Tree NestedSet...", "Jira Hierarchy Update")
        rebuild_tree("Task", "parent_task")
        
        save_progress("running", "Patching Epic Links...", 98.0)
        patch_epic_links_from_jira(project_key)

        # Everything is strictly complete. Hit 100%.
        save_progress("completed", "Migration Complete ✅", 100.0)

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Jira Migration Engine Failed")
        save_progress("failed", "Migration Failed (Check Logs)", 0)


# ──────────────────────────────────────────────
# PROGRESS & CONTROL
# ──────────────────────────────────────────────

def check_control(project_key):
    """
    Returns "running" | "paused" | "stopped".
    Blocks (sleeps) while paused.
    """
    control_key = f"jira_migration_control_{project_key}"

    def _state():
        v = frappe.cache().hget(control_key, "state")
        return v.decode() if isinstance(v, bytes) else (v or "running")

    state = _state()

    if state == "stopped":
        return "stopped"

    while state == "paused":
        time.sleep(2)
        state = _state()
        if state == "stopped":
            return "stopped"

    return "running"


@frappe.whitelist()
def get_migration_progress(project_key):
    # Fetch directly from the cache we set
    state = frappe.cache().get_value(f"jira_migration_state_{project_key}")

    if state and state.get("project_key") == project_key:
        processed  = int(state.get("processed", 0))
        total      = int(state.get("total",     0))
        failed     = int(state.get("failed",    0))
        status     = state.get("status", "running")
        phase      = state.get("phase", "Initializing...")
        percent    = float(state.get("percent", 0.0))
        heartbeat  = state.get("last_heartbeat")
        start_time = state.get("start_time")

        warning = None
        if heartbeat and status == "running":
            try:
                # If 2 minutes pass without a heartbeat, the worker died.
                if (now_datetime() - get_datetime(heartbeat)).total_seconds() > 120:
                    warning = "Migration heartbeat expired (no progress for 2 minutes). Worker likely crashed."
                    status = "failed"
                    phase = "Worker Crashed/Timeout"
            except Exception:
                pass

        eta = None
        if start_time and processed >= 10:
            try:
                elapsed = (now_datetime() - get_datetime(start_time)).total_seconds()
                if elapsed > 0:
                    speed = processed / elapsed
                    eta   = round(max(total - processed, 0) / speed, 2) if speed else None
            except Exception:
                pass

        return {
            "status":    status,
            "phase":     phase,
            "total":     total,
            "processed": processed,
            "failed":    failed,
            "percent":   percent,
            "eta":       eta,
            "warning":   warning,
        }

    return {"status": "idle", "phase": "Awaiting Start...", "total": 0, "processed": 0, "failed": 0, "percent": 0, "eta": None}

@frappe.whitelist()
def pause_migration(project_key):
    frappe.cache().hset(f"jira_migration_control_{project_key}", "state", "paused")
    return "⏸ Migration paused"

@frappe.whitelist()
def resume_migration(project_key):
    frappe.cache().hset(f"jira_migration_control_{project_key}", "state", "running")
    return "▶️ Migration resumed"

@frappe.whitelist()
def stop_migration(project_key):
    frappe.cache().hset(f"jira_migration_control_{project_key}", "state", "stopped")
    return "🛑 Migration stopped"


# ──────────────────────────────────────────────
# DEPENDENCY HIERARCHY
# ──────────────────────────────────────────────

def build_hierarchy_from_dependencies(project_key=None):
    filter_sql = """
    AND parent IN (
        SELECT name FROM `tabTask`
        WHERE issue_key IS NOT NULL AND issue_key != ''
    )
    """
    sql_params = {}

    if project_key:
        filter_sql = """
        AND parent IN (
            SELECT name FROM `tabTask`
            WHERE issue_key IS NOT NULL AND issue_key != ''
            AND issue_key LIKE %(proj_key)s
        )
        """
        sql_params["proj_key"] = f"{project_key}%"

    parent_tasks = frappe.db.sql(f"""
        SELECT DISTINCT parent
        FROM `tabTask Depends On`
        WHERE parenttype = 'Task' {filter_sql}
    """, values=sql_params, as_dict=True)

    for p in parent_tasks:
        parent_name = p.parent

        if not frappe.db.get_value("Task", parent_name, "is_group"):
            try:
                frappe.db.set_value("Task", parent_name, "is_group", 1, update_modified=False)
            except Exception as e:
                frappe.log_error(f"Failed to group {parent_name}: {str(e)}", "Jira Hierarchy Debug")

        children = frappe.db.get_all(
            "Task Depends On",
            filters={"parent": parent_name, "parenttype": "Task"},
            fields=["task"]
        )

        for child in children:
            child_name = child.task
            if not child_name:
                continue
            current_parent = frappe.db.get_value("Task", child_name, "parent_task")
            if not current_parent:
                try:
                    frappe.db.set_value(
                        "Task", child_name,
                        {"parent_task": parent_name, "parent_issue": parent_name},
                        update_modified=False
                    )
                except Exception as e:
                    pass

    frappe.db.commit()


def update_parent_end_dates():
    parent_names = frappe.db.sql("""
        SELECT DISTINCT parent_task
        FROM `tabTask`
        WHERE parent_task IS NOT NULL AND parent_task != ''
    """, as_dict=True)

    for p in parent_names:
        parent_name = p.parent_task
        parent_doc  = frappe.get_doc("Task", parent_name)
        children    = frappe.get_all("Task", fields=["exp_end_date"], filters={"parent_task": parent_name})
        if not children:
            continue

        max_end = parent_doc.exp_end_date
        for child in children:
            if child.exp_end_date and (max_end is None or child.exp_end_date > max_end):
                max_end = child.exp_end_date

        if max_end and (parent_doc.exp_end_date is None or parent_doc.exp_end_date < max_end):
            frappe.db.set_value("Task", parent_name, "exp_end_date", max_end, update_modified=False)

    frappe.db.commit()


# ──────────────────────────────────────────────
# THREAD-SAFE BATCH WATCHER FETCH
# ──────────────────────────────────────────────

def batch_fetch_watcher_emails(issue_keys, domain, auth):
    result = {k: [] for k in issue_keys}

    def fetch_emails(key):
        url = f"{domain}/rest/api/2/issue/{key}/watchers"
        try:
            r = requests.get(url, auth=auth, headers={"Accept": "application/json"}, timeout=5)
            if r.status_code == 200:
                watchers = r.json().get("watchers", [])
                return key, [w.get("emailAddress") for w in watchers if w.get("emailAddress")]
        except Exception:
            pass
        return key, []

    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = {pool.submit(fetch_emails, k): k for k in issue_keys}
        for future in as_completed(futures):
            key, emails = future.result()
            result[key] = emails

    return result


# ──────────────────────────────────────────────
# BACKGROUND PROCESSORS (With Live UI Pulses)
# ──────────────────────────────────────────────

def process_worklogs_queue(worklogs_buffer, project_key=None):
    total = len(worklogs_buffer)
    for i, item in enumerate(worklogs_buffer, 1):
        # Pulse the UI every 5 items
        if i % 5 == 0 or i == 1:
            pulse_worker(project_key, f"Syncing Worklogs ({i}/{total})...")
            
        jira_key  = item.get("jira_key")
        worklogs  = item.get("worklogs", [])
        task_name = frappe.db.get_value("Task", {"issue_key": jira_key}, "name")
        if not task_name:
            continue

        task_doc = frappe.get_doc("Task", task_name)
        existing_times = {wl.get("time_spent_seconds") for wl in task_doc.get("work_logs", [])}

        changed = False
        for wl in worklogs:
            time_secs = wl.get("timeSpentSeconds") or 0
            if time_secs in existing_times:
                continue

            author_email = (wl.get("author") or {}).get("emailAddress")
            started      = wl.get("started", "")[:10]
            comment      = wl.get("comment", "") or ""
            if isinstance(comment, dict):
                comment = extract_description(comment)

            task_doc.append("work_logs", {
                "user":               resolve_user(author_email) if author_email else "Administrator",
                "time_spent_seconds": time_secs,
                "time_spent_display": format_time(time_secs) or "0m",
                "work_date":          started or frappe.utils.today(),
                "description":        comment[:500] if comment else "Migrated from Jira",
                "logged_at":          wl.get("started", frappe.utils.now_datetime()),
            })
            changed = True

        if changed:
            try:
                task_doc.save(ignore_permissions=True)
            except Exception as e:
                frappe.log_error(f"Worklog save failed for {jira_key}: {str(e)}", "Jira Worklog Migration")

    frappe.db.commit()


def process_comments_queue(comments_buffer, domain, auth, project_key=None):
    total = len(comments_buffer)
    for i, item in enumerate(comments_buffer, 1):
        # HTTP requests are slow, pulse every single time so the UI doesn't freeze
        pulse_worker(project_key, f"Fetching Comments ({i}/{total})...")
        
        jira_key  = item.get("jira_key")
        task_name = frappe.db.get_value("Task", {"issue_key": jira_key}, "name")
        if not task_name:
            continue

        try:
            url = f"{domain}/rest/api/2/issue/{jira_key}/comment"
            r   = requests.get(url, auth=auth, headers={"Accept": "application/json"}, timeout=20)
            r.raise_for_status()
            comments = r.json().get("comments", [])
        except Exception as e:
            continue

        if not comments:
            continue

        existing_comms = frappe.get_all(
            "Comment",
            filters={"reference_doctype": "Task", "reference_name": task_name, "comment_type": "Comment"},
            fields=["content"]
        )
        existing_texts = {c.content for c in existing_comms if c.content}

        for c in comments:
            body = c.get("body")
            if not body:
                continue

            content = extract_description(body)
            if content in existing_texts:
                continue

            author_email = (c.get("author") or {}).get("emailAddress")
            author_name  = (c.get("author") or {}).get("displayName", "Unknown User")
            created_str  = c.get("created")

            try:
                doc = frappe.get_doc({
                    "doctype":          "Comment",
                    "comment_type":     "Comment",
                    "reference_doctype":"Task",
                    "reference_name":   task_name,
                    "content":          content,
                    "comment_email":    resolve_user(author_email) if author_email else "Administrator",
                    "comment_by":       author_name,
                })
                doc.flags.ignore_permissions = True
                doc.insert(ignore_permissions=True)
                existing_texts.add(content)

                if created_str:
                    created_dt = get_datetime(created_str[:19].replace("T", " "))
                    frappe.db.set_value("Comment", doc.name, "creation", created_dt, update_modified=False)
                    frappe.db.set_value("Comment", doc.name, "modified", created_dt, update_modified=False)

            except Exception as e:
                pass

    frappe.db.commit()


def resolve_issue_links(issuelinks, current_issue_key):
    if not issuelinks:
        return []

    rows = []
    for link in issuelinks:
        link_type    = link.get("type", {})
        target_issue = None
        relation     = ""

        if "inwardIssue" in link:
            target_issue = link["inwardIssue"]
            relation     = link_type.get("inward", "").lower()
        elif "outwardIssue" in link:
            target_issue = link["outwardIssue"]
            relation     = link_type.get("outward", "").lower()

        if not target_issue:
            continue

        if relation in ["is blocked by", "depends on", "has to be done after"]:
            dep_key = target_issue.get("key")
            if dep_key == current_issue_key:
                continue
            dep_name = frappe.db.get_value("Task", {"issue_key": dep_key}, "name")
            if dep_name:
                rows.append({
                    "task":    dep_name,
                    "subject": target_issue.get("fields", {}).get("summary", dep_key)
                })

    seen, unique_rows = set(), []
    for r in rows:
        if r["task"] not in seen:
            seen.add(r["task"])
            unique_rows.append(r)
    return unique_rows


def process_attachments_queue(attachments_buffer, auth, project_key=None):
    total = len(attachments_buffer)
    for i, item in enumerate(attachments_buffer, 1):
        # Pulse every time because downloading files is network-heavy
        pulse_worker(project_key, f"Downloading Attachments ({i}/{total})...")
        
        jira_key  = item.get("jira_key")
        task_name = frappe.db.get_value("Task", {"issue_key": jira_key}, "name")
        if not task_name:
            continue

        for att in item.get("attachments", []):
            file_name   = att.get("filename")
            content_url = att.get("content")

            if frappe.db.exists("File", {
                "attached_to_doctype": "Task",
                "attached_to_name":    task_name,
                "file_name":           file_name
            }):
                continue

            try:
                r = requests.get(content_url, auth=auth, stream=True, timeout=30)
                r.raise_for_status()
                frappe.get_doc({
                    "doctype":            "File",
                    "file_name":          file_name,
                    "attached_to_doctype":"Task",
                    "attached_to_name":   task_name,
                    "content":            r.content,
                    "is_private":         1,
                }).insert(ignore_permissions=True)
            except Exception as e:
                pass

    frappe.db.commit()


# ──────────────────────────────────────────────
# RETRY FAILED (Left as async for one-offs)
# ──────────────────────────────────────────────

@frappe.whitelist()
def retry_failed_issues(project_key):
    failure_key = f"jira_migration_failures_{project_key}"
    failed_keys = frappe.cache().lrange(failure_key, 0, -1)
    if not failed_keys:
        return "No failed issues"

    frappe.enqueue(
        'erpnext_agile.jira_sync.retry_failed_worker',
        queue='long', timeout=3600,
        project_key=project_key,
        failed_keys=[k.decode() if isinstance(k, bytes) else k for k in failed_keys]
    )
    return f"Retrying {len(failed_keys)} issues"


def retry_failed_worker(project_key, failed_keys):
    settings    = frappe.get_single("Jira Data Migration Tool")
    jira_domain = settings.jira_domain
    auth        = (settings.jira_email, settings.jira_api_token)

    for key in failed_keys:
        try:
            res = requests.get(f"{jira_domain}/rest/api/2/issue/{key}?expand=names", auth=auth)
            res.raise_for_status()
            issue     = res.json()
            names_map = issue.get("names", {})
            run_single_issue(issue, jira_domain, auth, names_map)
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"Retry Failed: {key}")


def run_single_issue(issue, domain, auth, names_map):
    jira_key  = issue.get("key")
    task_dict, dyn_fields, attachments, worklogs = build_task_dict_from_jira(
        issue, domain, auth, names_map
    )

    raw_emails = batch_fetch_watcher_emails([jira_key], domain, auth).get(jira_key, [])
    task_dict["watchers"] = [{"user": resolve_user(email)} for email in raw_emails]

    existing = frappe.db.get_value("Task", {"issue_key": jira_key}, "name")

    if existing:
        try:
            doc = frappe.get_doc("Task", existing)
            doc.update(task_dict)
            doc.save(ignore_permissions=True)
        except Exception as e:
            if "Circular" in str(e):
                try:
                    frappe.clear_messages()
                    doc        = frappe.get_doc("Task", existing)
                    safe_data  = {**task_dict, "depends_on": []}
                    doc.update(safe_data)
                    doc.save(ignore_permissions=True)
                except Exception:
                    pass
    else:
        try:
            frappe.get_doc(task_dict).insert(ignore_permissions=True)
        except Exception as e:
            if "Circular" in str(e):
                try:
                    frappe.clear_messages()
                    frappe.get_doc({**task_dict, "depends_on": []}).insert(ignore_permissions=True)
                except Exception:
                    pass

    frappe.db.commit()

    if attachments:
        frappe.enqueue('erpnext_agile.jira_sync.process_attachments_queue',
                       attachments_buffer=[{"jira_key": jira_key, "attachments": attachments}],
                       auth=auth, queue='long', timeout=3600)
    if worklogs:
        frappe.enqueue('erpnext_agile.jira_sync.process_worklogs_queue',
                       worklogs_buffer=[{"jira_key": jira_key, "worklogs": worklogs}],
                       queue='long', timeout=3600)

    frappe.enqueue('erpnext_agile.jira_sync.process_comments_queue',
                   comments_buffer=[{"jira_key": jira_key}],
                   domain=domain, auth=auth, queue='long', timeout=3600)


# ──────────────────────────────────────────────
# HIERARCHY
# ──────────────────────────────────────────────

def weave_hierarchies(redis_key, project_key=None):
    relationships = frappe.cache().hgetall(redis_key)
    if not relationships:
        return
        
    total = len(relationships)
    for i, (child, parent) in enumerate(relationships.items(), 1):
        if i % 10 == 0 or i == 1:
            pulse_worker(project_key, f"Mapping Epic Links ({i}/{total})...")
            
        child  = child.decode()  if isinstance(child,  bytes) else child
        parent = parent.decode() if isinstance(parent, bytes) else parent

        child_name  = frappe.db.get_value("Task", {"issue_key": child},  "name")
        parent_name = frappe.db.get_value("Task", {"issue_key": parent}, "name")

        if child_name and parent_name:
            try:
                if not frappe.db.get_value("Task", parent_name, "is_group"):
                    frappe.db.set_value("Task", parent_name, "is_group", 1, update_modified=False)

                frappe.db.set_value("Task", child_name, {
                    "parent_task":  parent_name,
                    "parent_issue": parent_name,
                }, update_modified=False)

                epic_doc = frappe.get_doc("Task", parent_name)
                existing_deps = [d.task for d in epic_doc.get("depends_on", [])]
                
                if child_name not in existing_deps:
                    epic_doc.append("depends_on", {
                        "task": child_name,
                        "subject": frappe.db.get_value("Task", child_name, "subject")
                    })
                    epic_doc.save(ignore_permissions=True)

            except Exception as e:
                pass

    frappe.db.commit()
    frappe.cache().delete_key(redis_key)


# ──────────────────────────────────────────────
# ENTITY RESOLVERS
# ──────────────────────────────────────────────

def parse_story_points(val):
    allowed = [0, 1, 2, 3, 5, 8, 13, 20]
    if val is None or val == "":
        return "0"
    try:
        num = float(val)
    except (ValueError, TypeError):
        return "0"
    closest = min(allowed, key=lambda x: abs(x - num))
    return str(closest)

def resolve_project(proj_data):
    if not proj_data:
        return None
    name = proj_data.get("name")
    if not frappe.db.exists("Project", {"project_name": name}):
        return frappe.get_doc({
            "doctype":      "Project",
            "project_name": name,
            "status":       "Open",
            "enable_agile": 1,
        }).insert(ignore_permissions=True).name
    return frappe.db.get_value("Project", {"project_name": name}, "name")

def resolve_sprint(sprint_payload, project_name):
    if not sprint_payload:
        return None
    sprint_name = start_date = end_date = None

    if isinstance(sprint_payload, list) and len(sprint_payload) > 0:
        first = sprint_payload[0]
        if isinstance(first, dict):
            sprint_name = first.get("name")
            start_date  = first.get("startDate")
            end_date    = first.get("endDate")
        elif isinstance(first, str):
            m = re.search(r'name=([^,\]]+)', first);       sprint_name = m.group(1) if m else None
            m = re.search(r'startDate=([^,\]]+)', first)
            if m and m.group(1) != '<null>': start_date = m.group(1)[:10]
            m = re.search(r'endDate=([^,\]]+)', first)
            if m and m.group(1) != '<null>': end_date   = m.group(1)[:10]

    if sprint_name and not frappe.db.exists("Agile Sprint", sprint_name):
        try:
            final_start = getdate(start_date) if start_date else frappe.utils.today()
            final_end   = getdate(end_date)   if end_date   else frappe.utils.add_days(final_start, 14)
            frappe.get_doc({
                "doctype":      "Agile Sprint",
                "sprint_name":  sprint_name,
                "project":      project_name,
                "sprint_state": "Active",
                "start_date":   final_start,
                "end_date":     final_end,
            }).insert(ignore_permissions=True)
        except Exception:
            pass
    return sprint_name

def resolve_version_table(versions_data, project_name):
    if not versions_data:
        return []
    result = []
    for v in versions_data:
        v_name = v.get("name")
        if not v_name:
            continue
        existing = frappe.db.exists("Agile Release Version", {"version_name": v_name, "project": project_name})
        if not existing:
            try:
                doc = frappe.get_doc({
                    "doctype":      "Agile Release Version",
                    "version_name": v_name,
                    "project":      project_name,
                }).insert(ignore_permissions=True)
                existing = doc.name
            except Exception:
                pass
        if existing:
            result.append({"version": existing})
    return result

def resolve_components(components_data):
    if not components_data:
        return []
    result = []
    for c in components_data:
        name = c.get("name")
        if not name:
            continue
        if not frappe.db.exists("Agile Issue Component", {"component_name": name}):
            try:
                frappe.get_doc({"doctype": "Agile Issue Component", "component_name": name}).insert(ignore_permissions=True)
            except Exception:
                pass
        doc_name = frappe.db.get_value("Agile Issue Component", {"component_name": name}, "name") or name
        result.append({"component": doc_name})
    return result

def resolve_labels(labels_data):
    if not labels_data:
        return []
    result = []
    for label in labels_data:
        if not label:
            continue
        if not frappe.db.exists("Agile Issue Label", {"label_name": label}):
            try:
                frappe.get_doc({"doctype": "Agile Issue Label", "label_name": label}).insert(ignore_permissions=True)
            except Exception:
                pass
        doc_name = frappe.db.get_value("Agile Issue Label", {"label_name": label}, "name") or label
        result.append({"label": doc_name})
    return result

def resolve_user(email):
    return email if email and frappe.db.exists("User", email) else "Administrator"

def map_resolution(val):
    allowed = ["Unresolved", "Done", "Won't Do", "Duplicate", "Cannot Reproduce"]
    return val if val in allowed else "Unresolved"


# ──────────────────────────────────────────────
# INTERNAL BATCH FLUSH HELPERS
# ──────────────────────────────────────────────

def _flush_inserts(buf):
    fail_count = 0
    for task_data in buf:
        ik = task_data.get("issue_key")
        try:
            frappe.get_doc(task_data).insert(ignore_permissions=True)
        except Exception as e:
            if "Circular" in str(e):
                try:
                    frappe.clear_messages()
                    frappe.get_doc({**task_data, "depends_on": []}).insert(ignore_permissions=True)
                    continue
                except Exception:
                    pass
            fail_count += 1
    frappe.db.commit()
    return fail_count


def _flush_updates(buf):
    fail_count = 0
    for payload in buf:
        try:
            doc     = frappe.get_doc("Task", payload["name"])
            changes = _get_changes(doc, payload["data"])
            if not changes:
                continue
            doc.update(changes)
            doc.save(ignore_permissions=True)
        except Exception as e:
            if "Circular" in str(e):
                try:
                    frappe.clear_messages()
                    doc       = frappe.get_doc("Task", payload["name"])
                    safe_data = {**payload["data"], "depends_on": []}
                    changes   = _get_changes(doc, safe_data)
                    if changes:
                        doc.update(changes)
                        doc.save(ignore_permissions=True)
                    continue
                except Exception:
                    pass
            fail_count += 1
    frappe.db.commit()
    return fail_count

@frappe.whitelist()
def patch_epic_links_from_jira(project_key):
    frappe.logger().info(f"Starting targeted Epic Link patch for project: {project_key}")
    
    settings = frappe.get_single("Jira Data Migration Tool")
    domain = settings.jira_domain
    auth = (settings.jira_email, settings.jira_api_token)

    start_at = 0
    patched_count = 0
    
    while True:
        # We only need the custom fields and parent data to map the hierarchy
        payload = {
            "jql": f"project = '{project_key}'",
            "expand": ["names"],
            "fields": ["parent", "customfield_10110"], # Grabbing standard parent and Epic Link
            "startAt": start_at,
            "maxResults": 100
        }
        
        try:
            res = requests.post(f"{domain}/rest/api/2/search", json=payload, auth=auth, headers={"Accept": "application/json"})
            res.raise_for_status()
            data = res.json()
        except Exception as e:
            return f"❌ Failed to reach Jira: {str(e)}"

        issues = data.get("issues", [])
        names_map = data.get("names", {})
        
        if not issues:
            break
            
        rev_map = {str(v).lower().strip(): k for k, v in names_map.items()}
        epic_field_key = rev_map.get("epic link", "")

        for issue in issues:
            child_key = issue.get("key")
            fields = issue.get("fields", {})
            
            # Safely grab standard parent
            parent_data = fields.get("parent")
            std_parent = parent_data if isinstance(parent_data, str) else (parent_data or {}).get("key")
            
            # Safely grab Epic Link
            epic_val = fields.get("customfield_10110") or (fields.get(epic_field_key) if epic_field_key else None)
            if isinstance(epic_val, dict): 
                epic_val = epic_val.get("key") or epic_val.get("value")
            
            target_parent = std_parent or epic_val
            
            if target_parent:
                child_name = frappe.db.get_value("Task", {"issue_key": child_key}, "name")
                parent_name = frappe.db.get_value("Task", {"issue_key": target_parent}, "name")
                
                if child_name and parent_name:
                    try:
                        # 1. Update the hidden backend tree links
                        frappe.db.set_value("Task", child_name, {
                            "parent_task": parent_name,
                            "parent_issue": parent_name
                        }, update_modified=False)
                        
                        # 2. Make sure Epic is a group
                        epic_doc = frappe.get_doc("Task", parent_name)
                        if not epic_doc.is_group:
                            epic_doc.db_set("is_group", 1, update_modified=False)
                            
                        # 3. Push to the UI child table
                        existing_deps = [d.task for d in epic_doc.get("depends_on", [])]
                        if child_name not in existing_deps:
                            epic_doc.append("depends_on", {
                                "task": child_name,
                                "subject": frappe.db.get_value("Task", child_name, "subject")
                            })
                            epic_doc.flags.ignore_permissions = True
                            epic_doc.save(ignore_version=True)
                            patched_count += 1
                            
                    except Exception as e:
                        frappe.log_error(f"Patch failed for {child_key} -> {target_parent}: {str(e)}", "Jira Patch Error")
                        
        start_at += len(issues)
        if start_at >= data.get("total", 0):
            break

    frappe.db.commit()
    
    # Rebuild the NestedSet so the Tree View renders perfectly
    from frappe.utils.nestedset import rebuild_tree
    rebuild_tree("Task", "parent_task")
    
    return f"✅ Fetched from Jira and successfully mapped {patched_count} child tasks to their Epics!"

# frappe.call({
#     method: "erpnext_agile.jira_sync.patch_epic_links_from_jira",
#     args: {
#         project_key: "CRISISIM"
#     },
#     callback: function(r) {
#         console.log(r.message);
#     }
# });