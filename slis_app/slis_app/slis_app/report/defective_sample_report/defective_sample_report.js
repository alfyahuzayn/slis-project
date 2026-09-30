// frappe.query_reports["Defective Sample Report"] = {
//     "filters": [],
//     "onload": function(report) {
//         report.page.add_inner_button(__("Print Report"), function() {
//             let data = report.data;
//             if (!data || data.length === 0) {
//                 frappe.msgprint(__('No data to print'));
//                 return;
//             }

//             // Fetch current user's lab or district office name from Employee doctype
//             frappe.call({
//                 method: "frappe.client.get_value",
//                 args: {
//                     doctype: "Employee",
//                     filters: { user_id: frappe.session.user },
//                     fieldname: ["custom_lab_name", "custom_district_office_name"]
//                 },
//                 callback: function(r) {
//                     let org_name = "Soil Laboratory Information System";
//                     if (r && r.message) {
//                         org_name = r.message.custom_lab_name || r.message.custom_district_office_name || org_name;
//                     }

//                     let currentDate = new Date().toLocaleDateString('en-GB', {
//                         day: '2-digit',
//                         month: '2-digit',
//                         year: 'numeric'
//                     });

//                     let print_window = window.open('', '_blank');
//                     let rows_html = data.map(row => `
//                         <tr>
//                             <td style="border: 1px solid #ddd; padding: 8px;">${row.sample_id || ''}</td>
//                             <td style="border: 1px solid #ddd; padding: 8px;">${row.status || ''}</td>
//                             <td style="border: 1px solid #ddd; padding: 8px;">${row.remark || ''}</td>
//                             <td style="border: 1px solid #ddd; padding: 8px;">${row.date || ''}</td>
//                             <td style="border: 1px solid #ddd; padding: 8px;">${row.district || ''}</td>
//                             <td style="border: 1px solid #ddd; padding: 8px;">${row.target_lab || ''}</td>
//                         </tr>
//                     `).join('');

//                     print_window.document.write(`
//                         <html>
//                             <head>
//                                 <title>Defective Sample Report</title>
//                                 <link rel="stylesheet" href="/assets/frappe/css/desk.min.css">
//                                 <style>
//                                     body { font-family: Arial, sans-serif; padding: 20px; color: #000; }
//                                     .header-container { display: flex; align-items: center; justify-content: space-between; border-bottom: 2px solid #000; padding-bottom: 15px; margin-bottom: 20px; }
//                                     .logo-left, .logo-right { width: 70px; height: auto; object-fit: contain; }
//                                     .header-text { text-align: center; flex-grow: 1; margin: 0 15px; }
//                                     .header-text h3 { margin: 0; font-size: 18px; font-weight: bold; }
//                                     .header-text .ml-text { font-size: 14px; margin-top: 4px; font-weight: 500; }
//                                     .header-text .report-title { font-size: 15px; margin-top: 6px; font-weight: bold; text-decoration: underline; }
//                                     .date-section { text-align: right; font-size: 12px; margin-bottom: 10px; }
//                                     table { width: 100%; border-collapse: collapse; margin-top: 10px; }
//                                     th { background-color: #f4f4f4; border: 1px solid #ddd; padding: 8px; text-align: left; font-size: 13px; }
//                                     td { font-size: 12px; }
//                                 </style>
//                             </head>
//                             <body>
//                                 <div class="header-container">
//                                     <img src="/files/Slis_logo.png" class="logo-left" alt="SLIS Logo">
//                                     <div class="header-text">
//                                         <h3>${org_name}</h3>
//                                         <div class="ml-text">മണ്ണ് പരിശോധനാ മണ്ണ് സംരക്ഷണ വകുപ്പ്<br>കേരളസർക്കാർ</div>
//                                         <div class="report-title">Defective Sample Report</div>
//                                     </div>
//                                     <img src="/files/kerala_govt_logo.png" class="logo-right" alt="Kerala Govt Logo">
//                                 </div>
//                                 <div class="date-section">
//                                     <strong>Date:</strong> ${currentDate}
//                                 </div>
//                                 <table>
//                                     <thead>
//                                         <tr>
//                                             <th>Sample ID</th>
//                                             <th>Status</th>
//                                             <th>Remark</th>
//                                             <th>Date</th>
//                                             <th>District</th>
//                                             <th>Target Lab</th>
//                                         </tr>
//                                     </thead>
//                                     <tbody>
//                                         ${rows_html}
//                                     </tbody>
//                                 </table>
//                             </body>
//                         </html>
//                     `);
//                     print_window.document.close();
//                     setTimeout(() => {
//                         print_window.focus();
//                         print_window.print();
//                     }, 400);
//                 }
//             });
//         });
//     }
// };




frappe.query_reports["Defective Sample Report"] = {
    "filters": [],
    "onload": function(report) {
        report.page.add_inner_button(__("Print Report"), function() {
            let data = report.data;
            if (!data || data.length === 0) {
                frappe.msgprint(__('No data to print'));
                return;
            }

            // Fetch current user's lab or district office name from Employee doctype
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

                    let print_window = window.open('', '_blank');
                    let rows_html = data.map(row => `
                        <tr>
                            <td style="border: 1px solid #ddd; padding: 8px;">${row.sample_id || ''}</td>
                            <td style="border: 1px solid #ddd; padding: 8px;">${row.status || ''}</td>
                            <td style="border: 1px solid #ddd; padding: 8px;">${row.remark || ''}</td>
                            <td style="border: 1px solid #ddd; padding: 8px;">${row.date || ''}</td>
                            <td style="border: 1px solid #ddd; padding: 8px;">${row.district || ''}</td>
                            <td style="border: 1px solid #ddd; padding: 8px;">${row.scheme_program_name || ''}</td>
                            <td style="border: 1px solid #ddd; padding: 8px;">${row.target_lab || ''}</td>
                            <td style="border: 1px solid #ddd; padding: 8px;">${row.receiving_lab || ''}</td>
                        </tr>
                    `).join('');

                    print_window.document.write(`
                        <html>
                            <head>
                                <title>Defective Sample Report</title>
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
                                        <div class="report-title">Defective Sample Report</div>
                                    </div>
                                    <img src="/files/kerala_govt_logo.png" class="logo-right" alt="Kerala Govt Logo">
                                </div>
                                <div class="date-section">
                                    <strong>Date:</strong> ${currentDate}
                                </div>
                                <table>
                                    <thead>
                                        <tr>
                                            <th>Sample ID</th>
                                            <th>Status</th>
                                            <th>Remark</th>
                                            <th>Date</th>
                                            <th>District</th>
                                            <th>Scheme/Program Name</th>
                                            <th>Target Lab</th>
                                            <th>Receiving Lab</th>
                                        </tr>
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