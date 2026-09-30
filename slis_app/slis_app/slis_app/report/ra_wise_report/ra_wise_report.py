# import frappe
# import calendar
# from datetime import date
# from frappe.utils import cint

# def execute(filters=None):
#     filters = filters or {}
#     html = build_report(filters)
#     return [], [], html


# def get_ra_list():

#     user = frappe.session.user
#     roles = frappe.get_roles(user)

#     # Get logged-in employee
#     employee = frappe.db.get_value(
#         "Employee",
#         {"user_id": user},
#         ["name", "custom_lab_name"],
#         as_dict=True
#     )

#     if not employee:
#         return []

#     # =========================================
#     # 1. SLIS Admin + Soil Intaker L2
#     #    → Show ALL Soil Sample Testers
#     # =========================================
#     if "SLIS Admin" in roles and "Soil Intaker L2" in roles:

#         return frappe.get_list(
#             "Employee",
#             filters={
#                 "custom_soil_sample_tester": 1,
#                 "status": "Active"
#             },
#             fields=[
#                 "name",
#                 "employee_name",
#                 "custom_lab_name"
#             ]
#         )

#     # =========================================
#     # 2. Soil Intaker L2
#     #    → Same Lab + Soil Sample Tester
#     # =========================================
#     if "Soil Intaker L2" in roles:

#         return frappe.get_list(
#             "Employee",
#             filters={
#                 "custom_soil_sample_tester": 1,
#                 "status": "Active",
#                 "custom_lab_name": employee.custom_lab_name
#             },
#             fields=[
#                 "name",
#                 "employee_name",
#                 "custom_lab_name"
#             ]
#         )

#     # =========================================
#     # 3. Soil Intaker L1
#     #    → Only logged-in employee
#     # =========================================
#     if "Soil Intaker L1" in roles:

#         return frappe.get_list(
#             "Employee",
#             filters={
#                 "name": employee.name
#             },
#             fields=[
#                 "name",
#                 "employee_name",
#                 "custom_lab_name"
#             ]
#         )

#     # =========================================
#     # Other roles → Nothing
#     # =========================================
#     return []
    


# def get_client_name(r):

#     if r.client_type != "Department":
#         return r.client_type

#     return f"{r.type_of_collection} - {r.name_of_type}"


# def build_report(filters):

#     month = int(filters.get("month"))
#     year = int(filters.get("year"))

#     month_start = date(year, month, 1)

#     month_end = date(
#         year,
#         month,
#         calendar.monthrange(year, month)[1]
#     )

#     fy_start = (
#         date(year, 4, 1)
#         if month >= 4
#         else date(year - 1, 4, 1)
#     )

#     fy_end = date(
#         fy_start.year + 1,
#         3,
#         31
#     )

#     ra_list = get_ra_list()

#     records = frappe.get_all(

#         "Soil Sample Collection",

#         filters={

#             "status": "completed",

#             "completed_date": [
#                 "between",
#                 [fy_start, fy_end]
#             ]
#         },

#         fields=[

#             "name",
#             "client_type",
#             "type_of_collection",
#             "name_of_type",
#             "completed_date",
#             "total_parameter_count",
#             "number_of_samples"
#         ]
#     )

#     client_map = {}
#     all_tests = set()

#     # =========================================
#     # BUILD STRUCTURE
#     # =========================================
#     for r in records:

#         if not r.completed_date:
#             continue

#         cname = get_client_name(r)

#         use_total = 1

#         # =========================================
#         # DEPARTMENT SETTINGS
#         # =========================================
#         if (
#             r.client_type == "Department"
#             and r.type_of_collection == "Scheme"
#             and r.name_of_type
#         ):

#             use_total = frappe.db.get_value(
#                 "Scheme or Programs",
#                 r.name_of_type,
#                 "count_the_total_parameter"
#             ) or 0

#         client_map[cname] = use_total

#         # =========================================
#         # TEST WISE MODE
#         # =========================================
#         if use_total == 0:

#             tests = frappe.get_all(

#                 "Test Details",

#                 filters={
#                     "parent": r.name
#                 },

#                 fields=["test_name"]
#             )

#             for t in tests:

#                 if t.test_name:
#                     all_tests.add(t.test_name)

#     all_tests = list(all_tests)

