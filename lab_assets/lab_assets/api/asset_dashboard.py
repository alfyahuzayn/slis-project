import frappe
from frappe.utils import flt
import json

@frappe.whitelist()
def get_filtered_categories(laboratory=None):
    """
    Returns Asset Categories associated with assets in the selected laboratory.
    """
    filters = {}
    if laboratory:
        filters["location"] = laboratory

    categories = frappe.get_all(
        "Asset",
        filters=filters,
        pluck="asset_category",
        distinct=True
    )
    return sorted([c for c in categories if c])


@frappe.whitelist()
def get_filtered_assets(laboratory=None, asset_category=None):
    """
    Returns Assets filtered by laboratory and/or asset category.
    """
    filters = {}
    if laboratory:
        filters["location"] = laboratory
    if asset_category:
        filters["asset_category"] = asset_category

    return frappe.get_all(
        "Asset",
        filters=filters,
        fields=["name", "asset_name"],
        order_by="asset_name asc",
        limit_page_length=1000
    )


@frappe.whitelist()
def get_dashboard_data(
    fiscal_year=None,
    laboratory=None,
    asset_category=None,
    asset=None
):
    """
    Calculates dynamic KPI metrics including exact JSON test parsing for Bulk Result Entry.
    Uses ORM counts to respect User Permissions.
    """
    # ----------------------------------------------------
    # 1. BASE ASSET FILTERS (Permission-aware)
    # ----------------------------------------------------
    base_filters = {}

    if fiscal_year:
        fy = frappe.get_doc("Fiscal Year", fiscal_year)
        base_filters["purchase_date"] = ["between", [fy.year_start_date, fy.year_end_date]]

    if laboratory:
        base_filters["location"] = laboratory

    if asset_category:
        base_filters["asset_category"] = asset_category

    if asset:
        base_filters["name"] = asset

    # Metrics
    total_assets = frappe.db.count("Asset", filters=base_filters)

    # Calculate Total Purchase Value
    assets_for_value = frappe.get_all("Asset", filters=base_filters, fields=["gross_purchase_amount"])
    purchase_value = sum([flt(a.gross_purchase_amount) for a in assets_for_value])

    # Active Assets
    active_filters = base_filters.copy()
    active_filters["docstatus"] = 1
    active_filters["status"] = ["!=", "Scrapped"]
    active_assets = frappe.db.count("Asset", filters=active_filters)

    # Scrapped Assets
    scrapped_filters = base_filters.copy()
    scrapped_filters["status"] = "Scrapped"
    scrapped_assets = frappe.db.count("Asset", filters=scrapped_filters)

    # AMC & Warranty Statuses
    amc_exp_filters = base_filters.copy()
    amc_exp_filters["custom_amc_status"] = "Expired"
    amc_expired = frappe.db.count("Asset", filters=amc_exp_filters)

    w_exp_filters = base_filters.copy()
    w_exp_filters["custom_warranty_status"] = "Expired"
    warranty_expired = frappe.db.count("Asset", filters=w_exp_filters)

    amc_soon_filters = base_filters.copy()
    amc_soon_filters["custom_amc_status"] = "Expiring Soon"
    amc_expiring_soon = frappe.db.count("Asset", filters=amc_soon_filters)

    w_soon_filters = base_filters.copy()
    w_soon_filters["custom_warranty_status"] = "Expiring Soon"
    warranty_expiring_soon = frappe.db.count("Asset", filters=w_soon_filters)

    # Under Repair
    repair_filters = {"repair_status": "Pending"}
    if asset:
        repair_filters["asset"] = asset
    elif laboratory or asset_category:
        lab_asset_names = frappe.get_all("Asset", filters=base_filters, pluck="name")
        repair_filters["asset"] = ["in", lab_asset_names] if lab_asset_names else ""

    under_repair = frappe.db.count("Asset Repair", filters=repair_filters)

    # ----------------------------------------------------
    # 2. JSON TESTS COMPLETED CALCULATION (Exact Match)
    # ----------------------------------------------------
    target_machine_names = []
    if asset:
        asset_doc = frappe.db.get_value("Asset", asset, ["asset_name", "name"], as_dict=True)
        if asset_doc:
            if asset_doc.asset_name:
                target_machine_names.append(asset_doc.asset_name.strip().lower())
            if asset_doc.name:
                target_machine_names.append(asset_doc.name.strip().lower())
    else:
        target_assets = frappe.get_all("Asset", filters=base_filters, fields=["asset_name", "name"])
        for a in target_assets:
            if a.asset_name:
                target_machine_names.append(a.asset_name.strip().lower())
            if a.name:
                target_machine_names.append(a.name.strip().lower())

    target_machine_names = list(set([m for m in target_machine_names if m]))

    tests_completed = 0

    if target_machine_names:
        ssc_cols = frappe.db.get_table_columns("Soil Sample Collection")

        sample_query = """
            SELECT child.values_json
            FROM `tabSample Data` child
            INNER JOIN `tabBulk Result Entry` parent ON child.parent = parent.name
            LEFT JOIN `tabSoil Sample Collection` ssc ON child.lab_code = ssc.name
            WHERE child.values_json IS NOT NULL AND child.values_json != ''
        """
        sample_params = {}

        if fiscal_year and "collection_date" in ssc_cols:
            fy = frappe.get_doc("Fiscal Year", fiscal_year)
            sample_query += " AND ssc.collection_date BETWEEN %(from_date)s AND %(to_date)s"
            sample_params["from_date"] = fy.year_start_date
            sample_params["to_date"] = fy.year_end_date

        # Only apply location restriction if no specific Asset filter is selected
        if laboratory and not asset:
            lab_fields = [col for col in ["lab", "soil_laboratory", "location", "laboratory", "branch"] if col in ssc_cols]
            if lab_fields:
                or_clauses = [f"ssc.{field} = %(laboratory)s" for field in lab_fields]
                sample_query += f" AND ({' OR '.join(or_clauses)})"
                sample_params["laboratory"] = laboratory

        json_rows = frappe.db.sql(sample_query, sample_params, as_dict=True)

        for row in json_rows:
            try:
                data = json.loads(row.values_json)
                if isinstance(data, dict):
                    for test_param, param_val in data.items():
                        if isinstance(param_val, dict):
                            machine = str(param_val.get("machine") or "").strip().lower()
                            if machine in target_machine_names:
                                tests_completed += 1
            except Exception:
                continue

    return {
        "total_assets": total_assets,
        "purchase_value": flt(purchase_value),
        "active_assets": active_assets,
        "scrapped_assets": scrapped_assets,
        "amc_expired": amc_expired,
        "warranty_expired": warranty_expired,
        "amc_expiring_soon": amc_expiring_soon,
        "warranty_expiring_soon": warranty_expiring_soon,
        "under_repair": under_repair,
        "tests_completed": tests_completed
    }
