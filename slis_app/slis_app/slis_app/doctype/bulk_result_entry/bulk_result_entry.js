

frappe.ui.form.on("Bulk Result Entry", {

    async refresh(frm) {

        if (!frm.selected_test) {
            frm.selected_test = "All";
        }

        // Cache for Soil Test Package documents
        if (!frm.test_packages) {
            frm.test_packages = {};
        }

        /*
         * IMPORTANT:
         * Initialize ALL tests using their default values.
         *
         * This means:
         * - User does NOT need to click every test tab.
         * - Default values are used automatically.
         * - Formula result is calculated automatically.
         * - values_json always contains the final result.
         */
        await initialize_all_test_results(frm);

        await render_table(frm);

        // ==========================================
        // VARIABLE VALUE CHANGE
        // ==========================================

        frm.fields_dict.html.$wrapper
            .off("input", ".cell")
            .on("input", ".cell", function () {

                let sample = $(this).data("sample");
                let test = $(this).data("test");
                let value = $(this).val();
                let key = $(this).data("key");

                let final_result = update_json(
                    frm,
                    sample,
                    test,
                    key,
                    value
                );

                /*
                 * Immediately update final value
                 * without refreshing whole table.
                 */
                $(this)
                    .closest("tr")
                    .find(".final-value")
                    .text(format_result(final_result));
            });


        // ==========================================
        // MACHINE CHANGE
        // ==========================================

        frm.fields_dict.html.$wrapper
            .off("change", ".machine-select")
            .on("change", ".machine-select", function () {

                update_machine_for_test(
                    frm,
                    frm.selected_test,
                    $(this).val()
                );
            });


        // ==========================================
        // TEST TAB CLICK
        // ==========================================

        frm.fields_dict.html.$wrapper
            .off("click", ".test-filter")
            .on("click", ".test-filter", async function () {

                frm.selected_test =
                    $(this).data("test");

                await render_table(frm);
            });
    },


    // ==========================================
    // BEFORE SAVE
    // ==========================================

    async validate(frm) {

        /*
         * Recalculate everything before actual save.
         *
         * So even if:
         * - User never opened a test
         * - Only default values exist
         * - User changed only one variable
         *
         * final result will still be correct.
         */

        await initialize_all_test_results(frm);
    },


    // ==========================================
    // AFTER SAVE
    // ==========================================

    async after_save(frm) {

        await render_table(frm);
    }
});


// ============================================================
// INITIALIZE ALL TESTS
// ============================================================

