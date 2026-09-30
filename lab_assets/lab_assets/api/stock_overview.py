import frappe
from frappe import _
from frappe.utils import flt
from frappe import _dict
from erpnext.stock.report.stock_balance.stock_balance import execute


# =====================================================
# BIN THRESHOLD UPDATE HOOKS
# =====================================================
def update_bin_threshold(item_code, warehouse, threshold):
    """Updates custom_minimum_threshold_quantity on tabBin."""
    if not warehouse or threshold is None:
        return

    bin_name = frappe.db.get_value(
        "Bin",
        {
            "item_code": item_code,
            "warehouse": warehouse
        }
    )

    if bin_name:
        frappe.db.set_value(
            "Bin",
            bin_name,
            "custom_minimum_threshold_quantity",
            flt(threshold)
        )


def purchase_receipt_on_submit(doc, method):
    """Triggered on Purchase Receipt submission to set Bin threshold."""
    for row in doc.items:
        if row.get("custom_minimum_threshold_quantity"):
            update_bin_threshold(
                row.item_code,
                row.warehouse,
                row.custom_minimum_threshold_quantity
            )


def stock_entry_on_submit(doc, method):
    """Triggered on Stock Entry (Material Receipt) submission to set Bin threshold."""
    if doc.stock_entry_type != "Material Receipt":
        return

    for row in doc.items:
        if row.get("custom_minimum_threshold_quantity"):
            update_bin_threshold(
                row.item_code,
                row.t_warehouse,
                row.custom_minimum_threshold_quantity
            )


# =====================================================
# DASHBOARD CASCADING FILTER APIs
# =====================================================
@frappe.whitelist()
def get_item_groups_by_lab(laboratory=None):
    """Returns Item Groups present in the given Laboratory (Warehouse) via Bin, or all active groups if no lab selected."""
    if laboratory:
        return frappe.db.sql("""
            SELECT DISTINCT i.item_group
            FROM `tabBin` b
            INNER JOIN `tabItem` i ON i.name = b.item_code
            WHERE b.warehouse = %s AND b.actual_qty > 0
            ORDER BY i.item_group ASC
        """, (laboratory,), as_dict=True)
    else:
        return frappe.db.get_all(
            "Item Group",
            filters={"is_group": 0},
            fields=["name as item_group"],
            order_by="name asc",
            limit_page_length=500
        )


@frappe.whitelist()
def get_items_by_group(item_group=None, laboratory=None):
    """Returns Items filtered by group and optionally by laboratory presence."""
    conditions = ["i.disabled = 0"]
    params = {}

    if item_group:
        conditions.append("i.item_group = %(item_group)s")
        params["item_group"] = item_group

    if laboratory:
        conditions.append("b.warehouse = %(laboratory)s AND b.actual_qty > 0")
        params["laboratory"] = laboratory

    where_clause = " AND ".join(conditions)

    if laboratory:
        return frappe.db.sql(f"""
            SELECT DISTINCT i.name, i.item_name
            FROM `tabItem` i
            INNER JOIN `tabBin` b ON b.item_code = i.name
            WHERE {where_clause}
            ORDER BY i.item_name ASC
        """, params, as_dict=True)
    else:
        return frappe.db.sql(f"""
            SELECT name, item_name
            FROM `tabItem` i
            WHERE {where_clause}
            ORDER BY item_name ASC
            LIMIT 1000
        """, params, as_dict=True)


