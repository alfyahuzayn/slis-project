frappe.query_reports["Department Office Report"] = {

    filters: [

        // =====================================================
        // MONTH
        // =====================================================

        {
            fieldname: "month",

            label: __("Month"),

            fieldtype: "Select",

            options: [
                "",
                "January",
                "February",
                "March",
                "April",
                "May",
                "June",
                "July",
                "August",
                "September",
                "October",
                "November",
                "December"
            ],

            default: [
                "",
                "January",
                "February",
                "March",
                "April",
                "May",
                "June",
                "July",
                "August",
                "September",
                "October",
                "November",
                "December"
            ][new Date().getMonth() + 1],

            reqd: 1
        },


        // =====================================================
        // YEAR
        // =====================================================

        {
            fieldname: "year",

            label: __("Year"),

            fieldtype: "Int",

            default: new Date().getFullYear(),

            reqd: 1
        }
    ],


    // =========================================================
    // ONLOAD
    // =========================================================

    onload: function(report) {

        add_department_report_css();

        create_custom_report_container(report);

    },


    // =========================================================
    // AFTER DATATABLE RENDER
    // =========================================================

    after_datatable_render: function(datatable) {

        let report = frappe.query_report;

        create_custom_report_container(report);

        render_department_report(report);

        hide_standard_report(report);

    },


    // =========================================================
    // REFRESH
    // =========================================================

    refresh: function(report) {

        /*
         * Wait for Python execution to finish.
         */

        setTimeout(function() {

            create_custom_report_container(report);

            render_department_report(report);

            hide_standard_report(report);

        }, 500);

    }

};


// =============================================================
// CREATE CUSTOM HTML CONTAINER
// =============================================================

function create_custom_report_container(report) {

    let wrapper = report.page.wrapper;


    /*
     * Already exists?
     */

    if (
        wrapper.find(
            ".department-office-custom-report"
        ).length
    ) {

        return;

    }


    let container = $(`
        <div class="department-office-custom-report">

            <div class="department-office-report-content">

            </div>

        </div>
    `);


    /*
     * Put the custom report AFTER
     * the standard report wrapper.
     */

    let report_wrapper = wrapper.find(
        ".report-wrapper"
    );


    if (report_wrapper.length) {

        report_wrapper.after(
            container
        );

    } else {

        wrapper
            .find(".layout-main-section")
            .append(container);

    }

}


// =============================================================
// RENDER DEPARTMENT REPORT
// =============================================================

function render_department_report(report) {

    let wrapper = report.page.wrapper;


    let container = wrapper.find(
        ".department-office-custom-report"
    );


    if (!container.length) {

        return;

    }


    let content = container.find(
        ".department-office-report-content"
    );


    /*
     * Get Python result.
     */

    let data = frappe.query_report.data;


    console.log(
        "Department Office Report Data:",
        data
    );


    if (
        !data ||
        !data.length
    ) {

        show_no_data(content);

        return;

    }


    /*
     * First row contains report_data.
     */

    let json_data = data[0].report_data;


    if (!json_data) {

        show_no_data(content);

        return;

    }


    let labs;


    try {

        labs = JSON.parse(
            json_data
        );

    } catch (error) {

        console.error(
            "Department Office Report JSON error:",
            error
        );

        show_no_data(content);

        return;

    }


    console.log(
        "Department Office Report Labs:",
        labs
    );


    /*
     * Build all lab tables.
     */

    let html = build_all_lab_tables(
        labs
    );


    content.html(
        html
    );

}


// =============================================================
// HIDE NORMAL FRAPPE DATATABLE
// =============================================================

function hide_standard_report(report) {

    let wrapper = report.page.wrapper;


    wrapper.find(
        ".report-wrapper"
    ).hide();


    wrapper.find(
        ".datatable"
    ).hide();


    wrapper.find(
        ".dt-instance"
    ).hide();


    wrapper.find(
        ".report-footer"
    ).hide();

}


// =============================================================
// BUILD ALL LAB TABLES
// =============================================================

function build_all_lab_tables(labs) {

    let html = "";


    let lab_names = Object.keys(
        labs
    );


    if (!lab_names.length) {

        return `

            <div class="department-no-data">

                No records found for the selected
                month and year.

            </div>

        `;

    }


    /*
     * One table for each Target Lab.
     */

    lab_names.forEach(
        function(lab_name) {

            html += build_single_lab_table(
                lab_name,
                labs[lab_name]
            );

        }
    );


    return html;

}


// =============================================================
// BUILD SINGLE LAB TABLE
// =============================================================

function build_single_lab_table(
    lab_name,
    lab_data
) {

    /*
     * Horizontal columns.
     *
     * Example:
     *
     * Farmer
     * Consultancy
     * NMSA
     * NSMP
     * PMKSY
     */

    let columns = Object.keys(
        lab_data
    );


    /*
     * Vertical rows.
     *
     * Example:
     *
     * With RA
     * Assigned RA
     * Completed
     */

    let statuses = get_statuses(
        lab_data
    );


    let html = `

        <div class="department-lab-section">

            <div class="department-lab-name">

                ${escape_html(
                    lab_name
                )}

            </div>


            <div class="department-table-wrapper">

                <table class="department-lab-table">

                    <thead>

                        <tr>

                            <th class="status-header">

                                Status

                            </th>

    `;


    /*
     * Horizontal columns.
     */

    columns.forEach(
        function(column_name) {

            html += `

                <th class="type-header">

                    ${escape_html(
                        column_name
                    )}

                </th>

            `;

        }
    );


    html += `

                        </tr>

                    </thead>


                    <tbody>

    `;


    /*
     * Vertical status rows.
     */

    statuses.forEach(
        function(status) {

            html += `

                <tr>

                    <td class="status-cell">

                        ${escape_html(
                            status
                        )}

                    </td>

            `;


            /*
             * Count for each column.
             */

            columns.forEach(
                function(column_name) {

                    let count = 0;


                    if (
                        lab_data[column_name] &&
                        lab_data[column_name][status]
                    ) {

                        count =
                            lab_data[column_name][status];

                    }


                    html += `

                        <td class="count-cell">

                            ${count}

                        </td>

                    `;

                }
            );


            html += `

                </tr>

            `;

        }
    );


    html += `

                    </tbody>

                </table>

            </div>

        </div>

    `;


    return html;

}


