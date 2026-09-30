# # Copyright (c) 2026, navaneeth and contributors
# # For license information, please see license.txt

# import frappe
# from frappe import _

# def execute(filters=None):
#     filters = filters or {}

#     columns = [
#         {"label": _("Sl. No"), "fieldname": "idx", "fieldtype": "Int", "width": 160},
#         {"label": _("District"), "fieldname": "district_name", "fieldtype": "Data", "width": 240},
#         {"label": _("Panchayat / Municipality"), "fieldname": "panchayat_name", "fieldtype": "Data", "width": 280},
#         {"label": _("Scheme Name"), "fieldname": "scheme_name", "fieldtype": "Data", "width": 280},
#         {"label": _("Target Lab"), "fieldname": "target_lab", "fieldtype": "Link", "options": "Soil Laboratory", "width": 250},
#         {"label": _("District Office Name"), "fieldname": "district_office_name", "fieldtype": "Data", "width": 260},
#         {"label": _("Number of Samples"), "fieldname": "sample_count", "fieldtype": "HTML", "width": 230}
#     ]

#     where_clauses = ["type_of_collection = 'Scheme'", "name_of_type IS NOT NULL", "name_of_type != ''"]
#     query_values = []

#     if filters.get("from_date") and filters.get("to_date"):
#         where_clauses.append("creation BETWEEN %s AND %s")
#         query_values.extend([filters.get("from_date"), filters.get("to_date")])

#     if filters.get("lab_name"):
#         where_clauses.append("(lab_name = %s OR target_lab = %s)")
#         query_values.extend([filters.get("lab_name"), filters.get("lab_name")])

#     if filters.get("scheme"):
#         where_clauses.append("name_of_type = %s")
#         query_values.append(filters.get("scheme"))

#     where_str = " AND ".join(where_clauses)

#     query = f"""
#         SELECT 
#             COALESCE(district_name, 'Not Specified') as district_name,
#             COALESCE(panchayath_name, municipality, 'Not Specified') as panchayat_name,
#             name_of_type as scheme_name,
#             COALESCE(target_lab, 'Not Specified') as target_lab,
#             COALESCE(district_office_name, 'Not Specified') as district_office_name,
#             COUNT(name) as sample_count
#         FROM `tabSoil Sample Collection`
#         WHERE {where_str}
#         GROUP BY district_name, panchayat_name, name_of_type, target_lab, district_office_name
#         ORDER BY district_name, panchayat_name, name_of_type asc
#     """

#     results = frappe.db.sql(query, tuple(query_values), as_dict=True)

#     data = []
#     for i, row in enumerate(results, start=1):
#         dist = row.get("district_name")
#         p_name = row.get("panchayat_name")
#         s_name = row.get("scheme_name")
#         t_lab = row.get("target_lab")

#         link = (
#             f'<a href="/app/soil-sample-collection?type_of_collection=Scheme'
#             f'&name_of_type={s_name}&district_name={dist}">'
#             f'<b>{row.get("sample_count")}</b></a>'
#         )

#         data.append({
#             "idx": i,
#             "district_name": dist,
#             "panchayat_name": p_name,
#             "scheme_name": s_name,
#             "target_lab": t_lab,
#             "district_office_name": row.get("district_office_name"),
#             "sample_count": link
#         })

#     return columns, data










# Copyright (c) 2026, navaneeth and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
    filters = filters or {}

    # Role-based restriction: If user is not 'slis_admin', force lab_name filter to their employee profile lab
    if "slis_admin" not in frappe.get_roles(frappe.session.user):
        user_lab = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "custom_lab_name")
        if user_lab:
            filters["lab_name"] = user_lab
        else:
            # Fallback value if no employee record or lab is linked, ensuring no unauthorized data leaks
            filters["lab_name"] = "__No_Lab_Assigned__"

    columns = [
        {"label": _("Sl. No"), "fieldname": "idx", "fieldtype": "Int", "width": 160},
        {"label": _("District"), "fieldname": "district_name", "fieldtype": "Data", "width": 240},
        {"label": _("Panchayat / Municipality"), "fieldname": "panchayat_name", "fieldtype": "Data", "width": 280},
        {"label": _("Scheme Name"), "fieldname": "scheme_name", "fieldtype": "Data", "width": 280},
        {"label": _("Target Lab"), "fieldname": "target_lab", "fieldtype": "Link", "options": "Soil Laboratory", "width": 250},
        {"label": _("District Office Name"), "fieldname": "district_office_name", "fieldtype": "Data", "width": 260},
        {"label": _("Number of Samples"), "fieldname": "sample_count", "fieldtype": "HTML", "width": 230}
    ]

    where_clauses = ["type_of_collection = 'Scheme'", "name_of_type IS NOT NULL", "name_of_type != ''"]
    query_values = []

    if filters.get("from_date") and filters.get("to_date"):
        where_clauses.append("creation BETWEEN %s AND %s")
        query_values.extend([filters.get("from_date"), filters.get("to_date")])

    if filters.get("lab_name"):
        where_clauses.append("(lab_name = %s OR target_lab = %s)")
        query_values.extend([filters.get("lab_name"), filters.get("lab_name")])

    if filters.get("scheme"):
        where_clauses.append("name_of_type = %s")
        query_values.append(filters.get("scheme"))

    where_str = " AND ".join(where_clauses)

    query = f"""
        SELECT 
            COALESCE(district_name, 'Not Specified') as district_name,
            COALESCE(panchayath_name, municipality, 'Not Specified') as panchayat_name,
            name_of_type as scheme_name,
            COALESCE(target_lab, 'Not Specified') as target_lab,
            COALESCE(district_office_name, 'Not Specified') as district_office_name,
            COUNT(name) as sample_count
        FROM `tabSoil Sample Collection`
        WHERE {where_str}
        GROUP BY district_name, panchayat_name, name_of_type, target_lab, district_office_name
        ORDER BY district_name, panchayat_name, name_of_type asc
    """

    results = frappe.db.sql(query, tuple(query_values), as_dict=True)

    data = []
    for i, row in enumerate(results, start=1):
        dist = row.get("district_name")
        p_name = row.get("panchayat_name")
        s_name = row.get("scheme_name")
        t_lab = row.get("target_lab")

        link = (
            f'<a href="/app/soil-sample-collection?type_of_collection=Scheme'
            f'&name_of_type={s_name}&district_name={dist}">'
            f'<b>{row.get("sample_count")}</b></a>'
        )

        data.append({
            "idx": i,
            "district_name": dist,
            "panchayat_name": p_name,
            "scheme_name": s_name,
            "target_lab": t_lab,
            "district_office_name": row.get("district_office_name"),
            "sample_count": link
        })

    return columns, data