from frappe.utils import nowdate

def set_status_date(doc, method):

    if doc.status == "With Senior Chemist" and not doc.assigned_to_lab_date:
        doc.db_set("assigned_to_lab_date", nowdate())

    if doc.status == "With Research Assistant" and not doc.assigned_to_ra__date:
        doc.db_set("assigned_to_ra__date", nowdate())
    
    if doc.status == "With Assistant Director" and not doc.assistant_director_date:
        doc.db_set("assistant_director_date", nowdate())

    if doc.status == "completed" and not doc.completed_date:
        doc.db_set("completed_date", nowdate())

    if doc.status == "Returned to Senior Chemist(Overload)" and not doc.return_to_sc_date:
        doc.db_set("return_to_sc_date", nowdate())

    if doc.status == "Returned to PSC (Overload)" and not doc.return_to_psc_date:
        doc.db_set("return_to_psc_date", nowdate())