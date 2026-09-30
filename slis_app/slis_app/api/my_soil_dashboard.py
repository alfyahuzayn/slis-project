# import frappe



# COMPLETED_STATUSES = [
#     "SC Verifying Results",
#     "SC Verified Results",
#     "AD Verifying Results",
#     "AD Verified Results",
#     "Ready to Publish",
#     "Result Published",
# ]


# def get_user_employee():
#     """
#     Returns the Employee record dict for the currently logged-in user,
#     or None if no Employee is linked to this user.
#     """
#     user = frappe.session.user
#     employee = frappe.db.get_value(
#         "Employee",
#         {"user_id": user},
#         ["employment_type", "custom_lab_name", "custom_district_office_name"],
#         as_dict=True
#     )
#     return employee


# def get_user_labs(employee=None):
#     """
#     Returns a list of labs/offices the currently logged-in user is allowed to see.
#     If the user is a District Office user, returns both their District Office name 
#     AND their corresponding mapped Soil Laboratory name.
#     """
#     if employee is None:
#         employee = get_user_employee()
#     if not employee:
#         return []

#     if employee.employment_type == "District Office":
#         district = employee.custom_district_office_name
#         if not district:
#             return []
            
#         district_lab_mapping = {
#             "Trivandrum": "Central Soil Analytical Lab, Parottukonam",
#             "Alappuzha": "Regional Soil Analytical Laboratory Alappuzha",
#             "Kasaragod": "Soil and Plant Health Clinic, Kasaragod",
#             "Pathanamthitta": "Soil and Plant Health Clinic, Pathanamthitta",
#             "Thrissur": "Regional Soil Analytical Laboratory Thrissur",
#             "Kozhikode": "Regional Soil Analytical Laboratory Kozhikode"
#         }
#         mapped_lab = district_lab_mapping.get(district)
        
#         # Include both the district office name and the mapped lab name
#         labs = [district]
#         if mapped_lab and mapped_lab != district:
#             labs.append(mapped_lab)
#         return labs
#     else:
#         return [employee.custom_lab_name] if employee.custom_lab_name else []


# def get_assignment_scope():
#     """
#     Determines whether the current session user should be scoped down to ONLY
#     the Soil Sample Collection records assigned to them personally (via Frappe's
#     built-in _assign field), rather than seeing all records for their lab.

#     This applies only when BOTH are true:
#       1. The user has the "Soil Intaker L1" role.
#       2. Their Employee record has employment_type == "Lab".

#     Returns:
#         (sql_condition, params) tuple. sql_condition is an empty string and
#         params is an empty list if no assignment scoping should be applied.
#     """
#     user = frappe.session.user

#     if "Soil Intaker L1" not in frappe.get_roles(user):
#         return "", []

#     employee = get_user_employee()
#     if not employee or employee.employment_type != "Lab":
#         return "", []

#     # Frappe stores _assign as a JSON-encoded list of user emails, e.g. '["user@example.com"]'
#     return "AND (_assign LIKE %s)", [f'%"{user}"%']


# @frappe.whitelist()
# def get_my_lab():
#     labs = get_user_labs()
#     return {"lab": labs[0] if labs else None}


# @frappe.whitelist()
# def get_my_soil_intake_data(selected_year=None):
#     if not selected_year:
#         return {"cards": {}, "table": []}

#     employee = get_user_employee()
#     laboratories = get_user_labs(employee)
#     if not laboratories:
#         return {"cards": {}, "table": [], "error": "no_lab"}

#     assign_cond, assign_params = get_assignment_scope()

#     year_int = int(selected_year)
#     prev_start, prev_end = f"{year_int - 1}-04-01", f"{year_int}-03-31"
#     curr_start, curr_end = f"{year_int}-04-01", f"{year_int + 1}-03-31"

#     lab_logic = "COALESCE(NULLIF(lab_name, ''), target_lab)"

#     # Hierarchical Counting Logic
#     count_logic = """
#         CASE 
#             WHEN is_generated_sample = 1 THEN 1
#             WHEN is_master_sample = 1 AND (number_of_samples <= 1 OR number_of_samples IS NULL) THEN 1
#             WHEN is_master_sample = 1 AND number_of_samples > 1 THEN 0
#             ELSE COALESCE(NULLIF(number_of_samples, 0), 1) 
#         END
#     """

#     # Dynamically build placeholders for multiple laboratories (e.g., IN (%s, %s))
#     lab_placeholders = ", ".join(["%s"] * len(laboratories))
#     completed_placeholders = ", ".join(["%s"] * len(COMPLETED_STATUSES))

