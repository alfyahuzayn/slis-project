# import frappe

# def update_bin_threshold(item_code, warehouse, threshold):

#     if not warehouse or threshold is None:
#         return

#     bin_name = frappe.db.get_value(
#         "Bin",
#         {
#             "item_code": item_code,
#             "warehouse": warehouse
#         }
#     )

#     if bin_name:
#         frappe.db.set_value(
#             "Bin",
#             bin_name,
#             "custom_minimum_threshold_quantity",
#             threshold
#         )


# def purchase_receipt_on_submit(doc, method):

#     for row in doc.items:

#         if row.custom_minimum_threshold_quantity:

#             update_bin_threshold(
#                 row.item_code,
#                 row.warehouse,
#                 row.custom_minimum_threshold_quantity
#             )


# def stock_entry_on_submit(doc, method):

#     if doc.stock_entry_type != "Material Receipt":
#         return

#     for row in doc.items:

#         if row.custom_minimum_threshold_quantity:

#             update_bin_threshold(
#                 row.item_code,
#                 row.t_warehouse,
#                 row.custom_minimum_threshold_quantity
#             )

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
            threshold
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
    # LOW STOCK / THRESHOLD ALERT COUNT
    # =====================================================
    low_stock_conditions = [
        "IFNULL(b.custom_minimum_threshold_quantity, 0) > 0",
        "b.actual_qty < b.custom_minimum_threshold_quantity",
        "i.disabled = 0"
    ]

    if laboratory:
        low_stock_conditions.append("b.warehouse = %(laboratory)s")

    if item_group:
        low_stock_conditions.append("i.item_group = %(item_group)s")

    if item_code:
        low_stock_conditions.append("b.item_code = %(item_code)s")

    low_stock_where = " AND ".join(low_stock_conditions)

    low_stock_count = frappe.db.sql(f"""
        SELECT COUNT(DISTINCT b.name)
        FROM `tabBin` b
        INNER JOIN `tabItem` i ON i.name = b.item_code
        WHERE {low_stock_where}
    """, params)[0][0] or 0

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
        data = [row for row in data if row.get("item_code") == item_code]

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
        purchase_conditions.append("pri.item_code = %(item_code)s")

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
        issue_conditions.append("sed.item_code = %(item_code)s")

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
        transfer_conditions.append("sed.item_code = %(item_code)s")

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
        damage_conditions.append("bir.item_code = %(item_code)s")

    if item_group:
        damage_conditions.append("i.item_group = %(item_group)s")

    if from_date and to_date:
        damage_conditions.append("bir.broken_date BETWEEN %(from_date)s AND %(to_date)s")

    damage_where = " AND ".join(damage_conditions)

    damaged_items = frappe.db.sql(f"""
        SELECT IFNULL(SUM(bir.quantity_broken), 0)
        FROM `tabBroken Item Register` bir
        INNER JOIN `tabItem` i ON i.name = bir.item_code 
        WHERE {damage_where}
    """, params)[0][0] or 0

    return {
        "total_stock_value": flt(total_stock_value),
        "available_qty": flt(available_qty),
        "purchase_value": flt(purchase_value),
        "material_issues": material_issues,
        "transfers": transfers,
        "damaged_items": damaged_items,
        "low_stock_count": low_stock_count
    }