#     # =========================================
#     # INIT DATA
#     # =========================================
#     data = {}

#     for ra in ra_list:

#         data[ra.name] = {}

#         for c in client_map:

#             data[ra.name][c] = {

#                 "ss_dm": 0,
#                 "ss_pt": 0,

#                 "est_dm": 0,
#                 "est_pt": 0,

#                 "tests": {

#                     t: {
#                         "dm": 0,
#                         "pt": 0
#                     }

#                     for t in all_tests
#                 }
#             }

#     # =========================================
#     # MAIN CALCULATION
#     # =========================================
#     for r in records:

#         cname = get_client_name(r)

#         # =========================================
#         # GET TODO USER
#         # =========================================
#         todo_user = frappe.db.get_value(

#             "ToDo",

#             {
#                 "reference_type":
#                     "Soil Sample Collection",

#                 "reference_name":
#                     r.name
#             },

#             "allocated_to"
#         )

#         if not todo_user:
#             continue

#         # =========================================
#         # MAP EMPLOYEE
#         # =========================================
#         ra_name = frappe.db.get_value(

#             "Employee",

#             {
#                 "user_id": todo_user
#             },

#             "name"
#         )

#         if (
#             not ra_name
#             or cname not in data.get(ra_name, {})
#         ):
#             continue

#         # =========================================
#         # 🔥 SS COUNT USING number_of_samples
#         # =========================================
#         samples = cint(
#             r.number_of_samples or 1
#         )

#         prev = 0
#         curr = 0

#         if fy_start <= r.completed_date < month_start:
#             prev = samples

#         if month_start <= r.completed_date <= month_end:
#             curr = samples

#         data[ra_name][cname]["ss_dm"] += curr

#         data[ra_name][cname]["ss_pt"] += (
#             prev + curr
#         )

#         # =========================================
#         # ESTIMATE
#         # =========================================
#         total = (
#             r.total_parameter_count or 0
#         )

#         use_total = client_map[cname]

#         # =========================================
#         # TOTAL MODE
#         # =========================================
#         if use_total == 1:

#             if fy_start <= r.completed_date < month_start:

#                 prev = total
#                 curr = 0

#             elif month_start <= r.completed_date <= month_end:

#                 prev = 0
#                 curr = total

#             else:

#                 prev = 0
#                 curr = 0

#             data[ra_name][cname]["est_dm"] += curr

#             data[ra_name][cname]["est_pt"] += (
#                 prev + curr
#             )

#         # =========================================
#         # TEST WISE MODE
#         # =========================================
#         else:

#             tests = frappe.get_all(

#                 "Test Details",

#                 filters={
#                     "parent": r.name
#                 },

#                 fields=[
#                     "test_name",
#                     "parameter_count"
#                 ]
#             )

#             for t in tests:

#                 if fy_start <= r.completed_date < month_start:

#                     prev = (
#                         t.parameter_count or 0
#                     )

#                     curr = 0

#                 elif month_start <= r.completed_date <= month_end:

#                     prev = 0

#                     curr = (
#                         t.parameter_count or 0
#                     )

#                 else:

#                     prev = 0
#                     curr = 0

#                 if (
#                     t.test_name
#                     in data[ra_name][cname]["tests"]
#                 ):

#                     data[ra_name][cname]["tests"][t.test_name]["dm"] += curr

#                     data[ra_name][cname]["tests"][t.test_name]["pt"] += (
#                         prev + curr
#                     )

#     return generate_html(
#         ra_list,
#         client_map,
#         all_tests,
#         data
#     )


# # =========================================
# # UI PART
# # =========================================
# def generate_html(
#     ra_list,
#     client_map,
#     all_tests,
#     data
# ):

#     html = """

#     <style>

#     .report-container{
#         width:100%;
#         overflow:auto;
#         max-height:600px;
#         border:1px solid #ccc;
#         cursor:grab;
#         user-select:none;
#         position:relative;
#     }

#     .report-container:active{
#         cursor:grabbing;
#     }

#     .report-table{
#         border-collapse:collapse;
#         width:max-content;
#         min-width:1400px;
#         font-size:13px;
#     }

#     .report-table th{
#         background:#f5f5f5;
#         font-weight:600;
#         position:sticky;
#         top:0;
#         z-index:2;
#     }