#     sql = f"""
#         SELECT
#             COALESCE({lab_logic}, 'Unassigned') AS lab,
#             SUM(CASE WHEN assigned_to_lab_date BETWEEN %s AND %s AND status NOT IN ('Draft', {completed_placeholders}, 'Cancelled') THEN {count_logic} ELSE 0 END) AS prev_pending,
#             SUM(CASE WHEN assigned_to_lab_date BETWEEN %s AND %s THEN {count_logic} ELSE 0 END) AS received_this_year,
#             SUM(CASE WHEN assigned_to_lab_date BETWEEN %s AND %s AND status IN ({completed_placeholders}) THEN {count_logic} ELSE 0 END) AS completed_this_year,
#             SUM(CASE WHEN assigned_to_lab_date BETWEEN %s AND %s AND status NOT IN ('Draft', {completed_placeholders}, 'Cancelled') THEN {count_logic} ELSE 0 END) AS pending_this_year
#         FROM `tabSoil Sample Collection`
#         WHERE ({lab_logic}) IN ({lab_placeholders})
#         {assign_cond}
#         GROUP BY {lab_logic}
#     """

#     params = (
#         [prev_start, prev_end] + COMPLETED_STATUSES
#         + [curr_start, curr_end]
#         + [curr_start, curr_end] + COMPLETED_STATUSES
#         + [curr_start, curr_end] + COMPLETED_STATUSES
#         + laboratories
#         + assign_params
#     )

#     rows = frappe.db.sql(sql, params, as_dict=True)

#     cards = {"prev_year_balance": 0, "received_this_year": 0, "completed_tests": 0, "cumulative_total": 0, "pending_test": 0}
#     table_data = []

#     for d in rows:
#         prev, received, completed, pending = int(d.prev_pending or 0), int(d.received_this_year or 0), int(d.completed_this_year or 0), int(d.pending_this_year or 0)
#         table_data.append({"lab": d.lab or laboratories[0], "prev_pending": prev, "received": received, "completed": completed, "current_pending": pending})
#         cards["prev_year_balance"] += prev
#         cards["received_this_year"] += received
#         cards["completed_tests"] += completed
#         cards["pending_test"] += pending

#     cards["cumulative_total"] = cards["prev_year_balance"] + cards["received_this_year"]
#     return {"lab": laboratories[0], "cards": cards, "table": table_data}






# @frappe.whitelist()
# def get_my_filtered_sample_names(selected_year=None, card_type=None):
#     if not selected_year or not card_type:
#         return []

#     employee = get_user_employee()
#     laboratories = get_user_labs(employee)
#     if not laboratories:
#         return []

#     assign_cond, assign_params = get_assignment_scope()

#     year_int = int(selected_year)
#     prev_start, prev_end = f"{year_int - 1}-04-01", f"{year_int}-03-31"
#     curr_start, curr_end = f"{year_int}-04-01", f"{year_int + 1}-03-31"
#     lab_logic = "COALESCE(NULLIF(lab_name, ''), target_lab)"

#     # Filter logic must match the counting logic (only retrieve records that contribute to the count)
#     filter_logic = """
#         (is_generated_sample = 1) OR 
#         (is_master_sample = 1 AND (number_of_samples <= 1 OR number_of_samples IS NULL)) OR 
#         (is_master_sample = 0 AND is_generated_sample = 0)
#     """

#     completed_placeholders = ", ".join(["%s"] * len(COMPLETED_STATUSES))

#     mapping = {
#         "prev_pending": {
#             "date": (prev_start, prev_end),
#             "status": f"AND status NOT IN ('Draft', {completed_placeholders}, 'Cancelled')",
#             "status_params": COMPLETED_STATUSES,
#         },
#         "received": {"date": (curr_start, curr_end), "status": "", "status_params": []},
#         "cumulative": {"date": (prev_start, curr_end), "status": "AND status NOT IN ('Draft', 'Cancelled')", "status_params": []},
#         "completed": {
#             "date": (curr_start, curr_end),
#             "status": f"AND status IN ({completed_placeholders})",
#             "status_params": COMPLETED_STATUSES,
#         },
#         "pending": {
#             "date": (curr_start, curr_end),
#             "status": f"AND status NOT IN ('Draft', {completed_placeholders}, 'Cancelled')",
#             "status_params": COMPLETED_STATUSES,
#         },
#     }

#     config = mapping.get(card_type)
#     if not config:
#         return []

#     lab_placeholders = ", ".join(["%s"] * len(laboratories))

#     sql = f"""
#         SELECT name FROM `tabSoil Sample Collection`
#         WHERE assigned_to_lab_date BETWEEN %s AND %s
#         {config['status']}
#         AND ({lab_logic}) IN ({lab_placeholders})
#         AND ({filter_logic})
#         {assign_cond}
#     """

