# import frappe
# from frappe import _
# import calendar

# # ======================================================
# # DATE RANGE HELPER
# # ======================================================

# def build_date_range(selected_year, selected_month):
#     year_int = int(selected_year)

#     if selected_month and selected_month not in ("", "All Months", "None"):
#         month_int   = int(selected_month)
#         actual_year = year_int if month_int >= 4 else year_int + 1
#         last_day    = calendar.monthrange(actual_year, month_int)[1]
#         start       = f"{actual_year}-{month_int:02d}-01"
#         end         = f"{actual_year}-{month_int:02d}-{last_day:02d}"
#     else:
#         start = f"{year_int}-04-01"
#         end   = f"{year_int + 1}-03-31"

#     return start, end


# # ======================================================
# # PRINCIPAL SOIL CHEMIST DASHBOARD API
# # ======================================================

# @frappe.whitelist()
# def get_principal_dashboard_data(selected_year=None, selected_month=None, selected_lab=None):
#     if not selected_year:
#         return {"error": "no_year"}

#     start, end = build_date_range(selected_year, selected_month)
#     fy_start = f"{int(selected_year)}-04-01"
    
#     lab_logic = "COALESCE(NULLIF(ssc.lab_name, ''), ssc.target_lab)"
#     lab_logic_aliased = "COALESCE(NULLIF(ssc.lab_name, ''), ssc.target_lab)"
    
#     # Base filter condition
#     lab_filter_sql = ""
    
#     if selected_lab and selected_lab != "All Labs":
#         lab_filter_sql = f" AND ({lab_logic}) = %s "

#     # 1. Calculate Overall / Filtered Summary Cards
#     prev_balance_qry = f"""
#         SELECT COUNT(*) as cnt FROM `tabSoil Sample Collection` ssc
#         WHERE 1=1 {lab_filter_sql}
#           AND creation < %s
#           AND (status NOT IN ('Closed', 'Cancelled') OR (status = 'Closed' AND modified >= %s))
#     """
#     if selected_lab and selected_lab != "All Labs":
#         pb_params = [selected_lab, fy_start, fy_start]
#     else:
#         pb_params = [fy_start, fy_start]
        
#     prev_balance = frappe.db.sql(prev_balance_qry, pb_params, as_dict=True)[0].cnt or 0

#     received_qry = f"""
#         SELECT COUNT(*) as cnt FROM `tabSoil Sample Collection` ssc
#         WHERE 1=1 {lab_filter_sql}
#           AND assigned_to_lab_date BETWEEN %s AND %s
#     """
#     rec_params = [selected_lab, start, end] if (selected_lab and selected_lab != "All Labs") else [start, end]
#     received_period = frappe.db.sql(received_qry, rec_params, as_dict=True)[0].cnt or 0

#     cumulative_total = prev_balance + received_period

#     status_qry = f"""
#         SELECT status, COUNT(*) as cnt FROM `tabSoil Sample Collection` ssc
#         WHERE 1=1 {lab_filter_sql}
#           AND assigned_to_lab_date BETWEEN %s AND %s
#         GROUP BY status
#     """
#     status_params = [selected_lab, start, end] if (selected_lab and selected_lab != "All Labs") else [start, end]
#     status_rows = frappe.db.sql(status_qry, status_params, as_dict=True)
    
#     completed_tests = sum([r.cnt for r in status_rows if r.status in ["Closed", "Completed", "Tested"]])
#     pending_tests = sum([r.cnt for r in status_rows if r.status not in ["Closed", "Completed", "Tested", "Cancelled"]])