# =====================================================
# DASHBOARD METRICS API
# =====================================================
@frappe.whitelist()
def get_stock_dashboard_data(
    financial_year=None,
    laboratory=None,
    item_group=None,
    item_code=None
):

    # =====================================================
    # FINANCIAL YEAR DATES
    # =====================================================
    from_date = None
    to_date = None

    if financial_year:
        fy = frappe.db.get_value(
            "Fiscal Year",
            financial_year,
            ["year_start_date", "year_end_date"],
            as_dict=True
        )
        if fy:
            from_date = fy.year_start_date
            to_date = fy.year_end_date

    # =====================================================
    # SHARED QUERY PARAMS
    # =====================================================
    params = {
        "laboratory": laboratory,
        "item_group": item_group,
        "item_code": item_code,
        "from_date": from_date,
        "to_date": to_date
    }

    # =====================================================
    # LOW STOCK / THRESHOLD ALERT COUNT & ITEMS
    # =====================================================
    low_stock_conditions = [
        "CAST(IFNULL(b.custom_minimum_threshold_quantity, 0) AS DECIMAL(18, 4)) > 0",
        "b.actual_qty < CAST(IFNULL(b.custom_minimum_threshold_quantity, 0) AS DECIMAL(18, 4))",
        "i.disabled = 0"
    ]

    if laboratory:
        low_stock_conditions.append("b.warehouse = %(laboratory)s")

    if item_group:
        low_stock_conditions.append("i.item_group = %(item_group)s")

    if item_code:
        low_stock_conditions.append("(b.item_code = %(item_code)s OR i.item_name = %(item_code)s)")

    low_stock_where = " AND ".join(low_stock_conditions)

    # Fetch list of low stock item codes for frontend routing
    low_stock_items = frappe.db.sql(f"""
        SELECT DISTINCT b.item_code
        FROM `tabBin` b
        INNER JOIN `tabItem` i ON i.name = b.item_code
        WHERE {low_stock_where}
    """, params, pluck=True) or []

    # =====================================================
    # STOCK BALANCE REPORT FILTERS
    # =====================================================
    filters = _dict({
        "company": "Soil Survey and Soil Conservation Department"
    })

    if from_date and to_date:
        filters.from_date = from_date
        filters.to_date = to_date

    if not financial_year and not laboratory and not item_group and not item_code:
        filters.include_zero_stock_items = 1

    if laboratory:
        filters.warehouse = laboratory

    # Run ERPNext Stock Balance Report
    columns, data = execute(filters)

    # Apply item_group and item_code filters safely in Python
    if item_group:
        data = [row for row in data if row.get("item_group") == item_group]

    if item_code:
        data = [row for row in data if row.get("item_code") == item_code or row.get("item_name") == item_code]

    total_stock_value = 0
    available_qty = 0

    for row in data:
        bal_qty = flt(row.get("bal_qty"))
        bal_val = flt(row.get("bal_val"))
        if bal_qty > 0:
            total_stock_value += bal_val
            available_qty += bal_qty

    # =====================================================
    # PURCHASE VALUE
    # =====================================================
    purchase_conditions = [
        "pr.docstatus = 1",
        "IFNULL(pri.custom_is_stock_item, 0) = 1"
    ]

    if laboratory:
        purchase_conditions.append("pri.warehouse = %(laboratory)s")

    if item_group:
        purchase_conditions.append("pri.item_group = %(item_group)s")

    if item_code:
        purchase_conditions.append("(pri.item_code = %(item_code)s OR pri.item_name = %(item_code)s)")

    if from_date and to_date:
        purchase_conditions.append("pr.posting_date BETWEEN %(from_date)s AND %(to_date)s")

    purchase_where = " AND ".join(purchase_conditions)

    purchase_value = frappe.db.sql(f"""
        SELECT IFNULL(SUM(pri.base_amount), 0)
        FROM `tabPurchase Receipt Item` pri
        INNER JOIN `tabPurchase Receipt` pr ON pr.name = pri.parent
        WHERE {purchase_where}
    """, params)[0][0] or 0

    # =====================================================
    # MATERIAL ISSUES
    # =====================================================
    issue_conditions = [
        "se.docstatus = 1",
        "se.stock_entry_type = 'Material Issue'",
        "IFNULL(se.custom_is_broken_item_entry, 0) = 0"
    ]

    if laboratory:
        issue_conditions.append("se.from_warehouse = %(laboratory)s")

    if item_code:
        issue_conditions.append("(sed.item_code = %(item_code)s OR sed.item_name = %(item_code)s)")

    if item_group:
        issue_conditions.append("sed.item_group = %(item_group)s")

    if from_date and to_date:
        issue_conditions.append("se.posting_date BETWEEN %(from_date)s AND %(to_date)s")

    issue_where = " AND ".join(issue_conditions)

    material_issues = frappe.db.sql(f"""
        SELECT COUNT(DISTINCT se.name)
        FROM `tabStock Entry` se
        INNER JOIN `tabStock Entry Detail` sed ON sed.parent = se.name
        WHERE {issue_where}
    """, params)[0][0] or 0

    # =====================================================
    # MATERIAL TRANSFERS
    # =====================================================
    transfer_conditions = [
        "se.docstatus = 1",
        "se.stock_entry_type = 'Material Transfer'"
    ]

    if laboratory:
        transfer_conditions.append("se.from_warehouse = %(laboratory)s")

    if item_code:
        transfer_conditions.append("(sed.item_code = %(item_code)s OR sed.item_name = %(item_code)s)")

    if item_group:
        transfer_conditions.append("sed.item_group = %(item_group)s")

    if from_date and to_date:
        transfer_conditions.append("se.posting_date BETWEEN %(from_date)s AND %(to_date)s")

    transfer_where = " AND ".join(transfer_conditions)

    transfers = frappe.db.sql(f"""
        SELECT COUNT(DISTINCT se.name)
        FROM `tabStock Entry` se
        INNER JOIN `tabStock Entry Detail` sed ON sed.parent = se.name
        WHERE {transfer_where}
    """, params)[0][0] or 0

    # =====================================================
    # DAMAGED ITEMS
    # =====================================================
    damage_conditions = ["bir.docstatus = 1"]

    if laboratory:
        damage_conditions.append("bir.lab_location = %(laboratory)s")

    if item_code:
        damage_conditions.append("(bir.item_name = %(item_code)s OR i.item_name = %(item_code)s)")

    if item_group:
        damage_conditions.append("i.item_group = %(item_group)s")

    if from_date and to_date:
        damage_conditions.append("bir.broken_date BETWEEN %(from_date)s AND %(to_date)s")

    damage_where = " AND ".join(damage_conditions)

    damaged_items = frappe.db.sql(f"""
        SELECT IFNULL(SUM(bir.quantity_broken), 0)
        FROM `tabBroken Item Register` bir
        INNER JOIN `tabItem` i ON i.name = bir.item_name
        WHERE {damage_where}
    """, params)[0][0] or 0

    return {
        "total_stock_value": flt(total_stock_value),
        "available_qty": flt(available_qty),
        "purchase_value": flt(purchase_value),
        "material_issues": material_issues,
        "transfers": transfers,
        "damaged_items": damaged_items,
        "low_stock_count": len(low_stock_items),
        "low_stock_alert": len(low_stock_items),
        "low_stock_items": low_stock_items
    }