#     params = [config['date'][0], config['date'][1]] + config['status_params'] + laboratories + assign_params

#     return [r.name for r in frappe.db.sql(sql, params, as_dict=True)]







import frappe



COMPLETED_STATUSES = [
    "SC Verifying Results",
    "SC Verified Results",
    "AD Verifying Results",
    "AD Verified Results",
    "Ready to Publish",
    "Result Published",
]

# Exclude master / master-profile sample rows from every count and every list of names.
# No bind params needed (no %s inside), so it's safe to drop into any WHERE clause as-is.
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

def get_user_employee():
    """
    Returns the Employee record dict for the currently logged-in user,
    or None if no Employee is linked to this user.
    """
    user = frappe.session.user
    employee = frappe.db.get_value(
        "Employee",
        {"user_id": user},
        ["employment_type", "custom_lab_name", "custom_district_office_name"],
        as_dict=True
    )
    return employee


def get_user_labs(employee=None):
    """
    Returns a list of labs/offices the currently logged-in user is allowed to see.
    If the user is a District Office user, returns both their District Office name 
    AND their corresponding mapped Soil Laboratory name.
    """
    if employee is None:
        employee = get_user_employee()
    if not employee:
        return []

    if employee.employment_type == "District Office":
        district = employee.custom_district_office_name
        if not district:
            return []
            
        district_lab_mapping = {
            "Trivandrum": "Central Soil Analytical Lab, Parottukonam",
            "Alappuzha": "Regional Soil Analytical Laboratory Alappuzha",
            "Kasaragod": "Soil and Plant Health Clinic, Kasaragod",
            "Pathanamthitta": "Soil and Plant Health Clinic, Pathanamthitta",
            "Thrissur": "Regional Soil Analytical Laboratory Thrissur",
            "Kozhikode": "Regional Soil Analytical Laboratory Kozhikode"
        }
        mapped_lab = district_lab_mapping.get(district)
        
        # Include both the district office name and the mapped lab name
        labs = [district]
        if mapped_lab and mapped_lab != district:
            labs.append(mapped_lab)
        return labs
    else:
        return [employee.custom_lab_name] if employee.custom_lab_name else []


def get_assignment_scope():
    """
    Determines whether the current session user should be scoped down to ONLY
    the Soil Sample Collection records assigned to them personally (via Frappe's
    built-in _assign field), rather than seeing all records for their lab.

    This applies only when BOTH are true:
      1. The user has the "Soil Intaker L1" role.
      2. Their Employee record has employment_type == "Lab".

    Returns:
        (sql_condition, params) tuple. sql_condition is an empty string and
        params is an empty list if no assignment scoping should be applied.
    """
    user = frappe.session.user

    if "Soil Intaker L1" not in frappe.get_roles(user):
        return "", []

    employee = get_user_employee()
    if not employee or employee.employment_type != "Lab":
        return "", []

    # Frappe stores _assign as a JSON-encoded list of user emails, e.g. '["user@example.com"]'
    return "AND (_assign LIKE %s)", [f'%"{user}"%']


@frappe.whitelist()
def get_my_lab():
    labs = get_user_labs()
    return {"lab": labs[0] if labs else None}


