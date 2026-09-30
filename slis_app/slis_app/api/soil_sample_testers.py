import frappe

@frappe.whitelist()
def get_soil_sample_testers(txt=""):
    # Find the current user's own lab via their Employee record
    current_lab = frappe.db.get_value(
        "Employee",
        {"user_id": frappe.session.user},
        "custom_lab_name"
    )

    if not current_lab:
        return []

    testers = frappe.get_all(
        "Employee",
        filters={
            "custom_soil_sample_tester": 1,
            "status": "Active",
            "user_id": ["is", "set"],
            "custom_lab_name": current_lab,
        },
        fields=["user_id as value", "employee_name as description"],
    )

    if txt:
        txt = txt.lower()
        testers = [
            t for t in testers
            if txt in t.value.lower() or txt in (t.description or "").lower()
        ]
    return testers