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

app_include_css = [
    "/assets/erpnext_agile/css/agile.css"
]

app_include_js = [
    "/assets/erpnext_agile/js/agile_board.js",
    "/assets/erpnext_agile/js/issue_quick_actions.js"
]

# include js, css files in header of desk.html
# app_include_css = "/assets/erpnext_agile/css/erpnext_agile.css"
# app_include_js = "/assets/erpnext_agile/js/erpnext_agile.js"

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
page_js = {
    "agile-board": "public/js/agile_board_page.js"
}

website_route_rules = [
    {"from_route": "/agile/<path:app_path>", "to_route": "agile"},
]

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
doctype_js = {
    "Task": "public/js/task_agile_integration.js",
    "Project": "public/js/project_agile_integration.js"
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
after_install = "erpnext_agile.after_install.after_install"

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

permission_query_conditions = {
    "Agile Issue": "erpnext_agile.permissions.get_agile_issue_permission_query_conditions"
}
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

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
        "after_insert": "erpnext_agile.utils.create_agile_issue_from_task",
        "on_update": "erpnext_agile.utils.sync_task_to_agile_issue"
    },
    "Project": {
        "after_insert": "erpnext_agile.utils.check_agile_project_creation"
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
    "daily": [
        "erpnext_agile.utils.sync_github_data"
    ],
    "hourly": [
        "erpnext_agile.utils.update_sprint_progress"
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
# 	"Task": "erpnext_agile.task.get_dashboard_data"
# }
override_doctype_dashboards = {
    "Project": "erpnext_agile.erpnext_agile.doctype.agile_project.agile_project.get_dashboard_data"
}

whitelist = [
    "erpnext_agile.api.get_board_data",
    "erpnext_agile.api.update_issue_status",
    "erpnext_agile.api.create_github_branch",
    "erpnext_agile.api.link_pull_request"
]


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