#employee wise stock overview(dashboard)



import frappe
from frappe import _dict
from frappe.utils import flt, today
from erpnext.stock.report.stock_balance.stock_balance import execute


# =========================================================
# HELPER: DYNAMIC THRESHOLD EXPRESSION BUILDER
# =========================================================
def get_threshold_sql_expression():
    """
    Builds SQL expression checking tabBin first, falling back to tabItem, then 0.
    """
    bin_has_col = frappe.db.has_column("Bin", "custom_minimum_threshold_quantity")
    item_has_col = frappe.db.has_column("Item", "custom_minimum_threshold_quantity")

    if bin_has_col and item_has_col:
        return "COALESCE(NULLIF(b.custom_minimum_threshold_quantity, 0), NULLIF(i.custom_minimum_threshold_quantity, 0), 0)"
    elif bin_has_col:
        return "IFNULL(b.custom_minimum_threshold_quantity, 0)"
    elif item_has_col:
        return "IFNULL(i.custom_minimum_threshold_quantity, 0)"
    else:
        return "0"


# =========================================================
# EMPLOYEE STOCK DASHBOARD
# =========================================================

@frappe.whitelist()
def get_employee_stock_dashboard(financial_year=None):
    user = frappe.session.user

    # =====================================================
    # USER WAREHOUSES
    # =====================================================
    allowed_warehouses = frappe.get_all(
        "User Permission",
        filters={
            "user": user,
            "allow": "Warehouse"
        },
        fields=["for_value"]
    )

    warehouse_list = [d.for_value for d in allowed_warehouses]

    # =====================================================
    # NO ACCESS
    # =====================================================
    if not warehouse_list:
        return {
            "lab_name": "-",
            "low_stock_alert": 0,
            "shelf_life_expired": 0,
            "total_stock_value": 0,
            "available_qty": 0,
            "purchase_value": 0,
            "material_issues": 0,
            "transfers": 0,
            "damaged_items": 0
        }

    target_warehouse = warehouse_list[0]

    # =====================================================
    # FY DATES
    # =====================================================
    from_date = None
    to_date = None

    if financial_year:
        fy = frappe.db.get_value(
            "Fiscal Year",
            financial_year,
            ["year_start_date", "year_end_date"],
            as_dict=True
        )

        if fy:
            from_date = fy.year_start_date
            to_date = fy.year_end_date

    # =====================================================
    # LOW STOCK ALERT COUNT (DYNAMIC THRESHOLD & <= CHECK)
    # =====================================================
    threshold_expr = get_threshold_sql_expression()

    low_stock_alert = frappe.db.sql(f"""
        SELECT COUNT(DISTINCT b.name)
        FROM `tabBin` b
        INNER JOIN `tabItem` i ON i.name = b.item_code
        WHERE b.warehouse = %(warehouse)s
          AND i.disabled = 0
          AND CAST({threshold_expr} AS DECIMAL(18, 4)) > 0
          AND b.actual_qty <= CAST({threshold_expr} AS DECIMAL(18, 4))
    """, {"warehouse": target_warehouse})[0][0] or 0

    # =====================================================
    # SHELF LIFE EXPIRED COUNT (DIRECT SYNC WITH DETAILS)
    # =====================================================
    expired_items = get_employee_expired_stock_details()
    shelf_life_expired = len(expired_items) if expired_items else 0

    # =====================================================
    # STOCK BALANCE
    # =====================================================
    filters = _dict({
        "company": "Soil Survey and Soil Conservation Department",
        "warehouse": target_warehouse
    })

    if from_date and to_date:
        filters.from_date = from_date
        filters.to_date = to_date

    columns, data = execute(filters)

    total_stock_value = 0
    available_qty = 0

    for row in data:
        bal_qty = flt(row.get("bal_qty"))
        bal_val = flt(row.get("bal_val"))

        if bal_qty > 0:
            total_stock_value += bal_val
            available_qty += bal_qty

    # =====================================================
    # PURCHASE VALUE
    # =====================================================
    purchase_conditions = [
        "pr.docstatus = 1",
        "pri.warehouse = %(warehouse)s"
    ]

    if from_date and to_date:
        purchase_conditions.append("pr.posting_date BETWEEN %(from_date)s AND %(to_date)s")

    purchase_where = " AND ".join(purchase_conditions)

    purchase_value = frappe.db.sql(f"""
        SELECT IFNULL(SUM(pri.base_amount), 0)
        FROM `tabPurchase Receipt Item` pri
        INNER JOIN `tabPurchase Receipt` pr ON pr.name = pri.parent
        WHERE {purchase_where}
    """, {
        "warehouse": target_warehouse,
        "from_date": from_date,
        "to_date": to_date
    })[0][0] or 0

    # =====================================================
    # MATERIAL ISSUES
    # =====================================================
    issue_conditions = [
        "docstatus = 1",
        "stock_entry_type = 'Material Issue'",
        "from_warehouse = %(warehouse)s"
    ]

    if from_date and to_date:
        issue_conditions.append("posting_date BETWEEN %(from_date)s AND %(to_date)s")

    issue_where = " AND ".join(issue_conditions)

    material_issues = frappe.db.sql(f"""
        SELECT COUNT(name)
        FROM `tabStock Entry`
        WHERE {issue_where}
    """, {
        "warehouse": target_warehouse,
        "from_date": from_date,
        "to_date": to_date
    })[0][0] or 0

    # =====================================================
    # TRANSFERS
    # =====================================================
    transfer_conditions = [
        "docstatus = 1",
        "stock_entry_type = 'Material Transfer'",
        "from_warehouse = %(warehouse)s"
    ]

    if from_date and to_date:
        transfer_conditions.append("posting_date BETWEEN %(from_date)s AND %(to_date)s")

    transfer_where = " AND ".join(transfer_conditions)

    transfers = frappe.db.sql(f"""
        SELECT COUNT(name)
        FROM `tabStock Entry`
        WHERE {transfer_where}
    """, {
        "warehouse": target_warehouse,
        "from_date": from_date,
        "to_date": to_date
    })[0][0] or 0

    # =====================================================
    # DAMAGED ITEMS
    # =====================================================
    damage_conditions = [
        "docstatus = 1",
        "lab_location = %(warehouse)s"
    ]

    if from_date and to_date:
        damage_conditions.append("broken_date BETWEEN %(from_date)s AND %(to_date)s")

    damage_where = " AND ".join(damage_conditions)

    damaged_items = frappe.db.sql(f"""
        SELECT IFNULL(SUM(quantity_broken), 0)
        FROM `tabBroken Item Register`
        WHERE {damage_where}
    """, {
        "warehouse": target_warehouse,
        "from_date": from_date,
        "to_date": to_date
    })[0][0] or 0

    # =====================================================
    # RETURN
    # =====================================================
    return {
        "lab_name": target_warehouse,
        "low_stock_alert": low_stock_alert,
        "shelf_life_expired": shelf_life_expired,
        "total_stock_value": flt(total_stock_value),
        "available_qty": flt(available_qty),
        "purchase_value": flt(purchase_value),
        "material_issues": material_issues,
        "transfers": transfers,
        "damaged_items": damaged_items
    }