#     .report-table th,
#     .report-table td{
#         border:1px solid #ccc;
#         padding:8px 14px;
#         text-align:center;
#         white-space:nowrap;
#     }

#     .ra-cell{
#         background:transparent;
#         font-weight:bold;
#     }

#     .total-cell{
#         background:transparent;
#         font-weight:bold;
#     }

#     </style>

#     <div
#         class="report-container"
#         id="report-container"
#     >

#     <table class="report-table">
#     """

#     # =========================================
#     # HEADER 1
#     # =========================================
#     html += """
#     <tr>

#     <th rowspan='3'>
#     Research Assistant
#     </th>

#     <th rowspan='3'>
#     Lab
#     </th>
#     """

#     for c in client_map:

#         if client_map[c] == 1:

#             html += f"""
#             <th colspan='4'>
#             {c}
#             </th>
#             """

#         else:

#             html += f"""
#             <th colspan='{
#                 2 + len(all_tests) * 2
#             }'>
#             {c}
#             </th>
#             """

#     html += """
#     <th colspan='2'>
#     SS TOTAL
#     </th>

#     <th colspan='2'>
#     EST TOTAL
#     </th>

#     </tr>
#     """

#     # =========================================
#     # HEADER 2
#     # =========================================
#     html += "<tr>"

#     for c in client_map:

#         html += """
#         <th colspan='2'>
#         SS
#         </th>
#         """

#         if client_map[c] == 1:

#             html += """
#             <th colspan='2'>
#             Estimate
#             </th>
#             """

#         else:

#             for t in all_tests:

#                 html += f"""
#                 <th colspan='2'>
#                 {t} Estimate
#                 </th>
#                 """

#     html += "<th colspan='4'></th>"
#     html += "</tr>"

#     # =========================================
#     # HEADER 3
#     # =========================================
#     html += "<tr>"

#     for c in client_map:

#         html += """
#         <th>DM</th>
#         <th>PT</th>
#         """

#         if client_map[c] == 1:

#             html += """
#             <th>DM</th>
#             <th>PT</th>
#             """

#         else:

#             for t in all_tests:

#                 html += """
#                 <th>DM</th>
#                 <th>PT</th>
#                 """

#     html += """
#     <th>DM</th>
#     <th>PT</th>

#     <th>DM</th>
#     <th>PT</th>
#     """

#     html += "</tr>"

#     # =========================================
#     # BODY
#     # =========================================
#     for ra in ra_list:

#         total_ss_dm = 0
#         total_ss_pt = 0

#         total_est_dm = 0
#         total_est_pt = 0

#         html += f"""

#         <tr>

#         <td class='ra-cell'>
#         {ra.employee_name}
#         </td>

#         <td>
#         {ra.custom_lab_name or '-'}
#         </td>
#         """

#         for c in client_map:

#             row = data[ra.name][c]

#             html += f"""
#             <td>{row['ss_dm']}</td>
#             <td>{row['ss_pt']}</td>
#             """

#             total_ss_dm += row['ss_dm']
#             total_ss_pt += row['ss_pt']

#             if client_map[c] == 1:

#                 html += f"""
#                 <td>{row['est_dm']}</td>
#                 <td>{row['est_pt']}</td>
#                 """

#                 total_est_dm += row['est_dm']
#                 total_est_pt += row['est_pt']

#             else:

#                 for t in all_tests:

#                     dm = row["tests"][t]["dm"]
#                     pt = row["tests"][t]["pt"]

#                     total_est_dm += dm
#                     total_est_pt += pt

#                     html += f"""
#                     <td>{dm}</td>
#                     <td>{pt}</td>
#                     """

#         html += f"""

#         <td class='total-cell'>
#         {total_ss_dm}
#         </td>

#         <td class='total-cell'>
#         {total_ss_pt}
#         </td>

#         <td class='total-cell'>
#         {total_est_dm}
#         </td>

#         <td class='total-cell'>
#         {total_est_pt}
#         </td>

#         </tr>
#         """

#     html += """
#     </table>
#     </div>

#     <script>

#     const slider = document.getElementById(
#         "report-container"
#     );

#     let isDown = false;

#     let startX;
#     let startY;

