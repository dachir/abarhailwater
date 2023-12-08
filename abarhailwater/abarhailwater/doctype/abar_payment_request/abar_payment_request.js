// Copyright (c) 2023, Kossivi and contributors
// For license information, please see license.txt

frappe.ui.form.on('Abar Payment Request', {
	setup: function(frm) {
		frm.set_query("party_type", function() {
			frm.events.validate_company(frm);
			return{
				filters: {
					"name": ["in", Object.keys(frappe.boot.party_account_types)],
				}
			}
		});
		frm.set_query("bank_account", function() {
			frm.events.validate_company(frm);
			return{
				filters: {
					"party": frm.doc.party_name,
				}
			}
		});
	},
	party_type: function(frm) {
		frm.set_value("party", "")
		//frm.set_value("party_name", "")
	},
	party: function(frm) {
		frm.call("get_party_name")
	},
	validate_company: (frm) => {
		if (!frm.doc.company){
			frappe.throw({message:__("Please select a Company first."), title: __("Mandatory")});
		}
	},
});
