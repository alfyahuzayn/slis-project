// Copyright (c) 2026, navaneeth and contributors
// For license information, please see license.txt

frappe.query_reports["Department Samples Source Report"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
            "reqd": 0
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 0
        },
        {
            "fieldname": "scheme",
            "label": __("Scheme / Program Name"),
            "fieldtype": "Data",
            "reqd": 0
        },
        {
            "fieldname": "lab",
            "label": __("Target Lab"),
            "fieldtype": "Data",
            "reqd": 0
        }
    ]
};