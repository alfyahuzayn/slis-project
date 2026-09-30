# # new code for the annual non tax revenue card inclusion
# import frappe
# from frappe import _
# import calendar

# # ======================================================
# # COMPLETED STATUS DEFINITION
# # ======================================================

# COMPLETED_STATUSES = [
#     "SC Verifying Results",
#     "SC Verified Results",
#     "AD Verifying Results",
#     "AD Verified Results",
#     "Ready to Publish",
#     "Result Published",
# ]

# # Exclude master / master-profile sample rows from every count and every list of names.
# MASTER_SAMPLE_EXCLUSION = """
#     AND (
#         (COALESCE(is_master_sample, 0) != 1 AND COALESCE(master_profile_sample, 0) != 1)
#         OR COALESCE(number_of_samples, 1) <= 1
#     )
# """

# MASTER_SAMPLE_EXCLUSION_SSC = """
#     AND (
#         (COALESCE(ssc.is_master_sample, 0) != 1 AND COALESCE(ssc.master_profile_sample, 0) != 1)
#         OR COALESCE(ssc.number_of_samples, 1) <= 1
#     )
# """


# # ======================================================
# # GET USER'S LAB
# # ======================================================

# def get_user_lab():
#     user = frappe.session.user

#     employee = frappe.db.get_value(
#         "Employee",
#         {"user_id": user},
#         ["employment_type", "custom_lab_name", "custom_district_office_name"],
#         as_dict=True
#     )

#     if not employee:
#         return None

#     if employee.employment_type == "District Office":
#         return employee.custom_district_office_name or None
#     else:
#         return employee.custom_lab_name or None


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
# # SUMMARY CARDS & TABLE DATA API
# # ======================================================

# @frappe.whitelist()
# def get_sc_dashboard_data(selected_year=None, selected_month=None):
#     if not selected_year:
#         return {"error": "no_year"}

#     laboratory = get_user_lab()
#     if not laboratory:
#         return {"error": "no_lab"}

#     start, end = build_date_range(selected_year, selected_month)
    
#     # Financial Year start for Prev Year Balance calculation
#     fy_start = f"{int(selected_year)}-04-01"
#     lab_logic = "COALESCE(NULLIF(lab_name, ''), target_lab)"
#     lab_logic_aliased = "COALESCE(NULLIF(ssc.lab_name, ''), ssc.target_lab)"

#     completed_placeholders = ", ".join(["%s"] * len(COMPLETED_STATUSES))

#     # 1. Calculate Metrics Cards
#     # Prev Year Balance: Samples created before FY start that were not closed/cancelled
#     prev_balance_qry = f"""
#         SELECT COUNT(*) as cnt FROM `tabSoil Sample Collection`
#         WHERE ({lab_logic}) = %s
#           AND creation < %s
#           AND (status NOT IN ({completed_placeholders}, 'Cancelled') OR (status IN ({completed_placeholders}) AND modified >= %s))
#           {MASTER_SAMPLE_EXCLUSION}
#     """
#     prev_balance_params = [laboratory, fy_start] + COMPLETED_STATUSES + COMPLETED_STATUSES + [fy_start]
#     prev_balance = frappe.db.sql(prev_balance_qry, prev_balance_params, as_dict=True)[0].cnt or 0

#     # Received Period: Assigned to lab within selected date range
#     received_qry = f"""
#         SELECT COUNT(*) as cnt FROM `tabSoil Sample Collection`
#         WHERE ({lab_logic}) = %s
#           AND assigned_to_lab_date BETWEEN %s AND %s
#           {MASTER_SAMPLE_EXCLUSION}
#     """
#     received_period = frappe.db.sql(received_qry, [laboratory, start, end], as_dict=True)[0].cnt or 0

#     cumulative_total = prev_balance + received_period

#     # Completed Tests & Pending Tests within range/status
#     status_qry = f"""
#         SELECT status, COUNT(*) as cnt FROM `tabSoil Sample Collection`
#         WHERE ({lab_logic}) = %s
#           AND assigned_to_lab_date BETWEEN %s AND %s
#           {MASTER_SAMPLE_EXCLUSION}
#         GROUP BY status
#     """
#     status_rows = frappe.db.sql(status_qry, [laboratory, start, end], as_dict=True)
    
#     completed_tests = sum([r.cnt for r in status_rows if r.status in COMPLETED_STATUSES])
#     pending_tests = sum([r.cnt for r in status_rows if r.status not in COMPLETED_STATUSES + ["Cancelled"]])

