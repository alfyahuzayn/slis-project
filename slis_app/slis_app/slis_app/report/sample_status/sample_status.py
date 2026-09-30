
# import frappe

# def execute(filters=None):
#     filters = filters or {}

#     columns = [
#         {
#             "label": "Status Category",
#             "fieldname": "status_category",
#             "fieldtype": "Data",
#             "width": 180
#         },
#         {
#             "label": "Total Completed",
#             "fieldname": "total_completed",
#             "fieldtype": "HTML",
#             "width": 140
#         },
#         {
#             "label": "Total Pending",
#             "fieldname": "total_pending",
#             "fieldtype": "HTML",
#             "width": 140
#         },
#         {
#             "label": "Farmer Total",
#             "fieldname": "farmer_total",
#             "fieldtype": "HTML",
#             "width": 130
#         },
#         {
#             "label": "Consultancy Total",
#             "fieldname": "consultancy_total",
#             "fieldtype": "HTML",
#             "width": 160
#         },
#         {
#             "label": "Department Total",
#             "fieldname": "department_total",
#             "fieldtype": "HTML",
#             "width": 150
#         },
#         {
#             "label": "Farmer Pending",
#             "fieldname": "farmer_pending",
#             "fieldtype": "HTML",
#             "width": 140
#         },
#         {
#             "label": "Consultancy Pending",
#             "fieldname": "consultancy_pending",
#             "fieldtype": "HTML",
#             "width": 170
#         },
#         {
#             "label": "Department Pending",
#             "fieldname": "department_pending",
#             "fieldtype": "HTML",
#             "width": 160
#         }
#     ]

#     def get_filtered_count(extra_where=""):
#         query = "SELECT COUNT(*) FROM `tabSoil Sample Collection` WHERE 1=1"
#         query_values = []

#         # Date Filter
#         if filters.get("from_date") and filters.get("to_date"):
#             query += " AND creation BETWEEN %s AND %s"
#             query_values.extend([filters.get("from_date"), filters.get("to_date")])

#         # Lab Name Filter (Lab Name OR (Department client type & Target Lab))
#         if filters.get("lab_name"):
#             query += " AND (lab_name = %s OR (client_type = 'Department' AND target_lab = %s))"
#             query_values.extend([filters.get("lab_name"), filters.get("lab_name")])

#         # Scheme Filter (Department client type & matching scheme name_of_type)
#         if filters.get("scheme"):
#             query += " AND client_type = 'Department' AND name_of_type = %s"
#             query_values.append(filters.get("scheme"))

#         # Extra dynamic conditions (e.g., status, client_type)
#         if extra_where:
#             query += f" AND {extra_where}"

#         return frappe.db.sql(query, tuple(query_values))[0][0] or 0

#     # Metrics calculation calls
#     completed_count = get_filtered_count("status = 'Completed'")
#     pending_count = get_filtered_count("status NOT IN ('Completed', 'Draft')")

#     farmer_total = get_filtered_count("client_type = 'Farmer'")
#     consultancy_total = get_filtered_count("client_type = 'Consultancy'")
#     department_total = get_filtered_count("client_type = 'Department'")

#     farmer_pending = get_filtered_count("status NOT IN ('Completed', 'Draft') AND client_type = 'Farmer'")
#     consultancy_pending = get_filtered_count("status NOT IN ('Completed', 'Draft') AND client_type = 'Consultancy'")
#     department_pending = get_filtered_count("status NOT IN ('Completed', 'Draft') AND client_type = 'Department'")

#     # HTML Links for drill-down redirection
#     completed_link = f'<a href="/app/soil-sample-collection?status=Completed"><b>{completed_count}</b></a>'
#     pending_link = f'<a href="/app/soil-sample-collection"><b>{pending_count}</b></a>'
    
#     farmer_total_link = f'<a href="/app/soil-sample-collection?client_type=Farmer"><b>{farmer_total}</b></a>'
#     consultancy_total_link = f'<a href="/app/soil-sample-collection?client_type=Consultancy"><b>{consultancy_total}</b></a>'
#     department_total_link = f'<a href="/app/soil-sample-collection?client_type=Department"><b>{department_total}</b></a>'

#     farmer_pending_link = f'<a href="/app/soil-sample-collection?client_type=Farmer"><b>{farmer_pending}</b></a>'
#     consultancy_pending_link = f'<a href="/app/soil-sample-collection?client_type=Consultancy"><b>{consultancy_pending}</b></a>'
#     department_pending_link = f'<a href="/app/soil-sample-collection?client_type=Department"><b>{department_pending}</b></a>'