#     let scrollLeft;
#     let scrollTop;

#     slider.addEventListener(
#         "mousedown",
#         (e) => {

#             isDown = true;

#             startX =
#                 e.pageX - slider.offsetLeft;

#             startY =
#                 e.pageY - slider.offsetTop;

#             scrollLeft =
#                 slider.scrollLeft;

#             scrollTop =
#                 slider.scrollTop;
#         }
#     );

#     slider.addEventListener(
#         "mouseleave",
#         () => {

#             isDown = false;
#         }
#     );

#     slider.addEventListener(
#         "mouseup",
#         () => {

#             isDown = false;
#         }
#     );

#     slider.addEventListener(
#         "mousemove",
#         (e) => {

#             if (!isDown)
#                 return;

#             e.preventDefault();

#             const x =
#                 e.pageX - slider.offsetLeft;

#             const y =
#                 e.pageY - slider.offsetTop;

#             const walkX =
#                 (x - startX) * 1.5;

#             const walkY =
#                 (y - startY) * 1.5;

#             slider.scrollLeft =
#                 scrollLeft - walkX;

#             slider.scrollTop =
#                 scrollTop - walkY;
#         }
#     );

#     </script>
#     """

#     return html

















import frappe
import calendar
from datetime import date
from frappe.utils import cint

def execute(filters=None):
    filters = filters or {}
    html = build_report(filters)
    return [], [], html


def get_ra_list():

    user = frappe.session.user
    roles = frappe.get_roles(user)

    # Get logged-in employee
    employee = frappe.db.get_value(
        "Employee",
        {"user_id": user},
        ["name", "custom_lab_name"],
        as_dict=True
    )

    if not employee:
        return []

    # =========================================
    # 1. SLIS Admin + Soil Intaker L2
    #    → Show ALL Soil Sample Testers
    # =========================================
    if "SLIS Admin" in roles and "Soil Intaker L2" in roles:

        return frappe.get_list(
            "Employee",
            filters={
                "custom_soil_sample_tester": 1,
                "status": "Active"
            },
            fields=[
                "name",
                "employee_name",
                "custom_lab_name"
            ]
        )

    # =========================================
    # 2. Soil Intaker L2
    #    → Same Lab + Soil Sample Tester
    # =========================================
    if "Soil Intaker L2" in roles:

        return frappe.get_list(
            "Employee",
            filters={
                "custom_soil_sample_tester": 1,
                "status": "Active",
                "custom_lab_name": employee.custom_lab_name
            },
            fields=[
                "name",
                "employee_name",
                "custom_lab_name"
            ]
        )

    # =========================================
    # 3. Soil Intaker L1
    #    → Only logged-in employee
    # =========================================
    if "Soil Intaker L1" in roles:

        return frappe.get_list(
            "Employee",
            filters={
                "name": employee.name
            },
            fields=[
                "name",
                "employee_name",
                "custom_lab_name"
            ]
        )

    # =========================================
    # Other roles → Nothing
    # =========================================
    return []
    


def get_client_name(r):

    if r.client_type != "Department":
        return r.client_type

    return f"{r.type_of_collection} - {r.name_of_type}"