#     # Annual Non Tax Revenue: Sum of net_payable_amount for farmer samples (FS-) joined with lab scoping and date filter
#     non_tax_qry = f"""
#         SELECT SUM(tsp.net_payable_amount) as total_revenue 
#         FROM `tabSoil Sample Payment` tsp
#         JOIN `tabSoil Sample Collection` ssc ON ssc.name = tsp.soil_sample_id
#         WHERE tsp.soil_sample_id LIKE 'FS-%%'
#           AND tsp.payment_date BETWEEN %s AND %s
#           AND ({lab_logic_aliased}) = %s
#     """
#     non_tax_res = frappe.db.sql(non_tax_qry, [start, end, laboratory], as_dict=True)
#     annual_non_tax_revenue = non_tax_res[0].total_revenue or 0.0 if non_tax_res else 0.0

#     # 2. Laboratory Summary Table Row (Scoped strictly to user's lab)
#     lab_summary = [{
#         "laboratory": laboratory,
#         "prev_balance": prev_balance,
#         "received": received_period,
#         "completed": completed_tests,
#         "pending": pending_tests
#     }]

#     # 3. Scheme-wise Sample Breakdown Table (Using aliased lab logic to avoid ambiguity)
#     scheme_qry = f"""
#         SELECT
#             COALESCE(c.custom_name_of_type, 'General / Other') AS scheme_name,
#             COUNT(ssc.name) AS received,
#             SUM(CASE WHEN ssc.status IN ({completed_placeholders}) THEN 1 ELSE 0 END) AS completed,
#             SUM(CASE WHEN ssc.status NOT IN ({completed_placeholders}, 'Cancelled') THEN 1 ELSE 0 END) AS pending
#         FROM `tabSoil Sample Collection` ssc
#         LEFT JOIN `tabClients` c ON c.name = ssc.client
#         WHERE ({lab_logic_aliased}) = %s
#           AND ssc.assigned_to_lab_date BETWEEN %s AND %s
#           {MASTER_SAMPLE_EXCLUSION_SSC}
#         GROUP BY scheme_name
#         ORDER BY received DESC
#     """
#     scheme_params = COMPLETED_STATUSES + COMPLETED_STATUSES + [laboratory, start, end]
#     scheme_rows = frappe.db.sql(scheme_qry, scheme_params, as_dict=True)

#     scheme_summary = []
#     for row in scheme_rows:
#         scheme_summary.append({
#             "laboratory": laboratory,
#             "scheme_name": row.scheme_name,
#             "received": row.received or 0,
#             "completed": row.completed or 0,
#             "pending": row.pending or 0
#         })

#     return {
#         "lab": laboratory,
#         "cards": {
#             "prev_year_balance": prev_balance,
#             "received_period": received_period,
#             "cumulative_total": cumulative_total,
#             "completed_tests": completed_tests,
#             "pending_tests": pending_tests,
#             "annual_non_tax_revenue": annual_non_tax_revenue
#         },
#         "lab_summary": lab_summary,
#         "scheme_summary": scheme_summary
#     }











# if the revenue inclues the dept. samples also:
import frappe
from frappe import _
import calendar

# ======================================================
# COMPLETED STATUS DEFINITION
# ======================================================

COMPLETED_STATUSES = [
    "SC Verifying Results",
    "SC Verified Results",
    "AD Verifying Results",
    "AD Verified Results",
    "Ready to Publish",
    "Result Published",
]

# Exclude master / master-profile sample rows from every count and every list of names.
MASTER_SAMPLE_EXCLUSION = """
    AND (
        (COALESCE(is_master_sample, 0) != 1 AND COALESCE(master_profile_sample, 0) != 1)
        OR COALESCE(number_of_samples, 1) <= 1
    )
"""

MASTER_SAMPLE_EXCLUSION_SSC = """
    AND (
        (COALESCE(ssc.is_master_sample, 0) != 1 AND COALESCE(ssc.master_profile_sample, 0) != 1)
        OR COALESCE(ssc.number_of_samples, 1) <= 1
    )
"""


# ======================================================
# GET USER'S LAB
# ======================================================

def get_user_lab():
    user = frappe.session.user

    employee = frappe.db.get_value(
        "Employee",
        {"user_id": user},
        ["employment_type", "custom_lab_name", "custom_district_office_name"],
        as_dict=True
    )

    if not employee:
        return None

    if employee.employment_type == "District Office":
        return employee.custom_district_office_name or None
    else:
        return employee.custom_lab_name or None


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
# SUMMARY CARDS & TABLE DATA API
# ======================================================

