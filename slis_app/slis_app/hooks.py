app_name = "slis_app"
app_title = "Slis App"
app_publisher = "navaneeth"
app_description = "custom soil survey department app"
app_email = "desk.navaneeth@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "slis_app",
# 		"logo": "/assets/slis_app/logo.png",
# 		"title": "Slis App",
# 		"route": "/slis_app",
# 		"has_permission": "slis_app.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

#assign to button hding feature
app_include_js = [
    "/assets/slis_app/js/global_listview.js",
    "/assets/slis_app/js/xlsx.full.min.js"
]


# include js, css files in header of desk.html
# app_include_css = "/assets/slis_app/css/slis_app.css"
# app_include_js = "/assets/slis_app/js/slis_app.js"

# include js, css files in header of web template
# web_include_css = "/assets/slis_app/css/slis_app.css"
# web_include_js = "/assets/slis_app/js/slis_app.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "slis_app/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "slis_app/public/icons.svg"

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
# 	"methods": "slis_app.utils.jinja_methods",
# 	"filters": "slis_app.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "slis_app.install.before_install"
# after_install = "slis_app.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "slis_app.uninstall.before_uninstall"
# after_uninstall = "slis_app.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "slis_app.utils.before_app_install"
# after_app_install = "slis_app.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "slis_app.utils.before_app_uninstall"
# after_app_uninstall = "slis_app.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "slis_app.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
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

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"slis_app.tasks.all"
# 	],
# 	"daily": [
# 		"slis_app.tasks.daily"
# 	],
# 	"hourly": [
# 		"slis_app.tasks.hourly"
# 	],
# 	"weekly": [
# 		"slis_app.tasks.weekly"
# 	],
# 	"monthly": [
# 		"slis_app.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "slis_app.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
 	
#     "frappe.desk.search.search_link": "slis_app.api.assignment.filtered_user_search"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "slis_app.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["slis_app.utils.before_request"]
# after_request = ["slis_app.utils.after_request"]

# Job Events
# ----------
# before_job = ["slis_app.utils.before_job"]
# after_job = ["slis_app.utils.after_job"]

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
# 	"slis_app.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []
doctype_list_js = {
    "Soil Sample Collection": [
        "public/js/soil_sample_collection_list.js",
        "public/js/soil_sample_collection_rejection.js"
    ],
}


permission_query_conditions = {
    "Soil Sample Collection": "slis_app.api.Permission.sample_permission_query",
    "Employee": "slis_app.api.Permission.employee_permission_query",
    "Clients": "slis_app.slis_app.doctype.clients.clients.get_permission_query_conditions"
}

has_permission = {
    "Clients": "slis_app.slis_app.doctype.clients.clients.has_permission"
}





# # lab wise view permission for the soil samples
# permission_query_conditions = {
#     "Soil Sample Collection": "slis_app.api.soil_sample_permission.soil_sample_location_permission"
# }



doc_events = {

    # Existing logic – keep as is
    "Soil Sample Collection": {
        "before_insert": "slis_app.api.Fetch_Employee.before_insert",
        "on_update": "slis_app.api.status_date_tracker.set_status_date",
    },
    "ToDo": {
        "on_update": "slis_app.api.todo_status_tracker.update_sample_status"
    }
}

fixtures = [
   {"dt": "Client Script", "filters": [["module", "=", "Slis App"]]},
    {"dt": "Server Script", "filters": [["module", "=", "Slis App"]]},
    {
        "dt": "Custom Field",
        "filters": [
            ["name", "in", [
                "Employee-custom_lab_name_",
                "Employee-custom_district_office_name",
                "Employee-custom_date_of_transfer",
                "Employee-custom_date_of_resign",
                "Employee-custom_soil_sample_tester",
                "ToDo-custom_ra_employee",
                "ToDo-custom_completed_date",
                "ToDo-custom_lab",
                "ToDo-custom_cancel_reason",
                "ToDo-custom_ra_employee_name"
            ]]
        ]
    },
    # Workflow
    {
        "doctype": "Workflow",
        "filters": [
            [
                "name",
                "=",
                "soil movements"
            ]
        ]
     },
     # Workflow State
      {
        "doctype": "Workflow State"
    },
    {
        "doctype": "Role",
        "filters": [
            ["role_name", "=", "auto workflow"]
        ]

    }
]




# generic hooks


fixtures = [

    # =========================
    # WORKSPACES
    # =========================
    {
        "dt": "Workspace",
        "filters": [
            ["module", "=", "Slis App"]
        ]
    },

    # =========================
    # CLIENT / SERVER SCRIPTS
    # =========================
    {
        "dt": "Client Script",
        "filters": [
            ["module", "=", "Slis App"]
        ]
    },

    {
        "dt": "Server Script",
        "filters": [
            ["module", "=", "Slis App"]
        ]
    },

    # =========================
    # REPORTS
    # =========================
    {
        "dt": "Report",
        "filters": [
            ["module", "=", "Slis App"]
        ]
    },

    # =========================
    # DASHBOARDS / CHARTS
    # =========================
    {
        "dt": "Dashboard Chart",
        "filters": [
            ["module", "=", "Slis App"]
        ]
    },

    {
        "dt": "Number Card",
        "filters": [
            ["module", "=", "Slis App"]
        ]
    },


    # =========================
    # CUSTOMIZATION
    # =========================
    {
        "dt": "Custom Field",
        "filters": [
            ["module", "=", "Slis App"]
        ]
    }

]