#     # Annual Non Tax Revenue: Statewide or Scoped to selected lab
#     if selected_lab and selected_lab != "All Labs":
#         non_tax_qry = f"""
#             SELECT SUM(tsp.net_payable_amount) as total_revenue 
#             FROM `tabSoil Sample Payment` tsp
#             JOIN `tabSoil Sample Collection` ssc ON ssc.name = tsp.soil_sample_id
#             WHERE tsp.soil_sample_id LIKE 'FS-%%'
#               AND tsp.payment_date BETWEEN %s AND %s
#               AND ({lab_logic_aliased}) = %s
#         """
#         non_tax_res = frappe.db.sql(non_tax_qry, [start, end, selected_lab], as_dict=True)
#     else:
#         non_tax_qry = f"""
#             SELECT SUM(net_payable_amount) as total_revenue 
#             FROM `tabSoil Sample Payment`
#             WHERE soil_sample_id LIKE 'FS-%%'
#               AND payment_date BETWEEN %s AND %s
#         """
#         non_tax_res = frappe.db.sql(non_tax_qry, [start, end], as_dict=True)

#     annual_non_tax_revenue = non_tax_res[0].total_revenue or 0.0 if non_tax_res else 0.0

#     # 2. Laboratory Summary Table (Breakdown across all labs or specific lab)
#     lab_summary_qry = f"""
#         SELECT 
#             COALESCE(NULLIF(ssc.lab_name, ''), ssc.target_lab, 'Unassigned') AS laboratory,
#             SUM(CASE WHEN ssc.creation < %s AND (ssc.status NOT IN ('Closed', 'Cancelled') OR (ssc.status = 'Closed' AND ssc.modified >= %s)) THEN 1 ELSE 0 END) AS prev_balance,
#             SUM(CASE WHEN ssc.assigned_to_lab_date BETWEEN %s AND %s THEN 1 ELSE 0 END) AS received,
#             SUM(CASE WHEN ssc.assigned_to_lab_date BETWEEN %s AND %s AND ssc.status IN ('Closed', 'Completed', 'Tested') THEN 1 ELSE 0 END) AS completed,
#             SUM(CASE WHEN ssc.assigned_to_lab_date BETWEEN %s AND %s AND ssc.status NOT IN ('Closed', 'Completed', 'Tested', 'Cancelled') THEN 1 ELSE 0 END) AS pending
#         FROM `tabSoil Sample Collection` ssc
#         WHERE 1=1 {lab_filter_sql}
#         GROUP BY laboratory
#         ORDER BY received DESC
#     """
    
#     if selected_lab and selected_lab != "All Labs":
#         ls_params = [fy_start, fy_start, start, end, start, end, start, end, selected_lab]
#     else:
#         ls_params = [fy_start, fy_start, start, end, start, end, start, end]

#     lab_summary_rows = frappe.db.sql(lab_summary_qry, ls_params, as_dict=True)
    
#     lab_summary = []
#     for r in lab_summary_rows:
#         lab_summary.append({
#             "laboratory": r.laboratory,
#             "prev_balance": r.prev_balance or 0,
#             "received": r.received or 0,
#             "completed": r.completed or 0,
#             "pending": r.pending or 0
#         })

#     # 3. Scheme-wise Breakdown Table
#     scheme_qry = f"""
#         SELECT
#             COALESCE(NULLIF(ssc.lab_name, ''), ssc.target_lab, 'Unassigned') AS laboratory,
#             COALESCE(c.custom_name_of_type, 'General / Other') AS scheme_name,
#             COUNT(ssc.name) AS received,
#             SUM(CASE WHEN ssc.status IN ('Closed', 'Completed', 'Tested') THEN 1 ELSE 0 END) AS completed,
#             SUM(CASE WHEN ssc.status NOT IN ('Closed', 'Completed', 'Tested', 'Cancelled') THEN 1 ELSE 0 END) AS pending
#         FROM `tabSoil Sample Collection` ssc
#         LEFT JOIN `tabClients` c ON c.name = ssc.client
#         WHERE 1=1 {lab_filter_sql}
#           AND ssc.assigned_to_lab_date BETWEEN %s AND %s
#         GROUP BY laboratory, scheme_name
#         ORDER BY received DESC
#     """

