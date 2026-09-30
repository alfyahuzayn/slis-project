import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname

class Clients(Document):

    def autoname(self):
        # 1. Administrator Bypass
        if frappe.session.user == "Administrator":
            self.name = make_autoname("ADM-CLT-.#####")
            return

        # 2. Existing Validations
        if not self.client_type:
            frappe.throw("Client Type is required")

        # 3. Define Mappings
        lab_map = {
            "Hi-Tech Soil Analytical Lab WYD": "WYD",
            "Regional Soil Analytical Laboratory Alappuzha": "ALP",
            "Regional Soil Analytical Laboratory Kozhikode": "KZK",
            "Regional Soil Analytical Laboratory Thrissur": "TSR",
            "Soil and Plant Health Clinic, Kasaragod": "KSD",
            "Soil and Plant Health Clinic, Pathanamthitta": "PTA",
            "Central Soil Analytical Lab, Parottukonam": "TVM",
            "Central Soil Analytical Laboratory, Parottukonam":"TVM"        
            }

        district_map = {
            "Trivandrum": "TVC", "Kollam": "QLN", "Pathanamthitta": "PTA",
            "Alappuzha": "ALP", "Kottayam": "KTM", "Idukki": "IDU",
            "Ernakulam": "ERS", "Thrissur": "TSR", "Palakad": "PGT",
            "Malappuram": "MLP", "Kozhikode": "KZK", "Wayanad": "WAY",
            "Kannur": "CAN", "Kasaragod": "KGQ"
        }

        # 4. Fetch Employee Data
        employee = frappe.db.get_value(
            "Employee", 
            {"user_id": frappe.session.user}, 
            ["custom_lab_name", "custom_district_office_name"], 
            as_dict=True
        )
        
        if not employee:
            frappe.throw(f"User {frappe.session.user} is not linked to an Employee record.")

        # 5. Determine Lab/District Code
        lab_code = None
        final_office_name = None

        # Try Lab first
        if employee.custom_lab_name:
            lab_code = lab_map.get(employee.custom_lab_name)
            final_office_name = employee.custom_lab_name
        
        # Fallback to District Office
        if not lab_code and employee.custom_district_office_name:
            lab_code = district_map.get(employee.custom_district_office_name)
            final_office_name = employee.custom_district_office_name

        if not lab_code:
            frappe.throw("Neither a valid Lab nor a District Office was found for your Employee record.")

        # Store the office name in the document field
        self.lab_name = final_office_name

        # 6. Client Type Prefix Mapping
        prefix_map = {
            "Farmer": "CL-FS",
            "Department": "CL-DS",
            "Consultancy": "CL-CS"
        }

        prefix = prefix_map.get(self.client_type)
        if not prefix:
            frappe.throw("Invalid Client Type")

        # 7. Generate Final Name
        # Format: CL-FS-ALP-.#####
        self.name = make_autoname(f"{prefix}-{lab_code}-.#####")




# #user permision to only see the clients created by their lab or district office

# import frappe

# def get_permission_query_conditions(user):
#     if not user:
#         user = frappe.session.user

#     # Full access for Administrator
#     if user == "Administrator":
#         return ""

#     employee = frappe.db.get_value(
#         "Employee",
#         {"user_id": user},
#         ["employment_type", "custom_lab_name", "custom_district_office_name"],
#         as_dict=True
#     )

#     if not employee:
#         return "1=0"

#     # District Office user
#     if employee.employment_type == "District Office" and employee.custom_district_office_name:
#         dept = frappe.db.escape(employee.custom_district_office_name)
#         return f"`tabClients`.`custom_collection_department` = {dept}"

#     # Lab user
#     if employee.employment_type == "Lab" and employee.custom_lab_name:
#         lab = frappe.db.escape(employee.custom_lab_name)
#         return f"`tabClients`.`login_lab_name` = {lab}"

#     return "1=0"


# def has_permission(doc, user=None):
#     if not user:
#         user = frappe.session.user

#     # Admin full access
#     if user == "Administrator":
#         return True

