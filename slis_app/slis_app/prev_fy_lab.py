import frappe
from frappe.utils import now_datetime

@frappe.whitelist()
def get_lab_summary_last_fy():
    today = now_datetime()
    current_year = today.year
    
    # Calculate Last Financial Year Date Range
    if today.month >= 4:
        # Currently in FY 2026-27. Last FY was April 2025 - March 2026.
        start_date = f"{current_year - 1}-04-01"
        end_date = f"{current_year}-03-31"
    else:
        # Currently in FY 2025-26. Last FY was April 2024 - March 2025.
        start_date = f"{current_year - 2}-04-01"
        end_date = f"{current_year - 1}-03-31"

    # 1. Get all unique labs from the 'target_lab' field
    all_labs = frappe.get_all("Soil Sample Collection", fields=["distinct target_lab"])
    summary = {}
    for l in all_labs:
        name = l.target_lab or "Unassigned"
        summary[name] = {"pending": 0, "completed": 0, "total": 0}

    # 2. Fetch samples from Last FY only
    data = frappe.get_all("Soil Sample Collection", 
        filters={
            "creation": ["between", [start_date, end_date]]
        },
        fields=["target_lab", "status"])

    # 3. Categorize counts
    for d in data:
        lab = d.target_lab or "Unassigned"
        if lab not in summary:
            summary[lab] = {"pending": 0, "completed": 0, "total": 0}
        
        # Consistent status check
        if d.status == "completed":
            summary[lab]["completed"] += 1
        elif d.status not in ["completed", "draft", "Cancelled"]:
            summary[lab]["pending"] += 1
            
        summary[lab]["total"] += 1

    # 4. Format for Table
    final_list = []
    for idx, (lab, counts) in enumerate(summary.items(), start=1):
        percentage = 0
        if counts["total"] > 0:
            percentage = round((counts["completed"] / counts["total"]) * 100, 1)
        
        final_list.append({
            "sn": idx,
            "lab": lab,
            "total": counts["total"],
            "pending": counts["pending"],
            "completed": counts["completed"],
            "status_pct": f"{percentage}%"
        })
    
    return final_list