def build_report(filters):

    month = int(filters.get("month"))
    year = int(filters.get("year"))

    month_start = date(year, month, 1)

    month_end = date(
        year,
        month,
        calendar.monthrange(year, month)[1]
    )

    fy_start = (
        date(year, 4, 1)
        if month >= 4
        else date(year - 1, 4, 1)
    )

    fy_end = date(
        fy_start.year + 1,
        3,
        31
    )

    ra_list = get_ra_list()

    records = frappe.get_all(

        "Soil Sample Collection",

        filters={

            "status": "completed",

            "completed_date": [
                "between",
                [fy_start, fy_end]
            ]
        },

        fields=[

            "name",
            "client_type",
            "type_of_collection",
            "name_of_type",
            "completed_date",
            "total_parameter_count",
            "number_of_samples"
        ]
    )

    client_map = {}
    all_tests = set()

    # =========================================
    # BUILD STRUCTURE
    # =========================================
    for r in records:

        if not r.completed_date:
            continue

        cname = get_client_name(r)

        use_total = 1

        # =========================================
        # DEPARTMENT SETTINGS
        # =========================================
        if (
            r.client_type == "Department"
            and r.type_of_collection == "Scheme"
            and r.name_of_type
        ):

            use_total = frappe.db.get_value(
                "Scheme or Programs",
                r.name_of_type,
                "count_the_total_parameter"
            ) or 0

        client_map[cname] = use_total

        # =========================================
        # TEST WISE MODE
        # =========================================
        if use_total == 0:

            tests = frappe.get_all(

                "Test Details",

                filters={
                    "parent": r.name
                },

                fields=["test_name"]
            )

            for t in tests:

                if t.test_name:
                    all_tests.add(t.test_name)

    all_tests = list(all_tests)

    # =========================================
    # INIT DATA
    # =========================================
    data = {}

    for ra in ra_list:

        data[ra.name] = {}

        for c in client_map:

            data[ra.name][c] = {

                "ss_dm": 0,
                "ss_pt": 0,

                "est_dm": 0,
                "est_pt": 0,

                "tests": {

                    t: {
                        "dm": 0,
                        "pt": 0
                    }

                    for t in all_tests
                }
            }

    # =========================================
    # MAIN CALCULATION
    # =========================================
    for r in records:

        cname = get_client_name(r)

        # =========================================
        # GET TODO USER
        # =========================================
        todo_user = frappe.db.get_value(

            "ToDo",

            {
                "reference_type":
                    "Soil Sample Collection",

                "reference_name":
                    r.name
            },

            "allocated_to"
        )

        if not todo_user:
            continue

        # =========================================
        # MAP EMPLOYEE
        # =========================================
        ra_name = frappe.db.get_value(

            "Employee",

            {
                "user_id": todo_user
            },

            "name"
        )

        if (
            not ra_name
            or cname not in data.get(ra_name, {})
        ):
            continue

        # =========================================
        # 🔥 SS COUNT USING number_of_samples
        # =========================================
        samples = cint(
            r.number_of_samples or 1
        )

        prev = 0
        curr = 0

        if fy_start <= r.completed_date < month_start:
            prev = samples

        if month_start <= r.completed_date <= month_end:
            curr = samples

        data[ra_name][cname]["ss_dm"] += curr

        data[ra_name][cname]["ss_pt"] += (
            prev + curr
        )

        # =========================================
        # ESTIMATE
        # =========================================
        total = (
            r.total_parameter_count or 0
        )

        use_total = client_map[cname]

        # =========================================
        # TOTAL MODE
        # =========================================
        if use_total == 1:

            if fy_start <= r.completed_date < month_start:

                prev = total
                curr = 0

            elif month_start <= r.completed_date <= month_end:

                prev = 0
                curr = total

            else:

                prev = 0
                curr = 0

            data[ra_name][cname]["est_dm"] += curr

            data[ra_name][cname]["est_pt"] += (
                prev + curr
            )

        # =========================================
        # TEST WISE MODE
        # =========================================
        else:

            tests = frappe.get_all(

                "Test Details",

                filters={
                    "parent": r.name
                },

                fields=[
                    "test_name",
                    "parameter_count"
                ]
            )

            for t in tests:

                if fy_start <= r.completed_date < month_start:

                    prev = (
                        t.parameter_count or 0
                    )

                    curr = 0

                elif month_start <= r.completed_date <= month_end:

                    prev = 0

                    curr = (
                        t.parameter_count or 0
                    )

                else:

                    prev = 0
                    curr = 0

                if (
                    t.test_name
                    in data[ra_name][cname]["tests"]
                ):

                    data[ra_name][cname]["tests"][t.test_name]["dm"] += curr

                    data[ra_name][cname]["tests"][t.test_name]["pt"] += (
                        prev + curr
                    )

    return generate_html(
        ra_list,
        client_map,
        all_tests,
        data
    )


