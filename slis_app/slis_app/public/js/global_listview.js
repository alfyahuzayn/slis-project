frappe.listview_settings['*'] = {
    onload: function(listview) {
        let allowed_roles = ["Administrator", "Senior Chemist"];

        let has_permission = allowed_roles.some(role => 
            frappe.user.has_role(role)
        );

        if (!has_permission) {
            setTimeout(() => {
                $(".layout-side-section").hide();

            }, 100);
        }
    }
};