import frappe
from frappe.utils import now_datetime

@frappe.whitelist()
def get_previous_fy_incomplete_samples():
    today = now_datetime()
    current_year = today.year
    
    # Financial Year Logic
    if today.month >= 4:
        # Previous FY: April 2025 - March 2026
        start_date = f"{current_year - 1}-04-01"
        end_date = f"{current_year}-03-31"
    else:
        # Previous FY: April 2024 - March 2025
        start_date = f"{current_year - 2}-04-01"
        end_date = f"{current_year - 1}-03-31"

    # Count samples where status is NOT "completed"
    # Note: Ensure "completed" matches the exact case in your DocType
    count = frappe.db.count("Soil Sample Collection", filters={
        "collection_date": ["between", [start_date, end_date]],
        "status": ["not in", ["completed", "draft"]] 
    })
    
    return count