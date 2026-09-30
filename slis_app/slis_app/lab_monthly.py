import frappe  # This line was missing!
from frappe.utils import now_datetime, get_first_day, get_last_day

@frappe.whitelist()
def get_monthly_lab_summary():
    # Get the date range for the current month
    today = now_datetime()
    first_day = get_first_day(today)
    last_day = get_last_day(today)

    # Fetch collections filtered by the current month's creation date
    data = frappe.get_all("Soil Sample Collection", 
        filters={
            "campaign_date": ["between", [first_day, last_day]]
        },
        fields=["target_lab", "status", "name"])

    summary = {}
    for d in data:
        lab = d.target_lab or "Unassigned"
        if lab not in summary:
            summary[lab] = {"pending": 0, "completed": 0, "cancelled": 0, "total": 0}
        
        # Ensure comparison matches your DocType's exact status values
        if d.status == "completed":
            summary[lab]["completed"] += 1
        elif d.status == "cancelled":
            summary[lab]["cancelled"] += 1
        else:
            summary[lab]["pending"] += 1
            
        summary[lab]["total"] += 1

    final_list = []
    for idx, (lab, counts) in enumerate(summary.items(), start=1):
        final_list.append({
            "sn": idx,
            "lab": lab,
            "total": counts["total"],
            "pending": counts["pending"],
            "completed": counts["completed"],
            "cancelled": counts["cancelled"]
        })
    
    return final_list