// Copyright (c) 2023, Kossivi and contributors
// For license information, please see license.txt

frappe.ui.form.on('Sales Reconciliation', {
	refresh: function(frm) {
		frm.add_custom_button(__("Get Stock"), function() {
			frm.call('get_items');
		},"Utilities");
		frm.add_custom_button(__("Generate Invoice"), function() {
			frm.call('generate_invoice');
		},"Utilities");
	}
});

frappe.ui.form.on('Sales Reconciliation Items', {
	
    final_stock(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
        if(row.final_stock){
			row.sales = row.initial_stock - row.final_stock;
		}
		else{
			row.final_stock = 0;
			row.sales = row.initial_stock;
		}
        frm.refresh_field('final_stock');
        frm.refresh();
    },
});
