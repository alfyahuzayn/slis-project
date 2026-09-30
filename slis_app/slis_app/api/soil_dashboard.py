# import frappe

# COMPLETED_STATUSES = [
#     "SC Verifying Results",
#     "SC Verified Results",
#     "AD Verifying Results",
#     "AD Verified Results",
#     "Ready to Publish",
#     "Result Published",
# ]


# def parse_start_year(selected_year):
#     """
#     Extracts the base integer year from inputs like '2026-27' or '2026'.
#     """
#     if not selected_year:
#         return None
#     try:
#         return int(str(selected_year).split('-')[0])
#     except ValueError:
#         return None


# @frappe.whitelist()
# def get_soil_intake_data(selected_year=None, laboratory=None):
#     year_int = parse_start_year(selected_year)
#     if not year_int:
#         return {"cards": {}, "table": []}

#     curr_start = f"{year_int}-04-01"
#     curr_end   = f"{year_int + 1}-03-31"
#     prev_start = f"{year_int - 1}-04-01"
#     prev_end   = f"{year_int}-03-31"

#     # Exclude parent/master samples so only actionable child/standalone samples are counted
#     exclusion_subquery = "(SELECT DISTINCT parent_sample FROM `tabSoil Sample Collection` WHERE parent_sample IS NOT NULL AND parent_sample != '')"
#     filter_logic = f"name NOT IN {exclusion_subquery}"

#     lab_logic  = "COALESCE(NULLIF(lab_name, ''), target_lab)"
#     date_logic = "COALESCE(assigned_to_lab_date, DATE(creation))"

#     completed_placeholders = ", ".join(["%s"] * len(COMPLETED_STATUSES))

#     lab_condition = ""
#     lab_params = []
#     if laboratory and laboratory not in ("", "All Laboratories"):
#         lab_condition = f"AND {lab_logic} = %s"
#         lab_params = [laboratory]

#     sql = f"""
#         SELECT
#             COALESCE({lab_logic}, 'Unassigned') AS lab,
#             SUM(CASE WHEN {date_logic} BETWEEN %s AND %s AND status NOT IN ('Draft', {completed_placeholders}, 'Cancelled', 'Rejected') THEN 1 ELSE 0 END) AS prev_pending,
#             SUM(CASE WHEN {date_logic} BETWEEN %s AND %s THEN 1 ELSE 0 END) AS received_this_year,
#             SUM(CASE WHEN {date_logic} BETWEEN %s AND %s AND status IN ({completed_placeholders}) THEN 1 ELSE 0 END) AS completed_this_year,
#             SUM(CASE WHEN {date_logic} BETWEEN %s AND %s AND status NOT IN ('Draft', {completed_placeholders}, 'Cancelled', 'Rejected') THEN 1 ELSE 0 END) AS pending_this_year,
#             SUM(CASE WHEN {date_logic} BETWEEN %s AND %s AND LOWER(status) = 'rejected' THEN 1 ELSE 0 END) AS rejected_this_year
#         FROM `tabSoil Sample Collection`
#         WHERE {filter_logic} {lab_condition}
#         GROUP BY {lab_logic}
#         ORDER BY lab ASC
#     """

#     params = (
#         [prev_start, prev_end] + COMPLETED_STATUSES +
#         [curr_start, curr_end] +
#         [curr_start, curr_end] + COMPLETED_STATUSES +
#         [curr_start, curr_end] + COMPLETED_STATUSES +
#         [curr_start, curr_end] +
#         lab_params
#     )

#     rows = frappe.db.sql(sql, params, as_dict=True)

#     cards = {
#         "prev_year_balance": 0,
#         "received_this_year": 0,
#         "completed_tests": 0,
#         "cumulative_total": 0,
#         "pending_test": 0,
#         "rejected_samples": 0
#     }
#     table_data = []

