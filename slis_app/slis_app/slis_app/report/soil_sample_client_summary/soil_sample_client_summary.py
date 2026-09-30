# import frappe

# def execute(filters=None):
#     filters = filters or {}

#     # Increased widths for a cleaner, wider layout across the screen
#     columns = [
#         {"label": "Sl. No", "fieldname": "idx", "fieldtype": "Int", "width": 280},
#         {"label": "District", "fieldname": "district", "fieldtype": "Data", "width": 340},
#         {"label": "Panchayat / Municipality", "fieldname": "panchayat_name", "fieldtype": "Data", "width": 340},
#         {"label": "Type of Client", "fieldname": "client_type", "fieldtype": "Data", "width": 340},
#         {"label": "Number of Samples", "fieldname": "sample_count", "fieldtype": "HTML", "width": 340}
#     ]

#     where_clauses = ["1=1"]
#     query_values = []

#     # Date Range Filter
#     if filters.get("from_date") and filters.get("to_date"):
#         where_clauses.append("creation BETWEEN %s AND %s")
#         query_values.extend([filters.get("from_date"), filters.get("to_date")])

#     # Client Type Filter
#     if filters.get("client_type"):
#         where_clauses.append("client_type = %s")
#         query_values.append(filters.get("client_type"))

#     # Lab Name Filter
#     if filters.get("lab_name"):
#         where_clauses.append("(lab_name = %s OR (client_type = 'Department' AND target_lab = %s))")
#         query_values.extend([filters.get("lab_name"), filters.get("lab_name")])

#     # Scheme Filter
#     if filters.get("scheme"):
#         where_clauses.append("client_type = 'Department' AND name_of_type = %s")
#         query_values.append(filters.get("scheme"))

#     where_str = " AND ".join(where_clauses)

#     query = f"""
#         SELECT 
#             COALESCE(district, 'Not Specified') as district,
#             COALESCE(panchayath_name, municipality, 'Not Specified') as panchayat_name,
#             COALESCE(client_type, 'Unspecified') as client_type,
#             COUNT(name) as sample_count
#         FROM `tabSoil Sample Collection`
#         WHERE {where_str}
#         GROUP BY district, panchayat_name, client_type
#         ORDER BY district, panchayat_name, client_type
#     """

#     results = frappe.db.sql(query, tuple(query_values), as_dict=True)

#     data = []
#     for i, row in enumerate(results, start=1):
#         p_name = row.get("panchayat_name")
#         dist = row.get("district")
#         c_type = row.get("client_type")

#         link = (
#             f'<a href="/app/soil-sample-collection?client_type={c_type}'
#             f'&district={dist}">'
#             f'<b>{row.get("sample_count")}</b></a>'
#         )

#         data.append({
#             "idx": i,
#             "district": dist,
#             "panchayat_name": p_name,
#             "client_type": c_type,
#             "sample_count": link
#         })

#     return columns, data

















import frappe

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

    # Increased widths for a cleaner, wider layout across the screen
    columns = [
        {"label": "Sl. No", "fieldname": "idx", "fieldtype": "Int", "width": 280},
        {"label": "District", "fieldname": "district", "fieldtype": "Data", "width": 340},
        {"label": "Panchayat / Municipality", "fieldname": "panchayat_name", "fieldtype": "Data", "width": 340},
        {"label": "Type of Client", "fieldname": "client_type", "fieldtype": "Data", "width": 340},
        {"label": "Number of Samples", "fieldname": "sample_count", "fieldtype": "HTML", "width": 340}
    ]

    where_clauses = ["1=1"]
    query_values = []

    # Date Range Filter
    if filters.get("from_date") and filters.get("to_date"):
        where_clauses.append("creation BETWEEN %s AND %s")
        query_values.extend([filters.get("from_date"), filters.get("to_date")])

    # Client Type Filter
    if filters.get("client_type"):
        where_clauses.append("client_type = %s")
        query_values.append(filters.get("client_type"))

    # Lab Name Filter
    if filters.get("lab_name"):
        where_clauses.append("(lab_name = %s OR (client_type = 'Department' AND target_lab = %s))")
        query_values.extend([filters.get("lab_name"), filters.get("lab_name")])

    # Scheme Filter
    if filters.get("scheme"):
        where_clauses.append("client_type = 'Department' AND name_of_type = %s")
        query_values.append(filters.get("scheme"))

    where_str = " AND ".join(where_clauses)

    query = f"""
        SELECT 
            COALESCE(district, 'Not Specified') as district,
            COALESCE(panchayath_name, municipality, 'Not Specified') as panchayat_name,
            COALESCE(client_type, 'Unspecified') as client_type,
            COUNT(name) as sample_count
        FROM `tabSoil Sample Collection`
        WHERE {where_str}
        GROUP BY district, panchayat_name, client_type
        ORDER BY district, panchayat_name, client_type
    """

    results = frappe.db.sql(query, tuple(query_values), as_dict=True)

    data = []
    for i, row in enumerate(results, start=1):
        p_name = row.get("panchayat_name")
        dist = row.get("district")
        c_type = row.get("client_type")

        link = (
            f'<a href="/app/soil-sample-collection?client_type={c_type}'
            f'&district={dist}">'
            f'<b>{row.get("sample_count")}</b></a>'
        )

        data.append({
            "idx": i,
            "district": dist,
            "panchayat_name": p_name,
            "client_type": c_type,
            "sample_count": link
        })

    return columns, data