#     # ✅ Allow creation safely
#     if doc.is_new():
#         return True

#     employee = frappe.db.get_value(
#         "Employee",
#         {"user_id": user},
#         ["employment_type", "custom_lab_name", "custom_district_office_name"],
#         as_dict=True
#     )

#     if not employee:
#         return False

#     # District Office user
#     if employee.employment_type == "District Office":
#         if not employee.custom_district_office_name:
#             return False
#         return doc.custom_collection_department == employee.custom_district_office_name

#     # Lab user
#     if employee.employment_type == "Lab":
#         if not employee.custom_lab_name:
#             return False
#         return doc.login_lab_name == employee.custom_lab_name

#     return False


#other code 
import frappe


# =====================================================
# LIST VIEW PERMISSION FILTER
# =====================================================

def get_permission_query_conditions(user):

    if not user:
        user = frappe.session.user

    # Administrator full access
    if user in [
    "Administrator",
    "slisadmin@gmail.com"]:
        return ""

    employee = frappe.get_all(
        "Employee",
        filters={
            "user_id": user
        },
        fields=[
            "employment_type",
            "custom_lab_name",
            "custom_district_office_name"
        ],
        limit=1
    )

    if not employee:
        return "1=0"

    employee = employee[0]

    # =========================
    # DISTRICT OFFICE USER
    # =========================

    if (
        employee.get("employment_type") == "District Office"
        and employee.get("custom_district_office_name")
    ):

        dept = frappe.db.escape(
            employee.get("custom_district_office_name")
        )

        return (
            f"`tabClients`.`custom_collection_department` = {dept}"
        )

    # =========================
    # LAB USER
    # =========================

    if (
        employee.get("employment_type") == "Lab"
        and employee.get("custom_lab_name")
    ):

        lab = frappe.db.escape(
            employee.get("custom_lab_name")
        )

        return (
            f"`tabClients`.`login_lab_name` = {lab}"
        )

    return "1=0"


# =====================================================
# DOCUMENT LEVEL PERMISSION
# =====================================================

def has_permission(doc, user=None):

    if not user:
        user = frappe.session.user

    # Administrator full access
    if user in [
    "Administrator",
    "slisadmin@gmail.com"]:
        return True

    # Allow new document creation
    if doc.is_new():
        return True

    employee = frappe.get_all(
        "Employee",
        filters={
            "user_id": user
        },
        fields=[
            "employment_type",
            "custom_lab_name",
            "custom_district_office_name"
        ],
        limit=1
    )

    if not employee:
        return False

    employee = employee[0]

    # =========================
    # DISTRICT OFFICE USER
    # =========================

    if employee.get("employment_type") == "District Office":

        if not employee.get(
            "custom_district_office_name"
        ):
            return False

        return (
            (doc.custom_collection_department or "")
            ==
            employee.get(
                "custom_district_office_name"
            )
        )

    # =========================
    # LAB USER
    # =========================

    if employee.get("employment_type") == "Lab":

        if not employee.get("custom_lab_name"):
            return False

        return (
            (doc.login_lab_name or "")
            ==
            employee.get("custom_lab_name")
        )

    return False


# =====================================================
# BEFORE INSERT
# =====================================================

def before_insert(doc, method=None):

    employee = frappe.get_all(
        "Employee",
        filters={
            "user_id": frappe.session.user
        },
        fields=[
            "employment_type",
            "custom_lab_name",
            "custom_district_office_name"
        ],
        limit=1
    )

    if not employee:
        return

    employee = employee[0]

    # =========================
    # LAB USER
    # =========================

    if employee.get("employment_type") == "Lab":

        doc.login_lab_name = (
            employee.get("custom_lab_name") or ""
        )

        doc.custom_collection_department = ""

    # =========================
    # DISTRICT OFFICE USER
    # =========================

    elif employee.get("employment_type") == "District Office":

        doc.custom_collection_department = (
            employee.get(
                "custom_district_office_name"
            ) or ""
        )

        doc.login_lab_name = ""