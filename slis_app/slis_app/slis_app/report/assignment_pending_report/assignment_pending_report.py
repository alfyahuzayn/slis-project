# Copyright (c) 2026, navaneeth and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
    filters = filters or {}

    columns = [
        {"label": _("Sample ID"), "fieldname": "name", "fieldtype": "Link", "options": "Soil Sample Collection", "width": 200},
        {"label": _("Client Type"), "fieldname": "client_type", "fieldtype": "Data", "width": 280},
        {"label": _("Scheme Name"), "fieldname": "name_of_type", "fieldtype": "Data", "width": 280},
        {"label": _("Current Status"), "fieldname": "status", "fieldtype": "Data", "width": 300},
        {"label": _("Assignment Group"), "fieldname": "assignment_group", "fieldtype": "Data", "width": 360},
        {"label": _("Date of Collection"), "fieldname": "date_of_collection", "fieldtype": "Date", "width": 240}
    ]

    where_clauses = [
        "status IN ('With Senior Chemist', 'Draft', 'With Assistant Director', 'Enter File number')"
    ]
    query_values = []

    # Date Range Filter
    if filters.get("from_date") and filters.get("to_date"):
        where_clauses.append("date_of_collection BETWEEN %s AND %s")
        query_values.extend([filters.get("from_date"), filters.get("to_date")])

    # Client Type Filter
    if filters.get("client_type"):
        where_clauses.append("client_type = %s")
        query_values.append(filters.get("client_type"))

    # Scheme Filter
    if filters.get("scheme"):
        where_clauses.append("name_of_type = %s")
        query_values.append(filters.get("scheme"))

    where_str = " AND ".join(where_clauses)

    query = f"""
        SELECT 
            name, 
            client_type, 
            name_of_type, 
            status, 
            date_of_collection
        FROM `tabSoil Sample Collection`
        WHERE {where_str}
        ORDER BY date_of_collection DESC
    """

    samples = frappe.db.sql(query, tuple(query_values), as_dict=True)

    data = []
    for sample in samples:
        data.append({
            "name": sample.name,
            "client_type": sample.client_type,
            "name_of_type": sample.name_of_type or "",
            "status": sample.status,
            "assignment_group": "Assignment Pending",
            "date_of_collection": sample.date_of_collection
        })

    return columns, data