@frappe.whitelist()
def get_sc_dashboard_data(selected_year=None, selected_month=None):
    if not selected_year:
        return {"error": "no_year"}

    laboratory = get_user_lab()
    if not laboratory:
        return {"error": "no_lab"}

    start, end = build_date_range(selected_year, selected_month)
    
    # Financial Year start for Prev Year Balance calculation
    fy_start = f"{int(selected_year)}-04-01"
    lab_logic = "COALESCE(NULLIF(lab_name, ''), target_lab)"
    lab_logic_aliased = "COALESCE(NULLIF(ssc.lab_name, ''), ssc.target_lab)"

    completed_placeholders = ", ".join(["%s"] * len(COMPLETED_STATUSES))

    # 1. Calculate Metrics Cards
    # Prev Year Balance: Samples created before FY start that were not closed/cancelled
    prev_balance_qry = f"""
        SELECT COUNT(*) as cnt FROM `tabSoil Sample Collection`
        WHERE ({lab_logic}) = %s
          AND creation < %s
          AND (status NOT IN ({completed_placeholders}, 'Cancelled') OR (status IN ({completed_placeholders}) AND modified >= %s))
          {MASTER_SAMPLE_EXCLUSION}
    """
    prev_balance_params = [laboratory, fy_start] + COMPLETED_STATUSES + COMPLETED_STATUSES + [fy_start]
    prev_balance = frappe.db.sql(prev_balance_qry, prev_balance_params, as_dict=True)[0].cnt or 0

    # Received Period: Assigned to lab within selected date range
    received_qry = f"""
        SELECT COUNT(*) as cnt FROM `tabSoil Sample Collection`
        WHERE ({lab_logic}) = %s
          AND assigned_to_lab_date BETWEEN %s AND %s
          {MASTER_SAMPLE_EXCLUSION}
    """
    received_period = frappe.db.sql(received_qry, [laboratory, start, end], as_dict=True)[0].cnt or 0

    cumulative_total = prev_balance + received_period

    # Completed Tests & Pending Tests within range/status
    status_qry = f"""
        SELECT status, COUNT(*) as cnt FROM `tabSoil Sample Collection`
        WHERE ({lab_logic}) = %s
          AND assigned_to_lab_date BETWEEN %s AND %s
          {MASTER_SAMPLE_EXCLUSION}
        GROUP BY status
    """
    status_rows = frappe.db.sql(status_qry, [laboratory, start, end], as_dict=True)
    
    completed_tests = sum([r.cnt for r in status_rows if r.status in COMPLETED_STATUSES])
    pending_tests = sum([r.cnt for r in status_rows if r.status not in COMPLETED_STATUSES + ["Cancelled"]])

    # Annual Non Tax Revenue: Sum of net_payable_amount for farmer samples belonging to this lab's samples
    non_tax_qry = f"""
        SELECT SUM(tsp.net_payable_amount) as total_revenue 
        FROM `tabSoil Sample Payment` tsp
        LEFT JOIN `tabSoil Sample Collection` ssc ON ssc.name = tsp.soil_sample_id
        WHERE (tsp.soil_sample_id LIKE 'FS-%%' OR tsp.soil_sample_id LIKE 'CS-%%')
          AND tsp.payment_date BETWEEN %s AND %s
          AND ({lab_logic_aliased}) = %s
    """
    non_tax_res = frappe.db.sql(non_tax_qry, [start, end, laboratory], as_dict=True)
    annual_non_tax_revenue = non_tax_res[0].total_revenue or 0.0 if non_tax_res else 0.0

    # 2. Laboratory Summary Table Row (Scoped strictly to user's lab)
    lab_summary = [{
        "laboratory": laboratory,
        "prev_balance": prev_balance,
        "received": received_period,
        "completed": completed_tests,
        "pending": pending_tests
    }]

    # 3. Scheme-wise Sample Breakdown Table (Using aliased lab logic to avoid ambiguity)
    scheme_qry = f"""
        SELECT
            COALESCE(c.custom_name_of_type, 'General / Other') AS scheme_name,
            COUNT(ssc.name) AS received,
            SUM(CASE WHEN ssc.status IN ({completed_placeholders}) THEN 1 ELSE 0 END) AS completed,
            SUM(CASE WHEN ssc.status NOT IN ({completed_placeholders}, 'Cancelled') THEN 1 ELSE 0 END) AS pending
        FROM `tabSoil Sample Collection` ssc
        LEFT JOIN `tabClients` c ON c.name = ssc.client
        WHERE ({lab_logic_aliased}) = %s
          AND ssc.assigned_to_lab_date BETWEEN %s AND %s
          {MASTER_SAMPLE_EXCLUSION_SSC}
        GROUP BY scheme_name
        ORDER BY received DESC
    """
    scheme_params = COMPLETED_STATUSES + COMPLETED_STATUSES + [laboratory, start, end]
    scheme_rows = frappe.db.sql(scheme_qry, scheme_params, as_dict=True)

    scheme_summary = []
    for row in scheme_rows:
        scheme_summary.append({
            "laboratory": laboratory,
            "scheme_name": row.scheme_name,
            "received": row.received or 0,
            "completed": row.completed or 0,
            "pending": row.pending or 0
        })

    return {
        "lab": laboratory,
        "cards": {
            "prev_year_balance": prev_balance,
            "received_period": received_period,
            "cumulative_total": cumulative_total,
            "completed_tests": completed_tests,
            "pending_tests": pending_tests,
            "annual_non_tax_revenue": annual_non_tax_revenue
        },
        "lab_summary": lab_summary,
        "scheme_summary": scheme_summary
    }