// =============================================================
// GET STATUS ORDER
// =============================================================

function get_statuses(lab_data) {

    let statuses = [];


    /*
     * Collect every status.
     */

    Object.keys(
        lab_data
    ).forEach(
        function(column_name) {

            let column_data =
                lab_data[column_name];


            Object.keys(
                column_data
            ).forEach(
                function(status) {

                    if (
                        !statuses.includes(
                            status
                        )
                    ) {

                        statuses.push(
                            status
                        );

                    }

                }
            );

        }
    );


    /*
     * Preferred status order.
     *
     * Any other status will be added
     * afterward automatically.
     */

    let preferred_order = [

        "With RA",

        "Assigned RA",

        "With Lab Incharge",

        "With Senior Chemist",

        "With Research Assistant",

        "With Assistant Director",

        "Under Lab Verification",

        "Sample Verification Completed",

        "Completed",

        "Rejected"

    ];


    let ordered_statuses = [];


    preferred_order.forEach(
        function(status) {

            if (
                statuses.includes(
                    status
                )
            ) {

                ordered_statuses.push(
                    status
                );

            }

        }
    );


    /*
     * Add any statuses not included
     * in preferred_order.
     */

    statuses.forEach(
        function(status) {

            if (
                !ordered_statuses.includes(
                    status
                )
            ) {

                ordered_statuses.push(
                    status
                );

            }

        }
    );


    return ordered_statuses;

}


// =============================================================
// NO DATA
// =============================================================

function show_no_data(content) {

    content.html(`

        <div class="department-no-data">

            No records found for the selected
            month and year.

        </div>

    `);

}


// =============================================================
// ESCAPE HTML
// =============================================================

function escape_html(value) {

    if (
        value === null ||
        value === undefined
    ) {

        return "";

    }


    return String(value)

        .replace(
            /&/g,
            "&amp;"
        )

        .replace(
            /</g,
            "&lt;"
        )

        .replace(
            />/g,
            "&gt;"
        )

        .replace(
            /"/g,
            "&quot;"
        )

        .replace(
            /'/g,
            "&#039;"
        );

}


// =============================================================
// CSS
// =============================================================

function add_department_report_css() {

    if (
        $("#department-office-report-css").length
    ) {

        return;

    }


    let css = `

        /* =====================================================
           MAIN REPORT
           ===================================================== */

        .department-office-custom-report {

            width: 100%;

            margin-top: 20px;

            padding: 10px 0 40px 0;

            background: #ffffff;

        }


        .department-office-report-content {

            width: 100%;

        }


        /* =====================================================
           LAB SECTION
           ===================================================== */

        .department-lab-section {

            width: 100%;

            margin-bottom: 45px;

        }


        /* =====================================================
           LAB NAME
           ===================================================== */

        .department-lab-name {

            font-size: 18px;

            font-weight: 600;

            margin-bottom: 10px;

            padding-left: 5px;

        }


        /* =====================================================
           TABLE WRAPPER
           ===================================================== */

        .department-table-wrapper {

            width: 100%;

            overflow-x: auto;

        }


        /* =====================================================
           TABLE
           ===================================================== */

        .department-lab-table {

            width: 100%;

            border-collapse: collapse;

            background: #ffffff;

        }


        /* =====================================================
           ALL CELLS
           ===================================================== */

        .department-lab-table th,

        .department-lab-table td {

            border: 1px solid #333333;

            padding: 9px 12px;

            vertical-align: middle;

        }


        /* =====================================================
           HEADER
           ===================================================== */

        .department-lab-table th {

            text-align: center;

            font-weight: 600;

            white-space: nowrap;

        }


        /* =====================================================
           STATUS HEADER
           ===================================================== */

        .department-lab-table .status-header {

            min-width: 200px;

            text-align: left;

        }


        /* =====================================================
           STATUS
           ===================================================== */

        .department-lab-table .status-cell {

            min-width: 200px;

            text-align: left;

            white-space: nowrap;

            font-weight: 500;

        }


        /* =====================================================
           NAME OF TYPE / CLIENT TYPE
           ===================================================== */

        .department-lab-table .type-header {

            min-width: 120px;

            text-align: center;

        }


        /* =====================================================
           COUNT
           ===================================================== */

        .department-lab-table .count-cell {

            min-width: 120px;

            text-align: center;

            font-weight: 500;

        }


        /* =====================================================
           NO DATA
           ===================================================== */

        .department-no-data {

            width: 100%;

            padding: 40px;

            text-align: center;

            color: #777777;

            font-size: 15px;

        }


        /* =====================================================
           PRINT
           ===================================================== */

        @media print {

            .department-office-custom-report {

                margin: 0;

                padding: 0;

            }


            .department-lab-section {

                page-break-inside: avoid;

                margin-bottom: 25px;

            }


            .department-lab-table {

                width: 100%;

            }


            .department-lab-table th,

            .department-lab-table td {

                border: 1px solid #000000 !important;

            }

        }

    `;


    $("<style>", {

        id: "department-office-report-css",

        type: "text/css",

        html: css

    }).appendTo("head");

}