# Copyright (c) 2023, Kossivi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from erpplus.utils import get_batch_qty_2

class SalesReconciliation(Document):
	
	@frappe.whitelist()
	def generate_invoice(self):
		if frappe.db.exists("Sales Invoices", {"sales_reconciliation": self.name}):
			frappe.throw("An invoice exists already for this Sales closing!")
			
		invoice_details = []
		temp_batches = []
		for i in self.items:
			if i.sales == 0:
				continue

			max_qty = i.sales
			#batches = frappe.db.get_list("Batch", fields=["name", "batch_qty"], filters={"item":i.item, "batch_qty": [">",0]}, order_by="manufacturing_date asc, batch_qty desc")
			batches = get_batch_qty_2(warehouse=self.warehouse, item_code = i.item, posting_date = self.date, posting_time = "23:55")

			for b in batches:
				t_batch = frappe._dict({"batch_no" : b.batch_no,"item_code":i.item, "qty": b.qty})
				temp_batches.append(t_batch)

			item_code = i.item
			filtered_batches = [d for d in temp_batches if d["item_code"] == item_code]

			for b in filtered_batches:
				if not b.qty:
					continue
				if b.qty <= 0:
					continue

				while b.qty > 0 and max_qty > 0:
					if b.qty >= max_qty:
						details = frappe._dict({
							"item_code": i.item,
							"qty": max_qty,
							"batch_no": b.batch_no,
							"doctype": "Sales Invoice Item",
						})
						invoice_details.append(details)
						b.qty -= max_qty
						max_qty = 0
						temp_batches[temp_batches.index(b)] = b
						break
					else:
						details = frappe._dict({
							"item_code": i.item,
							"qty": b.qty,
							"batch_no": b.batch_no,
							"doctype": "Sales Invoice Item",
						})
						invoice_details.append(details)
						max_qty = max_qty - b.qty
						b.qty = 0
						temp_batches[temp_batches.index(b)] = b

			if max_qty > 0:
				details = frappe._dict({
					"item_code": i.item,
					"qty": max_qty,
					"doctype": "Sales Invoice Item",
				})
				invoice_details.append(details)

		args = frappe._dict(
			{
				"customer": self.customer,
				"company": self.company,
				"set_posting_time": 1,
				#"posting_date": self.date,
				#"posting_time": "23:55",
				"currency": self.currency,
				"branch": self.branch,
				"set_warehouse": self.warehouse,
				"doctype": "Sales Invoice",
				"docstatus": 0,
				"update_stock": 1,
				"sales_reconciliation": self.name,
				"items": invoice_details,
			}
		)

		if invoice_details:
			tax = frappe._dict({
				"charge_type": "On Net Total",
				"account_head": "VAT 15% - AHW",
				"description": "VAT 15% @ 15.0",
				"rate": 15.0,
				"doctype": "Sales Taxes and Charges",
			})
			args.update({"taxes": [tax]})
			sale = frappe.get_doc(args)
			sale.insert()
			#sale.save()

	@frappe.whitelist()
	def get_items(self):
		if self.warehouse:
			items = frappe.db.sql(
				"""
					SELECT item_code, warehouse, actual_qty as qty
					FROM tabBin
					WHERE warehouse = %s
				""",(self.warehouse), as_dict = 1
			)
			
			self.items.clear()
			for i in items :
				self.append('items',{
						"item": i.item_code,
						"initial_stock": i.qty,
						"final_stock": 0,
						"sales": i.qty,
					}
				)
		else:
			frappe.throw("Enter a Warehouse!")
