frappe.pages['sample-status'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Sample Status ',
		single_column: true
	});
}