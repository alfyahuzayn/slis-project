# import frappe
# from frappe.utils import now_datetime

# @frappe.whitelist()
# def get_lab_summary_fy():
#     today = now_datetime()
#     current_year = today.year
    
#     # Financial Year Start Calculation
#     if today.month >= 4:
#         fy_start = f"{current_year}-04-01"
#     else:
#         fy_start = f"{current_year - 1}-04-01"

#     # 1. Get all unique labs from the 'target_lab' field
#     all_labs = frappe.get_all("Soil Sample Collection", fields=["distinct target_lab"])
#     summary = {}
#     for l in all_labs:
#         name = l.target_lab or "Unassigned"
#         summary[name] = {"pending": 0, "completed": 0, "total": 0}

#     # 2. Fetch samples from this FY
#     data = frappe.get_all("Soil Sample Collection", 
#         filters={
#             "creation": [">=", fy_start]
#         },
#         fields=["target_lab", "status"])

#     # 3. Categorize counts
#     for d in data:
#         lab = d.target_lab or "Unassigned"
#         if lab not in summary:
#             summary[lab] = {"pending": 0, "completed": 0, "total": 0}
        
#         # Match case to your DocType status options
#         if d.status == "completed":
#             summary[lab]["completed"] += 1
#         elif d.status not in ["completed", "draft", "Cancelled"]:
#             summary[lab]["pending"] += 1
            
#         summary[lab]["total"] += 1

#     # 4. Format for Table with Completion Status
#     final_list = []
#     for idx, (lab, counts) in enumerate(summary.items(), start=1):
#         # Calculate completion percentage for the 'Status' column
#         percentage = 0
#         if counts["total"] > 0:
#             percentage = round((counts["completed"] / counts["total"]) * 100, 1)
        
#         final_list.append({
#             "sn": idx,
#             "lab": lab,
#             "total": counts["total"],
#             "pending": counts["pending"],
#             "completed": counts["completed"],
#             "status_pct": f"{percentage}%"
#         })
    
#     return final_list








import frappe
from frappe.utils import now_datetime, getdate

@frappe.whitelist()
def get_lab_summary_fy():
    today = now_datetime()
    current_year = today.year
    
    # Financial Year Start Calculation (April 1st)
    if today.month >= 4:
        fy_start = f"{current_year}-04-01"
    else:
        fy_start = f"{current_year - 1}-04-01"

    # Fetch data using SQL for complex conditional sums
    # We exclude 'Draft' and 'Cancelled' from most logic as per standard ERP habits
    data = frappe.db.sql(f"""
        SELECT 
            target_lab,
            
            /* 1. Previous Year's Balance (Collected before FY start, not Completed/Draft) */
            SUM(CASE WHEN date_of_collection < '{fy_start}' 
                AND status NOT IN ('Completed', 'Draft', 'Cancelled') THEN 1 ELSE 0 END) as prev_balance,
            
            /* 2. Received This Year (Collected on/after FY start) */
            SUM(CASE WHEN date_of_collection >= '{fy_start}' THEN 1 ELSE 0 END) as received_this_year,
            
            /* 4. Analysis Completed This Year (Collected any time, but Completed after FY start) */
            /* Note: Usually 'Completed This Year' refers to the completion date, 
               but since we're using collection_date, we filter by status and current year */
            SUM(CASE WHEN date_of_collection >= '{fy_start}' 
                AND status = 'Completed' THEN 1 ELSE 0 END) as completed_this_year,
            
            /* 5. Cumulative Completed (All time status = Completed) */
            SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as cumulative_completed,
            
            /* 6. Pending This Year (Collected this FY, not Completed/Draft) */
            SUM(CASE WHEN date_of_collection >= '{fy_start}' 
                AND status NOT IN ('Completed', 'Draft', 'Cancelled') THEN 1 ELSE 0 END) as pending_this_year,
                
            /* 7. Cumulative Pending (All time, not Completed/Draft) */
            SUM(CASE WHEN status NOT IN ('Completed', 'Draft', 'Cancelled') THEN 1 ELSE 0 END) as cumulative_pending

        FROM `tabSoil Sample Collection`
        GROUP BY target_lab
    """, as_dict=True)

    final_list = []
    for idx, d in enumerate(data, start=1):
        lab_name = d.target_lab or "Unassigned"
        
        # 3. Cumulative Total Samples (1 + 2)
        total_samples = d.prev_balance + d.received_this_year
        
        final_list.append({
            "sn": idx,
            "lab": lab_name,
            "prev_balance": d.prev_balance,              # Column 1
            "received_this_year": d.received_this_year,  # Column 2
            "cumulative_total": total_samples,           # Column 3
            "completed_this_year": d.completed_this_year,# Column 4
            "cumulative_completed": d.cumulative_completed, # Column 5
            "pending_this_year": d.pending_this_year,    # Column 6
            "cumulative_pending": d.cumulative_pending    # Column 7
        })
    
    return final_list