#     if selected_lab and selected_lab != "All Labs":
#         sch_params = [selected_lab, start, end]
#     else:
#         sch_params = [start, end]

#     scheme_rows = frappe.db.sql(scheme_qry, sch_params, as_dict=True)

#     scheme_summary = []
#     for row in scheme_rows:
#         scheme_summary.append({
#             "laboratory": row.laboratory,
#             "scheme_name": row.scheme_name,
#             "received": row.received or 0,
#             "completed": row.completed or 0,
#             "pending": row.pending or 0
#         })

#     # 4. Designation-wise Employee Count (lab-aware)
#     emp_lab_filter_sql = ""
#     desig_params = []
#     if selected_lab and selected_lab != "All Labs":
#         emp_lab_filter_sql = " AND e.custom_lab_name = %s "
#         desig_params = [selected_lab]

#     designation_qry = f"""
#         SELECT
#             d.name AS designation,
#             COUNT(e.name) AS employee_count
#         FROM `tabDesignation` d
#         LEFT JOIN `tabEmployee` e
#             ON e.designation = d.name
#             AND e.status = 'Active'
#             {emp_lab_filter_sql}
#         GROUP BY d.name
#         ORDER BY employee_count DESC
#     """
#     designation_rows = frappe.db.sql(designation_qry, desig_params, as_dict=True)

#     designation_summary = [
#         {
#             "designation": row.designation,
#             "employee_count": row.employee_count or 0
#         }
#         for row in designation_rows
#     ]

#     # Fetch list of all available labs for the filter dropdown
#     all_labs = frappe.db.get_list("Soil Laboratory", pluck="name")

#     return {
#         "all_labs": all_labs,
#         "cards": {
#             "prev_year_balance": prev_balance,
#             "received_period": received_period,
#             "cumulative_total": cumulative_total,
#             "completed_tests": completed_tests,
#             "pending_tests": pending_tests,
#             "annual_non_tax_revenue": annual_non_tax_revenue
#         },
#         "lab_summary": lab_summary,
#         "scheme_summary": scheme_summary,
#         "designation_summary": designation_summary
#     }


import frappe
from frappe import _
import calendar

# ======================================================
# DATE RANGE HELPER
# ======================================================

def build_date_range(selected_year, selected_month):
    year_int = int(selected_year)

    if selected_month and selected_month not in ("", "All Months", "None"):
        month_int   = int(selected_month)
        actual_year = year_int if month_int >= 4 else year_int + 1
        last_day    = calendar.monthrange(actual_year, month_int)[1]
        start       = f"{actual_year}-{month_int:02d}-01"
        end         = f"{actual_year}-{month_int:02d}-{last_day:02d}"
    else:
        start = f"{year_int}-04-01"
        end   = f"{year_int + 1}-03-31"

    return start, end


# ======================================================
# PRINCIPAL SOIL CHEMIST DASHBOARD API
# ======================================================

