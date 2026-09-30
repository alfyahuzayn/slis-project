# import frappe
# from frappe import _


# def build_date_range(selected_year, selected_month):
#     """
#     Returns (start_date, end_date) based on FY and optional month.
#     FY runs April to March.
#     If month is given, scope to that calendar month within the FY.
#     """
#     year_int = int(selected_year)

#     if selected_month:
#         month_int = int(selected_month)
#         # Months 4-12 belong to the start year; 1-3 belong to the next year
#         if month_int >= 4:
#             start = f"{year_int}-{month_int:02d}-01"
#         else:
#             start = f"{year_int + 1}-{month_int:02d}-01"

#         # Last day of month
#         import calendar
#         actual_year = year_int if month_int >= 4 else year_int + 1
#         last_day    = calendar.monthrange(actual_year, month_int)[1]
#         end         = f"{actual_year}-{month_int:02d}-{last_day:02d}"
#     else:
#         # Full FY
#         start = f"{year_int}-04-01"
#         end   = f"{year_int + 1}-03-31"

#     return start, end


# def build_lab_condition(laboratory, field_expr):
#     """
#     Returns (condition_sql, params) for lab filtering.
#     field_expr is the SQL expression for the lab column.
#     """
#     if laboratory and laboratory not in ("", "All Laboratories"):
#         return f"AND ({field_expr}) = %s", [laboratory]
#     return "", []


# # ======================================================
# # SAMPLE STATUS CHART
# # Group by status from Soil Sample Collection
# # ======================================================

# @frappe.whitelist()
# def get_sample_status_data(selected_year=None, selected_month=None, laboratory=None):
#     if not selected_year:
#         return {"labels": [], "datasets": []}

#     start, end = build_date_range(selected_year, selected_month)
#     lab_logic   = "COALESCE(NULLIF(lab_name, ''), target_lab)"
#     lab_cond, lab_params = build_lab_condition(laboratory, lab_logic)

#     sql = f"""
#         SELECT
#             status,
#             COUNT(*) AS count
#         FROM `tabSoil Sample Collection`
#         WHERE assigned_to_lab_date BETWEEN %s AND %s
#         {lab_cond}
#         GROUP BY status
#         ORDER BY count DESC
#     """

#     params = [start, end] + lab_params
#     rows   = frappe.db.sql(sql, params, as_dict=True)

#     labels = [r.status for r in rows]
#     values = [int(r.count) for r in rows]

#     return {
#         "labels":   labels,
#         "datasets": [{"name": "Samples", "values": values}]
#     }


# # ======================================================
# # EMPLOYEE WISE WORK STATUS CHART
# # From ToDo, filtered by lab via Soil Sample Collection join
# # ======================================================

# @frappe.whitelist()
# def get_employee_status_data(selected_year=None, selected_month=None, laboratory=None):
#     if not selected_year:
#         return {"labels": [], "datasets": []}

#     start, end = build_date_range(selected_year, selected_month)
#     lab_logic   = "COALESCE(NULLIF(ssc.lab_name, ''), ssc.target_lab)"
#     lab_cond, lab_params = build_lab_condition(laboratory, lab_logic)

#     sql = f"""
#         SELECT
#             t.custom_ra_employee_name AS employee,
#             t.status
#         FROM `tabToDo` t
#         INNER JOIN `tabSoil Sample Collection` ssc
#             ON ssc.name = t.reference_name
#         WHERE t.reference_type = 'Soil Sample Collection'
#           AND t.custom_ra_employee_name IS NOT NULL
#           AND t.custom_ra_employee_name != ''
#           AND ssc.assigned_to_lab_date BETWEEN %s AND %s
#           {lab_cond}
#     """

#     params = [start, end] + lab_params
#     rows   = frappe.db.sql(sql, params, as_dict=True)

#     employees     = sorted(list(set([r.employee for r in rows if r.employee])))
#     completed_vals = []
#     pending_vals   = []
#     cancelled_vals = []

