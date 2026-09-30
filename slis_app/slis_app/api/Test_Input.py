# # import frappe
# # @frappe.whitelist()
# # def get_columns(test_list):

# #     columns = []
# #     seen = set()

# #     for test in test_list:

# #         doc_list = frappe.get_all(
# #             "Soil Test Package",
# #             filters={"test_name": test},
# #             fields=["name", "test_name"],
# #             limit_page_length=1
# #         )

# #         if not doc_list:
# #             val = str(test)
# #             if val not in seen:
# #                 columns.append(val)
# #                 seen.add(val)
# #             continue

# #         pkg = frappe.get_doc("Soil Test Package", doc_list[0].name)

# #         if pkg.included_tests:
# #             for row in pkg.included_tests:
# #                 val = str(row.linked_package)
# #                 if val and val not in seen:
# #                     columns.append(val)
# #                     seen.add(val)
# #         else:
# #             val = str(pkg.test_name)
# #             if val not in seen:
# #                 columns.append(val)
# #                 seen.add(val)

# #     return columns


# import frappe
# import json

# @frappe.whitelist()
# def get_columns(test_list):

#     # FIX: deserialize the JSON string into a proper Python list
#     if isinstance(test_list, str):
#         test_list = json.loads(test_list)

#     columns = []
#     seen = set()

#     for test in test_list:

#         doc_list = frappe.get_all(
#             "Soil Test Package",
#             filters={"test_name": test},
#             fields=["name", "test_name"],
#             limit_page_length=1
#         )

#         if not doc_list:
#             val = str(test)
#             if val not in seen:
#                 columns.append(val)
#                 seen.add(val)
#             continue

#         pkg = frappe.get_doc("Soil Test Package", doc_list[0].name)

#         if pkg.included_tests:
#             for row in pkg.included_tests:
#                 val = str(row.linked_package)
#                 if val and val not in seen:
#                     columns.append(val)
#                     seen.add(val)
#         else:
#             val = str(pkg.test_name)
#             if val not in seen:
#                 columns.append(val)
#                 seen.add(val)

#     return columns