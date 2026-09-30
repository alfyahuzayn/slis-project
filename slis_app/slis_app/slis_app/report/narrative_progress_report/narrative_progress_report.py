import frappe
import calendar
from datetime import date


# ======================================================
# MAIN
# ======================================================
def execute(filters=None):

    filters = filters or {}

    month = int(filters.get("month"))
    year = int(filters.get("year"))

    month_name = calendar.month_name[month]

    financial_year, fy_start, fy_end = (
        get_financial_year_range(month, year)
    )

    today = date.today()

    if date(year, month, 1) > today:
        return (
            [],
            [],
            f"<h3>No data for {month_name} {year} (Future Month)</h3>"
        )

    # ==================================================
    # SESSION 1
    # ==================================================
    session1_columns = get_columns()

    session1_data = get_data(
        filters,
        month,
        year,
        financial_year,
        fy_start
    )

    user = frappe.session.user
    ra = is_ra(user)

    # ==================================================
    # SESSION 2
    # ==================================================
    session2_raw = get_session_two_data(
        ra=ra,
        user=user
    )

    session2_columns = get_session_two_columns(
        session2_raw,
        ra=ra
    )

    session2_data = session2_raw["rows"]

    html = build_html(
        session1_columns,
        session1_data,
        session2_columns,
        session2_data,
        ra=ra
    )

    message = (
        f"Samples Analysed in "
        f"{month_name} {financial_year}"
        f"<br><br>{html}"
    )

    #  to print the report

    print_injection = """
    <div style="margin-bottom: 15px; text-align: right;">
        <button class="btn btn-primary btn-sm" onclick="printNarrativeReport()">Print Report</button>
    </div>
    <script>
    function printNarrativeReport() {
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

                let boxes = document.querySelectorAll('.box');
                let s1_html = boxes[0] ? boxes[0].querySelector('table').outerHTML : '';
                let s2_html = boxes[1] ? boxes[1].querySelector('table').outerHTML : '';

                let print_window = window.open('', '_blank');
                print_window.document.write(`
                    <html>
                        <head>
                            <title>Narrative Progress Report</title>
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
    th { background-color: #f4f4f4; border: 1px solid #ddd; padding: 4px 2px; text-align: center; font-size: 9px; word-break: break-word; }
    td { border: 1px solid #ddd; padding: 4px 2px; text-align: center; font-size: 9px; }
    /* Scales down the long Malayalam subtext inside headers */
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
                                    <div class="report-title">Narrative Progress Report</div>
                                </div>
                                <img src="/files/kerala_govt_logo.png" class="logo-right" alt="Kerala Govt Logo">
                            </div>
                            <div class="date-section"><strong>Date:</strong> ${currentDate}</div>
                            
                            <h4>Narrative Progress Report</h4>
                            ${s1_html}

                            <h4>Pending Work</h4>
                            ${s2_html}
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

    message = print_injection + message


    return [], [], message


# ======================================================
# RA CHECK
# ======================================================
def is_ra(user):

    emp_name = frappe.db.get_value(
        "Employee",
        {"user_id": user},
        "employee_name"
    )

    if not emp_name:
        return False

    return frappe.db.exists(
        "ToDo",
        {
            "allocated_to": user,
            "custom_ra_employee_name": emp_name
        }
    )


# ======================================================
# LAB LIST
# ======================================================
def get_labs(user):

    roles = frappe.get_roles(user)

    if (
        user == "Administrator"
        or "System Manager" in roles
    ):
        return frappe.get_all(
            "Soil Laboratory",
            pluck="name"
        )

    if "Soil Intaker L2" in roles:

        lab = frappe.db.get_value(
            "Employee",
            {"user_id": user},
            "custom_lab_name"
        )

        return [lab] if lab else []

    return frappe.get_all(
        "Soil Laboratory",
        pluck="name"
    )


# ======================================================
# LAB MAPPING
# ======================================================
def get_sample_lab(sample):

    if sample.client_type == "Department":
        return sample.target_lab

    return sample.lab_name


# ======================================================
# SAMPLE COUNTING
# ======================================================
def get_sample_count(
    sample,
    child_count_map=None
):

    client_type = str(
        sample.get("client_type") or ""
    ).strip()

    # ==================================================
    # FARMER
    #
    # IMPORTANT:
    # Master flags DO NOT matter for Farmer.
    #
    # number_of_samples > 0
    #     -> use number_of_samples
    #
    # number_of_samples empty / 0
    #     -> count as 1
    # ==================================================
    if client_type == "Farmer":

        number_of_samples = (
            sample.get("number_of_samples")
            or 0
        )

        try:

            number_of_samples = int(
                number_of_samples
            )

        except (
            TypeError,
            ValueError
        ):

            number_of_samples = 0

        if number_of_samples > 0:
            return number_of_samples

        return 1

    # ==================================================
    # DEPARTMENT / CONSULTANCY
    #
    # Master if:
    #
    # is_master_sample = 1
    # OR
    # master_profile_sample = 1
    #
    # Master with children:
    #     -> master count = 0
    #     -> children count individually
    #
    # Master without children:
    #     -> count master as 1
    # ==================================================

    is_master = (

        int(
            sample.get(
                "is_master_sample"
            ) or 0
        ) == 1

        or

        int(
            sample.get(
                "master_profile_sample"
            ) or 0
        ) == 1
    )

    if is_master:

        child_count = (
            child_count_map or {}
        ).get(
            sample.get("name"),
            0
        )

        # ----------------------------------------------
        # MASTER HAS CHILDREN
        # Do NOT count master.
        # ----------------------------------------------
        if child_count > 0:
            return 0

        # ----------------------------------------------
        # MASTER HAS NO CHILDREN
        # Count as one sample.
        # ----------------------------------------------
        return 1

    # ==================================================
    # NORMAL DEPARTMENT / CONSULTANCY
    # Includes child samples.
    # ==================================================
    return 1


# ======================================================
# CHILD COUNT MAP
# ======================================================
def get_child_count_map(samples):

    child_count_map = {}

    for sample in samples:

        parent = sample.get(
            "parent_sample"
        )

        if parent:

            child_count_map[parent] = (
                child_count_map.get(
                    parent,
                    0
                )
                + 1
            )

    return child_count_map


# ======================================================
# FINANCIAL YEAR
# ======================================================
def get_financial_year_range(
    month,
    year
):

    if month >= 4:

        return (
            f"{year}-{year + 1}",
            date(year, 4, 1),
            date(year + 1, 3, 31)
        )

    return (
        f"{year - 1}-{year}",
        date(year - 1, 4, 1),
        date(year, 3, 31)
    )


def get_month_end_date(
    month,
    year
):

    return date(
        year,
        month,
        calendar.monthrange(
            year,
            month
        )[1]
    )


# ======================================================
# SESSION 1 COLUMNS
# ======================================================
def get_columns():

    return [

        {
            "label": "Name",
            "fieldname": "name"
        },

        {
            "label": "Profile Target",
            "fieldname": "profile_target"
        },

        {
            "label": "Other Target",
            "fieldname": "other_target"
        },

        {
            "label": "Total Target",
            "fieldname": "target"
        },

        {
            "label": "DM",
            "fieldname": "dm"
        },

        {
            "label": "PT",
            "fieldname": "pt"
        },

        {
            "label": "Pending",
            "fieldname": "pending"
        }
    ]


# ======================================================
# SESSION 1 DATA
# ======================================================
def get_data(
    filters,
    month,
    year,
    financial_year,
    fy_start
):

    user = frappe.session.user

    month_start = date(
        year,
        month,
        1
    )

    month_end = get_month_end_date(
        month,
        year
    )

    # ==================================================
    # RA USER
    # ==================================================
    if is_ra(user):

        emp = frappe.db.get_value(
            "Employee",
            {"user_id": user},
            ["employee_name"],
            as_dict=True
        )

        target = frappe.db.get_value(
            "Monthly Target",
            {
                "financial_year":
                    financial_year
            },
            [
                "profile_sample_count",
                "other_sample_count"
            ],
            as_dict=True
        )

        profile = (
            target.profile_sample_count
            if target
            else 0
        )

        other = (
            target.other_sample_count
            if target
            else 0
        )

        samples = frappe.db.sql(
            """
            SELECT
                s.name,
                s.status,
                s.completed_date,
                s.client_type,
                s.number_of_samples,
                s.is_master_sample,
                s.master_profile_sample,
                s.parent_sample

            FROM
                `tabSoil Sample Collection` s

            INNER JOIN
                `tabToDo` t

            ON
                t.reference_name = s.name

            WHERE
                t.allocated_to = %s
            """,
            user,
            as_dict=True
        )

        child_count_map = (
            get_child_count_map(
                samples
            )
        )

        dm = 0
        pt = 0
        pending = 0

        for sample in samples:

            sample_count = (
                get_sample_count(
                    sample,
                    child_count_map
                )
            )

            if (
                sample.status
                == "completed"
                and
                sample.completed_date
            ):

                if (
                    month_start
                    <= sample.completed_date
                    <= month_end
                ):

                    dm += sample_count

                if (
                    fy_start
                    <= sample.completed_date
                    <= month_end
                ):

                    pt += sample_count

            elif (
                sample.status
                == "With Research Assistant"
            ):

                pending += sample_count

        return [{

            "name":
                emp.employee_name
                if emp
                else user,

            "profile_target":
                profile,

            "other_target":
                other,

            "target":
                profile + other,

            "dm":
                dm,

            "pt":
                pt,

            "pending":
                pending
        }]

    # ==================================================
    # NON-RA / LAB USER
    # ==================================================

    labs = get_labs(user)

    samples = frappe.get_all(
        "Soil Sample Collection",

        fields=[
            "name",
            "lab_name",
            "target_lab",
            "client_type",
            "status",
            "completed_date",
            "number_of_samples",
            "is_master_sample",
            "master_profile_sample",
            "parent_sample"
        ]
    )

    child_count_map = (
        get_child_count_map(
            samples
        )
    )

    data = []

    for lab in labs:

        dm = 0
        pt = 0
        pending = 0

        for sample in samples:

            sample_lab = (
                get_sample_lab(
                    sample
                )
            )

            if sample_lab != lab:
                continue

            sample_count = (
                get_sample_count(
                    sample,
                    child_count_map
                )
            )

            if (
                sample.status
                == "completed"
                and
                sample.completed_date
            ):

                if (
                    month_start
                    <= sample.completed_date
                    <= month_end
                ):

                    dm += sample_count

                if (
                    fy_start
                    <= sample.completed_date
                    <= month_end
                ):

                    pt += sample_count

            elif sample.status in (

                "With Senior Chemist",

                "With Research Assistant",

                "Returned to Senior Chemist(Overload)"
            ):

                pending += sample_count

        target = frappe.db.sql(
            """
            SELECT

                SUM(
                    mt.profile_sample_count
                    * lt.ra_count
                ) AS profile,

                SUM(
                    mt.other_sample_count
                    * lt.ra_count
                ) AS other

            FROM
                `tabMonthly Target` mt

            INNER JOIN
                `tabLab Target` lt

            ON
                lt.parent = mt.name

            WHERE
                lt.lab_name = %s

            AND
                mt.financial_year = %s
            """,

            (
                lab,
                financial_year
            ),

            as_dict=True
        )

        profile = (
            target[0]["profile"]
            or 0
        )

        other = (
            target[0]["other"]
            or 0
        )

        data.append({

            "name":
                lab,

            "profile_target":
                profile,

            "other_target":
                other,

            "target":
                profile + other,

            "dm":
                dm,

            "pt":
                pt,

            "pending":
                pending
        })

    return data


# ======================================================
# SESSION 2 COLUMNS
# ======================================================
def get_session_two_columns(
    data,
    ra=False
):

    first_col_label = (
        "Name"
        if ra
        else "Lab"
    )

    cols = [{

        "label":
            first_col_label,

        "fieldname":
            "lab_name"
    }]

    for client in data["clients"]:

        cols.append({

            "label":
                client,

            "fieldname":
                client
        })

    cols.append({

        "label":
            "Total Pending",

        "fieldname":
            "total_pending"
    })

    return cols


# ======================================================
# SESSION 2 DATA
# ======================================================
def get_session_two_data(
    ra=False,
    user=None
):

    if user is None:
        user = frappe.session.user

    # ==================================================
    # RA
    # Only samples assigned to this RA
    # ==================================================
    if ra:

        emp_name = frappe.db.get_value(
            "Employee",
            {"user_id": user},
            "employee_name"
        )

        assigned_samples = frappe.db.sql(
            """
            SELECT
                t.reference_name

            FROM
                `tabToDo` t

            WHERE
                t.allocated_to = %s

            AND
                t.custom_ra_employee_name = %s
            """,

            (
                user,
                emp_name
            ),

            as_dict=True
        )

        assigned_names = [

            row.reference_name

            for row in assigned_samples
        ]

        if not assigned_names:

            return {
                "rows": [],
                "clients": []
            }

        samples = frappe.get_all(
            "Soil Sample Collection",

            filters={
                "name": [
                    "in",
                    assigned_names
                ]
            },

            fields=[
                "name",
                "lab_name",
                "target_lab",
                "client_type",
                "type_of_collection",
                "name_of_type",
                "status",
                "number_of_samples",
                "is_master_sample",
                "master_profile_sample",
                "parent_sample"
            ]
        )

        child_count_map = (
            get_child_count_map(
                samples
            )
        )

        # ==============================================
        # CLIENT / SCHEME COLUMN NAME
        # ==============================================
        def get_client_names(sample):

            if (
                sample.client_type
                == "Department"
            ):

                type_col = str(
                    sample.get(
                        "type_of_collection"
                    )
                    or ""
                ).strip()

                name_type = str(
                    sample.get(
                        "name_of_type"
                    )
                    or ""
                ).strip()

                if (
                    type_col
                    and name_type
                ):

                    base_name = (
                        f"{type_col}"
                        f" - "
                        f"{name_type}"
                    )

                elif name_type:

                    base_name = (
                        name_type
                    )

                elif type_col:

                    base_name = (
                        type_col
                    )

                else:

                    base_name = (
                        "Department"
                    )

                test_items = (
                    frappe.get_all(

                        "Scheme Test List",

                        filters={
                            "parent":
                                sample.name_of_type
                        },

                        fields=[
                            "test_item"
                        ]
                    )
                )

                names = []

                for test in test_items:

                    if test.test_item:

                        names.append(

                            f"{base_name}"
                            f" - "
                            f"{test.test_item}"
                        )

                return (
                    names
                    if names
                    else [base_name]
                )

            return [
                sample.client_type
            ]

        clients = set()

        ra_row = {}

        # ==============================================
        # RA PENDING COUNT
        # ==============================================
        for sample in samples:

            if (
                sample.status
                == "completed"
            ):
                continue

            if sample.status not in (
                "With Research Assistant",
            ):
                continue

            sample_count = (
                get_sample_count(
                    sample,
                    child_count_map
                )
            )

            # ------------------------------------------
            # Master with children = 0
            # Do not count master.
            # ------------------------------------------
            if sample_count <= 0:
                continue

            cnames = (
                get_client_names(
                    sample
                )
            )

            for cname in cnames:

                clients.add(
                    cname
                )

                ra_row[cname] = (

                    ra_row.get(
                        cname,
                        0
                    )

                    + sample_count
                )

        # ==============================================
        # IMPORTANT:
        # Total must be calculated AFTER the loop.
        # ==============================================
        total = sum(
            ra_row.values()
        )

        ra_row["lab_name"] = (
            emp_name
            or user
        )

        ra_row["total_pending"] = (
            total
        )

        return {

            "rows": [
                ra_row
            ],

            "clients":
                list(clients)
        }

    # ==================================================
    # NON-RA / LAB
    # ==================================================

    labs = get_labs(user)

    samples = frappe.get_all(
        "Soil Sample Collection",

        fields=[
            "name",
            "lab_name",
            "target_lab",
            "client_type",

            # Required for Department scheme columns
            "type_of_collection",
            "name_of_type",

            "status",
            "completed_date",
            "number_of_samples",
            "is_master_sample",
            "master_profile_sample",
            "parent_sample"
        ]
    )

    child_count_map = (
        get_child_count_map(
            samples
        )
    )

    # ==================================================
    # CLIENT / SCHEME COLUMN NAME
    # ==================================================
    def get_client_names(sample):

        if (
            sample.client_type
            == "Department"
        ):

            type_col = str(
                sample.get(
                    "type_of_collection"
                )
                or ""
            ).strip()

            name_type = str(
                sample.get(
                    "name_of_type"
                )
                or ""
            ).strip()

            if (
                type_col
                and name_type
            ):

                base_name = (
                    f"{type_col}"
                    f" - "
                    f"{name_type}"
                )

            elif name_type:

                base_name = (
                    name_type
                )

            elif type_col:

                base_name = (
                    type_col
                )

            else:

                base_name = (
                    "Department"
                )

            test_items = frappe.get_all(

                "Scheme Test List",

                filters={
                    "parent":
                        sample.name_of_type
                },

                fields=[
                    "test_item"
                ]
            )

            names = []

            for test in test_items:

                if test.test_item:

                    names.append(

                        f"{base_name}"
                        f" - "
                        f"{test.test_item}"
                    )

            return (
                names
                if names
                else [base_name]
            )

        return [
            sample.client_type
        ]

    data = {}

    clients = set()

    for lab in labs:

        data[lab] = {}

    # ==================================================
    # NON-RA PENDING COUNT
    # ==================================================
    for sample in samples:

        sample_lab = (
            get_sample_lab(
                sample
            )
        )

        if sample_lab not in data:
            continue

        if (
            sample.status
            == "completed"
        ):
            continue

        if sample.status not in (

            "With Senior Chemist",

            "With Research Assistant",

            "Returned to Senior Chemist(Overload)"
        ):
            continue

        sample_count = (
            get_sample_count(
                sample,
                child_count_map
            )
        )

        # ----------------------------------------------
        # Master with children = 0
        # Do not count master.
        # ----------------------------------------------
        if sample_count <= 0:
            continue

        cnames = (
            get_client_names(
                sample
            )
        )

        for cname in cnames:

            clients.add(
                cname
            )

            data[
                sample_lab
            ][cname] = (

                data[
                    sample_lab
                ].get(
                    cname,
                    0
                )

                + sample_count
            )

    result = []

    for name in data:

        row = {
            "lab_name":
                name
        }

        total = 0

        for client in clients:

            value = (
                data[
                    name
                ].get(
                    client,
                    0
                )
            )

            row[client] = (
                value
            )

            total += value

        row[
            "total_pending"
        ] = total

        result.append(
            row
        )

    return {

        "rows":
            result,

        "clients":
            list(clients)
    }


# ======================================================
# HTML
# ======================================================
def build_html(
    c1,
    d1,
    c2,
    d2,
    ra=False
):

    html = """
    <style>

    .box{
        overflow:auto;
        border:1px solid #ccc;
        margin-bottom:20px;
        cursor:grab;
        user-select:none;
    }

    .box:active{
        cursor:grabbing;
    }

    table{
        border-collapse:collapse;
        width:max-content;
        min-width:100%;
    }

    th,td{
        border:1px solid #ccc;
        padding:8px;
        text-align:center;
        white-space:nowrap;
    }

    th{
        background:#f5f5f5;
    }

    </style>
    """

    # ==================================================
    # SESSION 1
    # ==================================================
    html += """
    <h3>
    Narrative Progress Report
    </h3>

    <div class='box'>
    <table>
    <tr>
    """

    for col in c1:

        html += f"""
        <th>
        {col['label']}
        </th>
        """

    html += "</tr>"

    for row in d1:

        html += "<tr>"

        for col in c1:

            html += f"""
            <td>
            {row.get(col['fieldname'], '')}
            </td>
            """

        html += "</tr>"

    html += """
    </table>
    </div>
    """

    # ==================================================
    # SESSION 2
    # ==================================================

    first_col_label = (

        c2[0]["label"]

        if c2

        else (

            "Name"

            if ra

            else "Lab"
        )
    )

    html += """
    <h3>
    Pending Work
    </h3>

    <div class='box'>
    <table>
    """

    main_headers = {}

    field_map = {}

    for col in c2:

        fname = col["fieldname"]

        label = col["label"]

        if fname in (
            "lab_name",
            "total_pending"
        ):
            continue

        parts = label.split(
            " - "
        )

        if len(parts) >= 3:

            main = " - ".join(
                parts[:2]
            )

            sub = parts[2]

        else:

            main = label

            sub = ""

        if (
            main
            not in main_headers
        ):

            main_headers[
                main
            ] = []

        main_headers[
            main
        ].append(
            sub
        )

        field_map[
            (
                main,
                sub
            )
        ] = fname

    order = [
        "Profile",
        "Surface"
    ]

    for main in main_headers:

        main_headers[
            main
        ] = sorted(

            main_headers[
                main
            ],

            key=lambda x:

                order.index(x)

                if x in order

                else 99
        )

    html += f"""
    <tr>

    <th rowspan='2'>
    {first_col_label}
    </th>
    """

    for main in main_headers:

        html += f"""
        <th colspan='{
            len(
                main_headers[
                    main
                ]
            )
        }'>
        {main}
        </th>
        """

    html += """
    <th rowspan='2'>
    Total Pending
    </th>

    </tr>
    """

    html += "<tr>"

    for main in main_headers:

        for sub in (
            main_headers[
                main
            ]
        ):

            html += f"""
            <th>
            {sub}
            </th>
            """

    html += "</tr>"

    for row in d2:

        html += "<tr>"

        html += f"""
        <td>
        {row.get('lab_name', '')}
        </td>
        """

        for main in main_headers:

            for sub in (
                main_headers[
                    main
                ]
            ):

                fname = (
                    field_map.get(
                        (
                            main,
                            sub
                        )
                    )
                )

                html += f"""
                <td>
                {row.get(fname, 0)}
                </td>
                """

        html += f"""
        <td>
        {row.get('total_pending', 0)}
        </td>
        """

        html += "</tr>"

    html += """
    </table>
    </div>
    """

    # ==================================================
    # DRAG SCROLL SCRIPT
    # ==================================================

    html += """

    <script>

    document
        .querySelectorAll('.box')
        .forEach(slider => {

        let isDown = false;

        let startX;
        let startY;

        let scrollLeft;
        let scrollTop;

        slider.addEventListener(
            'mousedown',
            (e) => {

                isDown = true;

                startX =
                    e.pageX -
                    slider.offsetLeft;

                startY =
                    e.pageY -
                    slider.offsetTop;

                scrollLeft =
                    slider.scrollLeft;

                scrollTop =
                    slider.scrollTop;
            }
        );

        slider.addEventListener(
            'mouseleave',
            () => {

                isDown = false;
            }
        );

        slider.addEventListener(
            'mouseup',
            () => {

                isDown = false;
            }
        );

        slider.addEventListener(
            'mousemove',
            (e) => {

                if (!isDown)
                    return;

                e.preventDefault();

                const x =
                    e.pageX -
                    slider.offsetLeft;

                const y =
                    e.pageY -
                    slider.offsetTop;

                const walkX =
                    (x - startX)
                    * 1.5;

                const walkY =
                    (y - startY)
                    * 1.5;

                slider.scrollLeft =
                    scrollLeft -
                    walkX;

                slider.scrollTop =
                    scrollTop -
                    walkY;
            }
        );

    });

    </script>
    """

    return html