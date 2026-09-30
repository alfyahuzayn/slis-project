import frappe
from frappe.utils import now_datetime

@frappe.whitelist()
def get_lab_summary():
    # Fetch all collections
    data = frappe.get_all("Soil Sample Collection", 
        fields=["lab_name", "status", "name"])

    summary = {}

    for d in data:
        lab = d.lab_name or "Unassigned"
        if lab not in summary:
            summary[lab] = {"pending": 0, "completed": 0, "cancelled": 0, "total": 0}
        
        # Logic for status categorization
        # Fixed: changed 'doc.status' to 'd.status' and fixed the operators
        if d.status == "completed":
            summary[lab]["completed"] += 1
        elif d.status == "cancelled":
            summary[lab]["cancelled"] += 1
        else:
            summary[lab]["pending"] += 1
            
        summary[lab]["total"] += 1

    # Convert dictionary to list for the frontend table
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