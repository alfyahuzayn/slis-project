import re
import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from .soil_utils import set_master_reference_sample_id


class SoilSampleCollection(Document):

    # =====================================================
    # AUTONAME
    # =====================================================

    def autoname(self):

        # 1. GENERATED SAMPLE VARIANT
        if getattr(self, "is_generated_sample", False):
            if hasattr(self, "custom_variant_name") and self.custom_variant_name:
                self.name = self.custom_variant_name
            else:
                self.name = f"{self.parent_sample}-{self.variant_number}"
            return

        # 2. ADMINISTRATOR
        if frappe.session.user == "Administrator":
            self.name = make_autoname("ADM-SSC-.#####")
            return

        # 3. BASIC VALIDATIONS
        if not self.client_type:
            frappe.throw("Client Type is required for naming.")

        if self.client_type in ["Farmer", "Consultancy"] and not getattr(self, "reference_name", None):
            frappe.throw("Reference Name is required for this Client Type.")

        prefix_map = {
            "Farmer": "FS",
            "Department": "DS",
            "Consultancy": "CS"
        }
        prefix = prefix_map.get(self.client_type, "SS")

        lab_map = {
            "Hi-Tech Soil Analytical Lab WYD": "WYD",
            "Regional Soil Analytical Laboratory Alappuzha": "ALP",
            "Regional Soil Analytical Laboratory Kozhikode": "KZK",
            "Regional Soil Analytical Laboratory Thrissur": "TSR",
            "Soil and Plant Health Clinic, Kasaragod": "KSD",
            "Soil and Plant Health Clinic, Pathanamthitta": "PTA",
            "Central Soil Analytical Lab, Parottukonam": "TVM",
            "Central Soil Analytical Laboratory, Parottukonam": "TVM",
        }

        district_map = {
            "Trivandrum": "TVM",
            "Kollam": "KLM",
            "Pathanamthitta": "PTA",
            "Alappuzha": "ALP",
            "Kottayam": "KTM",
            "Idukki": "IDK",
            "Ernakulam": "EKM",
            "Thrissur": "TSR",
            "Palakkad": "PKD",
            "Malappuram": "MLP",
            "Kozhikode": "KZK",
            "Wayanad": "WYD",
            "Kannur": "KAN",
            "Kasaragod": "KSD"
        }

        # 4. EMPLOYEE DATA
        employee_data = frappe.db.get_value(
            "Employee",
            {"user_id": frappe.session.user},
            ["custom_lab_name", "custom_district_office_name"],
            as_dict=True
        ) or {}

        # 5. LAB CODE LOGIC
        lab_code = None

        if getattr(self, "target_lab", None):
            lab_code = lab_map.get(self.target_lab)

        if not lab_code and employee_data.get("custom_lab_name"):
            lab_code = lab_map.get(employee_data.get("custom_lab_name"))

        if not lab_code and employee_data.get("custom_district_office_name"):
            lab_code = district_map.get(employee_data.get("custom_district_office_name"))

        if not lab_code:
            frappe.throw(
                "Neither a valid Lab nor a District Office was found "
                "for your selection or your Employee record."
            )

        self.lab_code_prefix = lab_code

        # 6. FINAL NAME GENERATION
        if getattr(self, "reference_name", None):
            ref = self.reference_name.strip().upper().replace(" ", "-")
            self.name = make_autoname(f"{prefix}-{lab_code}-{ref}-.#####")
        else:
            self.name = make_autoname(f"{prefix}-{lab_code}-.#####")

    # =====================================================
    # VALIDATE
    # =====================================================

    def validate(self):
        # SC VERIFIED FLAG
        if self.status == "SC Verified Results":
            self.sc_verified = 1

        num_samples = getattr(self, "number_of_samples", None) or (len(self.sample_data) if getattr(self, "sample_data", None) else 1)

        # SINGLE SAMPLE / GENERATED VARIANT GUARD
        if getattr(self, "is_generated_sample", False):
            self.is_master_sample = 0
            if self.name:
                self.reference_sample_id = self.name

        elif self.client_type in ["Farmer", "Consultancy"] and num_samples <= 1:
            if self.name and getattr(self, "reference_name", None):
                self.reference_sample_id = self.reference_name

        # POPULATE SAMPLE_DATA IDs
        if getattr(self, "sample_data", None) and self.name:
            if self.client_type == "Farmer" and num_samples <= 1:
                for row in self.sample_data:
                    if hasattr(row, "sample_id"):
                        row.sample_id = self.name
                    if hasattr(row, "lab_code") and not getattr(row, "lab_code", None):
                        row.lab_code = getattr(self, "lab_code_prefix", None) or "TVM"

            elif getattr(self, "is_master_sample", False):
                for idx, row in enumerate(self.sample_data, start=1):
                    row_default_id = f"{self.name}-{idx}"
                    if not getattr(row, "reference_name", None):
                        row.reference_name = f"{idx}"
                    
                    if hasattr(row, "sample_id") and not getattr(row, "sample_id", None):
                        row.sample_id = getattr(row, "reference_name", None) or row_default_id
                        
                    if hasattr(row, "lab_code") and not getattr(row, "lab_code", None):
                        row.lab_code = getattr(self, "lab_code_prefix", None) or "TVM"

        # 1. DYNAMICALLY SET MASTER REFERENCE SAMPLE ID
        set_master_reference_sample_id(self)

        # 2. MASTER PROFILE SAMPLE CHECKBOX LOGIC
        if getattr(self, "is_master_sample", False):
            self.master_profile_sample = 0

        elif getattr(self, "is_generated_sample", False):
            if self.client_type == "Department":
                is_profile_enabled = (
                    getattr(self, "enable_profile_sample", False) or 
                    getattr(self, "is_profile_sample", False) or 
                    getattr(self, "is_profile", False)
                )

                if not is_profile_enabled and getattr(self, "parent_sample", None):
                    is_profile_enabled = frappe.db.get_value(
                        self.doctype,
                        self.parent_sample,
                        "enable_profile_sample"
                    ) or 0

                ref_id = str(getattr(self, "reference_sample_id", "") or getattr(self, "name", "") or "")
                is_layer_sample = bool(re.search(r'\(\d+/\d+\)', ref_id))

                if is_profile_enabled and not is_layer_sample:
                    self.master_profile_sample = 1
                else:
                    self.master_profile_sample = 0
            else:
                self.master_profile_sample = 0
        else:
            self.master_profile_sample = 0

        # 3. TRANSFER & RETURN PERMISSIONS VALIDATION
        user = frappe.session.user

        if user != "Administrator":
            employee_lab = frappe.db.get_value(
                "Employee",
                {"user_id": user},
                "custom_lab_name"
            )

            old_doc = self.get_doc_before_save()
            old_status = old_doc.status if old_doc else ""

            if old_status == "With Senior Chemist" and self.status == "Transferred":
                if not getattr(self, "target_lab", None):
                    frappe.throw("Please select Target Lab")

                if employee_lab and self.target_lab == employee_lab:
                    frappe.throw(
                        "Target Lab cannot be the same as your Lab. Please change the Target Lab before Transfer."
                    )

                self.is_transferred = 1
                self.is_returned = 0
                self.transfer_status = f"Transferred to {self.target_lab}"

            elif old_status == "Transferred" and self.status == "Returned":
                if employee_lab and getattr(self, "target_lab", None) != employee_lab:
                    frappe.throw("Only the Target Lab can return this sample.")

                self.is_returned = 1
                self.transfer_status = f"Returned to {self.target_lab}"

    # =====================================================
    # ON UPDATE
    # =====================================================

    # 
    def on_update(self):
    # Only the master sample should create and synchronize variants.
    # Generated variants must never trigger synchronization back to themselves.
        if self.is_master_sample and not self.is_generated_sample:
            self.create_sample_variants()
            self.sync_variant_status()

    # =====================================================
    # SYNC VARIANT STATUS
    # =====================================================

    def sync_variant_status(self):
        """Directly updates child variants to prevent recursive loop saves."""
        update_data = {"status": self.status}
        if getattr(self, "workflow_state", None):
            update_data["workflow_state"] = self.workflow_state

        frappe.db.set_value(
            self.doctype,
            {"parent_sample": self.name},
            update_data,
            update_modified=False
        )

    # =====================================================
    # CREATE SAMPLE VARIANTS
    # =====================================================

    def create_sample_variants(self):
        sample_rows = getattr(self, "sample_data", []) or []
        if not sample_rows:
            return

        existing_variants = frappe.get_all(
            self.doctype,
            filters={"parent_sample": self.name},
            pluck="name"
        )

        if len(existing_variants) >= len(sample_rows):
            return

        prefix_map = {"Farmer": "FS", "Department": "DS", "Consultancy": "CS"}
        prefix = prefix_map.get(self.client_type, "SS")
        lab_code = getattr(self, "lab_code_prefix", None) or "TVM"

        parent_parts = self.name.split("-")
        parent_seq = parent_parts[-1] if parent_parts else "00001"

        is_profile_master = (
            getattr(self, "enable_profile_sample", False) or 
            getattr(self, "is_profile_sample", False) or 
            getattr(self, "is_profile", False)
        )

        master_workflow_state = getattr(self, "workflow_state", None) or self.status

        for idx, row in enumerate(sample_rows, start=1):
            row_ref_name = getattr(row, "reference_name", None) or f"{idx}"

            if self.client_type in ["Consultancy", "Farmer"]:
                parent_ref = getattr(self, "reference_name", "").strip().replace(" ", "-") if getattr(self, "reference_name", None) else ""
                if parent_ref:
                    variant_sample_id = f"{prefix}-{lab_code}-{parent_ref}-{parent_seq}-{idx}"
                else:
                    variant_sample_id = f"{prefix}-{lab_code}-{row_ref_name}-{parent_seq}-{idx}"
            else:
                row_custom_id = getattr(row, "sample_id", None) or getattr(row, "lab_code", None)
                variant_sample_id = row_custom_id if row_custom_id else f"{self.name}-{idx}"

            if frappe.db.exists(self.doctype, {"reference_sample_id": variant_sample_id, "parent_sample": self.name}):
                continue

            new_doc = frappe.new_doc(self.doctype)

            # Copy top-level fields
            for field in self.meta.fields:
                fieldname = field.fieldname
                if field.fieldtype in ["Table", "Section Break", "Column Break", "HTML"]:
                    continue
                if fieldname in ["name", "owner", "creation", "modified", "modified_by", "docstatus"]:
                    continue
                if fieldname in ["is_master_sample", "is_generated_sample", "parent_sample", "variant_number"]:
                    continue

                new_doc.set(fieldname, self.get(fieldname))

            # Helper function for copying child table rows cleanly
            def clean_child_rows(source_rows):
                cleaned = []
                for child in source_rows:
                    cdict = child.as_dict()
                    for key in ["name", "parent", "parentfield", "parenttype", "idx", "creation", "modified", "owner", "modified_by", "docstatus"]:
                        cdict.pop(key, None)
                    cleaned.append(cdict)
                return cleaned

            if hasattr(self, "tests") and self.tests:
                for tdata in clean_child_rows(self.tests):
                    new_doc.append("tests", tdata)

            if hasattr(self, "crops_list") and self.crops_list:
                for cdata in clean_child_rows(self.crops_list):
                    new_doc.append("crops_list", cdata)

            new_doc.docstatus = 0
            new_doc.is_master_sample = 0
            new_doc.is_generated_sample = 1
            new_doc.parent_sample = self.name
            new_doc.variant_number = idx
            new_doc.custom_variant_name = variant_sample_id
            new_doc.reference_sample_id = variant_sample_id

            new_doc.status = self.status
            if hasattr(new_doc, "workflow_state"):
                new_doc.workflow_state = master_workflow_state

            if hasattr(new_doc, "total_parameter_count"):
                new_doc.total_parameter_count = len(new_doc.tests) if getattr(new_doc, "tests", None) else 0

            is_layer_sample = bool(re.search(r'\(\d+/\d+\)', variant_sample_id))
            if self.client_type == "Department" and is_profile_master and not is_layer_sample:
                new_doc.master_profile_sample = 1
            else:
                new_doc.master_profile_sample = 0
            
            if hasattr(new_doc, "reference_name"):
                new_doc.reference_name = row_ref_name

            # Cleanly append single sample_data row
            child_dict = row.as_dict()
            for key in ["name", "parent", "parentfield", "parenttype", "idx", "creation", "modified", "owner", "modified_by", "docstatus"]:
                child_dict.pop(key, None)

            child_dict["sample_id"] = variant_sample_id
            child_dict["lab_code"] = getattr(row, "lab_code", None) or getattr(self, "lab_code_prefix", None)
            child_dict["variant_reference"] = variant_sample_id
            child_dict["reference_name"] = row_ref_name

            new_doc.sample_data = []
            new_doc.append("sample_data", child_dict)
            new_doc.number_of_samples = 1

            # Flags to ensure clean insertion
            new_doc.flags.ignore_permissions = True
            new_doc.flags.ignore_mandatory = True
            new_doc.flags.ignore_links = True
            new_doc.flags.ignore_validate = True

            new_doc.insert()

        frappe.db.commit()


@frappe.whitelist()
def get_last_sample_number(base_prefix):
    if not base_prefix:
        return 0

    rows = frappe.db.sql(
        """
        SELECT sample_id
        FROM `tabSample Data`
        WHERE sample_id LIKE %s
        """,
        (f"{base_prefix}/%",),
        as_dict=True
    )

    max_number = 0
    for row in rows:
        sample_id = row.sample_id or ""
        try:
            number = int(sample_id.rsplit("/", 1)[-1])
            if number > max_number:
                max_number = number
        except (ValueError, TypeError):
            continue

    return max_number


@frappe.whitelist()
def get_last_lab_number(lab_base):
    if not lab_base:
        return 0

    rows = frappe.db.sql(
        """
        SELECT lab_code
        FROM `tabSample Data`
        WHERE lab_code LIKE %s
        """,
        (f"{lab_base}/%",),
        as_dict=True
    )

    max_number = 0
    for row in rows:
        lab_code = row.lab_code or ""
        try:
            number = int(lab_code.rsplit("/", 1)[-1])
            if number > max_number:
                max_number = number
        except (ValueError, TypeError):
            continue

    return max_number