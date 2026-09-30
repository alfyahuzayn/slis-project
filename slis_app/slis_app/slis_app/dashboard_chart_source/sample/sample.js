frappe.dashboards.chart_sources["sample"] = {
    method: "slis_app.slis_app.dashboard_chart_source.sample.sample.get",
    filters: [
        {
            fieldname: "lab_name",
            label: __("Lab Name"),
            fieldtype: "Link",
            options: "Lab Name", // Ensure this matches your actual DocType name
        }
    ]
};