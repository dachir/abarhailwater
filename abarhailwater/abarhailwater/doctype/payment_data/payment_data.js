// Copyright (c) 2023, Kossivi and contributors
// For license information, please see license.txt

frappe.ui.form.on('Payment Data', {
	setup: function(frm) {
		frm.set_query("paid_to", function() {
			frm.events.validate_company(frm);
			return {
				filters: {
					"account_type": "Cash",
					"is_group": 0,
					"company": frm.doc.company
				}
			}
		});
	},

	validate_company: (frm) => {
		if (!frm.doc.company){
			frappe.throw({message:__("Please select a Company first."), title: __("Mandatory")});
		}
	},
});