#     for d in rows:
#         prev      = int(d.prev_pending or 0)
#         received  = int(d.received_this_year or 0)
#         completed = int(d.completed_this_year or 0)
#         pending   = int(d.pending_this_year or 0)
#         rejected  = int(d.rejected_this_year or 0)

#         table_data.append({
#             "lab": d.lab or "Unassigned",
#             "prev_pending": prev,
#             "received": received,
#             "completed": completed,
#             "current_pending": pending,
#             "rejected": rejected
#         })

#         cards["prev_year_balance"] += prev
#         cards["received_this_year"] += received
#         cards["completed_tests"]    += completed
#         cards["pending_test"]       += pending
#         cards["rejected_samples"]   += rejected

#     cards["cumulative_total"] = cards["prev_year_balance"] + cards["received_this_year"]
#     return {"cards": cards, "table": table_data}


# @frappe.whitelist()
# def get_filtered_sample_names(selected_year=None, laboratory=None, card_type=None):
#     year_int = parse_start_year(selected_year)
#     if not year_int or not card_type:
#         return []

#     curr_start = f"{year_int}-04-01"
#     curr_end   = f"{year_int + 1}-03-31"
#     prev_start = f"{year_int - 1}-04-01"
#     prev_end   = f"{year_int}-03-31"

#     exclusion_subquery = "(SELECT DISTINCT parent_sample FROM `tabSoil Sample Collection` WHERE parent_sample IS NOT NULL AND parent_sample != '')"
#     filter_logic = f"name NOT IN {exclusion_subquery}"

#     lab_logic  = "COALESCE(NULLIF(lab_name, ''), target_lab)"
#     date_logic = "COALESCE(assigned_to_lab_date, DATE(creation))"

#     completed_placeholders = ", ".join(["%s"] * len(COMPLETED_STATUSES))

#     status_params = []

#     if card_type == "prev_pending":
#         date_cond = f"{date_logic} BETWEEN %s AND %s"
#         date_params = [prev_start, prev_end]
#         status_cond = f"AND status NOT IN ('Draft', {completed_placeholders}, 'Cancelled', 'Rejected')"
#         status_params = COMPLETED_STATUSES
#     elif card_type == "received":
#         date_cond = f"{date_logic} BETWEEN %s AND %s"
#         date_params = [curr_start, curr_end]
#         status_cond = ""
#     elif card_type == "cumulative":
#         date_cond = f"{date_logic} BETWEEN %s AND %s"
#         date_params = [prev_start, curr_end]
#         status_cond = "AND status NOT IN ('Draft', 'Cancelled')"
#     elif card_type == "completed":
#         date_cond = f"{date_logic} BETWEEN %s AND %s"
#         date_params = [curr_start, curr_end]
#         status_cond = f"AND status IN ({completed_placeholders})"
#         status_params = COMPLETED_STATUSES
#     elif card_type == "pending":
#         date_cond = f"{date_logic} BETWEEN %s AND %s"
#         date_params = [curr_start, curr_end]
#         status_cond = f"AND status NOT IN ('Draft', {completed_placeholders}, 'Cancelled', 'Rejected')"
#         status_params = COMPLETED_STATUSES
#     elif card_type == "rejected":
#         date_cond = f"{date_logic} BETWEEN %s AND %s"
#         date_params = [curr_start, curr_end]
#         status_cond = "AND LOWER(status) = 'rejected'"
#     else:
#         return []

#     lab_condition = ""
#     lab_params = []
#     if laboratory and laboratory not in ("", "All Laboratories"):
#         lab_condition = f"AND ({lab_logic}) = %s"
#         lab_params = [laboratory]

#     sql = f"""
#         SELECT name
#         FROM `tabSoil Sample Collection`
#         WHERE {filter_logic}
#         AND {date_cond}
#         {status_cond}
#         {lab_condition}
#     """

#     params = date_params + status_params + lab_params
#     rows = frappe.db.sql(sql, params, as_dict=True)
#     return [r.name for r in rows]


