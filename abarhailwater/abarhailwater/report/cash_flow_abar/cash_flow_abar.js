// Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.require("assets/erpnext/js/financial_statements.js", function() {
	frappe.query_reports["Cash Flow Abar"] = $.extend({},
		erpnext.financial_statements);

	erpnext.utils.add_dimensions('Cash Flow Abar', 10);

	// The last item in the array is the definition for Presentation Currency
	// filter. It won't be used in cash flow for now so we pop it. Please take
	// of this if you are working here.

	frappe.query_reports["Cash Flow Abar"]["filters"].splice(8, 1);

	frappe.query_reports["Cash Flow Abar"]["filters"].push(
		{
			"fieldname": "include_default_book_entries",
			"label": __("Include Default Book Entries"),
			"fieldtype": "Check",
			"default": 1
		}
	);
});
