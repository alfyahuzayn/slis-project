import frappe

def clear_session_cookies():
    frappe.local.cookie_manager.delete_cookie("redirect_to")