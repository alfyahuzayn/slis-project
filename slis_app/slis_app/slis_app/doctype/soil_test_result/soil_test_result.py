import frappe
import json
from frappe.model.document import Document
from frappe.model.naming import make_autoname


class SoilTestResult(Document):
    def autoname(self):
        if frappe.session.user == "Administrator":
            self.name = make_autoname("ADM-STR-.#####")
            return

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
            "Thrissur": "TCR",
            "Palakkad": "PKD",
            "Malappuram": "MLP",
            "Kozhikode": "KKD",
            "Wayanad": "WYD",
            "Kannur": "KNR",
            "Kasaragod": "KAS"
        }

        employee = frappe.db.get_value(
            "Employee",
            {"user_id": frappe.session.user},
            ["custom_lab_name", "custom_district_office_name"],
            as_dict=True
        )

        if not employee:
            frappe.throw(f"User {frappe.session.user} is not linked to an Employee record.")

        lab_code = None
        if employee.custom_lab_name:
            lab_code = lab_map.get(employee.custom_lab_name)
        if not lab_code and employee.custom_district_office_name:
            lab_code = district_map.get(employee.custom_district_office_name)

        if not lab_code:
            frappe.throw("No valid Lab or District Office found for your Employee record.")

        self.name = make_autoname(f"STR-{lab_code}-.#####")


    # def before_print(self, settings=None):
    #     client_type = self.client_type or ""
    #     format_map = {
    #         "Farmer": "PoP Recommendation",
    #         "Consultancy": "Soil Test Report - Consultancy",
    #         "Department": "Soil Test Report - Department",
    #     }
    #     self.print_format = format_map.get(client_type, "PoP Recommendation")

    def get_parsed_samples(self):
        result = []
        for sample in self.test_sample_data or []:
            if sample.values_json:
                try:
                    values = json.loads(sample.values_json)
                    result.append(values)
                except Exception:
                    pass
        return result
 


    # def get_consultancy_table(self):
    #     headers = []
    #     rows = []

    #     for sample in self.test_sample_data or []:
    #         if not sample.values_json:
    #             continue

    #         try:
    #             results = json.loads(sample.values_json)
    #         except Exception:
    #             continue

    #         if not headers:
    #             headers = list(results.keys())

    #         rows.append({
    #             "lab_code": sample.lab_code or "",
    #             "sample_code": sample.sample_id or "",
    #             "results": results
    #         })

    #     return {
    #         "headers": headers,
    #         "rows": rows
    #     }


    def get_department_table(self, chunk_size=6):
        headers = []
        rows = []

        for sample in self.test_sample_data or []:
            if not sample.values_json:
                continue

            try:
                results = json.loads(sample.values_json)
            except Exception:
                continue

            if not headers:
                headers = list(results.keys())

            rows.append({
                "lab_code": sample.lab_code or "",
                "sample_code": sample.sample_id or "",
                "depth": sample.depth or "",
                "results": results
            })

        # Split the full header list into fixed-size groups.
        # Each group becomes its own table block in the print format,
        # so wide result sets wrap onto new blocks instead of overflowing
        # the page width. Blocks flow naturally in document order and can
        # land on whichever page they fall on.
        header_chunks = [
            headers[i:i + chunk_size]
            for i in range(0, len(headers), chunk_size)
        ]

        chunks = [
            {"headers": chunk_headers, "rows": rows}
            for chunk_headers in header_chunks
        ]

        return {
            "headers": headers,
            "rows": rows,
            "chunks": chunks
        }    


    def get_consultancy_table(self, chunk_size=6):
        headers = []
        rows = []

        for sample in self.test_sample_data or []:
            if not sample.values_json:
                continue

            try:
                results = json.loads(sample.values_json)
            except Exception:
                continue

            if not headers:
                headers = list(results.keys())

            rows.append({
                "lab_code": sample.lab_code or "",
                "sample_code": sample.reference_name or "",
                "results": results
            })

        # Split the full header list into fixed-size groups.
        # Each group becomes its own table block in the print format,
        # so wide result sets wrap onto new blocks instead of overflowing
        # the page width. Blocks flow naturally in document order and can
        # land on whichever page they fall on.
        header_chunks = [
            headers[i:i + chunk_size]
            for i in range(0, len(headers), chunk_size)
        ]

        chunks = [
            {"headers": chunk_headers, "rows": rows}
            for chunk_headers in header_chunks
        ]

        return {
            "headers": headers,
            "rows": rows,
            "chunks": chunks
        }    