#for employee dashboard 


import frappe
from frappe.utils import flt


@frappe.whitelist()
def get_employee_dashboard_data(fiscal_year=None):

    user = frappe.session.user

    roles = frappe.get_roles(user)

    is_admin = (
        user == "Administrator"
        or "System Manager" in roles
    )

    # ==========================================
    # GET USER LAB PERMISSIONS
    # ==========================================

    lab_names = []

    if not is_admin:

        lab_names = frappe.get_all(
            "User Permission",
            filters={
                "user": user,
                "allow": "Soil Laboratory"
            },
            pluck="for_value"
        )

        if not lab_names:

            return {
                "total_assets": 0,
                "purchase_value": 0,
                "active_assets": 0,
                "under_repair": 0,
                "scrapped_assets": 0,
                "amc_expired": 0,
                "warranty_expired": 0
            }

    # ==========================================
    # FY CONDITION
    # ==========================================

    conditions = []
    values = {}

    if fiscal_year:

        fy = frappe.get_doc("Fiscal Year", fiscal_year)

        conditions.append("""
            purchase_date
            BETWEEN %(from_date)s
            AND %(to_date)s
        """)

        values["from_date"] = fy.year_start_date
        values["to_date"] = fy.year_end_date

    if not is_admin:

        conditions.append(
            "location IN %(labs)s"
        )

        values["labs"] = tuple(lab_names)

    where = ""

    if conditions:

        where = "WHERE " + " AND ".join(conditions)

    # ==========================================
    # TOTAL ASSETS
    # ==========================================

    total_assets = frappe.db.sql(f"""
        SELECT COUNT(name)
        FROM `tabAsset`
        {where}
    """, values)[0][0] or 0

    # ==========================================

    purchase_value = frappe.db.sql(f"""
        SELECT SUM(gross_purchase_amount)
        FROM `tabAsset`
        {where}
    """, values)[0][0] or 0

    # ==========================================

    active_where = where

    if active_where:

        active_where += " AND status!='Scrapped'"

    else:

        active_where = "WHERE status!='Scrapped'"

    active_assets = frappe.db.sql(f"""
        SELECT COUNT(name)
        FROM `tabAsset`
        {active_where}
    """, values)[0][0] or 0

    # ==========================================

    scrap_where = where

    if scrap_where:

        scrap_where += " AND status='Scrapped'"

    else:

        scrap_where = "WHERE status='Scrapped'"

    scrapped_assets = frappe.db.sql(f"""
        SELECT COUNT(name)
        FROM `tabAsset`
        {scrap_where}
    """, values)[0][0] or 0

    # ==========================================

    amc_where = where

    if amc_where:

        amc_where += " AND custom_amc_status='Expired'"

    else:

        amc_where = "WHERE custom_amc_status='Expired'"

    amc_expired = frappe.db.sql(f"""
        SELECT COUNT(name)
        FROM `tabAsset`
        {amc_where}
    """, values)[0][0] or 0

    # ==========================================

    warranty_where = where

    if warranty_where:

        warranty_where += " AND custom_warranty_status='Expired'"

    else:

        warranty_where = "WHERE custom_warranty_status='Expired'"

    warranty_expired = frappe.db.sql(f"""
        SELECT COUNT(name)
        FROM `tabAsset`
        {warranty_where}
    """, values)[0][0] or 0

    # ==========================================
    # UNDER REPAIR
    # ==========================================

    repair_conditions = [
        "ar.repair_status='Pending'"
    ]

    if fiscal_year:

        repair_conditions.append("""
            a.purchase_date
            BETWEEN %(from_date)s
            AND %(to_date)s
        """)

    if not is_admin:

        repair_conditions.append(
            "a.location IN %(labs)s"
        )

    repair_where = "WHERE " + " AND ".join(repair_conditions)

    under_repair = frappe.db.sql(f"""
        SELECT COUNT(ar.name)
        FROM `tabAsset Repair` ar
        LEFT JOIN `tabAsset` a
        ON ar.asset = a.name

        {repair_where}
    """, values)[0][0] or 0

    return {

        "total_assets": total_assets,

        "purchase_value": flt(purchase_value),

        "active_assets": active_assets,

        "under_repair": under_repair,

        "scrapped_assets": scrapped_assets,

        "amc_expired": amc_expired,

        "warranty_expired": warranty_expired

    }