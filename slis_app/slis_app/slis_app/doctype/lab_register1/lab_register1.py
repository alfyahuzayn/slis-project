# Copyright (c) 2026, navaneeth and contributors
# For license information, please see license.txt

# lab_register1.py
import frappe
from frappe.model.document import Document

class LabRegister1(Document):

    def on_trash(self):
        if self.soil_sample_collection:
            parent = frappe.get_doc(
                "Soil Sample Collection",
                self.soil_sample_collection
            )

            # Check if any other lab records exist
            remaining = frappe.db.exists(
                "Lab Register",
                {
                    "soil_sample_collection": parent.name,
                    "name": ["!=", self.name]
                }
            )

            if not remaining:
                parent.lab_register1_created = 0
                parent.lab_register1_ref = None
                parent.save(ignore_permissions=True)
