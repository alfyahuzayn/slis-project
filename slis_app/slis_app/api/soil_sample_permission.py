import frappe

def soil_sample_location_permission(user=None):
    user = user or frappe.session.user

    # Admin should see everything
    if user == "Administrator":
        return ""

    employee = frappe.db.get_value(
        "Employee",
        {"user_id": user},
        ["custom_lab_name"],
        as_dict=True
    )

    if not employee or not employee.custom_lab_name:
        return ""

    return f"`tabSoil Sample Collection`.district = '{employee.custom_lab_name}'"