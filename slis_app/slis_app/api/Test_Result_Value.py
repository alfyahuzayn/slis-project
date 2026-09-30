# import frappe

# @frappe.whitelist()
# def Test_Result_Value(test_name):

#     doc_list = frappe.get_all(
#         "Soil Test Package",
#         filters={"test_name": test_name},
#         limit_page_length=1
#     )

#     if not doc_list:
#         return None

#     doc = frappe.get_doc("Soil Test Package", doc_list[0].name)

#     # 🔥 RATINGS (SAFE + OPTIONAL)
#     ratings = [
#         {
#             "min": d.min,
#             "max": d.max,
#             "label": getattr(d, "status", None) or getattr(d, "result", None) or ""
#         }
#         for d in doc.rating
#     ]

#     return {
#         "formula": doc.formula,

#         "variables": [
#             {
#                 "key": d.variable_key,
#                 "default": d.default_value,
#                 "label": f"{d.label} ({d.variable_key})",
#                 "unit": d.unit
#             }
#             for d in doc.variable_table
#         ],

#         "ratings": ratings
#     }