#     for emp in employees:
#         emp_tasks = [r for r in rows if r.employee == emp]
#         completed_vals.append(len([t for t in emp_tasks if t.status == "Closed"]))
#         pending_vals.append(len([t for t in emp_tasks if t.status not in ["Closed", "Cancelled"]]))
#         cancelled_vals.append(len([t for t in emp_tasks if t.status == "Cancelled"]))

#     return {
#         "labels": employees,
#         "datasets": [
#             {"name": _("Completed"), "values": completed_vals},
#             {"name": _("Pending"),   "values": pending_vals},
#             {"name": _("Cancelled"), "values": cancelled_vals}
#         ]
#     }


# # ======================================================
# # SCHEME-WISE TOTAL SAMPLES CHART
# # From Clients doctype, filtered by lab via Soil Sample Collection
# # Groups by custom_name_of_type to show individual scheme names
# # ======================================================

# @frappe.whitelist()
# def get_scheme_data(selected_year=None, selected_month=None, laboratory=None):
#     if not selected_year:
#         return {"labels": [], "datasets": []}

#     start, end = build_date_range(selected_year, selected_month)
#     lab_logic   = "COALESCE(NULLIF(ssc.lab_name, ''), ssc.target_lab)"
#     lab_cond, lab_params = build_lab_condition(laboratory, lab_logic)

#     sql = f"""
#         SELECT
#             c.custom_name_of_type AS scheme,
#             COUNT(ssc.name) AS count
#         FROM `tabSoil Sample Collection` ssc
#         INNER JOIN `tabClients` c
#             ON c.name = ssc.client
#         WHERE c.client_type        = 'Department'
#           AND c.type_of_collection = 'Scheme'
#           AND ssc.assigned_to_lab_date BETWEEN %s AND %s
#           {lab_cond}
#         GROUP BY c.custom_name_of_type
#         ORDER BY count DESC
#     """

#     params = [start, end] + lab_params
#     rows   = frappe.db.sql(sql, params, as_dict=True)

#     labels = [r.scheme or "Unknown" for r in rows]
#     values = [int(r.count) for r in rows]

#     return {
#         "labels":   labels,
#         "datasets": [{"name": "Samples", "values": values}]
#     }














# import calendar
# import frappe
# from frappe import _


# def build_date_range(selected_year, selected_month):
#   """Returns (start_date, end_date) based on FY and optional month."""
#   year_int = int(selected_year)

#   if selected_month:
#     month_int = int(selected_month)
#     if month_int >= 4:
#       start = f"{year_int}-{month_int:02d}-01"
#     else:
#       start = f"{year_int + 1}-{month_int:02d}-01"

#     actual_year = year_int if month_int >= 4 else year_int + 1
#     last_day = calendar.monthrange(actual_year, month_int)[1]
#     end = f"{actual_year}-{month_int:02d}-{last_day:02d}"
#   else:
#     start = f"{year_int}-04-01"
#     end = f"{year_int + 1}-03-31"

#   return start, end


# def build_lab_condition(laboratory, field_expr):
#   """Returns (condition_sql, params) for lab filtering."""
#   if laboratory and laboratory not in ("", "All Laboratories"):
#     return f"AND ({field_expr}) = %s", [laboratory]
#   return "", []


# # ======================================================
# # SAMPLE STATUS CHART
# # ======================================================


# @frappe.whitelist()
# def get_sample_status_data(
#     selected_year=None, selected_month=None, laboratory=None
# ):
#   if not selected_year:
#     return {"labels": [], "datasets": []}

#   start, end = build_date_range(selected_year, selected_month)
#   lab_logic = "COALESCE(NULLIF(lab_name, ''), target_lab)"
#   lab_cond, lab_params = build_lab_condition(laboratory, lab_logic)

#   sql = f"""
#         SELECT
#             status,
#             COUNT(*) AS count
#         FROM `tabSoil Sample Collection`
#         WHERE assigned_to_lab_date BETWEEN %s AND %s
#         {lab_cond}
#         GROUP BY status
#         ORDER BY count DESC
#     """