@frappe.whitelist()
def get_my_soil_intake_data(selected_year=None):
    if not selected_year:
        return {"cards": {}, "table": []}

    employee = get_user_employee()
    laboratories = get_user_labs(employee)
    if not laboratories:
        return {"cards": {}, "table": [], "error": "no_lab"}

    assign_cond, assign_params = get_assignment_scope()

    year_int = int(selected_year)
    prev_start, prev_end = f"{year_int - 1}-04-01", f"{year_int}-03-31"
    curr_start, curr_end = f"{year_int}-04-01", f"{year_int + 1}-03-31"

    lab_logic = "COALESCE(NULLIF(lab_name, ''), target_lab)"

    # Hierarchical Counting Logic
    count_logic = """
        CASE 
            WHEN is_generated_sample = 1 THEN 1
            WHEN is_master_sample = 1 AND (number_of_samples <= 1 OR number_of_samples IS NULL) THEN 1
            WHEN is_master_sample = 1 AND number_of_samples > 1 THEN 0
            ELSE COALESCE(NULLIF(number_of_samples, 0), 1) 
        END
    """

    # Dynamically build placeholders for multiple laboratories (e.g., IN (%s, %s))
    lab_placeholders = ", ".join(["%s"] * len(laboratories))
    completed_placeholders = ", ".join(["%s"] * len(COMPLETED_STATUSES))

    sql = f"""
        SELECT
            COALESCE({lab_logic}, 'Unassigned') AS lab,
            SUM(CASE WHEN assigned_to_lab_date BETWEEN %s AND %s AND status NOT IN ('Draft', {completed_placeholders}, 'Cancelled') THEN {count_logic} ELSE 0 END) AS prev_pending,
            SUM(CASE WHEN assigned_to_lab_date BETWEEN %s AND %s THEN {count_logic} ELSE 0 END) AS received_this_year,
            SUM(CASE WHEN assigned_to_lab_date BETWEEN %s AND %s AND status IN ({completed_placeholders}) THEN {count_logic} ELSE 0 END) AS completed_this_year,
            SUM(CASE WHEN assigned_to_lab_date BETWEEN %s AND %s AND status NOT IN ('Draft', {completed_placeholders}, 'Cancelled') THEN {count_logic} ELSE 0 END) AS pending_this_year
        FROM `tabSoil Sample Collection`
        WHERE ({lab_logic}) IN ({lab_placeholders})
        {assign_cond}
        {MASTER_SAMPLE_EXCLUSION}
        GROUP BY {lab_logic}
    """

    params = (
        [prev_start, prev_end] + COMPLETED_STATUSES
        + [curr_start, curr_end]
        + [curr_start, curr_end] + COMPLETED_STATUSES
        + [curr_start, curr_end] + COMPLETED_STATUSES
        + laboratories
        + assign_params
    )

    rows = frappe.db.sql(sql, params, as_dict=True)

    cards = {"prev_year_balance": 0, "received_this_year": 0, "completed_tests": 0, "cumulative_total": 0, "pending_test": 0}
    table_data = []

    for d in rows:
        prev, received, completed, pending = int(d.prev_pending or 0), int(d.received_this_year or 0), int(d.completed_this_year or 0), int(d.pending_this_year or 0)
        table_data.append({"lab": d.lab or laboratories[0], "prev_pending": prev, "received": received, "completed": completed, "current_pending": pending})
        cards["prev_year_balance"] += prev
        cards["received_this_year"] += received
        cards["completed_tests"] += completed
        cards["pending_test"] += pending

    cards["cumulative_total"] = cards["prev_year_balance"] + cards["received_this_year"]
    return {"lab": laboratories[0], "cards": cards, "table": table_data}






@frappe.whitelist()
def get_my_filtered_sample_names(selected_year=None, card_type=None):
    if not selected_year or not card_type:
        return []

    employee = get_user_employee()
    laboratories = get_user_labs(employee)
    if not laboratories:
        return []

    assign_cond, assign_params = get_assignment_scope()

    year_int = int(selected_year)
    prev_start, prev_end = f"{year_int - 1}-04-01", f"{year_int}-03-31"
    curr_start, curr_end = f"{year_int}-04-01", f"{year_int + 1}-03-31"
    lab_logic = "COALESCE(NULLIF(lab_name, ''), target_lab)"

    # Filter logic must match the counting logic (only retrieve records that contribute to the count)
    filter_logic = """
        (is_generated_sample = 1) OR 
        (is_master_sample = 1 AND (number_of_samples <= 1 OR number_of_samples IS NULL)) OR 
        (is_master_sample = 0 AND is_generated_sample = 0)
    """

    completed_placeholders = ", ".join(["%s"] * len(COMPLETED_STATUSES))

    mapping = {
        "prev_pending": {
            "date": (prev_start, prev_end),
            "status": f"AND status NOT IN ('Draft', {completed_placeholders}, 'Cancelled')",
            "status_params": COMPLETED_STATUSES,
        },
        "received": {"date": (curr_start, curr_end), "status": "", "status_params": []},
        "cumulative": {"date": (prev_start, curr_end), "status": "AND status NOT IN ('Draft', 'Cancelled')", "status_params": []},
        "completed": {
            "date": (curr_start, curr_end),
            "status": f"AND status IN ({completed_placeholders})",
            "status_params": COMPLETED_STATUSES,
        },
        "pending": {
            "date": (curr_start, curr_end),
            "status": f"AND status NOT IN ('Draft', {completed_placeholders}, 'Cancelled')",
            "status_params": COMPLETED_STATUSES,
        },
    }

    config = mapping.get(card_type)
    if not config:
        return []

    lab_placeholders = ", ".join(["%s"] * len(laboratories))

    sql = f"""
        SELECT name FROM `tabSoil Sample Collection`
        WHERE assigned_to_lab_date BETWEEN %s AND %s
        {config['status']}
        AND ({lab_logic}) IN ({lab_placeholders})
        AND ({filter_logic})
        {assign_cond}
        {MASTER_SAMPLE_EXCLUSION}
    """

    params = [config['date'][0], config['date'][1]] + config['status_params'] + laboratories + assign_params

    return [r.name for r in frappe.db.sql(sql, params, as_dict=True)]