# =========================================================
# GET EMPLOYEE LOW STOCK DETAILS (FOR DIALOG POPUP)
# =========================================================

@frappe.whitelist()
def get_employee_low_stock_details():
    user = frappe.session.user

    allowed_warehouses = frappe.get_all(
        "User Permission",
        filters={
            "user": user,
            "allow": "Warehouse"
        },
        fields=["for_value"]
    )

    warehouse_list = [d.for_value for d in allowed_warehouses]

    if not warehouse_list:
        return []

    threshold_expr = get_threshold_sql_expression()

    return frappe.db.sql(f"""
        SELECT 
            b.item_code,
            i.item_name,
            b.warehouse,
            b.actual_qty,
            CAST({threshold_expr} AS DECIMAL(18, 4)) AS min_threshold
        FROM `tabBin` b
        INNER JOIN `tabItem` i ON i.name = b.item_code
        WHERE b.warehouse IN %(warehouses)s
          AND i.disabled = 0
          AND CAST({threshold_expr} AS DECIMAL(18, 4)) > 0
          AND b.actual_qty <= CAST({threshold_expr} AS DECIMAL(18, 4))
        ORDER BY b.warehouse ASC, i.item_name ASC
    """, {"warehouses": tuple(warehouse_list)}, as_dict=True)