#   params = [start, end] + lab_params
#   rows = frappe.db.sql(sql, params, as_dict=True)

#   labels = [r.status for r in rows]
#   values = [int(r.count) for r in rows]

#   return {"labels": labels, "datasets": [{"name": "Samples", "values": values}]}


# # ======================================================
# # EMPLOYEE WISE WORK STATUS CHART
# # ======================================================


# @frappe.whitelist()
# def get_employee_status_data(
#     selected_year=None, selected_month=None, laboratory=None
# ):
#   if not selected_year:
#     return {"labels": [], "datasets": []}

#   start, end = build_date_range(selected_year, selected_month)
#   lab_logic = "COALESCE(NULLIF(ssc.lab_name, ''), ssc.target_lab)"
#   lab_cond, lab_params = build_lab_condition(laboratory, lab_logic)

#   sql = f"""
#         SELECT
#             t.custom_ra_employee_name AS employee,
#             t.status
#         FROM `tabToDo` t
#         INNER JOIN `tabSoil Sample Collection` ssc
#             ON ssc.name = t.reference_name
#         WHERE t.reference_type = 'Soil Sample Collection'
#           AND t.custom_ra_employee_name IS NOT NULL
#           AND t.custom_ra_employee_name != ''
#           AND ssc.assigned_to_lab_date BETWEEN %s AND %s
#           {lab_cond}
#     """

#   params = [start, end] + lab_params
#   rows = frappe.db.sql(sql, params, as_dict=True)

#   employees = sorted(list(set([r.employee for r in rows if r.employee])))
#   completed_vals = []
#   pending_vals = []
#   cancelled_vals = []

#   for emp in employees:
#     emp_tasks = [r for r in rows if r.employee == emp]
#     completed_vals.append(len([t for t in emp_tasks if t.status == "Closed"]))
#     pending_vals.append(
#         len([t for t in emp_tasks if t.status not in ["Closed", "Cancelled"]])
#     )
#     cancelled_vals.append(
#         len([t for t in emp_tasks if t.status == "Cancelled"])
#     )

#   return {
#       "labels": employees,
#       "datasets": [
#           {"name": _("Completed"), "values": completed_vals},
#           {"name": _("Pending"), "values": pending_vals},
#           {"name": _("Cancelled"), "values": cancelled_vals},
#       ],
#   }

# # ======================================================
# # SCHEME-WISE TOTAL SAMPLES CHART (With Local Filters)
# # ======================================================


# @frappe.whitelist()
# def get_scheme_data(
#     selected_year=None,
#     selected_month=None,
#     laboratory=None,
#     block=None,
#     panchayat=None,
# ):
#   if not selected_year:
#     return {"labels": [], "datasets": []}

#   start, end = build_date_range(selected_year, selected_month)
#   lab_logic = "COALESCE(NULLIF(ssc.lab_name, ''), ssc.target_lab)"
#   lab_cond, lab_params = build_lab_condition(laboratory, lab_logic)

#   extra_conditions = []
#   extra_params = []

#   if block and block not in ("", "All Blocks"):
#     extra_conditions.append("(ssc.block = %s OR ssc.block_name = %s)")
#     extra_params.extend([block, block])

#   # Fixed to use 'panchayat' everywhere consistently
#   if panchayat and panchayat not in ("", "All Panchayats"):
#     extra_conditions.append(
#         "(ssc.panchayath = %s OR ssc.panchayath_name = %s)"
#     )
#     extra_params.extend([panchayat, panchayat])

#   extra_cond_str = ""
#   if extra_conditions:
#     extra_cond_str = "AND " + " AND ".join(extra_conditions)