#     data = [
#         {
#             "status_category": "Metrics Summary",
#             "total_completed": completed_link,
#             "total_pending": pending_link,
#             "farmer_total": farmer_total_link,
#             "consultancy_total": consultancy_total_link,
#             "department_total": department_total_link,
#             "farmer_pending": farmer_pending_link,
#             "consultancy_pending": consultancy_pending_link,
#             "department_pending": department_pending_link
#         }
#     ]

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

    columns = [
        {
            "label": "Status Category",
            "fieldname": "status_category",
            "fieldtype": "Data",
            "width": 180
        },
        {
            "label": "Total Completed",
            "fieldname": "total_completed",
            "fieldtype": "HTML",
            "width": 140
        },
        {
            "label": "Total Pending",
            "fieldname": "total_pending",
            "fieldtype": "HTML",
            "width": 140
        },
        {
            "label": "Farmer Total",
            "fieldname": "farmer_total",
            "fieldtype": "HTML",
            "width": 130
        },
        {
            "label": "Consultancy Total",
            "fieldname": "consultancy_total",
            "fieldtype": "HTML",
            "width": 160
        },
        {
            "label": "Department Total",
            "fieldname": "department_total",
            "fieldtype": "HTML",
            "width": 150
        },
        {
            "label": "Farmer Pending",
            "fieldname": "farmer_pending",
            "fieldtype": "HTML",
            "width": 140
        },
        {
            "label": "Consultancy Pending",
            "fieldname": "consultancy_pending",
            "fieldtype": "HTML",
            "width": 170
        },
        {
            "label": "Department Pending",
            "fieldname": "department_pending",
            "fieldtype": "HTML",
            "width": 160
        }
    ]

    def get_filtered_count(extra_where=""):
        query = "SELECT COUNT(*) FROM `tabSoil Sample Collection` WHERE 1=1"
        query_values = []

        # Date Filter
        if filters.get("from_date") and filters.get("to_date"):
            query += " AND creation BETWEEN %s AND %s"
            query_values.extend([filters.get("from_date"), filters.get("to_date")])

        # Lab Name Filter (Lab Name OR (Department client type & Target Lab))
        if filters.get("lab_name"):
            query += " AND (lab_name = %s OR (client_type = 'Department' AND target_lab = %s))"
            query_values.extend([filters.get("lab_name"), filters.get("lab_name")])

        # Scheme Filter (Department client type & matching scheme name_of_type)
        if filters.get("scheme"):
            query += " AND client_type = 'Department' AND name_of_type = %s"
            query_values.append(filters.get("scheme"))

        # Extra dynamic conditions (e.g., status, client_type)
        if extra_where:
            query += f" AND {extra_where}"

        return frappe.db.sql(query, tuple(query_values))[0][0] or 0

    # Metrics calculation calls
    completed_count = get_filtered_count("status = 'Completed'")
    pending_count = get_filtered_count("status NOT IN ('Completed', 'Draft')")

    farmer_total = get_filtered_count("client_type = 'Farmer'")
    consultancy_total = get_filtered_count("client_type = 'Consultancy'")
    department_total = get_filtered_count("client_type = 'Department'")

    farmer_pending = get_filtered_count("status NOT IN ('Completed', 'Draft') AND client_type = 'Farmer'")
    consultancy_pending = get_filtered_count("status NOT IN ('Completed', 'Draft') AND client_type = 'Consultancy'")
    department_pending = get_filtered_count("status NOT IN ('Completed', 'Draft') AND client_type = 'Department'")

    # HTML Links for drill-down redirection
    completed_link = f'<a href="/app/soil-sample-collection?status=Completed"><b>{completed_count}</b></a>'
    pending_link = f'<a href="/app/soil-sample-collection"><b>{pending_count}</b></a>'
    
    farmer_total_link = f'<a href="/app/soil-sample-collection?client_type=Farmer"><b>{farmer_total}</b></a>'
    consultancy_total_link = f'<a href="/app/soil-sample-collection?client_type=Consultancy"><b>{consultancy_total}</b></a>'
    department_total_link = f'<a href="/app/soil-sample-collection?client_type=Department"><b>{department_total}</b></a>'

    farmer_pending_link = f'<a href="/app/soil-sample-collection?client_type=Farmer"><b>{farmer_pending}</b></a>'
    consultancy_pending_link = f'<a href="/app/soil-sample-collection?client_type=Consultancy"><b>{consultancy_pending}</b></a>'
    department_pending_link = f'<a href="/app/soil-sample-collection?client_type=Department"><b>{department_pending}</b></a>'

    data = [
        {
            "status_category": "Metrics Summary",
            "total_completed": completed_link,
            "total_pending": pending_link,
            "farmer_total": farmer_total_link,
            "consultancy_total": consultancy_total_link,
            "department_total": department_total_link,
            "farmer_pending": farmer_pending_link,
            "consultancy_pending": consultancy_pending_link,
            "department_pending": department_pending_link
        }
    ]

    return columns, data