async function initialize_all_test_results(frm) {

    let rows = frm.doc.sample_data || [];

    if (!rows.length) {
        return;
    }

    if (!frm.test_packages) {
        frm.test_packages = {};
    }

    // ------------------------------------------------
    // Find every test from values_json
    // ------------------------------------------------

    let test_names = new Set();

    rows.forEach(row => {

        try {

            let obj = JSON.parse(
                row.values_json || "{}"
            );

            Object.keys(obj).forEach(test => {
                test_names.add(test);
            });

        } catch (e) {

            console.error(
                "Invalid values_json",
                row,
                e
            );
        }
    });

    test_names = Array.from(test_names);

    if (!test_names.length) {
        return;
    }


    // ------------------------------------------------
    // Load ALL Soil Test Packages
    // ------------------------------------------------

    for (const test of test_names) {

        if (!frm.test_packages[test]) {

            try {

                let package_doc =
                    await frappe.db.get_doc(
                        "Soil Test Package",
                        test
                    );

                frm.test_packages[test] =
                    package_doc;

            } catch (e) {

                console.error(
                    "Unable to load Soil Test Package:",
                    test,
                    e
                );
            }
        }
    }


    // ------------------------------------------------
    // Initialize every row + every test
    // ------------------------------------------------

    rows.forEach(row => {

        let obj = {};

        try {

            obj = JSON.parse(
                row.values_json || "{}"
            );

        } catch (e) {

            console.error(e);
            obj = {};
        }

        let changed = false;

        test_names.forEach(test => {

            let package_doc =
                frm.test_packages[test];

            if (!package_doc) {
                return;
            }

            /*
             * Convert old/simple structure into object.
             */
            if (
                !obj[test] ||
                typeof obj[test] !== "object" ||
                Array.isArray(obj[test])
            ) {

                obj[test] = {
                    machine: ""
                };

                changed = true;
            }


            // ----------------------------------------
            // Add missing DEFAULT VALUES
            // ----------------------------------------

            (package_doc.variable_table || [])
                .forEach(v => {

                    let existing =
                        obj[test][v.variable_key];

                    /*
                     * Only apply default when no saved/user value exists.
                     *
                     * IMPORTANT:
                     * 0 is considered a valid value.
                     */

                    if (
                        existing === undefined ||
                        existing === null ||
                        existing === ""
                    ) {

                        let default_value =
                            parse_number(
                                v.default_value,
                                0
                            );

                        obj[test][v.variable_key] =
                            default_value;

                        changed = true;
                    }
                });


            // ----------------------------------------
            // Calculate FINAL RESULT
            // ----------------------------------------

            let calculated_result =
                calculate_test_result(
                    package_doc,
                    obj[test]
                );

            if (
                obj[test].result !==
                calculated_result
            ) {

                obj[test].result =
                    calculated_result;

                changed = true;
            }
        });


        // ----------------------------------------
        // Update child row JSON
        // ----------------------------------------

        if (changed) {

            frappe.model.set_value(
                row.doctype,
                row.name,
                "values_json",
                JSON.stringify(obj)
            );
        }
    });
}


// ============================================================
// CALCULATE ONE TEST RESULT
// ============================================================

function calculate_test_result(
    package_doc,
    test_data
) {

    if (!package_doc) {
        return 0;
    }

    let formula =
        package_doc.formula || "";

    if (!formula.trim()) {
        return 0;
    }

    let variables =
        package_doc.variable_table || [];


    // ------------------------------------------------
    // Replace EVERY formula variable
    //
    // Priority:
    // 1. User/saved value
    // 2. Default value
    // 3. 0
    // ------------------------------------------------

    variables.forEach(v => {

        let value =
            test_data?.[v.variable_key];

        if (
            value === undefined ||
            value === null ||
            value === ""
        ) {

            value =
                parse_number(
                    v.default_value,
                    0
                );
        }

        value =
            parse_number(
                value,
                0
            );

        /*
         * Use regex word boundary so variable "A"
         * does not accidentally replace another word.
         */

        let escaped_key =
            escape_regex(v.variable_key);

        let regex =
            new RegExp(
                `\\b${escaped_key}\\b`,
                "g"
            );

        formula =
            formula.replace(
                regex,
                `(${value})`
            );
    });


    try {

        /*
         * Formula comes from trusted Soil Test Package.
         */
        let result = eval(formula);

        if (
            result === undefined ||
            result === null ||
            !Number.isFinite(Number(result))
        ) {

            return 0;
        }

        return Number(result);

    } catch (e) {

        console.error(
            "FORMULA CALCULATION ERROR",
            {
                original_formula:
                    package_doc.formula,

                calculated_formula:
                    formula,

                data:
                    test_data,

                error:
                    e
            }
        );

        return 0;
    }
}


// ============================================================
// HTML TABLE
// ============================================================

