import frappe
from frappe.utils import now_datetime

@frappe.whitelist()
def get_cumulative_completed_samples():
    today = now_datetime()
    current_year = today.year
    
    # Calculate the start date of the PREVIOUS financial year
    if today.month >= 4:
        # We are in April-Dec 2026. Prev FY started April 2025.
        start_date = f"{current_year - 1}-04-01"
    else:
        # We are in Jan-March 2026. Prev FY started April 2024.
        start_date = f"{current_year - 2}-04-01"

    # Count samples from that start date until NOW
    # Excluding 'completed' and 'draft'
    count = frappe.db.count("Soil Sample Collection", filters={
        "date_of_collection": [">=", start_date],
        "status": "completed"
    })
    
    return count