# @frappe.whitelist()
# def get_scheme_wise_data(selected_year=None, laboratory=None):
#     year_int = parse_start_year(selected_year)
#     if not year_int:
#         return []

#     curr_start = f"{year_int}-04-01"
#     curr_end   = f"{year_int + 1}-03-31"

#     exclusion_subquery = "(SELECT DISTINCT parent_sample FROM `tabSoil Sample Collection` WHERE parent_sample IS NOT NULL AND parent_sample != '')"
#     filter_logic = f"name NOT IN {exclusion_subquery}"

#     lab_logic  = "COALESCE(NULLIF(lab_name, ''), target_lab)"
#     date_logic = "COALESCE(assigned_to_lab_date, DATE(creation))"

#     completed_placeholders = ", ".join(["%s"] * len(COMPLETED_STATUSES))

#     schemes = frappe.get_all("Scheme or Programs", pluck="name")
#     if not schemes:
#         return []

#     lab_condition = ""
#     lab_params    = []
#     if laboratory and laboratory not in ("", "All Laboratories"):
#         lab_condition = f"AND {lab_logic} = %s"
#         lab_params    = [laboratory]

#     scheme_placeholders = ", ".join(["%s"] * len(schemes))

#     sql = f"""
#         SELECT
#             COALESCE({lab_logic}, 'Unassigned') AS lab,
#             name_of_type AS scheme,
#             SUM(CASE WHEN {date_logic} BETWEEN %s AND %s THEN 1 ELSE 0 END) AS received,
#             SUM(CASE WHEN {date_logic} BETWEEN %s AND %s AND status IN ({completed_placeholders}) THEN 1 ELSE 0 END) AS completed,
#             SUM(CASE WHEN {date_logic} BETWEEN %s AND %s AND status NOT IN ('Draft', {completed_placeholders}, 'Cancelled', 'Rejected') THEN 1 ELSE 0 END) AS pending,
#             SUM(CASE WHEN {date_logic} BETWEEN %s AND %s AND LOWER(status) = 'rejected' THEN 1 ELSE 0 END) AS rejected
#         FROM `tabSoil Sample Collection`
#         WHERE {filter_logic}
#         AND   name_of_type IN ({scheme_placeholders})
#         {lab_condition}
#         GROUP BY {lab_logic}, name_of_type
#         ORDER BY lab ASC, scheme ASC
#     """

#     params = (
#         [curr_start, curr_end] +
#         [curr_start, curr_end] + COMPLETED_STATUSES +
#         [curr_start, curr_end] + COMPLETED_STATUSES +
#         [curr_start, curr_end] +
#         schemes +
#         lab_params
#     )

#     return frappe.db.sql(sql, params, as_dict=True)


# @frappe.whitelist()
# def get_lab_scheme_breakdown(selected_year=None, laboratory=None):
#     year_int = parse_start_year(selected_year)
#     if not year_int:
#         return {"schemes": [], "data": []}

#     curr_start = f"{year_int}-04-01"
#     curr_end   = f"{year_int + 1}-03-31"

#     exclusion_subquery = "(SELECT DISTINCT parent_sample FROM `tabSoil Sample Collection` WHERE parent_sample IS NOT NULL AND parent_sample != '')"
#     filter_logic = f"name NOT IN {exclusion_subquery}"
#     lab_logic  = "COALESCE(NULLIF(lab_name, ''), target_lab)"
#     date_logic = "COALESCE(assigned_to_lab_date, DATE(creation))"

#     completed_placeholders = ", ".join(["%s"] * len(COMPLETED_STATUSES))

#     schemes = frappe.get_all("Scheme or Programs", pluck="name")
#     if not schemes:
#         return {"schemes": [], "data": []}

#     lab_condition = ""
#     lab_params = []
#     if laboratory and laboratory not in ("", "All Laboratories"):
#         lab_condition = f"AND {lab_logic} = %s"
#         lab_params = [laboratory]