async function render_table(frm) {

    let rows =
        frm.doc.sample_data || [];

    let tests = [];

    let selected_test =
        frm.selected_test || "All";

    let package_doc = null;


    if (!frm.test_packages) {
        frm.test_packages = {};
    }


    // ------------------------------------------------
    // Get test names
    // ------------------------------------------------

    rows.forEach(row => {

        try {

            let obj = JSON.parse(
                row.values_json || "{}"
            );

            Object.keys(obj).forEach(test => {

                if (!tests.includes(test)) {
                    tests.push(test);
                }
            });

        } catch (e) {

            console.error(e);
        }
    });


    // ------------------------------------------------
    // Load selected package
    // ------------------------------------------------

    if (selected_test !== "All") {

        try {

            if (
                frm.test_packages[
                    selected_test
                ]
            ) {

                package_doc =
                    frm.test_packages[
                        selected_test
                    ];

            } else {

                package_doc =
                    await frappe.db.get_doc(
                        "Soil Test Package",
                        selected_test
                    );

                frm.test_packages[
                    selected_test
                ] = package_doc;
            }

        } catch (e) {

            console.error(
                "PACKAGE ERROR",
                e
            );
        }
    }


    // ------------------------------------------------
    // Devices
    // ------------------------------------------------

    let devices = [];

    try {

        devices =
            await frappe.db.get_list(
                "Asset",
                {
                    filters: {
                        asset_category:
                            "Devices"
                    },

                    fields: [
                        "name",
                        "asset_name"
                    ],

                    limit: 500
                }
            );

    } catch (e) {

        console.error(e);
    }


    // ------------------------------------------------
    // TEST BUTTONS
    // ------------------------------------------------

    let html = `
        <div style="margin-bottom:10px;">

            <button
                class="test-filter btn btn-xs ${
                    selected_test === "All"
                        ? "btn-primary"
                        : "btn-default"
                }"
                data-test="All"
            >
                All
            </button>
    `;


    tests.forEach(test => {

        html += `
            <button
                class="test-filter btn btn-xs ${
                    selected_test === test
                        ? "btn-primary"
                        : "btn-default"
                }"
                data-test="${escape_html(test)}"
                style="margin-left:5px;"
            >
                ${escape_html(test)}
            </button>
        `;
    });


    // ------------------------------------------------
    // SELECTED MACHINE
    // ------------------------------------------------

    let selected_machine = "";

    if (
        rows.length > 0 &&
        selected_test !== "All"
    ) {

        try {

            let first_obj =
                JSON.parse(
                    rows[0].values_json ||
                    "{}"
                );

            if (
                first_obj[selected_test] &&
                typeof
                    first_obj[selected_test]
                    === "object"
            ) {

                selected_machine =
                    first_obj[
                        selected_test
                    ].machine || "";
            }

        } catch (e) {

            console.error(e);
        }
    }


    // ------------------------------------------------
    // MACHINE SELECT
    // ------------------------------------------------

    if (selected_test !== "All") {

        html += `
            <div style="margin-top:15px; margin-bottom:15px;">

                <label>
                    <b>Machine Name</b>
                </label>

                <select
                    class="machine-select form-control"
                    style="width:300px;"
                >

                    <option value="">
                        Select Machine
                    </option>
        `;


        devices.forEach(d => {

            let machine =
                d.asset_name || "";

            html += `
                <option
                    value="${escape_html(machine)}"
                    ${
                        selected_machine ===
                        machine
                            ? "selected"
                            : ""
                    }
                >
                    ${escape_html(machine)}
                </option>
            `;
        });


        html += `
                </select>
            </div>
        `;
    }


    html += `
        </div>

        <div style="overflow:auto;">

        <table
            class="table table-bordered table-sm"
        >

        <thead>

            <tr>

                <th>Sample ID</th>

                <th>Lab Code</th>
    `;

    // ==========================================
    // REFERENCE NAME - CONSULTANCY ONLY
    // ==========================================

    if (frm.doc.client_type === "Consultancy") {

        html += `
            <th>Reference Name</th>
        `;
    }


    if (selected_test !== "All") {

        html += `
            <th>Machine Name</th>
        `;
    }


    // ------------------------------------------------
    // ALL TEST COLUMNS
    // ------------------------------------------------

    if (selected_test === "All") {

        tests.forEach(test => {

            html += `
                <th>
                    ${escape_html(test)}
                </th>
            `;
        });

    }

    // ------------------------------------------------
    // SINGLE TEST COLUMNS
    // ------------------------------------------------

    else if (package_doc) {

        (
            package_doc.variable_table ||
            []
        ).forEach(v => {

            html += `
                <th>
                    ${escape_html(
                        v.label ||
                        v.variable_key
                    )}
                </th>
            `;
        });


        html += `
            <th>Formula</th>

            <th>
                ${escape_html(
                    selected_test
                )}
            </th>
        `;
    }


    html += `
            </tr>

        </thead>

        <tbody>
    `;


    // ========================================================
    // ROWS
    // ========================================================

    rows.forEach(row => {

        let sample_id =
            row.sample_id ||
            row.variant_reference ||
            "";

        let obj = {};

        try {

            obj = JSON.parse(
                row.values_json ||
                "{}"
            );

        } catch (e) {

            console.error(e);
        }


        html += `
            <tr>

                <td>
                    ${escape_html(sample_id)}
                </td>

                <td>
                    ${escape_html(
                        row.lab_code || ""
                    )}
                </td>
        `;

        if (frm.doc.client_type === "Consultancy") {

            html += `
                <td>
                    ${escape_html(
                        row.reference_name || ""
                    )}
                </td>
            `;
        }


        if (selected_test !== "All") {

            let row_machine =
                obj[selected_test]
                    ?.machine ||
                selected_machine ||
                "";

            html += `
                <td>
                    ${escape_html(
                        row_machine
                    )}
                </td>
            `;
        }


        // ====================================================
        // SINGLE TEST VIEW
        // ====================================================

        if (
            selected_test !== "All" &&
            package_doc
        ) {

            if (
                !obj[selected_test] ||
                typeof
                    obj[selected_test]
                    !== "object"
            ) {

                obj[selected_test] = {
                    machine: ""
                };
            }


            (
                package_doc.variable_table ||
                []
            ).forEach(v => {

                let value =
                    obj[selected_test][
                        v.variable_key
                    ];

                if (
                    value === undefined ||
                    value === null ||
                    value === ""
                ) {

                    value =
                        v.default_value ?? "";
                }


                html += `
                    <td>

                        <input
                            type="number"

                            class="
                                cell
                                form-control
                                variable-input
                            "

                            data-sample="${
                                escape_html(
                                    sample_id
                                )
                            }"

                            data-test="${
                                escape_html(
                                    selected_test
                                )
                            }"

                            data-key="${
                                escape_html(
                                    v.variable_key
                                )
                            }"

                            value="${
                                escape_html(
                                    value
                                )
                            }"
                        >

                    </td>
                `;
            });


            // ----------------------------------------
            // Always calculate using current/defaults
            // ----------------------------------------

            let result =
                calculate_test_result(
                    package_doc,
                    obj[selected_test]
                );


            /*
             * Keep JSON result synchronized.
             */

            if (
                obj[selected_test].result !==
                result
            ) {

                obj[selected_test].result =
                    result;

                frappe.model.set_value(
                    row.doctype,
                    row.name,
                    "values_json",
                    JSON.stringify(obj)
                );
            }


            html += `
                <td>
                    ${
                        escape_html(
                            package_doc.formula ||
                            ""
                        )
                    }
                </td>

                <td class="final-value">
                    ${format_result(result)}
                </td>
            `;
        }


        // ====================================================
        // ALL VIEW
        // ====================================================

        else {

            tests.forEach(test => {

                let value = 0;

                if (
                    obj[test] &&
                    typeof obj[test]
                    === "object"
                ) {

                    /*
                     * IMPORTANT:
                     * Use ?? instead of ||
                     * because 0 is a valid result.
                     */

                    value =
                        obj[test].result ?? 0;

                } else {

                    value =
                        obj[test] ?? 0;
                }


                html += `
                    <td>
                        ${format_result(value)}
                    </td>
                `;
            });
        }


        html += `
            </tr>
        `;
    });


    html += `
        </tbody>

        </table>

        </div>
    `;


    frm.fields_dict.html
        .$wrapper
        .html(html);
}


