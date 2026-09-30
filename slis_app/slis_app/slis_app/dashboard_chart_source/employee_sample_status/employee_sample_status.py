import frappe
from frappe import _

@frappe.whitelist()
def get(chart_name=None, chart=None, no_cache=None, filters=None, **kwargs):
    # 1. Fetch all ToDo assignments for Soil Samples
    data = frappe.get_all("ToDo",
        filters={
            "reference_type": "Soil Sample Collection",
            "custom_ra_employee_name": ["!=", ""]
        },
        fields=["custom_ra_employee_name", "status"]
    )

    # 2. Identify unique employees (like 'vaiga')
    employees = sorted(list(set([d.custom_ra_employee_name for d in data])))
    
    completed_vals = []
    pending_vals = []
    cancelled_vals = []

    for emp in employees:
        # Filter records for this specific employee
        emp_tasks = [d for d in data if d.custom_ra_employee_name == emp]

        # Apply your logic:
        # Closed -> Completed
        # Cancelled -> Cancelled
        # Open (or anything else) -> Pending
        comp = len([t for t in emp_tasks if t.status == "Closed"])
        canc = len([t for t in emp_tasks if t.status == "Cancelled"])
        pend = len([t for t in emp_tasks if t.status not in ["Closed", "Cancelled"]])

        completed_vals.append(comp)
        pending_vals.append(pend)
        cancelled_vals.append(canc)

    return {
        "labels": employees,
        "datasets": [
            {"name": _("Completed"), "values": completed_vals},
            {"name": _("Pending"), "values": pending_vals},
            {"name": _("Cancelled"), "values": cancelled_vals}
        ],
        "type": "bar",
        "colors": ["#2ecc71", "#f1c40f", "#e74c3c"] # Green, Yellow, Red
    }