#     scheme_placeholders = ", ".join(["%s"] * len(schemes))

#     sql = f"""
#         SELECT
#             COALESCE({lab_logic}, 'Unassigned') AS lab,
#             name_of_type AS scheme,
#             SUM(CASE WHEN {date_logic} BETWEEN %s AND %s THEN 1 ELSE 0 END) AS received,
#             SUM(CASE WHEN {date_logic} BETWEEN %s AND %s AND status IN ({completed_placeholders}) THEN 1 ELSE 0 END) AS completed,
#             SUM(CASE WHEN {date_logic} BETWEEN %s AND %s AND status NOT IN ('Draft', {completed_placeholders}, 'Cancelled', 'Rejected') THEN 1 ELSE 0 END) AS pending,
#             SUM(CASE WHEN {date_logic} BETWEEN %s AND %s AND LOWER(status) = 'rejected' THEN 1 ELSE 0 END) AS rejected
#         FROM `tabSoil Sample Collection`
#         WHERE {filter_logic}
#           AND name_of_type IN ({scheme_placeholders})
#           {lab_condition}
#         GROUP BY {lab_logic}, name_of_type
#         ORDER BY lab ASC, scheme ASC
#     """

#     params = (
#         [curr_start, curr_end] +
#         [curr_start, curr_end] + COMPLETED_STATUSES +
#         [curr_start, curr_end] + COMPLETED_STATUSES +
#         [curr_start, curr_end] +
#         schemes +
#         lab_params
#     )

#     data = frappe.db.sql(sql, params, as_dict=True)

#     return {
#         "schemes": schemes,
#         "data": data
#     }


# @frappe.whitelist()
# def get_lab_client_breakdown(selected_year=None, laboratory=None):
#     year_int = parse_start_year(selected_year)
#     if not year_int:
#         return {"client_types": [], "data": []}

#     curr_start = f"{year_int}-04-01"
#     curr_end   = f"{year_int + 1}-03-31"

#     exclusion_subquery = "(SELECT DISTINCT parent_sample FROM `tabSoil Sample Collection` WHERE parent_sample IS NOT NULL AND parent_sample != '')"
#     filter_logic = f"name NOT IN {exclusion_subquery}"
#     lab_logic  = "COALESCE(NULLIF(lab_name, ''), target_lab)"
#     date_logic = "COALESCE(assigned_to_lab_date, DATE(creation))"

#     completed_placeholders = ", ".join(["%s"] * len(COMPLETED_STATUSES))

#     client_types = frappe.get_all("Soil Sample Collection", pluck="client_type", group_by="client_type")
#     client_types = [c for c in client_types if c]

#     lab_condition = ""
#     lab_params = []
#     if laboratory and laboratory not in ("", "All Laboratories"):
#         lab_condition = f"AND {lab_logic} = %s"
#         lab_params = [laboratory]

#     sql = f"""
#         SELECT
#             COALESCE({lab_logic}, 'Unassigned') AS lab,
#             client_type,
#             SUM(CASE WHEN {date_logic} BETWEEN %s AND %s THEN 1 ELSE 0 END) AS received,
#             SUM(CASE WHEN {date_logic} BETWEEN %s AND %s AND status IN ({completed_placeholders}) THEN 1 ELSE 0 END) AS completed,
#             SUM(CASE WHEN {date_logic} BETWEEN %s AND %s AND status NOT IN ('Draft', {completed_placeholders}, 'Cancelled', 'Rejected') THEN 1 ELSE 0 END) AS pending,
#             SUM(CASE WHEN {date_logic} BETWEEN %s AND %s AND LOWER(status) = 'rejected' THEN 1 ELSE 0 END) AS rejected
#         FROM `tabSoil Sample Collection`
#         WHERE {filter_logic}
#           AND client_type IS NOT NULL AND client_type != ''
#           {lab_condition}
#         GROUP BY {lab_logic}, client_type
#         ORDER BY lab ASC, client_type ASC
#     """