// ============================================================
// UPDATE VARIABLE VALUE + AUTO CALCULATE
// ============================================================

function update_json(
    frm,
    sample,
    test,
    key,
    value
) {

    let final_result = 0;


    (frm.doc.sample_data || [])
        .forEach(row => {

            let row_sample =
                row.sample_id ||
                row.variant_reference ||
                "";


            if (row_sample != sample) {
                return;
            }


            let obj = {};

            try {

                obj = JSON.parse(
                    row.values_json ||
                    "{}"
                );

            } catch (e) {

                console.error(e);
                obj = {};
            }


            if (
                !obj[test] ||
                typeof obj[test]
                !== "object"
            ) {

                obj[test] = {
                    machine: ""
                };
            }


            // ----------------------------------------
            // Save changed value
            // ----------------------------------------

            obj[test][key] =
                parse_number(
                    value,
                    0
                );


            // ----------------------------------------
            // Get package
            // ----------------------------------------

            let package_doc =
                frm.test_packages?.[test];


            if (package_doc) {

                /*
                 * Make sure ALL missing variables
                 * receive their default values.
                 */

                (
                    package_doc.variable_table ||
                    []
                ).forEach(v => {

                    let current_value =
                        obj[test][
                            v.variable_key
                        ];

                    if (
                        current_value ===
                            undefined ||
                        current_value === null ||
                        current_value === ""
                    ) {

                        obj[test][
                            v.variable_key
                        ] =
                            parse_number(
                                v.default_value,
                                0
                            );
                    }
                });


                // ------------------------------------
                // AUTO CALCULATE FINAL VALUE
                // ------------------------------------

                final_result =
                    calculate_test_result(
                        package_doc,
                        obj[test]
                    );

                obj[test].result =
                    final_result;
            }


            // ----------------------------------------
            // Save back to values_json
            // ----------------------------------------

            frappe.model.set_value(
                row.doctype,
                row.name,
                "values_json",
                JSON.stringify(obj)
            );
        });


    frm.dirty();

    return final_result;
}