# =========================================================
# STOCK GROUP DISTRIBUTION
# =========================================================

@frappe.whitelist()
def get_stock_group_distribution():
    user = frappe.session.user

    allowed_warehouses = frappe.get_all(
        "User Permission",
        filters={
            "user": user,
            "allow": "Warehouse"
        },
        fields=["for_value"]
    )

    warehouse_list = [d.for_value for d in allowed_warehouses]

    allowed_labs = frappe.get_all(
        "User Permission",
        filters={
            "user": user,
            "allow": "Soil Laboratory"
        },
        fields=["for_value"]
    )

    lab_names = [d.for_value for d in allowed_labs]

    if not warehouse_list:
        return {
            "labs": [],
            "groups": []
        }

    groups = frappe.db.sql("""
        SELECT
            ig.name as item_group,
            COUNT(i.name) as qty
        FROM `tabItem Group` ig
        INNER JOIN `tabItem Default` id ON id.parent = ig.name
        LEFT JOIN `tabItem` i ON i.item_group = ig.name
        WHERE id.default_warehouse IN %(warehouses)s
        GROUP BY ig.name
        ORDER BY qty DESC
    """, {
        "warehouses": tuple(warehouse_list)
    }, as_dict=1)

    return {
        "labs": lab_names,
        "groups": groups
    }


# =========================================================
# GET EMPLOYEE EXPIRED STOCK DETAILS (FOR DIALOG POPUP)
# =========================================================

@frappe.whitelist()
def get_employee_expired_stock_details():
    user = frappe.session.user
    warehouses = frappe.get_all(
        "User Permission",
        filters={"user": user, "allow": "Warehouse"},
        pluck="for_value"
    )
    lab_warehouse = warehouses[0] if warehouses else None
    wh_cond = "AND sbe.warehouse = %(warehouse)s" if lab_warehouse else ""
    
    query = f"""
        SELECT 
            i.name AS item_code,
            i.item_name,
            sbe.batch_no,
            sbe.warehouse,
            b.manufacturing_date AS purchased_date,
            b.expiry_date,
            SUM(
                CASE 
                    WHEN sbe.is_outward = 1 THEN -ABS(sbe.qty) 
                    ELSE ABS(sbe.qty) 
                END
            ) AS qty
        FROM `tabSerial and Batch Entry` sbe
        INNER JOIN `tabSerial and Batch Bundle` sab ON sab.name = sbe.parent
        INNER JOIN `tabBatch` b ON b.name = sbe.batch_no
        INNER JOIN `tabItem` i ON i.name = b.item
        WHERE 
            b.expiry_date IS NOT NULL
            AND b.expiry_date < %(today)s
            AND i.has_batch_no = 1
            AND i.has_expiry_date = 1
            AND sab.docstatus = 1
            AND sab.is_cancelled = 0
            AND sab.is_rejected = 0
            {wh_cond}
        GROUP BY sbe.batch_no, sbe.warehouse
        HAVING qty > 0
        ORDER BY b.expiry_date ASC
    """
    
    return frappe.db.sql(query, {
        "today": today(),
        "warehouse": lab_warehouse
    }, as_dict=True)