@frappe.whitelist()
def get_principal_dashboard_data(selected_year=None, selected_month=None, selected_lab=None):
    if not selected_year:
        return {"error": "no_year"}

    start, end = build_date_range(selected_year, selected_month)
    fy_start = f"{int(selected_year)}-04-01"
    
    lab_logic = "COALESCE(NULLIF(ssc.lab_name, ''), ssc.target_lab)"
    lab_logic_aliased = "COALESCE(NULLIF(ssc.lab_name, ''), ssc.target_lab)"
    
    # Base filter condition
    lab_filter_sql = ""
    
    if selected_lab and selected_lab != "All Labs":
        lab_filter_sql = f" AND ({lab_logic}) = %s "

    # 1. Calculate Overall / Filtered Summary Cards
    prev_balance_qry = f"""
        SELECT COUNT(*) as cnt FROM `tabSoil Sample Collection` ssc
        WHERE 1=1 {lab_filter_sql}
          AND creation < %s
          AND (status NOT IN ('Closed', 'Cancelled') OR (status = 'Closed' AND modified >= %s))
    """
    if selected_lab and selected_lab != "All Labs":
        pb_params = [selected_lab, fy_start, fy_start]
    else:
        pb_params = [fy_start, fy_start]
        
    prev_balance = frappe.db.sql(prev_balance_qry, pb_params, as_dict=True)[0].cnt or 0

    received_qry = f"""
        SELECT COUNT(*) as cnt FROM `tabSoil Sample Collection` ssc
        WHERE 1=1 {lab_filter_sql}
          AND assigned_to_lab_date BETWEEN %s AND %s
    """
    rec_params = [selected_lab, start, end] if (selected_lab and selected_lab != "All Labs") else [start, end]
    received_period = frappe.db.sql(received_qry, rec_params, as_dict=True)[0].cnt or 0

    cumulative_total = prev_balance + received_period

    status_qry = f"""
        SELECT status, COUNT(*) as cnt FROM `tabSoil Sample Collection` ssc
        WHERE 1=1 {lab_filter_sql}
          AND assigned_to_lab_date BETWEEN %s AND %s
        GROUP BY status
    """
    status_params = [selected_lab, start, end] if (selected_lab and selected_lab != "All Labs") else [start, end]
    status_rows = frappe.db.sql(status_qry, status_params, as_dict=True)
    
    completed_tests = sum([r.cnt for r in status_rows if r.status in ["Closed", "Completed", "Tested"]])
    pending_tests = sum([r.cnt for r in status_rows if r.status not in ["Closed", "Completed", "Tested", "Cancelled"]])

    # Annual Non Tax Revenue: Statewide or Scoped to selected lab
    if selected_lab and selected_lab != "All Labs":
        non_tax_qry = f"""
            SELECT SUM(tsp.net_payable_amount) as total_revenue 
            FROM `tabSoil Sample Payment` tsp
            JOIN `tabSoil Sample Collection` ssc ON ssc.name = tsp.soil_sample_id
             WHERE (tsp.soil_sample_id LIKE 'FS-%%' OR tsp.soil_sample_id LIKE 'CS-%%')
              AND tsp.payment_date BETWEEN %s AND %s
              AND ({lab_logic_aliased}) = %s
        """
        non_tax_res = frappe.db.sql(non_tax_qry, [start, end, selected_lab], as_dict=True)
    else:
        non_tax_qry = f"""
            SELECT SUM(net_payable_amount) as total_revenue 
            FROM `tabSoil Sample Payment`
            WHERE (soil_sample_id LIKE 'FS-%%' OR soil_sample_id LIKE 'CS-%%')
              AND payment_date BETWEEN %s AND %s
        """
        non_tax_res = frappe.db.sql(non_tax_qry, [start, end], as_dict=True)

    annual_non_tax_revenue = non_tax_res[0].total_revenue or 0.0 if non_tax_res else 0.0

    # 2. Laboratory Summary Table (Breakdown across all labs or specific lab)
    lab_summary_qry = f"""
        SELECT 
            COALESCE(NULLIF(ssc.lab_name, ''), ssc.target_lab, 'Unassigned') AS laboratory,
            SUM(CASE WHEN ssc.creation < %s AND (ssc.status NOT IN ('Closed', 'Cancelled') OR (ssc.status = 'Closed' AND ssc.modified >= %s)) THEN 1 ELSE 0 END) AS prev_balance,
            SUM(CASE WHEN ssc.assigned_to_lab_date BETWEEN %s AND %s THEN 1 ELSE 0 END) AS received,
            SUM(CASE WHEN ssc.assigned_to_lab_date BETWEEN %s AND %s AND ssc.status IN ('Closed', 'Completed', 'Tested') THEN 1 ELSE 0 END) AS completed,
            SUM(CASE WHEN ssc.assigned_to_lab_date BETWEEN %s AND %s AND ssc.status NOT IN ('Closed', 'Completed', 'Tested', 'Cancelled') THEN 1 ELSE 0 END) AS pending
        FROM `tabSoil Sample Collection` ssc
        WHERE 1=1 {lab_filter_sql}
        GROUP BY laboratory
        ORDER BY received DESC
    """
    
    if selected_lab and selected_lab != "All Labs":
        ls_params = [fy_start, fy_start, start, end, start, end, start, end, selected_lab]
    else:
        ls_params = [fy_start, fy_start, start, end, start, end, start, end]

    lab_summary_rows = frappe.db.sql(lab_summary_qry, ls_params, as_dict=True)
    
    lab_summary = []
    for r in lab_summary_rows:
        lab_summary.append({
            "laboratory": r.laboratory,
            "prev_balance": r.prev_balance or 0,
            "received": r.received or 0,
            "completed": r.completed or 0,
            "pending": r.pending or 0
        })

    # 3. Scheme-wise Breakdown Table
    scheme_qry = f"""
        SELECT
            COALESCE(NULLIF(ssc.lab_name, ''), ssc.target_lab, 'Unassigned') AS laboratory,
            COALESCE(c.custom_name_of_type, 'General / Other') AS scheme_name,
            COUNT(ssc.name) AS received,
            SUM(CASE WHEN ssc.status IN ('Closed', 'Completed', 'Tested') THEN 1 ELSE 0 END) AS completed,
            SUM(CASE WHEN ssc.status NOT IN ('Closed', 'Completed', 'Tested', 'Cancelled') THEN 1 ELSE 0 END) AS pending
        FROM `tabSoil Sample Collection` ssc
        LEFT JOIN `tabClients` c ON c.name = ssc.client
        WHERE 1=1 {lab_filter_sql}
          AND ssc.assigned_to_lab_date BETWEEN %s AND %s
        GROUP BY laboratory, scheme_name
        ORDER BY received DESC
    """

    if selected_lab and selected_lab != "All Labs":
        sch_params = [selected_lab, start, end]
    else:
        sch_params = [start, end]

    scheme_rows = frappe.db.sql(scheme_qry, sch_params, as_dict=True)

    scheme_summary = []
    for row in scheme_rows:
        scheme_summary.append({
            "laboratory": row.laboratory,
            "scheme_name": row.scheme_name,
            "received": row.received or 0,
            "completed": row.completed or 0,
            "pending": row.pending or 0
        })

    # 4. Designation-wise Employee Count (lab-aware)
    emp_lab_filter_sql = ""
    desig_params = []
    if selected_lab and selected_lab != "All Labs":
        emp_lab_filter_sql = " AND e.custom_lab_name = %s "
        desig_params = [selected_lab]

    designation_qry = f"""
        SELECT
            d.name AS designation,
            COUNT(e.name) AS employee_count
        FROM `tabDesignation` d
        LEFT JOIN `tabEmployee` e
            ON e.designation = d.name
            AND e.status = 'Active'
            {emp_lab_filter_sql}
        GROUP BY d.name
        ORDER BY employee_count DESC
    """
    designation_rows = frappe.db.sql(designation_qry, desig_params, as_dict=True)

    designation_summary = [
        {
            "designation": row.designation,
            "employee_count": row.employee_count or 0
        }
        for row in designation_rows
    ]

    # Fetch list of all available labs for the filter dropdown
    all_labs = frappe.db.get_list("Soil Laboratory", pluck="name")

    return {
        "all_labs": all_labs,
        "cards": {
            "prev_year_balance": prev_balance,
            "received_period": received_period,
            "cumulative_total": cumulative_total,
            "completed_tests": completed_tests,
            "pending_tests": pending_tests,
            "annual_non_tax_revenue": annual_non_tax_revenue
        },
        "lab_summary": lab_summary,
        "scheme_summary": scheme_summary,
        "designation_summary": designation_summary
    }