#   sql = f"""
#         SELECT
#             c.custom_name_of_type AS scheme,
#             COUNT(ssc.name) AS count
#         FROM `tabSoil Sample Collection` ssc
#         INNER JOIN `tabClients` c
#             ON c.name = ssc.client
#         WHERE c.client_type        = 'Department'
#           AND c.type_of_collection = 'Scheme'
#           AND ssc.assigned_to_lab_date BETWEEN %s AND %s
#           {lab_cond}
#           {extra_cond_str}
#         GROUP BY c.custom_name_of_type
#         ORDER BY count DESC
#     """

#   params = [start, end] + lab_params + extra_params
#   rows = frappe.db.sql(sql, params, as_dict=True)

#   labels = [r.scheme or "Unknown" for r in rows]
#   values = [int(r.count) for r in rows]

#   return {"labels": labels, "datasets": [{"name": "Samples", "values": values}]}




import calendar
import frappe
from frappe import _


# ======================================================
# ACCESS CONTROL — lab restriction for non-privileged users
# ======================================================

PRIVILEGED_ROLES = {"Administrator", "slis_admin"}  # <-- adjust to your real role names


def _get_user_lab_name(user):
  """Resolve the logged-in user's lab_name — the same string stored in
  Soil Sample Collection's lab_name/target_lab columns and used by the
  dashboard's Laboratory filter dropdown."""
  employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
  if not employee:
    return None

  lab_link = frappe.db.get_value("Employee", employee, "custom_lab_name")  # <-- confirm this fieldname on Employee
  if not lab_link:
    return None

  # lab_link is the Soil Laboratory doctype's `name` (docname). If that doctype
  # isn't auto-named as lab_name itself, resolve it explicitly so it matches
  # what's stored in Soil Sample Collection.lab_name / target_lab.
  return frappe.db.get_value("Soil Laboratory", lab_link, "lab_name") or lab_link


@frappe.whitelist()
def get_current_user_context():
  """Called by the dashboard JS on load to decide the default/locked lab filter."""
  user = frappe.session.user
  roles = set(frappe.get_roles(user))
  is_privileged = bool(roles & PRIVILEGED_ROLES)

  return {
      "laboratory": _get_user_lab_name(user),
      "is_privileged": is_privileged,
  }


def enforce_lab_restriction(laboratory):
  """Call at the top of every dashboard data method. Non-privileged users get
  their own lab forced regardless of what the client sent."""
  user = frappe.session.user
  roles = set(frappe.get_roles(user))
  
  user_lab = _get_user_lab_name(user)
  frappe.logger().debug(f"User: {user} | Resolved Lab: {user_lab} | Roles: {roles}")

  if roles & PRIVILEGED_ROLES:
    return laboratory  # privileged: trust whatever was passed, including "" for All

  user_lab = _get_user_lab_name(user)
  if not user_lab:
    frappe.throw(_("No laboratory is linked to your employee record. Contact the admin."))

  return user_lab


def build_date_range(selected_year, selected_month):
  """Returns (start_date, end_date) based on FY and optional month."""
  year_int = int(selected_year)

  if selected_month:
    month_int = int(selected_month)
    if month_int >= 4:
      start = f"{year_int}-{month_int:02d}-01"
    else:
      start = f"{year_int + 1}-{month_int:02d}-01"

    actual_year = year_int if month_int >= 4 else year_int + 1
    last_day = calendar.monthrange(actual_year, month_int)[1]
    end = f"{actual_year}-{month_int:02d}-{last_day:02d}"
  else:
    start = f"{year_int}-04-01"
    end = f"{year_int + 1}-03-31"

  return start, end


def build_lab_condition(laboratory, field_expr):
  """Returns (condition_sql, params) for lab filtering."""
  if laboratory and laboratory not in ("", "All Laboratories"):
    return f"AND ({field_expr}) = %s", [laboratory]
  return "", []


# ======================================================
# SAMPLE STATUS CHART
# ======================================================


