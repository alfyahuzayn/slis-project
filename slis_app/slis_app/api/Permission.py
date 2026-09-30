import frappe

def sample_permission_query(user=None):
    user = user or frappe.session.user
    roles = frappe.get_roles(user)

    # ADMIN / MD - Full access
    if user == "Administrator" or "slis_admin" in roles:
        return ""

    # Employee details fetch cheyyunnu
    employee = frappe.db.get_value(
        "Employee",
        {"user_id": user},
        ["employment_type", "custom_lab_name", "custom_district_office_name"],
        as_dict=True
    )

    if not employee:
        return f"`tabSoil Sample Collection`.owner = '{user}'"

    conditions = []

    # =====================================================
    # COMMON FINAL STATUSES - ALL ROLES
    # =====================================================
    common_status_condition = (
        "status IN ("
        "'Test Completed', "
        "'Ready to Publish', "
        "'Result Published', "
        "'SC Verified Results'"
        ")"
    )

    # =====================================================
    # SOIL INTAKER L1 / SOIL TESTER L1
    # ONLY OWN CREATED + ASSIGNED SAMPLES, PLUS (for Soil
    # Intaker L1 only) Farmer/Consultancy samples that have
    # reached the final stages, lab-wise.
    # =====================================================
    if "Soil Intaker L1" in roles or "Soil Tester L1" in roles:

        base_condition = (
            f"`tabSoil Sample Collection`.owner = '{user}' "
            f"OR `tabSoil Sample Collection`.`_assign` LIKE '%%\"{user}\"%%'"
        )

        extra_condition = ""
        if "Soil Intaker L1" in roles and employee.custom_lab_name:
            extra_condition = (
                f" OR (client_type IN ('Farmer', 'Consultancy') "
                f"AND employee_type = 'Lab' "
                f"AND lab_name = '{employee.custom_lab_name}' "
                f"AND status IN ("
                f"'Test Completed', "
                f"'Ready to Publish', "
                f"'Result Published', "
                f"'SC Verified Results'"
                f"))"
            )

        return (
            f"({base_condition}"
            f"{extra_condition}"
            f" OR {common_status_condition})"
        )

    # =====================================================
    # SOIL INTAKER L3
    # ONLY ASSIGNED SAMPLES
    # =====================================================
    if "Soil Intaker L3" in roles:
        return (
            f"(`tabSoil Sample Collection`.`_assign` LIKE '%%\"{user}\"%%' "
            f"OR {common_status_condition})"
        )

    # DISTRICT OFFICE
    if employee.employment_type == "District Office":
        conditions.append("(client_type = 'Department')")

    # BASIC PERMISSIONS
    conditions.append(
        f"`tabSoil Sample Collection`.owner = '{user}'"
    )

    conditions.append(
        f"(`tabSoil Sample Collection`.`_assign` LIKE '%%\"{user}\"%%')"
    )

    # =====================================================
    # COMMON FINAL STATUSES - ALL OTHER ROLES
    # =====================================================
    conditions.append(
        f"({common_status_condition})"
    )

    # PSC OFFICER
    if "slis_admin" in roles or "PSC Officer" in roles:
        conditions.append(
            "("
            "employee_type = 'Lab' "
            "OR (client_type = 'Department' "
            "AND status IN ('With PSC Officer', 'Returned to PSC Officer (Overload)'))"
            ")"
        )

    # ASSISTANT DIRECTOR
    if "Soil Intaker L2" in roles and employee.custom_district_office_name:
        conditions.append(
            f"(employee_type = 'District Office' "
            f"AND district_office_name = '{employee.custom_district_office_name}')"
        )

    # SENIOR CHEMIST
    if "Soil Intaker L2" in roles and employee.custom_lab_name:
        conditions.append(
            f"(client_type = 'Department' "
            f"AND target_lab = '{employee.custom_lab_name}' "
            f"AND status IN ("
            f"'With Senior Chemist', "
            f"'With Research Assistant', "
            f"'Transferred', "
            f"'Returned', "
            f"'completed', "
            f"'SC Verifying Results', "
            f"'Test Completed', "
            f"'Under Lab Verification', "
            f"'cancelled',"
            f"'rejected',"
            f"'sc verified results', "
            f"'Ready to Publish', "
            f"'Result Published'"
            f"))"
        )
    
    # =====================================================
    # SOIL INTAKER L2 - AD VERIFICATION
    # All Soil Intaker L2 users can see Department samples
    # at AD verification stage
    # =====================================================
    if "Soil Intaker L2" in roles:
        conditions.append(
            "(client_type = 'Department' "
            "AND status IN ("
            "'AD Verifying Results', "
            "'AD Verified Results'"
            "))"
        )

    # =====================================================
    # NEW: SC VERIFICATION STAGE (Department) - EXPLICIT
    # Soil Intaker L2 whose own lab matches target_lab should
    # see samples currently at SC Verifying Results / Under
    # Lab Verification.
    # =====================================================
    if "Soil Intaker L2" in roles and employee.custom_lab_name:
        conditions.append(
            f"(client_type = 'Department' "
            f"AND target_lab = '{employee.custom_lab_name}' "
            f"AND status IN ('SC Verifying Results', 'Under Lab Verification', "
            f"'rejected', 'Test Completed', 'ready to publish', "
            f"'Result Published', 'SC Verified Results', "
            f"'AD Verified Results', 'AD Verifying Results'))"
        )

    # =====================================================
    # NEW: RESULT-VERIFICATION STAGE ROUTES BACK TO THE
    # ORIGINATING DISTRICT OFFICE (Department only).
    # Once status reaches one of these, the sample belongs
    # with the Assistant Director (Soil Intaker L2) of the
    # district office it originally came from.
    # =====================================================
    if "Soil Intaker L2" in roles and employee.custom_district_office_name:
        conditions.append(
            f"(client_type = 'Department' "
            f"AND employee_type = 'District Office' "
            f"AND district_office_name = '{employee.custom_district_office_name}' "
            f"AND status IN ("
            f"'SC Verified Results', "
            f"'AD Verified Results', "
            f"'AD Verifying Results'"
            f"))"
        )

    # =====================================================
    # NOTE: Farmer/Consultancy final stages
    # =====================================================

    # FARMER / CONSULTANCY
    if employee.custom_lab_name and employee.employment_type != "District Office":
        conditions.append(
            f"(client_type IN ('Farmer', 'Consultancy') "
            f"AND lab_name = '{employee.custom_lab_name}')"
        )

    if conditions:
        return f"({' OR '.join(set(conditions))})"

    return ""


def employee_permission_query(user=None):
    user = user or frappe.session.user
    roles = frappe.get_roles(user)

    # ADMIN / MD - Full access
    if user == "Administrator" or "slis_admin" in roles:
        return ""

    # Soil Intaker L2 - only employees from the same lab
    if "Soil Intaker L2" in roles:

        employee = frappe.db.get_value(
            "Employee",
            {"user_id": user},
            ["custom_lab_name"],
            as_dict=True
        )

        # If logged-in user has no Employee or Lab Name,
        # don't show any Employee records
        if not employee or not employee.custom_lab_name:
            return "1=0"

        lab_name = frappe.db.escape(employee.custom_lab_name)

        return f"`tabEmployee`.`custom_lab_name` = {lab_name}"

    # Other roles are not restricted by this query
    return ""