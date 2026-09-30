// Copyright (c) 2026, navaneeth and contributors
// For license information, please see license.txt

frappe.query_reports["Sample Status"] = {
    "filters": [
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            default: frappe.datetime.month_start()
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            default: frappe.datetime.get_today()
        },
        {
            fieldname: "lab_name",
            label: __("Lab Name"),
            fieldtype: "Link",
            options: "Soil Laboratory"
        },
        {
            fieldname: "scheme",
            label: __("Scheme"),
            fieldtype: "Link",
            options: "Scheme or Programs"
        }
    ],
    "onload": function(report) {
        report.page.add_inner_button(__("Print Report"), function() {
            let data = report.data;
            let columns = report.columns;

            if (!data || data.length === 0) {
                frappe.msgprint(__('No data to print'));
                return;
            }

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
                        day: '2-digit',
                        month: '2-digit',
                        year: 'numeric'
                    });

                    // Automatically map whatever columns are currently visible in the report
                    let headers_html = columns.map(col => `<th>${col.label || col.fieldname}</th>`).join('');

                    let rows_html = data.map(row => {
                        let cells = columns.map(col => {
                            let val = row[col.fieldname] !== undefined && row[col.fieldname] !== null ? row[col.fieldname] : '';
                            return `<td style="border: 1px solid #ddd; padding: 8px;">${val}</td>`;
                        }).join('');
                        return `<tr>${cells}</tr>`;
                    }).join('');

                    let report_title = report.report_name || "System Report";

                    let print_window = window.open('', '_blank');
                    print_window.document.write(`
                        <html>
                            <head>
                                <title>${report_title}</title>
                                <link rel="stylesheet" href="/assets/frappe/css/desk.min.css">
                                <style>
                                    body { font-family: Arial, sans-serif; padding: 20px; color: #000; }
                                    .header-container { display: flex; align-items: center; justify-content: space-between; border-bottom: 2px solid #000; padding-bottom: 15px; margin-bottom: 20px; }
                                    .logo-left, .logo-right { width: 70px; height: auto; object-fit: contain; }
                                    .header-text { text-align: center; flex-grow: 1; margin: 0 15px; }
                                    .header-text h3 { margin: 0; font-size: 18px; font-weight: bold; }
                                    .header-text .ml-text { font-size: 14px; margin-top: 4px; font-weight: 500; }
                                    .header-text .report-title { font-size: 15px; margin-top: 6px; font-weight: bold; text-decoration: underline; }
                                    .date-section { text-align: right; font-size: 12px; margin-bottom: 10px; }
                                    table { width: 100%; border-collapse: collapse; margin-top: 10px; }
                                    th { background-color: #f4f4f4; border: 1px solid #ddd; padding: 8px; text-align: left; font-size: 13px; }
                                    td { font-size: 12px; }
                                </style>
                            </head>
                            <body>
                                <div class="header-container">
                                    <img src="/files/Slis_logo.png" class="logo-left" alt="SLIS Logo">
                                    <div class="header-text">
                                        <h3>${org_name}</h3>
                                        <div class="ml-text">മണ്ണ് പരിശോധനാ മണ്ണ് സംരക്ഷണ വകുപ്പ്<br>കേരളസർക്കാർ</div>
                                        <div class="report-title">${report_title}</div>
                                    </div>
                                    <img src="/files/kerala_govt_logo.png" class="logo-right" alt="Kerala Govt Logo">
                                </div>
                                <div class="date-section">
                                    <strong>Date:</strong> ${currentDate}
                                </div>
                                <table>
                                    <thead>
                                        <tr>${headers_html}</tr>
                                    </thead>
                                    <tbody>
                                        ${rows_html}
                                    </tbody>
                                </table>
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
        });
    }
};