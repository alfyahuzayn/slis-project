import frappe

@frappe.whitelist()
def get_district_wise_counts():
    # Only querying district_name now
    data = frappe.db.sql("""
        SELECT UPPER(district_name) as district, COUNT(name) as count 
        FROM `tabSoil Sample Collection` 
        WHERE district_name IS NOT NULL AND district_name != ''
        GROUP BY district_name
    """, as_dict=True)
    
    return {d.district: d.count for d in data}


# import frappe

# @frappe.whitelist()
# def get_district_wise_counts():
#     # We use COALESCE to pick the first non-null value between the two fields
#     # NULLIF handles cases where the field might be an empty string ''
#     data = frappe.db.sql("""
#         SELECT 
#             UPPER(COALESCE(NULLIF(district, ''), NULLIF(district_name, ''))) as district, 
#             COUNT(name) as count 
#         FROM `tabSoil Sample Collection` 
#         WHERE (district IS NOT NULL AND district != '') 
#            OR (district_name IS NOT NULL AND district_name != '')
#         GROUP BY district
#     """, as_dict=True)
    
#     # Return as a dictionary: {"IDUKKI": 34, "KOLLAM": 12...}
#     return {d.district: d.count for d in data if d.district}