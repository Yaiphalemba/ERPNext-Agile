app_name = "erpnext_agile"
app_title = "Erpnext Agile"
app_publisher = "Yanky"
app_description = "Jira-like agile project management for ERPNext"
app_email = "tamocha44@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "erpnext_agile",
# 		"logo": "/assets/erpnext_agile/logo.png",
# 		"title": "Erpnext Agile",
# 		"route": "/erpnext_agile",
# 		"has_permission": "erpnext_agile.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# app_include_css = "/assets/erpnext_agile/css/erpnext_agile.css"
# app_include_js = [
#     "/assets/erpnext_agile/js/agile_board.js",
#     "/assets/erpnext_agile/js/agile_utils.js"
# ]

# include js, css files in header of desk.html
# app_include_css = "/assets/erpnext_agile/css/erpnext_agile.css"
app_include_css = "/assets/erpnext_agile/css/task_gantt_override.css"
# app_include_js = "/assets/erpnext_agile/js/erpnext_agile.js"
app_include_js = "/assets/erpnext_agile/js/task_gantt_override.js"

# include js, css files in header of web template
# web_include_css = "/assets/erpnext_agile/css/erpnext_agile.css"
# web_include_js = "/assets/erpnext_agile/js/erpnext_agile.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "erpnext_agile/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}
# page_js = {
#     "agile-board": "public/js/agile_board_page.js"
# }

# website_route_rules = [
#     {"from_route": "/agile/<path:app_path>", "to_route": "agile"},
# ]

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
doctype_js = {
    "Task": "public/js/task_agile.js",
    "Project": [
            "public/js/project_agile.js",
            "public/js/project_time_tracking.js"
        ]
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "erpnext_agile/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "erpnext_agile.utils.jinja_methods",
# 	"filters": "erpnext_agile.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "erpnext_agile.install.before_install"
# after_install = "erpnext_agile.install.after_install"
after_install = "erpnext_agile.after_install.setup_agile"

# Uninstallation
# ------------

# before_uninstall = "erpnext_agile.uninstall.before_uninstall"
# after_uninstall = "erpnext_agile.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "erpnext_agile.utils.before_app_install"
# after_app_install = "erpnext_agile.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "erpnext_agile.utils.before_app_uninstall"
# after_app_uninstall = "erpnext_agile.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "erpnext_agile.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }

# permission_query_conditions = {
#     "Agile Issue": "erpnext_agile.permissions.get_agile_issue_permission_query_conditions"
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

permission_query_conditions = {
    "Project": "erpnext_agile.overrides.project.get_project_permission_query_conditions",
    "Task": "erpnext_agile.overrides.project.get_task_permission_query_conditions",
    "Agile Sprint": "erpnext_agile.overrides.project.get_agile_sprint_permission_query_conditions",
    "Test Cycle": "erpnext_agile.overrides.project.get_test_cycle_permission_query_conditions",
    "Test Case":  "erpnext_agile.overrides.project.get_test_case_permission_query_conditions",
    "Test Execution":  "erpnext_agile.overrides.project.get_test_execution_permission_query_conditions"
}

has_permission = {
    "Project": "erpnext_agile.overrides.project.has_project_permission",
    "Task": "erpnext_agile.overrides.project.has_task_permission",
    "Agile Sprint": "erpnext_agile.overrides.project.has_agile_sprint_permission",
    "Test Cycle": "erpnext_agile.overrides.project.has_test_cycle_permission",
    "Test Case": "erpnext_agile.overrides.project.has_test_case_permission",
    "Test Execution": "erpnext_agile.overrides.project.has_test_execution_permission"
}

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

override_doctype_class = {
    "Project": "erpnext_agile.overrides.project.AgileProject",
    "Task": "erpnext_agile.overrides.task.AgileTask"
}

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }
doc_events = {
    "Task": {
        "validate": "erpnext_agile.agile_doctype_controllers.task_validate",
        "on_update": [
            "erpnext_agile.agile_doctype_controllers.task_on_update",
            "erpnext_agile.project_time_tracking.update_project_user_time_on_task_update",
            "erpnext_agile.test_management.events.task_check_test_coverage"
        ],
        "after_insert": "erpnext_agile.agile_doctype_controllers.task_after_insert",
        "on_trash": "erpnext_agile.agile_doctype_controllers.task_on_trash"
    },
    "Agile Issue Work Log": {
        "after_insert": "erpnext_agile.project_time_tracking.update_project_user_time_on_work_log",
        "on_update": "erpnext_agile.project_time_tracking.update_project_user_time_on_work_log"
    },
    "Test Execution": {
        "on_submit": "erpnext_agile.test_management.events.test_execution_on_submit",
        "on_cancel": "erpnext_agile.test_management.events.test_execution_on_cancel"
    },
    "Test Cycle": {
        "on_update": "erpnext_agile.test_management.events.test_cycle_on_update",
        "validate": "erpnext_agile.test_management.events.test_cycle_validate"
    }
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"erpnext_agile.tasks.all"
# 	],
# 	"daily": [
# 		"erpnext_agile.tasks.daily"
# 	],
# 	"hourly": [
# 		"erpnext_agile.tasks.hourly"
# 	],
# 	"weekly": [
# 		"erpnext_agile.tasks.weekly"
# 	],
# 	"monthly": [
# 		"erpnext_agile.tasks.monthly"
# 	],
# }

scheduler_events = {
    "hourly": [
        "erpnext_agile.scheduler_events.hourly.update_sprint_metrics",
        "erpnext_agile.scheduler_events.hourly.create_burndown_entries",
        "erpnext_agile.test_management.scheduler.update_cycle_metrics",
        "erpnext_agile.project_time_tracking.recalculate_all_project_times_scheduled",
        "erpnext_agile.test_management.scheduler.send_test_reminders"
    ],
    "daily": [
        "erpnext_agile.scheduler_events.daily.send_sprint_digest",
        "erpnext_agile.scheduler_events.daily.cleanup_old_timers"
    ],
    "weekly": [
        "erpnext_agile.version_control.cleanup_all_old_versions",
        "erpnext_agile.scheduler_events.weekly.generate_team_velocity_report"
    ]
}

# Testing
# -------

# before_tests = "erpnext_agile.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "erpnext_agile.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "erpnext_agile.dashboard.get_dashboard_data"
# }

# whitelist = [
#     "erpnext_agile.api.get_board_data",
#     "erpnext_agile.api.update_issue_status",
#     "erpnext_agile.api.create_github_branch",
#     "erpnext_agile.api.link_pull_request"
# ]


# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["erpnext_agile.utils.before_request"]
# after_request = ["erpnext_agile.utils.after_request"]

# Job Events
# ----------
# before_job = ["erpnext_agile.utils.before_job"]
# after_job = ["erpnext_agile.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"erpnext_agile.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

fixtures = [
    {"doctype": "Custom Field", "filters": [["module" , "in" , ("Erpnext Agile")]]}
]