# Copyright (c) 2026, navaneeth and contributors
# For license information, please see license.txt

# import frappe
# from frappe.model.document import Document
# from frappe.model.naming import make_autoname

# class Register(Document):
#     def autoname(self):
#         # 1. Administrator Bypass
#         if frappe.session.user == "Administrator":
#             self.name = make_autoname("ADM-REG-.#####")
#             return

#         # 2. Fetch Lab Name from Employee record
#         user_full_lab_name = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "custom_lab_name")
        
#         if not user_full_lab_name:
#             frappe.throw(f"User {frappe.session.user} is not linked to an Employee record with a Lab assigned.")
        
#         # 3. Lab Abbreviation Mapping
#         lab_abbreviation_map = {
#             "Hi-Tech Soil Analytical Lab WYD": "WYD",
#             "Regional Soil Analytical Laboratory Alappuzha": "ALP",
#             "Regional Soil Analytical Laboratory Kozhikode": "KZK",
#             "Regional Soil Analytical Laboratory Thrissur": "TSR",
#             "Soil and Plant Health Clinic, Kasaragod": "KSD",
#             "Soil and Plant Health Clinic, Pathanamthitta": "PTA",
#             "Central Soil Analytical Lab, Parottukonam": "TVM"
#         }

#         lab_code = lab_abbreviation_map.get(user_full_lab_name)
#         if not lab_code:
#             frappe.throw(f"Naming prefix not found for lab: {user_full_lab_name}")

#         # 4. Write to Document field (ensure your field is named 'lab_name' in this DocType)
#         self.lab_name = user_full_lab_name

#         # 5. Generate Final Name
#         # Format: REG-ALP-00001
#         self.name = make_autoname(f"REG-{lab_code}-.#####")

#     def validate(self):
#         # Basic validation bypass for Admin
#         if frappe.session.user == "Administrator":
#             return
            
#         # Add any Register-specific validation logic here if needed
#         pass




import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname

class Register(Document):
    def autoname(self):
        # 1. Administrator Bypass
        if frappe.session.user == "Administrator":
            self.name = make_autoname("ADM-REG-.#####")
            return

        # 2. Define Mappings
        lab_map = {
            "Hi-Tech Soil Analytical Lab WYD": "WYD",
            "Regional Soil Analytical Laboratory Alappuzha": "ALP",
            "Regional Soil Analytical Laboratory Kozhikode": "KZK",
            "Regional Soil Analytical Laboratory Thrissur": "TSR",
            "Soil and Plant Health Clinic, Kasaragod": "KSD",
            "Soil and Plant Health Clinic, Pathanamthitta": "PTA",
            "Central Soil Analytical Lab, Parottukonam": "TVM"
        }

        # Mapping for District Offices - Thiruvananthapuram set to TVC
        district_map = {
            "Trivandrum": "TVC", 
            "Kollam": "QLN", 
            "Pathanamthitta": "PTA",
            "Alappuzha": "ALP", 
            "Kottayam": "KTM", 
            "Idukki": "IDU",
            "Ernakulam": "ERS", 
            "Thrissur": "TSR", 
            "Palakkad": "PGT", 
            "Malappuram": "MLP",
            "Kozhikode": "KZK",
            "Wayanad": "WAY",
            "Kannur": "CAN", 
            "Kasaragod": "KGQ"
        }

        # 3. Fetch Employee Data
        employee = frappe.db.get_value(
            "Employee", 
            {"user_id": frappe.session.user}, 
            ["custom_lab_name", "custom_district_office_name"], 
            as_dict=True
        )
        
        if not employee:
            frappe.throw(f"User {frappe.session.user} is not linked to an Employee record.")

        # 4. Determine Lab/District Code
        lab_code = None
        final_office_name = None

        # Check Lab Name first
        if employee.custom_lab_name:
            lab_code = lab_map.get(employee.custom_lab_name)
            final_office_name = employee.custom_lab_name
        
        # Fallback to District Office if Lab didn't match or was empty
        if not lab_code and employee.custom_district_office_name:
            lab_code = district_map.get(employee.custom_district_office_name)
            final_office_name = employee.custom_district_office_name

        # 5. Final Validation Check
        if not lab_code:
            frappe.throw("Neither a valid Lab nor a District Office was found for your Employee record to generate a Name.")

        # Write to Document field
        self.lab_name = final_office_name

        # 6. Generate Final Name
        # Format: REG-TVC-00001 or REG-ALP-00001
        self.name = make_autoname(f"REG-{lab_code}-.#####")

    def validate(self):
        # Basic validation bypass for Admin
        if frappe.session.user == "Administrator":
            return
            
        # Add any Register-specific validation logic here if needed
        pass