#     params = (
#         [curr_start, curr_end] +
#         [curr_start, curr_end] + COMPLETED_STATUSES +
#         [curr_start, curr_end] + COMPLETED_STATUSES +
#         [curr_start, curr_end] +
#         lab_params
#     )

#     data = frappe.db.sql(sql, params, as_dict=True)

#     return {
#         "client_types": client_types,
#         "data": data
#     }







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

def parse_start_year(selected_year):
    """
    Extracts the base integer year from inputs like '2026-27' or '2026'.
    """
    if not selected_year:
        return None
    try:
        return int(str(selected_year).split('-')[0])
    except ValueError:
        return None


@frappe.whitelist()
def get_soil_intake_data(selected_year=None, laboratory=None):
    year_int = parse_start_year(selected_year)
    if not year_int:
        return {"cards": {}, "table": []}

    curr_start = f"{year_int}-04-01"
    curr_end   = f"{year_int + 1}-03-31"
    prev_start = f"{year_int - 1}-04-01"
    prev_end   = f"{year_int}-03-31"

    # Exclude parent/master samples so only actionable child/standalone samples are counted
    exclusion_subquery = "(SELECT DISTINCT parent_sample FROM `tabSoil Sample Collection` WHERE parent_sample IS NOT NULL AND parent_sample != '')"
    filter_logic = f"name NOT IN {exclusion_subquery}"

    lab_logic  = "COALESCE(NULLIF(lab_name, ''), target_lab)"
    date_logic = "COALESCE(assigned_to_lab_date, DATE(creation))"

    completed_placeholders = ", ".join(["%s"] * len(COMPLETED_STATUSES))

    lab_condition = ""
    lab_params = []
    if laboratory and laboratory not in ("", "All Laboratories"):
        lab_condition = f"AND {lab_logic} = %s"
        lab_params = [laboratory]

    sql = f"""
        SELECT
            COALESCE({lab_logic}, 'Unassigned') AS lab,
            SUM(CASE WHEN {date_logic} BETWEEN %s AND %s AND status NOT IN ('Draft', {completed_placeholders}, 'Cancelled', 'Rejected') THEN 1 ELSE 0 END) AS prev_pending,
            SUM(CASE WHEN {date_logic} BETWEEN %s AND %s THEN 1 ELSE 0 END) AS received_this_year,
            SUM(CASE WHEN {date_logic} BETWEEN %s AND %s AND status IN ({completed_placeholders}) THEN 1 ELSE 0 END) AS completed_this_year,
            SUM(CASE WHEN {date_logic} BETWEEN %s AND %s AND status NOT IN ('Draft', {completed_placeholders}, 'Cancelled', 'Rejected') THEN 1 ELSE 0 END) AS pending_this_year,
            SUM(CASE WHEN {date_logic} BETWEEN %s AND %s AND LOWER(status) = 'rejected' THEN 1 ELSE 0 END) AS rejected_this_year
        FROM `tabSoil Sample Collection`
        WHERE {filter_logic} {lab_condition}
        {MASTER_SAMPLE_EXCLUSION}
        GROUP BY {lab_logic}
        ORDER BY lab ASC
    """

    params = (
        [prev_start, prev_end] + COMPLETED_STATUSES +
        [curr_start, curr_end] +
        [curr_start, curr_end] + COMPLETED_STATUSES +
        [curr_start, curr_end] + COMPLETED_STATUSES +
        [curr_start, curr_end] +
        lab_params
    )

    rows = frappe.db.sql(sql, params, as_dict=True)

    cards = {
        "prev_year_balance": 0,
        "received_this_year": 0,
        "completed_tests": 0,
        "cumulative_total": 0,
        "pending_test": 0,
        "rejected_samples": 0
    }
    table_data = []

    for d in rows:
        prev      = int(d.prev_pending or 0)
        received  = int(d.received_this_year or 0)
        completed = int(d.completed_this_year or 0)
        pending   = int(d.pending_this_year or 0)
        rejected  = int(d.rejected_this_year or 0)

        table_data.append({
            "lab": d.lab or "Unassigned",
            "prev_pending": prev,
            "received": received,
            "completed": completed,
            "current_pending": pending,
            "rejected": rejected
        })

        cards["prev_year_balance"] += prev
        cards["received_this_year"] += received
        cards["completed_tests"]    += completed
        cards["pending_test"]       += pending
        cards["rejected_samples"]   += rejected

    cards["cumulative_total"] = cards["prev_year_balance"] + cards["received_this_year"]
    return {"cards": cards, "table": table_data}


