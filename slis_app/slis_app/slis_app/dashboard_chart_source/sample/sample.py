import frappe
from frappe import _

@frappe.whitelist()
def get(chart_name=None, chart=None, no_cache=None, filters=None, **kwargs):
    # Fetch all unique lab names currently in your Soil Sample Collection
    # This ensures labs like Trivandrum and Kollam appear automatically
    labs = frappe.get_all("Soil Sample Collection", fields=["lab_name"], distinct=True)
    lab_list = [l.lab_name for l in labs if l.lab_name]

    pending_values = []
    completed_values = []

    for lab in lab_list:
        # Count Completed for this specific lab
        completed = frappe.db.count("Soil Sample Collection", filters={
            "status": "completed",
            "lab_name": lab
        })
        completed_values.append(completed)

        # Count Pending (not completed/draft/cancelled) for this specific lab
        pending = frappe.db.count("Soil Sample Collection", filters={
            "status": ["not in", ["completed", "Draft", "Cancelled"]],
            "lab_name": lab
        })
        pending_values.append(pending)

    return {
        "labels": lab_list, # Shows lab names on the X-axis
        "datasets": [
            {
                "name": _("Pending"),
                "values": pending_values
            },
            {
                "name": _("Completed"),
                "values": completed_values
            }
        ],
        "type": "bar",
        "colors": ["#3498db", "#e74c3c"] # Blue for Pending, Red/Pink for Completed
    }