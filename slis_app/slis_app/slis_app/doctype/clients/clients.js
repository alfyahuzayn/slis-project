// Copyright (c) 2026, navaneeth and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Clients", {
// 	refresh(frm) {

// 	},
// });

frappe.ui.form.on('Clients', {
    refresh: function(frm) {
        // Force hide on initial load of an existing document
        if (!frm.is_new() && !frm.is_dirty()) {
            frm.page.clear_primary_action();
        }
    },

    // This trigger is the most reliable for state changes
    set_dirty: function(frm) {
        // If the primary action was cleared, put it back
        if (!frm.page.has_primary_action()) {
            frm.page.set_primary_action(__('Save'), () => {
                frm.save();
            });
        }
    },

    after_save: function(frm) {
        // Immediately clear it again once the save is successful
        frm.page.clear_primary_action();
    }
});