@frappe.whitelist()
def get_filtered_sample_names(selected_year=None, laboratory=None, card_type=None):
    year_int = parse_start_year(selected_year)
    if not year_int or not card_type:
        return []

    curr_start = f"{year_int}-04-01"
    curr_end   = f"{year_int + 1}-03-31"
    prev_start = f"{year_int - 1}-04-01"
    prev_end   = f"{year_int}-03-31"

    exclusion_subquery = "(SELECT DISTINCT parent_sample FROM `tabSoil Sample Collection` WHERE parent_sample IS NOT NULL AND parent_sample != '')"
    filter_logic = f"name NOT IN {exclusion_subquery}"

    lab_logic  = "COALESCE(NULLIF(lab_name, ''), target_lab)"
    date_logic = "COALESCE(assigned_to_lab_date, DATE(creation))"

    completed_placeholders = ", ".join(["%s"] * len(COMPLETED_STATUSES))

    status_params = []

    if card_type == "prev_pending":
        date_cond = f"{date_logic} BETWEEN %s AND %s"
        date_params = [prev_start, prev_end]
        status_cond = f"AND status NOT IN ('Draft', {completed_placeholders}, 'Cancelled', 'Rejected')"
        status_params = COMPLETED_STATUSES
    elif card_type == "received":
        date_cond = f"{date_logic} BETWEEN %s AND %s"
        date_params = [curr_start, curr_end]
        status_cond = ""
    elif card_type == "cumulative":
        date_cond = f"{date_logic} BETWEEN %s AND %s"
        date_params = [prev_start, curr_end]
        status_cond = "AND status NOT IN ('Draft', 'Cancelled')"
    elif card_type == "completed":
        date_cond = f"{date_logic} BETWEEN %s AND %s"
        date_params = [curr_start, curr_end]
        status_cond = f"AND status IN ({completed_placeholders})"
        status_params = COMPLETED_STATUSES
    elif card_type == "pending":
        date_cond = f"{date_logic} BETWEEN %s AND %s"
        date_params = [curr_start, curr_end]
        status_cond = f"AND status NOT IN ('Draft', {completed_placeholders}, 'Cancelled', 'Rejected')"
        status_params = COMPLETED_STATUSES
    elif card_type == "rejected":
        date_cond = f"{date_logic} BETWEEN %s AND %s"
        date_params = [curr_start, curr_end]
        status_cond = "AND LOWER(status) = 'rejected'"
    else:
        return []

    lab_condition = ""
    lab_params = []
    if laboratory and laboratory not in ("", "All Laboratories"):
        lab_condition = f"AND ({lab_logic}) = %s"
        lab_params = [laboratory]

    sql = f"""
        SELECT name
        FROM `tabSoil Sample Collection`
        WHERE {filter_logic}
        AND {date_cond}
        {status_cond}
        {lab_condition}
        {MASTER_SAMPLE_EXCLUSION}
    """

    params = date_params + status_params + lab_params
    rows = frappe.db.sql(sql, params, as_dict=True)
    return [r.name for r in rows]