@frappe.whitelist()
def get_sample_status_data(
    selected_year=None, selected_month=None, laboratory=None
):
  if not selected_year:
    return {"labels": [], "datasets": []}

  laboratory = enforce_lab_restriction(laboratory)  # <-- added

  start, end = build_date_range(selected_year, selected_month)
  lab_logic = "COALESCE(NULLIF(lab_name, ''), target_lab)"
  lab_cond, lab_params = build_lab_condition(laboratory, lab_logic)

  sql = f"""
        SELECT
            status,
            COUNT(*) AS count
        FROM `tabSoil Sample Collection`
        WHERE assigned_to_lab_date BETWEEN %s AND %s
        {lab_cond}
        GROUP BY status
        ORDER BY count DESC
    """

  params = [start, end] + lab_params
  rows = frappe.db.sql(sql, params, as_dict=True)

  labels = [r.status for r in rows]
  values = [int(r.count) for r in rows]

  return {"labels": labels, "datasets": [{"name": "Samples", "values": values}]}


# ======================================================
# EMPLOYEE WISE WORK STATUS CHART
# ======================================================


@frappe.whitelist()
def get_employee_status_data(
    selected_year=None, selected_month=None, laboratory=None
):
  if not selected_year:
    return {"labels": [], "datasets": []}

  laboratory = enforce_lab_restriction(laboratory)  # <-- added

  start, end = build_date_range(selected_year, selected_month)
  lab_logic = "COALESCE(NULLIF(ssc.lab_name, ''), ssc.target_lab)"
  lab_cond, lab_params = build_lab_condition(laboratory, lab_logic)

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
          {lab_cond}
    """

  params = [start, end] + lab_params
  rows = frappe.db.sql(sql, params, as_dict=True)

  employees = sorted(list(set([r.employee for r in rows if r.employee])))
  completed_vals = []
  pending_vals = []
  cancelled_vals = []

  for emp in employees:
    emp_tasks = [r for r in rows if r.employee == emp]
    completed_vals.append(len([t for t in emp_tasks if t.status == "Closed"]))
    pending_vals.append(
        len([t for t in emp_tasks if t.status not in ["Closed", "Cancelled"]])
    )
    cancelled_vals.append(
        len([t for t in emp_tasks if t.status == "Cancelled"])
    )

  return {
      "labels": employees,
      "datasets": [
          {"name": _("Completed"), "values": completed_vals},
          {"name": _("Pending"), "values": pending_vals},
          {"name": _("Cancelled"), "values": cancelled_vals},
      ],
  }

# ======================================================
# SCHEME-WISE TOTAL SAMPLES CHART (With Local Filters)
# ======================================================


@frappe.whitelist()
def get_scheme_data(
    selected_year=None,
    selected_month=None,
    laboratory=None,
    block=None,
    panchayat=None,
):
  if not selected_year:
    return {"labels": [], "datasets": []}

  laboratory = enforce_lab_restriction(laboratory)  # <-- added

  start, end = build_date_range(selected_year, selected_month)
  lab_logic = "COALESCE(NULLIF(ssc.lab_name, ''), ssc.target_lab)"
  lab_cond, lab_params = build_lab_condition(laboratory, lab_logic)

  extra_conditions = []
  extra_params = []

  if block and block not in ("", "All Blocks"):
    extra_conditions.append("(ssc.block = %s OR ssc.block_name = %s)")
    extra_params.extend([block, block])

  if panchayat and panchayat not in ("", "All Panchayats"):
    extra_conditions.append(
        "(ssc.panchayath = %s OR ssc.panchayath_name = %s)"
    )
    extra_params.extend([panchayat, panchayat])

  extra_cond_str = ""
  if extra_conditions:
    extra_cond_str = "AND " + " AND ".join(extra_conditions)

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
          {lab_cond}
          {extra_cond_str}
        GROUP BY c.custom_name_of_type
        ORDER BY count DESC
    """

  params = [start, end] + lab_params + extra_params
  rows = frappe.db.sql(sql, params, as_dict=True)

  labels = [r.scheme or "Unknown" for r in rows]
  values = [int(r.count) for r in rows]

  return {"labels": labels, "datasets": [{"name": "Samples", "values": values}]}