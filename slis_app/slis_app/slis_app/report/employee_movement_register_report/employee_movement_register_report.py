# Copyright (c) 2026, navaneeth and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
    if not filters:
        filters = {}

    columns = get_columns()
    data = get_data(filters)

    return columns, data

def get_columns():
    return [
        {"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 150},
        {"label": _("Program Name"), "fieldname": "name_of_type", "fieldtype": "Data", "width": 200},
        {"label": _("From Date"), "fieldname": "from_date", "fieldtype": "Date", "width": 120},
        {"label": _("To Date"), "fieldname": "to_date", "fieldtype": "Date", "width": 120},
        {"label": _("Description"), "fieldname": "description", "fieldtype": "Small Text", "width": 300},
    ]

def get_data(filters):
    conditions = {}
    
    # Apply Date Filters
    if filters.get("from_date") and filters.get("to_date"):
        conditions["from_date"] = [">=", filters.get("from_date")]
        conditions["to_date"] = ["<=", filters.get("to_date")]

    return frappe.get_all("Movement Register", 
        fields=["employee", "name_of_type", "from_date", "to_date", "description"],
        filters=conditions,
        order_by="from_date desc"
    )