@frappe.whitelist()
def get_scheme_wise_data(selected_year=None, laboratory=None):
    year_int = parse_start_year(selected_year)
    if not year_int:
        return []

    curr_start = f"{year_int}-04-01"
    curr_end   = f"{year_int + 1}-03-31"

    exclusion_subquery = "(SELECT DISTINCT parent_sample FROM `tabSoil Sample Collection` WHERE parent_sample IS NOT NULL AND parent_sample != '')"
    filter_logic = f"name NOT IN {exclusion_subquery}"

    lab_logic  = "COALESCE(NULLIF(lab_name, ''), target_lab)"
    date_logic = "COALESCE(assigned_to_lab_date, DATE(creation))"

    completed_placeholders = ", ".join(["%s"] * len(COMPLETED_STATUSES))

    schemes = frappe.get_all("Scheme or Programs", pluck="name")
    if not schemes:
        return []

    lab_condition = ""
    lab_params    = []
    if laboratory and laboratory not in ("", "All Laboratories"):
        lab_condition = f"AND {lab_logic} = %s"
        lab_params    = [laboratory]

    scheme_placeholders = ", ".join(["%s"] * len(schemes))

    sql = f"""
        SELECT
            COALESCE({lab_logic}, 'Unassigned') AS lab,
            name_of_type AS scheme,
            SUM(CASE WHEN {date_logic} BETWEEN %s AND %s THEN 1 ELSE 0 END) AS received,
            SUM(CASE WHEN {date_logic} BETWEEN %s AND %s AND status IN ({completed_placeholders}) THEN 1 ELSE 0 END) AS completed,
            SUM(CASE WHEN {date_logic} BETWEEN %s AND %s AND status NOT IN ('Draft', {completed_placeholders}, 'Cancelled', 'Rejected') THEN 1 ELSE 0 END) AS pending,
            SUM(CASE WHEN {date_logic} BETWEEN %s AND %s AND LOWER(status) = 'rejected' THEN 1 ELSE 0 END) AS rejected
        FROM `tabSoil Sample Collection`
        WHERE {filter_logic}
        AND   name_of_type IN ({scheme_placeholders})
        {lab_condition}
        {MASTER_SAMPLE_EXCLUSION}
        GROUP BY {lab_logic}, name_of_type
        ORDER BY lab ASC, scheme ASC
    """

    params = (
        [curr_start, curr_end] +
        [curr_start, curr_end] + COMPLETED_STATUSES +
        [curr_start, curr_end] + COMPLETED_STATUSES +
        [curr_start, curr_end] +
        schemes +
        lab_params
    )

    return frappe.db.sql(sql, params, as_dict=True)


@frappe.whitelist()
def get_lab_scheme_breakdown(selected_year=None, laboratory=None):
    year_int = parse_start_year(selected_year)
    if not year_int:
        return {"schemes": [], "data": []}

    curr_start = f"{year_int}-04-01"
    curr_end   = f"{year_int + 1}-03-31"

    exclusion_subquery = "(SELECT DISTINCT parent_sample FROM `tabSoil Sample Collection` WHERE parent_sample IS NOT NULL AND parent_sample != '')"
    filter_logic = f"name NOT IN {exclusion_subquery}"
    lab_logic  = "COALESCE(NULLIF(lab_name, ''), target_lab)"
    date_logic = "COALESCE(assigned_to_lab_date, DATE(creation))"

    completed_placeholders = ", ".join(["%s"] * len(COMPLETED_STATUSES))

    schemes = frappe.get_all("Scheme or Programs", pluck="name")
    if not schemes:
        return {"schemes": [], "data": []}

    lab_condition = ""
    lab_params = []
    if laboratory and laboratory not in ("", "All Laboratories"):
        lab_condition = f"AND {lab_logic} = %s"
        lab_params = [laboratory]

    scheme_placeholders = ", ".join(["%s"] * len(schemes))

    sql = f"""
        SELECT
            COALESCE({lab_logic}, 'Unassigned') AS lab,
            name_of_type AS scheme,
            SUM(CASE WHEN {date_logic} BETWEEN %s AND %s THEN 1 ELSE 0 END) AS received,
            SUM(CASE WHEN {date_logic} BETWEEN %s AND %s AND status IN ({completed_placeholders}) THEN 1 ELSE 0 END) AS completed,
            SUM(CASE WHEN {date_logic} BETWEEN %s AND %s AND status NOT IN ('Draft', {completed_placeholders}, 'Cancelled', 'Rejected') THEN 1 ELSE 0 END) AS pending,
            SUM(CASE WHEN {date_logic} BETWEEN %s AND %s AND LOWER(status) = 'rejected' THEN 1 ELSE 0 END) AS rejected
        FROM `tabSoil Sample Collection`
        WHERE {filter_logic}
          AND name_of_type IN ({scheme_placeholders})
          {lab_condition}
          {MASTER_SAMPLE_EXCLUSION}
        GROUP BY {lab_logic}, name_of_type
        ORDER BY lab ASC, scheme ASC
    """

    params = (
        [curr_start, curr_end] +
        [curr_start, curr_end] + COMPLETED_STATUSES +
        [curr_start, curr_end] + COMPLETED_STATUSES +
        [curr_start, curr_end] +
        schemes +
        lab_params
    )

    data = frappe.db.sql(sql, params, as_dict=True)

    return {
        "schemes": schemes,
        "data": data
    }


