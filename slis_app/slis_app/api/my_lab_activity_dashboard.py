import frappe
from frappe import _


# ======================================================
# GET USER'S LAB
# Same logic as my_soil_dashboard.py
# employment_type = "District Office" -> custom_district_office_name
# else -> custom_lab_name
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
    import calendar
    year_int = int(selected_year)

    if selected_month:
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
# SAMPLE STATUS CHART
# ======================================================

@frappe.whitelist()
def get_my_sample_status_data(selected_year=None, selected_month=None):
    if not selected_year:
        return {"labels": [], "datasets": []}

    laboratory = get_user_lab()
    if not laboratory:
        return {"labels": [], "datasets": [], "error": "no_lab"}

    start, end = build_date_range(selected_year, selected_month)
    lab_logic  = "COALESCE(NULLIF(lab_name, ''), target_lab)"

    sql = f"""
        SELECT
            status,
            COUNT(*) AS count
        FROM `tabSoil Sample Collection`
        WHERE assigned_to_lab_date BETWEEN %s AND %s
          AND ({lab_logic}) = %s
        GROUP BY status
        ORDER BY count DESC
    """

    rows   = frappe.db.sql(sql, [start, end, laboratory], as_dict=True)
    labels = [r.status for r in rows]
    values = [int(r.count) for r in rows]

    return {
        "lab":      laboratory,
        "labels":   labels,
        "datasets": [{"name": "Samples", "values": values}]
    }


# ======================================================
# EMPLOYEE WISE WORK STATUS CHART
# ======================================================

@frappe.whitelist()
def get_my_employee_status_data(selected_year=None, selected_month=None):
    if not selected_year:
        return {"labels": [], "datasets": []}

    laboratory = get_user_lab()
    if not laboratory:
        return {"labels": [], "datasets": [], "error": "no_lab"}

    start, end = build_date_range(selected_year, selected_month)
    lab_logic  = "COALESCE(NULLIF(ssc.lab_name, ''), ssc.target_lab)"

    sql = f"""
        SELECT
            t.custom_ra_employee_name AS employee,
            t.status
        FROM `tabToDo` t
        INNER JOIN `tabSoil Sample Collection` ssc
            ON ssc.name = t.reference_name
        WHERE t.reference_type = 'Soil Sample Collection'
          AND t.custom_ra_employee_name IS NOT NULL
          AND t.custom_ra_employee_name != ''
          AND ssc.assigned_to_lab_date BETWEEN %s AND %s
          AND ({lab_logic}) = %s
    """

    rows      = frappe.db.sql(sql, [start, end, laboratory], as_dict=True)
    employees = sorted(list(set([r.employee for r in rows if r.employee])))

    completed_vals = []
    pending_vals   = []
    cancelled_vals = []

    for emp in employees:
        emp_tasks = [r for r in rows if r.employee == emp]
        completed_vals.append(len([t for t in emp_tasks if t.status == "Closed"]))
        pending_vals.append(len([t for t in emp_tasks if t.status not in ["Closed", "Cancelled"]]))
        cancelled_vals.append(len([t for t in emp_tasks if t.status == "Cancelled"]))

    return {
        "lab":    laboratory,
        "labels": employees,
        "datasets": [
            {"name": _("Completed"), "values": completed_vals},
            {"name": _("Pending"),   "values": pending_vals},
            {"name": _("Cancelled"), "values": cancelled_vals}
        ]
    }


# ======================================================
# SCHEME-WISE TOTAL SAMPLES CHART
# ======================================================

@frappe.whitelist()
def get_my_scheme_data(selected_year=None, selected_month=None):
    if not selected_year:
        return {"labels": [], "datasets": []}

    laboratory = get_user_lab()
    if not laboratory:
        return {"labels": [], "datasets": [], "error": "no_lab"}

    start, end = build_date_range(selected_year, selected_month)
    lab_logic  = "COALESCE(NULLIF(ssc.lab_name, ''), ssc.target_lab)"

    sql = f"""
        SELECT
            c.custom_name_of_type AS scheme,
            COUNT(ssc.name) AS count
        FROM `tabSoil Sample Collection` ssc
        INNER JOIN `tabClients` c
            ON c.name = ssc.client
        WHERE c.client_type        = 'Department'
          AND c.type_of_collection = 'Scheme'
          AND ssc.assigned_to_lab_date BETWEEN %s AND %s
          AND ({lab_logic}) = %s
        GROUP BY c.custom_name_of_type
        ORDER BY count DESC
    """

    rows   = frappe.db.sql(sql, [start, end, laboratory], as_dict=True)
    labels = [r.scheme or "Unknown" for r in rows]
    values = [int(r.count) for r in rows]

    return {
        "lab":      laboratory,
        "labels":   labels,
        "datasets": [{"name": "Samples", "values": values}]
    }

