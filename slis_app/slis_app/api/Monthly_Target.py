import frappe
from datetime import datetime
import calendar


@frappe.whitelist()
def calculate_target(docname):

    doc = frappe.get_doc("Monthly Target", docname)

    # ------------------------------------------
    # TEST PER RA
    # ------------------------------------------
    doc.test_per_ra = (doc.profile_sample_count or 0) + (doc.other_sample_count or 0)
    per_ra = doc.test_per_ra

    year = int(doc.financial_year.split("-")[1])

    # ------------------------------------------
    # SESSION LAB
    # ------------------------------------------
    employee = frappe.get_value(
        "Employee",
        {"user_id": frappe.session.user},
        ["custom_lab_name"],
        as_dict=True
    )

    lab = employee.custom_lab_name if employee else None

    # ------------------------------------------
    # AUTO CREATE CURRENT MONTH IF EMPTY
    # ------------------------------------------
    current_month = calendar.month_name[datetime.now().month]

    existing_months = [row.month for row in doc.lab_target if row.month]

    if not existing_months:
        doc.append("lab_target", {
            "month": current_month,
            "lab_name": lab
        })

    # ------------------------------------------
    # CALCULATION
    # ------------------------------------------
    for row in doc.lab_target:

        if not row.month:
            continue

        month = list(calendar.month_name).index(row.month)
        days_in_month = calendar.monthrange(year, month)[1]

        lab_name = row.lab_name or lab

        if not lab_name:
            continue

        employees = frappe.get_all(
            "Employee",
            filters={"custom_lab_name": lab_name},
            fields=[
                "name",
                "user_id",
                "date_of_joining",
                "custom_date_of_transfer",
                "custom_date_of_resign"
            ]
        )

        total_target = 0
        count = 0

        for emp in employees:

            # ✅ CHECK ROLE INSTEAD OF DESIGNATION
            if not emp.user_id:
                continue

            has_role = frappe.db.exists(
                "Has Role",
                {
                    "parent": emp.user_id,
                    "role": "Soil Tester L1"
                }
            )

            if not has_role:
                continue

            target = per_ra

            # JOIN
            if emp.date_of_joining and emp.date_of_joining.month == month:
                day = days_in_month - emp.date_of_joining.day + 1
                target = (per_ra / days_in_month) * day

            # RESIGN
            if emp.custom_date_of_resign and emp.custom_date_of_resign.month == month:
                day = emp.custom_date_of_resign.day
                target = (per_ra / days_in_month) * day

            # TRANSFER
            if emp.custom_date_of_transfer and emp.custom_date_of_transfer.month == month:
                day = emp.custom_date_of_transfer.day
                target = (per_ra / days_in_month) * day

            total_target += target
            count += 1

        row.ra_count = count
        row.monthly_target = round(total_target)

    doc.save()