@frappe.whitelist()
def get_lab_client_breakdown(selected_year=None, laboratory=None):
    year_int = parse_start_year(selected_year)
    if not year_int:
        return {"client_types": [], "data": []}

    curr_start = f"{year_int}-04-01"
    curr_end   = f"{year_int + 1}-03-31"

    exclusion_subquery = "(SELECT DISTINCT parent_sample FROM `tabSoil Sample Collection` WHERE parent_sample IS NOT NULL AND parent_sample != '')"
    filter_logic = f"name NOT IN {exclusion_subquery}"
    lab_logic  = "COALESCE(NULLIF(lab_name, ''), target_lab)"
    date_logic = "COALESCE(assigned_to_lab_date, DATE(creation))"

    completed_placeholders = ", ".join(["%s"] * len(COMPLETED_STATUSES))

    client_types = frappe.get_all("Soil Sample Collection", pluck="client_type", group_by="client_type")
    client_types = [c for c in client_types if c]

    lab_condition = ""
    lab_params = []
    if laboratory and laboratory not in ("", "All Laboratories"):
        lab_condition = f"AND {lab_logic} = %s"
        lab_params = [laboratory]

    sql = f"""
        SELECT
            COALESCE({lab_logic}, 'Unassigned') AS lab,
            client_type,
            SUM(CASE WHEN {date_logic} BETWEEN %s AND %s THEN 1 ELSE 0 END) AS received,
            SUM(CASE WHEN {date_logic} BETWEEN %s AND %s AND status IN ({completed_placeholders}) THEN 1 ELSE 0 END) AS completed,
            SUM(CASE WHEN {date_logic} BETWEEN %s AND %s AND status NOT IN ('Draft', {completed_placeholders}, 'Cancelled', 'Rejected') THEN 1 ELSE 0 END) AS pending,
            SUM(CASE WHEN {date_logic} BETWEEN %s AND %s AND LOWER(status) = 'rejected' THEN 1 ELSE 0 END) AS rejected
        FROM `tabSoil Sample Collection`
        WHERE {filter_logic}
          AND client_type IS NOT NULL AND client_type != ''
          {lab_condition}
          {MASTER_SAMPLE_EXCLUSION}
        GROUP BY {lab_logic}, client_type
        ORDER BY lab ASC, client_type ASC
    """

    params = (
        [curr_start, curr_end] +
        [curr_start, curr_end] + COMPLETED_STATUSES +
        [curr_start, curr_end] + COMPLETED_STATUSES +
        [curr_start, curr_end] +
        lab_params
    )

    data = frappe.db.sql(sql, params, as_dict=True)

    return {
        "client_types": client_types,
        "data": data
    }