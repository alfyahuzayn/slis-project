import frappe
from frappe.utils import now_datetime

@frappe.whitelist()
def get_current_financial_year():
    today = now_datetime()
    if today.month >= 4:
        # Returns 2026-27
        fy = f"{today.year}-{str(today.year + 1)[2:]}"
    else:
        # Returns 2025-26
        fy = f"{today.year - 1}-{str(today.year)[2:]}"
    return fy