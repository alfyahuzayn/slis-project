# Copyright (c) 2026, navaneeth and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today


class DepartmentSampleCoverLetter(Document):
    pass


@frappe.whitelist()
def generate_cover_letter(collection_name):

    # Prevent duplicate cover letters
    existing = frappe.db.exists(
        "Department Sample Cover Letter",
        {
            "department_sample_collection": collection_name
        }
    )

    if existing:
        return existing

    # Get Soil Sample Collection
    collection = frappe.get_doc(
        "Soil Sample Collection",
        collection_name
    )

    # Create Cover Letter
    cover = frappe.new_doc(
        "Department Sample Cover Letter"
    )

    cover.cover_letter_date = today()
    cover.department_sample_collection = collection.name
    cover.district_office = collection.district_office_name

    # Copy Sample IDs
    for row in collection.sample_data:

        # For profile samples, include only child samples (those with brackets)
        if collection.enable_profile_sample:
            if "(" not in (row.sample_id or ""):
                continue

        cover.append(
            "samples",
            {
                "sample_id": row.sample_id,
                "lab_code": row.lab_code,
            },
        )

    cover.insert(ignore_permissions=True)
    frappe.db.commit()

    return cover.name