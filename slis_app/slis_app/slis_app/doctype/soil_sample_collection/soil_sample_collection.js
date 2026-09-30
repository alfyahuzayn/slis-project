// =========================
// FORM EVENTS
// =========================
frappe.ui.form.on("Soil Sample Collection", {
    refresh(frm) {

        // Top-center alert CSS
        if (!$("#top-center-alert-style").length) {
            $("head").append(`
                <style id="top-center-alert-style">
                    .alert-container {
                        top: 70px !important;
                        left: 50% !important;
                        right: auto !important;
                        bottom: auto !important;
                        transform: translateX(-50%) !important;
                    }
                </style>
            `);
        }

        console.log("Backend JS loaded");

        // Remove default Save button
        frm.page.clear_primary_action();
       

        // ── Download Template Button ───────────────────────────────
        if (
            !frm.is_new() &&
            frm.doc.sample_data &&
            frm.doc.sample_data.length > 0
        ) {
            frm.add_custom_button(
                __("Download Template"),
                function () {

                    // First check status
                    if (frm.doc.status !== "With Senior Chemist") {

                        frappe.msgprint({
                            title: __("Status Error"),
                            indicator: "red",
                            message: __(
                                "Status should be With Senior Chemist before downloading the template."
                            )
                        });

                        return;
                    }

                    // Second check Save Table Data
                    if (!frm._save_table_data_during_ra) {

                        frappe.msgprint({
                            title: __("Save Table Data Required"),
                            indicator: "orange",
                            message: __(
                                "Status is With Senior Chemist. You need to click Save Table Data before downloading the template."
                            )
                        });

                        return;
                    }

                    // Both checks passed
                    export_template(frm);
                }
            );
                        frm.add_custom_button(
                __("Import Template"),
                function () {
                    import_template(frm);
                }
            );
        }

        // ── Add Sample Button ─────────────────────────────────────
        if (!frm.is_new() && frm.doc.docstatus === 0) {
            frm.add_custom_button(
                __("Add Sample"),
                function () {
                    frappe.new_doc(
                        "Soil Sample Collection",
                        {
                            client: frm.doc.client,
                            reference_name:
                                frm.doc.reference_name
                        }
                    );
                }
            );
        }

        // ── Move to Test Button ───────────────────────────────────
        if (false) {
            frm.add_custom_button(
                __("Move to Test"),
                () => {

                    console.log(
                        "Move to Test clicked"
                    );

                    // Validation
                    if (
                        ["Department", "Consultancy"]
                            .includes(
                                frm.doc.client_type
                            ) &&
                        frm.doc.is_master_sample
                    ) {

                        frappe.msgprint({
                            title:
                                __("Selection Not Allowed"),
                            indicator:
                                "orange",
                            message:
                                __(
                                    "Only generated samples can be moved to test for Department and Consultancy clients."
                                )
                        });

                        return;
                    }

                    // Status guard
                    if (
                        frm.doc.status !==
                        "With Research Assistant"
                    ) {

                        frappe.msgprint({
                            title:
                                __("Status Error"),
                            indicator:
                                "red",
                            message:
                                __(
                                    "Either not assigned/ Completed!"
                                )
                        });

                        return;
                    }

                    // Duplicate check
                    frappe.call({
                        method:
                            "frappe.client.get_list",

                        args: {
                            doctype:
                                "Soil Test Result",

                            filters: {
                                main_sample_id:
                                    frm.doc.name
                            },

                            fields: ["name"],
                            limit_page_length: 1
                        },

                        callback: function (r) {

                            console.log(
                                "API Response:",
                                r
                            );

                            if (
                                r &&
                                r.message &&
                                r.message.length > 0
                            ) {

                                let existing_name =
                                    r.message[0].name;

                                frappe.confirm(
                                    `Soil Test Result already exists (${existing_name})<br><br>Open existing record?`,

                                    function () {
                                        frappe.set_route(
                                            "Form",
                                            "Soil Test Result",
                                            existing_name
                                        );
                                    },

                                    function () {}
                                );

                            } else {

                                create_test_result(
                                    frm
                                );

                            }
                        },

                        error: function () {

                            create_test_result(
                                frm
                            );

                        }
                    });

                }
            ).addClass("btn-primary");
        }
    }
});
// =========================
// IMPORT TEMPLATE
// =========================
async function import_template(frm) {

    await frappe.require(
        "/assets/slis_app/js/xlsx.full.min.js"
    );

    let input =
        $('<input type="file" accept=".xlsx,.xls">');

    input.on(
        "change",
        function (e) {

            let file =
                e.target.files[0];

            if (!file)
                return;

            let reader =
                new FileReader();

            reader.onload =
                function (evt) {

                    let workbook =
                        XLSX.read(
                            evt.target.result,
                            {
                                type: "binary"
                            }
                        );

                    let sheet =
                        workbook.Sheets[
                            workbook.SheetNames[0]
                        ];

                    let rows =
                        XLSX.utils
                            .sheet_to_json(
                                sheet,
                                {
                                    defval: ""
                                }
                            );

                    fill_table_from_excel(
                        frm,
                        rows
                    );
                };

            reader.readAsBinaryString(
                file
            );
        }
    );

    input.click();
}
function fill_table_from_excel(
    frm,
    rows
) {

    rows.forEach(
        excel_row => {

            let lab_code =
                excel_row["Lab Code"];

            if (!lab_code)
                return;

            let tr =
                frm.fields_dict.html
                    .$wrapper
                    .find("tbody tr")
                    .filter(function () {

                        let td_index =
                            $(this)
                                .find("td")
                                .length > 2
                                ? 1
                                : 0;

                        return (
                            $(this)
                                .find("td")
                                .eq(td_index)
                                .text()
                                .trim() ===
                            lab_code
                        );
                    });

            if (!tr.length)
                return;

            tr.find(".test-input")
                .each(function () {

                    let input =
                        $(this);

                    let test =
                        input.data(
                            "test"
                        );

                    if (
                        excel_row[test] !==
                        undefined
                    ) {

                        input.val(
                            excel_row[
                                test
                            ]
                        );

                    }
                });
        }
    );

    frappe.show_alert({
        message:
            "Excel imported successfully. Click Save Table Data.",
        indicator:
            "green"
    });
}

