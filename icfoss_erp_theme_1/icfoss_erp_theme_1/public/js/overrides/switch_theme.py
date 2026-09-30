import frappe

@frappe.whitelist()
def switch_theme(theme):
    # Add 'icfoss' to the allowed list
    if theme in ["Light", "Dark", "Automatic", "icfoss"]:
        frappe.db.set_value("User", frappe.session.user, "desk_theme", theme)