# =========================================
# UI PART
# =========================================
def generate_html(
    ra_list,
    client_map,
    all_tests,
    data
):

    print_injection = """
    <div style="margin-bottom: 15px; text-align: right;">
        <button class="btn btn-primary btn-sm" onclick="printRAReport()">Print Report</button>
    </div>
    <script>
    function printRAReport() {
        frappe.call({
            method: "frappe.client.get_value",
            args: {
                doctype: "Employee",
                filters: { user_id: frappe.session.user },
                fieldname: ["custom_lab_name", "custom_district_office_name"]
            },
            callback: function(r) {
                let org_name = "Soil Laboratory Information System";
                if (r && r.message) {
                    org_name = r.message.custom_lab_name || r.message.custom_district_office_name || org_name;
                }

                let currentDate = new Date().toLocaleDateString('en-GB', {
                    day: '2-digit', month: '2-digit', year: 'numeric'
                });

                let table_html = document.getElementById('report-container').innerHTML;

                let print_window = window.open('', '_blank');
                print_window.document.write(`
                    <html>
                        <head>
                            <title>RA Wise Report</title>
                            <link rel="stylesheet" href="/assets/frappe/css/desk.min.css">
                            <style>
                                @page { size: landscape; margin: 10mm; }
                                body { font-family: Arial, sans-serif; padding: 10px; color: #000; }
                                .header-container { display: flex; align-items: center; justify-content: space-between; border-bottom: 2px solid #000; padding-bottom: 10px; margin-bottom: 15px; }
                                .logo-left, .logo-right { width: 60px; height: auto; object-fit: contain; }
                                .header-text { text-align: center; flex-grow: 1; margin: 0 15px; }
                                .header-text h3 { margin: 0; font-size: 16px; font-weight: bold; }
                                .header-text .ml-text { font-size: 11px; margin-top: 3px; font-weight: 500; }
                                .header-text .report-title { font-size: 14px; margin-top: 5px; font-weight: bold; text-decoration: underline; }
                                .date-section { text-align: right; font-size: 11px; margin-bottom: 8px; }
                                
                                /* --- COMPRESSED CELL & TABLE STYLES --- */
                                table { width: 100%; border-collapse: collapse; margin-top: 8px; margin-bottom: 15px; font-size: 9px; }
                                th { background-color: #f4f4f4 !important; border: 1px solid #ddd; padding: 4px 2px; text-align: center; font-size: 9px; word-break: break-word; }
                                td { border: 1px solid #ddd; padding: 4px 2px; text-align: center; font-size: 9px; }
                                th div, th span { font-size: 8px; line-height: 1.1; }
                                /* ------------------------------------- */

                                h4 { margin-top: 15px; margin-bottom: 6px; font-size: 12px; }
                            </style>
                        </head>
                        <body>
                            <div class="header-container">
                                <img src="/files/Slis_logo.png" class="logo-left" alt="SLIS Logo">
                                <div class="header-text">
                                    <h3>${org_name}</h3>
                                    <div class="ml-text">മണ്ണ് പരിശോധനാ മണ്ണ് സംരക്ഷണ വകുപ്പ്<br>കേരളസർക്കാർ</div>
                                    <div class="report-title">RA Wise Report</div>
                                </div>
                                <img src="/files/kerala_govt_logo.png" class="logo-right" alt="Kerala Govt Logo">
                            </div>
                            <div class="date-section"><strong>Date:</strong> ${currentDate}</div>
                            ${table_html}
                        </body>
                    </html>
                `);
                print_window.document.close();
                setTimeout(() => {
                    print_window.focus();
                    print_window.print();
                }, 400);
            }
        });
    }
    </script>
    """

    html = print_injection + """

    <style>

    .report-container{
        width:100%;
        overflow:auto;
        max-height:600px;
        border:1px solid #ccc;
        cursor:grab;
        user-select:none;
        position:relative;
    }

    .report-container:active{
        cursor:grabbing;
    }

    .report-table{
        border-collapse:collapse;
        width:max-content;
        min-width:1400px;
        font-size:13px;
    }

    .report-table th{
        background:#f5f5f5;
        font-weight:600;
        position:sticky;
        top:0;
        z-index:2;
    }

    .report-table th,
    .report-table td{
        border:1px solid #ccc;
        padding:8px 14px;
        text-align:center;
        white-space:nowrap;
    }

    .ra-cell{
        background:transparent;
        font-weight:bold;
    }

    .total-cell{
        background:transparent;
        font-weight:bold;
    }

    </style>

    <div
        class="report-container"
        id="report-container"
    >

    <table class="report-table">
    """

    # =========================================
    # HEADER 1
    # =========================================
    html += """
    <tr>

    <th rowspan='3'>
    Research Assistant
    </th>

    <th rowspan='3'>
    Lab
    </th>
    """

    for c in client_map:

        if client_map[c] == 1:

            html += f"""
            <th colspan='4'>
            {c}
            </th>
            """

        else:

            html += f"""
            <th colspan='{
                2 + len(all_tests) * 2
            }'>
            {c}
            </th>
            """

    html += """
    <th colspan='2'>
    SS TOTAL
    </th>

    <th colspan='2'>
    EST TOTAL
    </th>

    </tr>
    """

    # =========================================
    # HEADER 2
    # =========================================
    html += "<tr>"

    for c in client_map:

        html += """
        <th colspan='2'>
        SS
        </th>
        """

        if client_map[c] == 1:

            html += """
            <th colspan='2'>
            Estimate
            </th>
            """

        else:

            for t in all_tests:

                html += f"""
                <th colspan='2'>
                {t} Estimate
                </th>
                """

    html += "<th colspan='4'></th>"
    html += "</tr>"

    # =========================================
    # HEADER 3
    # =========================================
    html += "<tr>"

    for c in client_map:

        html += """
        <th>DM</th>
        <th>PT</th>
        """

        if client_map[c] == 1:

            html += """
            <th>DM</th>
            <th>PT</th>
            """

        else:

            for t in all_tests:

                html += """
                <th>DM</th>
                <th>PT</th>
                """

    html += """
    <th>DM</th>
    <th>PT</th>

    <th>DM</th>
    <th>PT</th>
    """

    html += "</tr>"

    # =========================================
    # BODY
    # =========================================
    for ra in ra_list:

        total_ss_dm = 0
        total_ss_pt = 0

        total_est_dm = 0
        total_est_pt = 0

        html += f"""

        <tr>

        <td class='ra-cell'>
        {ra.employee_name}
        </td>

        <td>
        {ra.custom_lab_name or '-'}
        </td>
        """

        for c in client_map:

            row = data[ra.name][c]

            html += f"""
            <td>{row['ss_dm']}</td>
            <td>{row['ss_pt']}</td>
            """

            total_ss_dm += row['ss_dm']
            total_ss_pt += row['ss_pt']

            if client_map[c] == 1:

                html += f"""
                <td>{row['est_dm']}</td>
                <td>{row['est_pt']}</td>
                """

                total_est_dm += row['est_dm']
                total_est_pt += row['est_pt']

            else:

                for t in all_tests:

                    dm = row["tests"][t]["dm"]
                    pt = row["tests"][t]["pt"]

                    total_est_dm += dm
                    total_est_pt += pt

                    html += f"""
                    <td>{dm}</td>
                    <td>{pt}</td>
                    """

        html += f"""

        <td class='total-cell'>
        {total_ss_dm}
        </td>

        <td class='total-cell'>
        {total_ss_pt}
        </td>

        <td class='total-cell'>
        {total_est_dm}
        </td>

        <td class='total-cell'>
        {total_est_pt}
        </td>

        </tr>
        """

    html += """
    </table>
    </div>

    <script>

    const slider = document.getElementById(
        "report-container"
    );

    let isDown = false;

    let startX;
    let startY;

    let scrollLeft;
    let scrollTop;

    slider.addEventListener(
        "mousedown",
        (e) => {

            isDown = true;

            startX =
                e.pageX - slider.offsetLeft;

            startY =
                e.pageY - slider.offsetTop;

            scrollLeft =
                slider.scrollLeft;

            scrollTop =
                slider.scrollTop;
        }
    );

    slider.addEventListener(
        "mouseleave",
        () => {

            isDown = false;
        }
    );

    slider.addEventListener(
        "mouseup",
        () => {

            isDown = false;
        }
    );

    slider.addEventListener(
        "mousemove",
        (e) => {

            if (!isDown)
                return;

            e.preventDefault();

            const x =
                e.pageX - slider.offsetLeft;

            const y =
                e.pageY - slider.offsetTop;

            const walkX =
                (x - startX) * 1.5;

            const walkY =
                (y - startY) * 1.5;

            slider.scrollLeft =
                scrollLeft - walkX;

            slider.scrollTop =
                scrollTop - walkY;
        }
    );

    </script>
    """

    return html