// =========================
// DOWNLOAD TEMPLATE
// =========================
async function export_template(frm) {

    console.log("Download Template Clicked");

    await frappe.require(
        "/assets/slis_app/js/xlsx.full.min.js"
    );

    frappe.show_alert({
        message: __("Preparing template download..."),
        indicator: "blue"
    });

    let client_type =
        (frm.doc.client_type || "")
            .toLowerCase()
            .trim();

    let is_consultancy =
        client_type === "consultancy";

    // Header
    let headers = [];

    if (!is_consultancy) {
        headers.push("Sample ID");
    }

    headers.push("Lab Code");

    if (is_consultancy) {
        headers.push("Reference Name");
    }

    // HTML table-il already kaanunna test names edukkuka
    frm.fields_dict.html.$wrapper
        .find("thead th")
        .each(function (index) {

            let text =
                $(this).text().trim();

            if (
                text !== "Sample ID" &&
                text !== "Lab Code" &&
                text !== "Reference Name"
            ) {
                headers.push(text);
            }
        });

    let data = [headers];

    // Rows
    (frm.doc.sample_data || []).forEach(
        row => {

            let row_data = [];

            if (!is_consultancy) {
                row_data.push(
                    row.sample_id || ""
                );
            }

            row_data.push(
                row.lab_code || ""
            );

            if (is_consultancy) {
                row_data.push(
                    row.reference_name || ""
                );
            }

            // Empty cells for test values
            for (
                let i =
                    headers.length -
                    row_data.length;
                i > 0;
                i--
            ) {
                row_data.push("");
            }

            data.push(row_data);
        }
    );

    const ws =
        XLSX.utils
            .aoa_to_sheet(data);

    const wb =
        XLSX.utils
            .book_new();

    XLSX.utils
        .book_append_sheet(
            wb,
            ws,
            "Sample Data"
        );

    XLSX.writeFile(
        wb,
        `${frm.doc.name}_Template.xlsx`
    );

    frappe.show_alert({
        message:
            __("Template downloaded successfully"),
        indicator:
            "green"
    }, 5);
}
// =========================
// CREATE SOIL TEST RESULT
// =========================
async function create_test_result(frm) {

    await frappe.model.with_doctype(
        "Soil Test Result"
    );

    let new_doc =
        frappe.model.get_new_doc(
            "Soil Test Result"
        );

    // Existing create_test_result code
    // ivide ningalude current code
    // exact aayi continue cheyyuka
}


// =========================
// LIST VIEW SETTINGS
// =========================
frappe.listview_settings[
    "Soil Sample Collection"
] = {

    onload(listview) {

        listview.filter_area.add([
            [
                "Soil Sample Collection",
                "is_generated_sample",
                "=",
                1
            ]
        ]);

        setTimeout(function () {
            $('[data-label="New"]').hide();
        }, 300);
    }
};


frappe.ui.form.on('Soil Sample Collection', {
    onload_post_render: function(frm) {
        // If this is a generated variant loaded from database
        if (frm.doc.is_generated_sample && !frm.is_new()) {
            // 1. Force Frappe dirty flag to false
            frm.doc.__unsaved = 0;
            
            // 2. Clear changed fields tracking list
            frm.clear_custom_buttons();
            
            // 3. Update page indicators to Saved state
            frm.dirty(false);
            frm.page.clear_indicator();
            
            if (frm.doc.workflow_state) {
                frm.page.set_indicator(frm.doc.workflow_state, 'blue');
            } else {
                frm.page.set_indicator('Saved', 'green');
            }
        }
    },

    refresh: function(frm) {
        if (frm.doc.is_generated_sample && !frm.is_new()) {
            // Prevent dynamic form field script triggers from marking unsaved
            setTimeout(function() {
                if (frm.doc.__unsaved) {
                    frm.doc.__unsaved = 0;
                    frm.dirty(false);
                }
            }, 300);
        }
    }
});