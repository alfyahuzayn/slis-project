// console.log("SOIL SAMPLE LIST JS LOADED");

// setInterval(() => {ved

//     if (
//         !cur_list ||
//         cur_list.doctype !==
//         "Soil Sample Collection"
//     ) {
//         return;
//     }

//     // BUTTON ALREADY EXISTS

//     if (
//         $(".custom-move-test-btn")
//         .length
//     ) {
//         return;
//     }

//     console.log("ADDING BUTTON");

//     let button =
//         cur_list.page.add_inner_button(

//             __("Move to Test"),

//             function () {

//                 frappe.msgprint(
//                     "Button Working"
//                 );
//             }
//         );

//     $(button).addClass(
//         "custom-move-test-btn"
//     );

//     console.log("BUTTON ADDED");

// }, 2000);



console.log("SOIL SAMPLE LIST JS LOADED");

setInterval(() => {

    if (
        !cur_list ||
        cur_list.doctype !==
        "Soil Sample Collection"
    ) {
        return;
    }

    // BUTTON ALREADY EXISTS

    if (
        $(".custom-move-test-btn")
        .length
    ) {
        return;
    }

    console.log("ADDING BUTTON");

    let button =
        cur_list.page.add_inner_button(

            __("Move to Test"),

            async function () {

                console.log("BUTTON CLICKED");
                

                let selected =
                    cur_list.get_checked_items();

                if (
                    !selected ||
                    selected.length === 0
                ) {

                    frappe.msgprint(
                        "Please select at least one sample"
                    );

                    return;
                }

                

                

                // =====================================
        // FETCH FULL DOCS
        // =====================================

        let children_docs = [];
        window.last_selected_samples = [];

        for (let item of selected) {

            let doc =
                await frappe.db.get_doc(
                    "Soil Sample Collection",
                    item.name
                );
                // =====================================
                // FARMER PARENT:
                // If its children are also selected,
                // skip parent and send only children.
                // =====================================
                // =====================================
                // FARMER
                // number_of_samples > 1:
                // parent should NOT move to test
                // =====================================
                if (
                    doc.client_type === "Farmer" &&
                    !doc.parent_sample &&
                    Number(doc.number_of_samples || 0) > 1
                ) {
                    continue;
                }

            children_docs.push(doc);
        }


        // =====================================
        // CHECK LAB CODE BEFORE MOVE TO TEST
        // =====================================

        let missing_lab_codes = [];

        for (let doc of children_docs) {
            

            let lab_code = "";

            // =====================================
            // FARMER
            // Lab Code is stored in own sample_data
            // =====================================
            // =====================================
            // FARMER
            // =====================================
            if (doc.client_type === "Farmer") {

                let farmer_row =
                    (doc.sample_data || [])[0];

                // First try Sample Data row.
                // If row lab_code is empty, use parent document lab_code.
                lab_code =
                    farmer_row?.lab_code ||
                    doc.lab_code ||
                    "";

                values_json =
                    farmer_row?.values_json ||
                    "{}";

                console.log("FARMER BULK RESULT:", {
                    name: doc.name,
                    doc_lab_code: doc.lab_code,
                    farmer_row: farmer_row,
                    final_lab_code: lab_code,
                    values_json: values_json
                });
            }

            // =====================================
            // DEPARTMENT / CONSULTANCY CHILD
            // =====================================
            else if (doc.parent_sample) {

                let parent_doc =
                    await frappe.db.get_doc(
                        "Soil Sample Collection",
                        doc.parent_sample
                    );

                console.log(
                    "CHILD:",
                    doc.name
                );

                console.log(
                    "REFERENCE SAMPLE ID:",
                    doc.reference_sample_id
                );

                console.log(
                    "PARENT SAMPLE DATA:",
                    parent_doc.sample_data
                );

                // First try matching Sample ID
                let matched_row = null;

                if (doc.client_type === "Consultancy") {

                    // Example:
                    // CS-TVM-a-00001-3 -> row 3
                    let match =
                        (doc.reference_sample_id || "")
                            .match(/-(\d+)$/);

                    if (match) {

                        let row_number =
                            parseInt(match[1]);

                        matched_row =
                            (parent_doc.sample_data || [])[row_number - 1];
                    }

                } else {

                    // Department - keep existing behaviour
                    matched_row =
                        (parent_doc.sample_data || []).find(
                            row =>
                                row.sample_id ===
                                doc.reference_sample_id
                        );
                }
                // If found, take Lab Code
                if (matched_row) {

                    lab_code =
                        (matched_row.lab_code || "").trim();
                }

                // =====================================
                // FALLBACK
                // Check child's own sample_data
                // =====================================
                if (!lab_code) {

                    let own_row =
                        (doc.sample_data || [])[0];

                    if (own_row) {

                        lab_code =
                            (own_row.lab_code || "").trim();
                    }
                }

                console.log(
                    "FINAL LAB CODE:",
                    doc.name,
                    lab_code
                );
            }

            // =====================================
            // PARENT SELECTED DIRECTLY
            // =====================================
            else {

                let sample_rows =
                    doc.sample_data || [];

                let empty_rows =
                    sample_rows.filter(
                        row =>
                            !(row.lab_code || "").trim()
                    );

                if (empty_rows.length > 0) {

                    empty_rows.forEach(row => {

                        missing_lab_codes.push(
                            row.sample_id || doc.name
                        );
                    });

                    continue;
                }

                lab_code =
                    sample_rows.length
                        ? "VALID"
                        : "";
            }

            // =====================================
            // ONLY ADD IF REALLY MISSING
            // =====================================
            if (!lab_code) {

                missing_lab_codes.push(
                    doc.reference_sample_id ||
                    doc.name
                );
            }
        }


        // =====================================
        // STOP MOVE TO TEST IF ANY LAB CODE
        // IS MISSING
        // =====================================

        if (missing_lab_codes.length > 0) {

            let unique_missing =
                [...new Set(missing_lab_codes)];

            frappe.msgprint({
                title: __("Reminder"),
                indicator: "orange",
                message:
                    __("Please fill Lab Code for the selected sample(s) before clicking Move to Test.")
                    + "<br><br><b>Sample(s):</b> "
                    + unique_missing.join(", ")
            });

            return;
        }

      

                // =====================================
                // GROUP BY PARENT
                // =====================================

                let parent_map = {};

                for (let doc of children_docs) {

                    let parent_name =
                        doc.parent_sample || doc.name;

                    if (!parent_map[parent_name]) {

                        parent_map[parent_name] = [];
                    }

                    parent_map[parent_name].push(doc);
                }
   
                // =====================================
                // PROCESS EACH PARENT
                // =====================================
                let valid_count = 0;

                for (let item of selected) {

                    let doc = await frappe.db.get_doc(
                        "Soil Sample Collection",
                        item.name
                    );

                    valid_count++;
                }

                

                
                let moved_count = 0;
                let done = 0;

                for (
                    let parent_name of
                    Object.keys(parent_map)
                ) {

                    let child_docs =
                        parent_map[parent_name];

                    let parent_doc =
                        await frappe.db.get_doc(
                            "Soil Sample Collection",
                            parent_name
                        );

                   

                    // =====================================
                    // SAVE SELECTED SAMPLES
                    // =====================================

                   

                    selected.forEach(row => {

                        let row_name = row.name;

                        // Parent skip cheyyuka
                        if (row_name === parent_name) {
                            return;
                        }

                        if (
                            !window.last_selected_samples.includes(
                                row_name
                            )
                        ) {

                            window.last_selected_samples.push(
                                row_name
                            );
                        }
                    });

                    // Single sample case
                    if (
                        window.last_selected_samples.length === 0 &&
                        selected.length === 1
                    ) {

                        window.last_selected_samples.push(
                            parent_name
                        );
                    }

                    if (parent_doc.moved_to_test == 1) {

                        let proceed =
                            await new Promise(resolve => {

                                frappe.confirm(
                                    `${parent_name} is already moved to test.<br><br>Do you want to update the existing test result?`,
                                    () => resolve(true),
                                    () => resolve(false)
                                );
                            });

                        if (!proceed) {

                            frappe.show_alert({
                                message: `${parent_name} skipped`,
                                indicator: "orange"
                            });

                            continue;
                        }
                    }
                    if (done === 0) {
                        frappe.show_progress(
                            "Moving to Test...",
                            0,
                            valid_count
                        );
                    }
                                                                            
                    // CHECK EXISTING TEST RESULT
                    // =====================================

                    let existing_list =
                        await frappe.db.get_list(
                            "Soil Test Result",
                            {
                                filters: {
                                    main_sample_id:
                                        parent_name
                                },

                                fields: ["name"],

                                limit: 1
                            }
                        );

                    let test_result_doc;

                    // =====================================
                    // EXISTING RESULT
                    // =====================================

                    if (
                        existing_list &&
                        existing_list.length > 0
                    ) { 

                        // =====================================
                        // LOAD EXISTING DOC
                        // =====================================

                        test_result_doc =
                            await frappe.db.get_doc(
                                "Soil Test Result",
                                existing_list[0].name
                            );


                        frappe.show_alert({

                            message:
                                `${parent_name} existing data updated`,

                            indicator:
                                "blue"
                        });

                    } else {

                        // =====================================
                        // CREATE NEW TEST RESULT
                        // =====================================

                        await frappe.model.with_doctype(
                            "Soil Test Result"
                        );

                        test_result_doc =
                            frappe.model.get_new_doc(
                                "Soil Test Result"
                            );

                        // BASIC FIELDS

                        test_result_doc.main_sample_id =
                            parent_name;

                        test_result_doc.client =
                            parent_doc.client;

                        test_result_doc.client_type =
                            parent_doc.client_type;

                        test_result_doc.latitude =
                            parent_doc.latitude;

                        test_result_doc.longitude =
                            parent_doc.longitude;

                        test_result_doc.plot_size =
                            parent_doc.plot_size;

                        test_result_doc.name_of_type =
                            parent_doc.name_of_type;

                        test_result_doc.type_of_collection =
                            parent_doc.type_of_collection;

                        test_result_doc.number_of_sample =
                            parent_doc.number_of_samples;

                        test_result_doc.lab_code_prefix =
                            parent_doc.lab_code_prefix;

                        test_result_doc.lab_code_start =
                            parent_doc.lab_code_start;

                        test_result_doc.test_sample_data = [];
                    }

                    // =====================================
                    // EXISTING SAMPLE IDS
                    // =====================================

                    let existing_sample_ids =
                        (
                            test_result_doc
                            .test_sample_data || []
                        ).map(
                            r => r.sample_id
                        );

                    // =====================================
                    // CLIENT TYPE
                    // =====================================

                    let is_consultancy =
                        (
                            parent_doc.client_type || ""
                        ) === "Consultancy";

                    let is_farmer =
                        (
                            parent_doc.client_type || ""
                        ) === "Farmer";

                    // =====================================
                    // LOOP CHILD DOCS
                    // =====================================

                    for (
                        let child_doc of child_docs
                    ) {

                        let ref_id =
                            child_doc
                            .reference_sample_id || "";

                      
// FARMER
                        // Sample ID = reference_sample_id
                        // Lab Code = matching parent sample_data row
                        // =====================================
                        if (is_farmer) {

                            let reference_id =
                                child_doc.reference_sample_id || "";

                            // FS-TVM-ust-00052-1 -> 1
                            // FS-TVM-ust-00052-2 -> 2
                            // FS-TVM-ust-00052-3 -> 3
                            let match =
                                reference_id.match(/-(\d+)$/);

                            let matched_row = null;

                            if (match) {

                                let row_number =
                                    parseInt(match[1], 10);

                                matched_row =
                                    (parent_doc.sample_data || [])
                                        [row_number - 1];
                            }

                            // Child row only as fallback
                            let own_row =
                                (child_doc.sample_data || [])[0];

                            let final_sample_id =
                                reference_id ||
                                child_doc.name;

                            let final_lab_code =
                                matched_row?.lab_code ||
                                own_row?.lab_code ||
                                child_doc.lab_code ||
                                "";

                            let final_values_json =
                                matched_row?.values_json ||
                                own_row?.values_json ||
                                "{}";

                            console.log("FARMER MOVE TO TEST:", {
                                child: child_doc.name,
                                reference_id: reference_id,
                                matched_row: matched_row,
                                final_sample_id: final_sample_id,
                                final_lab_code: final_lab_code
                            });

                            if (
                                existing_sample_ids.includes(
                                    final_sample_id
                                )
                            ) {
                                let existing_row =
                                    test_result_doc.test_sample_data.find(
                                        row => row.sample_id === final_sample_id
                                    );

                                if (existing_row) {
                                    existing_row.lab_code = final_lab_code;
                                    existing_row.values_json = final_values_json;
                                }

                                continue;
                            }

                            if (
                                !test_result_doc.test_sample_data
                            ) {
                                test_result_doc.test_sample_data = [];
                            }

                            test_result_doc.test_sample_data.push({

                                sample_id:
                                    final_sample_id,

                                lab_code:
                                    final_lab_code,
                                
                               

                                values_json:
                                    final_values_json
                            });

                            existing_sample_ids.push(
                                final_sample_id
                            );

                            continue;
                        }
                        // =====================================
                        // DEPARTMENT / CONSULTANCY
                        // =====================================

                        // =====================================
                        // DEPARTMENT / CONSULTANCY
                        // =====================================

                        let matched_row = null;

                        if (is_consultancy) {

                            // =====================================
                            // CONSULTANCY ONLY
                            // reference_sample_id:
                            // CS-TVM-a-00051-1
                            // CS-TVM-a-00051-2
                            // CS-TVM-a-00051-3
                            // =====================================

                            let consultancy_ref_id =
                                child_doc.reference_sample_id || "";

                            console.log(
                                "CONSULTANCY CHILD:",
                                child_doc.name
                            );

                            console.log(
                                "CONSULTANCY REFERENCE SAMPLE ID:",
                                consultancy_ref_id
                            );

                            // Get last number from reference_sample_id
                            let match =
                                consultancy_ref_id.match(/-(\d+)$/);

                            if (match) {

                                let row_number =
                                    parseInt(match[1], 10);

                                // Get corresponding row from PARENT
                                matched_row =
                                    (parent_doc.sample_data || [])
                                        [row_number - 1];
                            }

                            console.log(
                                "CONSULTANCY PARENT SAMPLE DATA:",
                                parent_doc.sample_data
                            );

                            console.log(
                                "CONSULTANCY MATCHED ROW:",
                                matched_row
                            );

                        } else {

                            // =====================================
                            // DEPARTMENT - NO CHANGE
                            // =====================================

                            matched_row =
                                (parent_doc.sample_data || []).find(
                                    r => r.sample_id === ref_id
                                );
                        }

                        if (!matched_row)
                            continue;


                        // =====================================
                        // SAMPLE ID
                        // =====================================

                        let row_sample_id =
                            is_consultancy
                                ? child_doc.reference_sample_id
                                : matched_row.sample_id;


                        // =====================================
                        // SKIP DUPLICATE
                        // =====================================

                        if (
                            existing_sample_ids.includes(
                                row_sample_id
                            )
                        ) {
                            let existing_row =
                                test_result_doc.test_sample_data.find(
                                    row => row.sample_id === row_sample_id
                                );

                            if (existing_row) {
                                existing_row.lab_code =
                                    matched_row.lab_code;

                                existing_row.depth =
                                    (
                                        parent_doc.client_type === "Department" &&
                                        /\(\d+\/\d+\)$/.test(
                                            matched_row.sample_id || ""
                                        )
                                    )
                                        ? (matched_row.depth || "")
                                        : "";

                                existing_row.reference_name =
                                    is_consultancy
                                        ? (matched_row.reference_name || "")
                                        : "";

                                existing_row.values_json =
                                    matched_row.values_json || "{}";
                            }

                            continue;
                        }


                        if (
                            !test_result_doc.test_sample_data
                        ) {

                            test_result_doc.test_sample_data = [];
                        }


                        // =====================================
                        // ADD TO SOIL TEST RESULT
                        // =====================================

                        test_result_doc.test_sample_data.push({

                            sample_id:
                                row_sample_id,

                            lab_code:
                                matched_row.lab_code,

                            // DEPTH ONLY FOR DEPARTMENT PROFILE SAMPLES
                            depth:
                                (
                                    parent_doc.client_type === "Department" &&
                                    /\(\d+\/\d+\)$/.test(
                                        matched_row.sample_id || ""
                                    )
                                )
                                    ? (matched_row.depth || "")
                                    : "",
                            reference_name:
                                is_consultancy
                                    ? (matched_row.reference_name || "")
                                    : "",

                            values_json:
                                matched_row.values_json || "{}"
                        });


                        existing_sample_ids.push(
                            row_sample_id
                        );

                        
                    }

                    // =====================================
                    // SAVE / INSERT
                    // =====================================

                    if (
                        existing_list &&
                        existing_list.length > 0
                    ) {

                        await frappe.call({

                            method:
                                "frappe.client.save",

                            args: {
                                doc:
                                    test_result_doc
                            }
                        });

                        frappe.show_alert({

                            message:
                                "Soil Test Result Updated",

                            indicator:
                                "green"
                        });

                    } else {

                        await frappe.call({

                            method:
                                "frappe.client.insert",

                            args: {
                                doc:
                                    test_result_doc
                            }
                        });

                        frappe.show_alert({

                            message:
                                "Soil Test Result Created",

                            indicator:
                                "green"
                        });
                    }

                    // =====================================
                    // UPDATE STATUS
                    // =====================================
                    for (let child_doc of child_docs) {

                        await frappe.db.set_value(
                            "Soil Sample Collection",
                            child_doc.name,
                            {
                                status: "With Research Assistant",
                                moved_to_test: 1,
                                lab_name: parent_doc.target_lab
                            }
                        );
                    }
                    await frappe.db.set_value(
                        "Soil Sample Collection",
                        parent_name,
                        {
                            status: "With Research Assistant",
                            moved_to_test: 1,
                            lab_name: parent_doc.target_lab
                        }
                    );
                    frappe.show_alert({
                        message: `${parent_name} moved to test successfully`,
                        indicator: "green"
                    });
                    moved_count++;

                    done += child_docs.length;

                    frappe.show_progress(
                        "Moving to Test...",
                        done,
                        valid_count
                    );
                }

               frappe.hide_progress();

                if (moved_count > 0) {

                    frappe.msgprint({
                        title: __("Move To Test Completed"),
                        indicator: "green",
                        message: `${moved_count} sample(s) moved successfully`
                    });
                    

                }
                

                cur_list.refresh();

                setTimeout(() => {

                    if (window.last_selected_samples) {

                        window.last_selected_samples.forEach(name => {

                            cur_list.$result
                                .find(`input[data-name="${name}"]`)
                                .prop("checked", true)
                                .trigger("change");
                        });
                    }

                }, 2500);
            }
        );

        $(button).addClass(
        "custom-move-test-btn"
    );

//     cur_list.page.add_action_item(
//     __("Sample Verification Completed"),

//     async function () {

//         let selected =
//             cur_list.get_checked_items();

//         if (
//             !selected ||
//             selected.length === 0
//         ) {

//             frappe.msgprint(
//                 __("Please select at least one sample")
//             );

//             return;
//         }

//         let updated_count = 0;

//         for (let item of selected) {

//             let doc =
//                 await frappe.db.get_doc(
//                     "Soil Sample Collection",
//                     item.name
//                 );

//             if (doc.verified_physical_sample) {
//                 continue;
//             }

//             await frappe.db.set_value(
//                 "Soil Sample Collection",
//                 doc.name,
//                 {
//                     verified_physical_sample: 1
//                 }
//             );

//             updated_count++;
//         }

//         frappe.show_alert({
//             message:
//                 `${updated_count} sample(s) verified successfully`,
//             indicator: "green"
//         });

//         cur_list.refresh();
//     }
// );
  
    // =====================================
    // BULK RESULT ENTRY BUTTON
    // =====================================

    if (!$(".custom-bulk-result-btn").length) {

        let bulk_button =
            cur_list.page.add_inner_button(

                __("Bulk Result Entry"),

                async function () {

                    let selected =
                        cur_list.get_checked_items();

                    if (
                        (!selected || selected.length === 0) &&
                        window.last_selected_samples
                    ) {
                        selected =
                            window.last_selected_samples.map(
                                name => ({ name })
                            );
                    }

                    if (!selected || selected.length === 0) {
                        frappe.msgprint(
                            "Please select at least one sample"
                        );
                        return;
                    }

                    await frappe.model.with_doctype(
                        "Bulk Result Entry"
                    );

                    let bulk_doc =
                        frappe.model.get_new_doc(
                            "Bulk Result Entry"
                        );

                    bulk_doc.sample_data = [];
                    bulk_doc.client_type = "";
                    

                    for (let item of selected) {

                        let doc =
                            await frappe.db.get_doc(
                                "Soil Sample Collection",
                                item.name
                            );


                        // CONSULTANCY CLIENT TYPE FOR BULK RESULT
                        if (doc.client_type === "Consultancy") {
                            bulk_doc.client_type = "Consultancy";
}
                        // Farmer => Parent only
                        

                        if (!doc.verified_physical_sample) {

                            frappe.msgprint(
                                `${doc.name} : Verified Physical Sample must be checked`
                            );

                            return;
                        }

                        if (!doc.moved_to_test) {

                            frappe.msgprint(
                                `${doc.name} : Please click Move To Test first`
                            );

                            return;
                        }

                        if (
                            doc.status !==
                            "With Research Assistant"
                        ) {

                            frappe.msgprint(
                                `${doc.name} : Status must be Research Assistant`
                            );

                            return;
                        }

                        
                        // Parent selected -> skip
                        // Parent with child samples -> skip
                        if (
                            doc.client_type !== "Farmer" &&
                            !doc.parent_sample &&
                            doc.sample_data &&
                            doc.sample_data.length > 1
                        ) {
                            continue;
                        }
                        // Department / Consultancy parent -> skip
                        if (
                            doc.client_type === "Farmer" &&
                            !doc.parent_sample &&
                            Number(doc.number_of_samples || 0) > 1
                        ) {
                            continue;
                        }
                                            
                        let lab_code = "";
                        let values_json = "{}";
                        let sample_id = "";
                        let variant_reference = "";
                        let reference_name = "";


                        // =====================================
                        // FARMER CHILD
                        // Sample ID = reference_sample_id
                        // Full Lab Code = parent's matching row
                        // =====================================
                        if (
                            doc.client_type === "Farmer" &&
                            doc.parent_sample
                        ) {

                            let parent_doc =
                                await frappe.db.get_doc(
                                    "Soil Sample Collection",
                                    doc.parent_sample
                                );

                            let reference_id =
                                doc.reference_sample_id || "";

                            // Example:
                            // FS-TVM-ust-00052-1 -> 1
                            // FS-TVM-ust-00052-2 -> 2
                            // FS-TVM-ust-00052-3 -> 3
                            let match =
                                reference_id.match(/-(\d+)$/);

                            let matched_row = null;

                            if (match) {

                                let row_number =
                                    parseInt(match[1], 10);

                                matched_row =
                                    (parent_doc.sample_data || [])
                                        [row_number - 1];
                            }

                            console.log(
                                "FARMER REFERENCE ID:",
                                reference_id
                            );

                            console.log(
                                "FARMER PARENT SAMPLE DATA:",
                                parent_doc.sample_data
                            );

                            console.log(
                                "FARMER MATCHED ROW:",
                                matched_row
                            );

                            let own_row =
                                (doc.sample_data || [])[0];

                            // IMPORTANT
                            // Sample ID comes from child reference_sample_id
                            sample_id =
                                reference_id ||
                                doc.name;

                            variant_reference =
                                reference_id ||
                                doc.name;

                            // IMPORTANT
                            // Full Lab Code comes FIRST from parent row
                            lab_code =
                                matched_row?.lab_code ||
                                own_row?.lab_code ||
                                doc.lab_code ||
                                "";

                            values_json =
                                matched_row?.values_json ||
                                own_row?.values_json ||
                                "{}";

                            console.log(
                                "FARMER FINAL:",
                                {
                                    sample_id: sample_id,
                                    lab_code: lab_code,
                                    matched_row: matched_row
                                }
                            );
                        }


                        // =====================================
                        // CONSULTANCY / DEPARTMENT CHILD
                        // =====================================
                        else if (doc.parent_sample) {

                            let parent_doc =
                                await frappe.db.get_doc(
                                    "Soil Sample Collection",
                                    doc.parent_sample
                                );

                            let matched_row = null;

                            if (doc.client_type === "Consultancy") {

                                // Consultancy:
                                // CS-TVM-a-00001-2 -> row 2
                                let match =
                                    (doc.reference_sample_id || "")
                                        .match(/-(\d+)$/);

                                if (match) {

                                    let row_number =
                                        parseInt(match[1]);

                                    matched_row =
                                        (parent_doc.sample_data || [])[row_number - 1];
                                }

                            } else {

                                // Department - existing logic unchanged
                                matched_row =
                                    (parent_doc.sample_data || []).find(
                                        row =>
                                            row.sample_id ===
                                            doc.reference_sample_id
                                    );
                            }

                            console.log(
                                "REFERENCE SAMPLE:",
                                doc.reference_sample_id
                            );

                            console.log(
                                "MATCHED PARENT ROW:",
                                matched_row
                            );

                            // Parent row found
                            if (matched_row) {

                                sample_id =
                                    doc.client_type === "Consultancy"
                                        ? (doc.reference_sample_id || "")
                                        : (
                                            doc.reference_sample_id ||
                                            matched_row.sample_id
                                        );

                                variant_reference =
                                    doc.reference_sample_id ||
                                    doc.name;

                                lab_code =
                                    matched_row.lab_code ||
                                    "";

                                values_json =
                                    matched_row.values_json ||
                                    "{}";

                                // CONSULTANCY ONLY
                                if (doc.client_type === "Consultancy") {

                                    reference_name =
                                        matched_row.reference_name || "";
                                }
                            }


                            // Child's own sample_data fallback
                            if (
                                !matched_row ||
                                !lab_code ||
                                !values_json ||
                                values_json === "{}"
                            ) {

                                let own_row =
                                    (doc.sample_data || [])[0];

                                console.log(
                                    "CHILD OWN SAMPLE ROW:",
                                    own_row
                                );

                                if (own_row) {

                                    if (!sample_id) {
                                        sample_id =
                                            doc.reference_sample_id ||
                                            own_row.sample_id ||
                                            doc.name;
                                    }

                                    if (!variant_reference) {
                                        variant_reference =
                                            doc.reference_sample_id ||
                                            doc.name;
                                    }

                                    if (!lab_code) {
                                        lab_code =
                                            own_row.lab_code ||
                                            "";
                                    }

                                    if (
                                        !values_json ||
                                        values_json === "{}"
                                    ) {
                                        values_json =
                                            own_row.values_json ||
                                            "{}";
                                    }
                                }
                            }

                            console.log("CHILD FINAL DATA:", {
                                document: doc.name,
                                sample_id: sample_id,
                                lab_code: lab_code,
                                values_json: values_json
                            });
                        }


                        // =====================================
                        // SINGLE DOCUMENT
                        // =====================================
                        else {

                            let own_row =
                                (doc.sample_data || [])[0];

                            sample_id =
                                own_row?.sample_id ||
                                doc.name;

                            variant_reference =
                                doc.name;

                            lab_code =
                                own_row?.lab_code ||
                                doc.lab_code ||
                                "";

                            values_json =
                                own_row?.values_json ||
                                "{}";
                        }


                        // =====================================
                        // ADD ROW TO BULK RESULT ENTRY
                        // =====================================
                        bulk_doc.sample_data.push({

                            sample_id:
                                sample_id,

                            variant_reference:
                                variant_reference,
                            
                            reference_name:
                                doc.client_type === "Consultancy"
                                    ? reference_name
                                    : "",

                            lab_code:
                                lab_code,

                            values_json:
                                values_json
                        });
                    }

                    frappe.set_route(
                        "Form",
                        "Bulk Result Entry",
                        bulk_doc.name
                    );

                                    } // end async function
                                ); // end add_inner_button

                            $(bulk_button).addClass(
                                "custom-bulk-result-btn"
                            );
                        }

                     
                       
                        // =====================================
                        // MASTER/PARENT -> AUTO SELECT CHILDREN
                        // =====================================

                        $(document)
                            .off(
                                "change.master_child_select",
                                '.list-row-container input[type="checkbox"]'
                            )
                            .on(
                                "change.master_child_select",
                                '.list-row-container input[type="checkbox"]',
                                async function () {

                                    let checkbox = $(this);

                                    let checked =
                                        checkbox.prop("checked");

                                    // IMPORTANT:
                                    // Get actual Frappe document name,
                                    // NOT visible Reference Sample ID.
                                    let row_name =
                                        checkbox.attr("data-name");

                                    if (!row_name) {

                                        row_name =
                                            checkbox
                                            .closest(".list-row-container")
                                            .attr("data-name");
                                    }

                                    if (!row_name) {

                                        console.log(
                                            "Could not find document name"
                                        );

                                        return;
                                    }

                                    console.log(
                                        "ACTUAL DOCUMENT NAME:",
                                        row_name
                                    );

                                    let doc;

                                    try {

                                        doc =
                                            await frappe.db.get_doc(
                                                "Soil Sample Collection",
                                                row_name
                                            );

                                    } catch (error) {

                                        console.error(
                                            "Could not load document:",
                                            row_name,
                                            error
                                        );

                                        return;
                                    }

                                    // =====================================
                                    // FARMER -> SKIP
                                    // =====================================


                                    // =====================================
                                    // MASTER/PARENT SELECTED
                                    // =====================================

                                    if (
                                        Number(doc.is_master_sample) === 1
                                    ) {

                                        console.log(
                                            "MASTER SELECTED:",
                                            doc.name
                                        );

                                        // Find children where
                                        // parent_sample = actual parent doc.name

                                        let children =
                                            await frappe.db.get_list(
                                                "Soil Sample Collection",
                                                {
                                                    filters: {
                                                        parent_sample:
                                                            doc.name
                                                    },

                                                    fields: [
                                                        "name",
                                                        "reference_sample_id",
                                                        "status"
                                                    ],

                                                    limit: 1000
                                                }
                                            );

                                        console.log(
                                            "CHILDREN FOUND:",
                                            children
                                        );


                                        // =====================================
                                        // SELECT EACH CHILD
                                        // =====================================

                                        for (let child of children) {

                                            let child_checkbox =
                                                cur_list.$result.find(
                                                    `input[type="checkbox"][data-name="${CSS.escape(child.name)}"]`
                                                );

                                            if (!child_checkbox.length) {
                                                continue;
                                            }

                                            // =====================================
                                            // REJECTED CHILD
                                            // DO NOT SELECT
                                            // =====================================

                                            if (child.status === "Rejected") {

                                                child_checkbox
                                                    .prop("checked", false)
                                                    .trigger("change");

                                                console.log(
                                                    "REJECTED CHILD AUTO UNSELECTED:",
                                                    child.name
                                                );

                                                continue;
                                            }

                                            // =====================================
                                            // NON-REJECTED CHILD
                                            // FOLLOW PARENT SELECTION
                                            // =====================================

                                            if (
                                                child_checkbox.prop("checked") !== checked
                                            ) {

                                                child_checkbox
                                                    .prop("checked", checked)
                                                    .trigger("change");
                                            }
                                        }

                                        return;
                                    }


                                    // =====================================
                                    // CHILD SELECTED / UNSELECTED
                                    // =====================================

                                    if (doc.parent_sample) {

                                        console.log(
                                            "CHILD:",
                                            doc.name,
                                            "PARENT:",
                                            doc.parent_sample
                                        );

                                        let siblings =
                                            await frappe.db.get_list(
                                                "Soil Sample Collection",
                                                {
                                                    filters: {
                                                        parent_sample:
                                                            doc.parent_sample
                                                    },

                                                    fields: [
                                                        "name"
                                                    ],

                                                    limit: 1000
                                                }
                                            );


                                        let all_checked = true;

                                        for (
                                            let sibling of siblings
                                        ) {

                                            let sibling_checkbox =
                                                cur_list.$result.find(
                                                    `input[type="checkbox"][data-name="${CSS.escape(sibling.name)}"]`
                                                );

                                            // Child not visible
                                            if (
                                                !sibling_checkbox.length
                                            ) {

                                                all_checked = false;

                                                break;
                                            }

                                            // Child visible but unchecked
                                            if (
                                                !sibling_checkbox.prop(
                                                    "checked"
                                                )
                                            ) {

                                                all_checked = false;

                                                break;
                                            }
                                        }


                                        // =====================================
                                        // UPDATE MASTER CHECKBOX
                                        // =====================================

                                        let parent_checkbox =
                                            cur_list.$result.find(
                                                `input[type="checkbox"][data-name="${CSS.escape(doc.parent_sample)}"]`
                                            );

                                        if (
                                            parent_checkbox.length &&
                                            parent_checkbox.prop(
                                                "checked"
                                            ) !== all_checked
                                        ) {

                                            parent_checkbox.prop(
                                                "checked",
                                                all_checked
                                            );
                                        }
                                    }
                                }
                            );
                    

                        


                        console.log("BUTTON ADDED");

                        }, 2000);