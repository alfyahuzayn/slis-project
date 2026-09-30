import frappe

def execute(filters=None):
    # Get filters
    filters = filters or {}
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    scheme = filters.get("scheme")
    lab = filters.get("lab")

    columns = [
        {"label": "Serial No", "fieldname": "serial_number", "fieldtype": "Int", "width": 10},
        {"label": "Sample ID", "fieldname": "sample_id", "fieldtype": "Link", "options": "Soil Sample Collection", "width": 230},
        {"label": "Target Lab", "fieldname": "target_lab", "fieldtype": "Data", "width": 250},
        {"label": "Received Office", "fieldname": "received_office", "fieldtype": "Data", "width": 250},
        {"label": "Collection Date", "fieldname": "collection_date", "fieldtype": "Date", "width": 320},
        {"label": "Collection Program Name", "fieldname": "collection_program_name", "fieldtype": "Data", "width": 330}
    ]

    # Build conditions based on filters
    conditions = ""
    values = {}
    
    if from_date:
        conditions += " AND collection_date >= %(from_date)s"
        values["from_date"] = from_date
    if to_date:
        conditions += " AND collection_date <= %(to_date)s"
        values["to_date"] = to_date
    if scheme:
        conditions += " AND name_of_type = %(scheme)s"
        values["scheme"] = scheme
    if lab:
        conditions += " AND target_lab = %(lab)s"
        values["lab"] = lab

    # Fetch data using the conditions
    data = frappe.db.sql(f"""
        SELECT 
            name, target_lab, district_office_name, collection_date, name_of_type 
        FROM `tabSoil Sample Collection` 
        WHERE 1=1 {conditions}
        ORDER BY collection_date DESC
    """, values, as_dict=True)

    results = []
    for i, row in enumerate(data, start=1):
        results.append({
            "serial_number": i,
            "sample_id": row.name,
            "target_lab": row.target_lab,
            "received_office": row.district_office_name,
            "collection_date": row.collection_date,
            "collection_program_name": row.name_of_type
        })

    print_injection = """
    <div style="margin-bottom: 15px; text-align: right;">
        <button class="btn btn-primary btn-sm" onclick="printDepartmentReport()">Print Report</button>
    </div>
    <script>
    function printDepartmentReport() {
        let print_window = window.open('', '_blank');
        
        // Grab the actual report table directly from the DOM
        let report_table = document.querySelector('.page-content table') ? document.querySelector('.page-content table').outerHTML : '';
        
        let currentDate = new Date().toLocaleDateString('en-GB', {
            day: '2-digit', month: '2-digit', year: 'numeric'
        });

        print_window.document.write(`
            <html>
                <head>
                    <title>Department Samples Source Report</title>
                    <link rel="stylesheet" href="/assets/frappe/css/desk.min.css">
                    <style>
                        @page { size: landscape; margin: 10mm; }
                        body { font-family: Arial, sans-serif; padding: 15px; color: #000; }
                        .header-container { display: flex; align-items: center; justify-content: space-between; border-bottom: 2px solid #000; padding-bottom: 10px; margin-bottom: 15px; }
                        .logo-left, .logo-right { width: 60px; height: auto; object-fit: contain; }
                        .header-text { text-align: center; flex-grow: 1; margin: 0 15px; }
                        .header-text h3 { margin: 0; font-size: 16px; font-weight: bold; }
                        .header-text .ml-text { font-size: 11px; margin-top: 3px; font-weight: 500; }
                        .header-text .report-title { font-size: 14px; margin-top: 5px; font-weight: bold; text-decoration: underline; }
                        .date-section { text-align: right; font-size: 11px; margin-bottom: 10px; }
                        table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 10px; }
                        th { background-color: #f4f4f4; border: 1px solid #ddd; padding: 6px; text-align: center; font-size: 10px; }
                        td { border: 1px solid #ddd; padding: 6px; text-align: center; font-size: 10px; }
                    </style>
                </head>
                <body>
                    <div class="header-container">
                        <img src="/files/Slis_logo.png" class="logo-left" alt="SLIS Logo">
                        <div class="header-text">
                            <h3>Soil Laboratory Information System</h3>
                            <div class="ml-text">മണ്ണ് പരിശോധനാ മണ്ണ് സംരക്ഷണ വകുപ്പ്<br>കേരളസർക്കാർ</div>
                            <div class="report-title">Department Samples Source Report</div>
                        </div>
                        <img src="/files/kerala_govt_logo.png" class="logo-right" alt="Kerala Govt Logo">
                    </div>
                    <div class="date-section"><strong>Date:</strong> ${currentDate}</div>
                    ${report_table}
                </body>
            </html>
        `);
        print_window.document.close();
        setTimeout(() => {
            print_window.focus();
            print_window.print();
        }, 400);
    }
    </script>
    """
    message = print_injection

    return columns, results, message