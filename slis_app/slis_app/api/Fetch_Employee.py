import frappe

def before_insert(doc, method):
    if frappe.session.user == "Administrator":
        return

    user = frappe.session.user

    employee = frappe.db.get_value(
        "Employee",
        {"user_id": user},
        [
            "name",
            "employee_name",
            "employment_type",
            "custom_lab_name",
            "custom_district_office_name",
            "designation"
        ],
        as_dict=True
    )

    if not employee:
        frappe.throw("Employee not mapped to this user")

    employee_type = (employee.employment_type or "").strip()

    # Creator details
    doc.created_by = employee.employee_name   # Full Name
    doc.custom_designation = employee.designation  # Custom Designation
    doc.creator_user = user                   # Email/User ID

    doc.employee_type = employee_type

    # Reset
    doc.lab_name = None
    doc.district_office_name = None

    if employee_type == "Lab":
        doc.lab_name = employee.custom_lab_name

    elif employee_type == "District Office":
        doc.district_office_name = employee.custom_district_office_name