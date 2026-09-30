// =====================================================
// SOIL SAMPLE COLLECTION - REJECTION REMARK
// Uses EXISTING Actions -> Reject
// =====================================================

console.log("SOIL SAMPLE REJECTION JS LOADED");


// =====================================================
// CONFIGURATION
// =====================================================

const SOIL_SAMPLE_DOCTYPE = "Soil Sample Collection";
const REJECT_ACTION = "Reject";
const REMARK_FIELD = "custom_remarks";


// =====================================================
// GET SELECTED SAMPLE NAMES
// =====================================================

function get_selected_soil_sample_names() {

    if (
        !window.cur_list ||
        cur_list.doctype !== SOIL_SAMPLE_DOCTYPE
    ) {
        return [];
    }

    const checked_items = cur_list.get_checked_items();

    if (!checked_items) {
        return [];
    }

    return checked_items
        .map(function(item) {

            if (typeof item === "string") {
                return item;
            }

            return item.name;
        })
        .filter(Boolean);
}


// =====================================================
// SAVE REMARK INTO custom_remarks
// =====================================================

async function save_soil_sample_rejection_remark(
    sample_name,
    rejection_remark
) {

    console.log(
        "Saving remark for:",
        sample_name
    );

    await frappe.db.set_value(
        SOIL_SAMPLE_DOCTYPE,
        sample_name,
        REMARK_FIELD,
        rejection_remark
    );

    console.log(
        "Remark saved successfully:",
        sample_name
    );
}


// =====================================================
// PERFORM EXISTING WORKFLOW REJECT
// =====================================================

async function perform_soil_sample_reject(
    selected_names
) {

    console.log(
        "Executing existing workflow Reject..."
    );

    await frappe.xcall(
        "frappe.model.workflow.bulk_workflow_approval",
        {
            docnames: selected_names,
            doctype: SOIL_SAMPLE_DOCTYPE,
            action: REJECT_ACTION
        }
    );

    console.log(
        "Existing workflow Reject completed."
    );
}


// =====================================================
// SHOW REMARK POPUP
// =====================================================

function show_soil_sample_rejection_dialog(
    selected_names,
    list_view
) {

    console.log(
        "Opening rejection remark popup."
    );

    const dialog = new frappe.ui.Dialog({

        title: __("Reject Sample"),

        fields: [

            {
                fieldname: "rejection_remark",
                fieldtype: "Small Text",
                label: __("Rejection Remark"),
                reqd: 1
            }

        ],

        primary_action_label: __("Reject"),

        primary_action: async function(values) {

            // ---------------------------------------------
            // GET REMARK
            // ---------------------------------------------

            const rejection_remark =
                (values.rejection_remark || "").trim();


            // ---------------------------------------------
            // VALIDATE REMARK
            // ---------------------------------------------

            if (!rejection_remark) {

                frappe.msgprint({
                    title: __("Required"),
                    indicator: "orange",
                    message: __(
                        "Please enter a rejection remark."
                    )
                });

                return;
            }


            // ---------------------------------------------
            // DISABLE REJECT BUTTON
            // ---------------------------------------------

            dialog.get_primary_btn().prop(
                "disabled",
                true
            );


            try {

                console.log(
                    "Rejection remark:",
                    rejection_remark
                );


                // =========================================
                // STEP 1
                // SAVE REMARK TO custom_remarks
                // =========================================

                for (
                    const sample_name of selected_names
                ) {

                    await save_soil_sample_rejection_remark(
                        sample_name,
                        rejection_remark
                    );
                }


                console.log(
                    "All rejection remarks saved."
                );


                // =========================================
                // STEP 2
                // RUN EXISTING WORKFLOW REJECT
                // =========================================

                await perform_soil_sample_reject(
                    selected_names
                );


                // =========================================
                // STEP 3
                // CLOSE POPUP
                // =========================================

                dialog.hide();


                // =========================================
                // STEP 4
                // SUCCESS MESSAGE
                // =========================================

                frappe.show_alert({
                    message: __(
                        "{0} sample(s) rejected successfully",
                        [selected_names.length]
                    ),
                    indicator: "green"
                });


                // =========================================
                // STEP 5
                // REFRESH LIST
                // =========================================

                if (list_view) {

                    list_view.clear_checked_items();

                    list_view.refresh();
                }


            } catch (error) {

                console.error(
                    "REJECTION FAILED:",
                    error
                );


                frappe.msgprint({
                    title: __("Rejection Failed"),
                    indicator: "red",
                    message: __(
                        "The sample could not be rejected. Please check the browser console."
                    )
                });


                // Enable button again

                dialog.get_primary_btn().prop(
                    "disabled",
                    false
                );
            }
        }
    });


    // ---------------------------------------------
    // SHOW DIALOG
    // ---------------------------------------------

    dialog.show();
}


// =====================================================
// INTERCEPT EXISTING ACTIONS -> REJECT
// =====================================================
//
// IMPORTANT:
// We are NOT creating a new Reject action.
//
// We are catching the existing Reject menu item.
// =====================================================

function setup_soil_sample_existing_reject() {

    if (
        !window.cur_list ||
        cur_list.doctype !== SOIL_SAMPLE_DOCTYPE
    ) {
        return;
    }


    if (window.soil_sample_reject_listener_added) {
        return;
    }


    window.soil_sample_reject_listener_added = true;


    console.log(
        "Existing Reject action listener attached."
    );


    // =================================================
    // CAPTURE CLICK BEFORE FRAPPE'S DEFAULT HANDLER
    // =================================================

    document.addEventListener(
        "click",
        function(event) {

            // -----------------------------------------
            // FIND CLICKED ELEMENT
            // -----------------------------------------

            const clicked_element =
                event.target.closest(
                    ".dropdown-menu a, .dropdown-menu button"
                );


            if (!clicked_element) {
                return;
            }


            // -----------------------------------------
            // CHECK CURRENT DOCTYPE
            // -----------------------------------------

            if (
                !window.cur_list ||
                cur_list.doctype !== SOIL_SAMPLE_DOCTYPE
            ) {
                return;
            }


            // -----------------------------------------
            // GET ACTION TEXT
            // -----------------------------------------

            const action_text =
                clicked_element.innerText
                    .trim();


            // -----------------------------------------
            // ONLY INTERCEPT "REJECT"
            // -----------------------------------------

            if (action_text !== REJECT_ACTION) {
                return;
            }


            console.log(
                "EXISTING ACTION -> REJECT CLICKED"
            );


            // =========================================
            // STOP FRAPPE'S ORIGINAL REJECT HANDLER
            // =========================================

            event.preventDefault();

            event.stopPropagation();

            event.stopImmediatePropagation();


            // =========================================
            // GET SELECTED SAMPLES
            // =========================================

            const selected_names =
                get_selected_soil_sample_names();


            console.log(
                "Selected samples:",
                selected_names
            );


            // =========================================
            // CHECK SELECTION
            // =========================================

            if (
                !selected_names ||
                selected_names.length === 0
            ) {

                frappe.msgprint({
                    title: __("No Sample Selected"),
                    indicator: "orange",
                    message: __(
                        "Please select at least one sample."
                    )
                });

                return false;
            }


            // =========================================
            // OPEN OUR REMARK POPUP
            // =========================================

            show_soil_sample_rejection_dialog(
                selected_names,
                cur_list
            );


            return false;

        },
        true
    );
}


// =====================================================
// START
// =====================================================

setInterval(
    function() {

        setup_soil_sample_existing_reject();

    },
    500
);