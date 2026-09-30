import frappe
from frappe.utils import nowdate

def update_sample_status(doc, method):

    if doc.reference_type == "Soil Sample Collection" and doc.reference_name:

        sample = frappe.get_doc("Soil Sample Collection", doc.reference_name)

        if doc.status == "Open":
            sample.db_set("status", "With Research Assistant")
            sample.db_set("assigned_to_ra__date", nowdate())

        elif doc.status == "Closed":
            sample.db_set("status", "completed")
            sample.db_set("completed_date", nowdate())

        elif doc.status == "Cancelled":
            sample.db_set("status", "Returned to Senior Chemist(Overload)")
            sample.db_set("return_to_sc_date", nowdate())