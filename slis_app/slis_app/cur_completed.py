import frappe
from frappe.utils import now_datetime

@frappe.whitelist()
def get_current_fy_completed_count():
    today = now_datetime()
    current_year = today.year
    
    # Financial Year Logic: Determine the start of the current FY (April 1st)
    if today.month >= 4:
        # We are in April 2026 - March 2027
        start_date = f"{current_year}-04-01"
    else:
        # We are in Jan - March 2026, so FY started in April 2025
        start_date = f"{current_year - 1}-04-01"

    # Count only 'completed' samples created since the start of this FY
    # Ensure "completed" matches your DocType's exact case (e.g., "Completed")
    count = frappe.db.count("Soil Sample Collection", filters={
        "creation": [">=", start_date],
        "status": "completed" 
    })
    
    return count