// ============================================================
// UPDATE MACHINE FOR SELECTED TEST
// ============================================================

function update_machine_for_test(
    frm,
    test,
    machine
) {

    if (
        !test ||
        test === "All"
    ) {

        return;
    }


    (frm.doc.sample_data || [])
        .forEach(row => {

            let obj = {};

            try {

                obj = JSON.parse(
                    row.values_json ||
                    "{}"
                );

            } catch (e) {

                console.error(e);
                obj = {};
            }


            if (
                !obj[test] ||
                typeof obj[test]
                !== "object"
            ) {

                obj[test] = {};
            }


            obj[test].machine =
                machine;


            /*
             * Do NOT remove/recalculate incorrectly.
             * Preserve current final result.
             */

            let package_doc =
                frm.test_packages?.[test];

            if (package_doc) {

                obj[test].result =
                    calculate_test_result(
                        package_doc,
                        obj[test]
                    );
            }


            frappe.model.set_value(
                row.doctype,
                row.name,
                "values_json",
                JSON.stringify(obj)
            );
        });


    frm.dirty();

    /*
     * Just render table.
     * No frm.trigger("refresh") needed.
     */

    render_table(frm);
}


// ============================================================
// HELPERS
// ============================================================

function parse_number(
    value,
    fallback = 0
) {

    if (
        value === undefined ||
        value === null ||
        value === ""
    ) {

        return fallback;
    }

    let number =
        parseFloat(value);

    return Number.isFinite(number)
        ? number
        : fallback;
}


function format_result(value) {

    let number =
        Number(value);

    if (!Number.isFinite(number)) {
        return 0;
    }

    /*
     * Avoid unnecessary:
     * 10.0000000001
     */

    return parseFloat(
        number.toFixed(6)
    );
}


function escape_regex(value) {

    return String(value)
        .replace(
            /[.*+?^${}()|[\]\\]/g,
            "\\$&"
        );
}


function escape_html(value) {

    return $("<div>")
        .text(
            value ?? ""
        )
        .html();
}