# Copyright (c) 2023, Kossivi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class SalesReconciliation(Document):

	def on_submit(self):
		pass
		"""
		invoice_details = []
		for i in self.items:
			max_qty = i.sales
			batches = frappe.db.get_list("Batch", fields=["name", "batch_qty"], filters={"item":i.item, "batch_qty": [">",0]}, order_by="batch_qty desc")
			for b in batches:
				if b.batch_qty >= max_qty:
					details = frappe._dict({
						"item_code": i.item,
						"qty": max_qty,
						"doctype": "Sales Invoice Item",
					})
					invoice_details.append(details)
					max_qty = 0
					break
				else:
					details = frappe._dict({
						"item_code": i.item,
						"qty": b.batch_qty,
						"doctype": "Sales Invoice Item",
					})
					invoice_details.append(details)
					max_qty = max_qty - b.batch_qty

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
				"posting_date": d.date,
				"currency": self.currency,
				"branch": self.branch,
				"set_warehouse": self.warehouse,
				"doctype": "Sales Invoice",
				"docstatus": 0,
				"update_stock": 1,
				"sales_data": self.name,
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
			sale.submit()
		"""

	@frappe.whitelist()
	def get_items(self):
		if self.warehouse:
			items = frappe.db.sql(
				"""
					SELECT item_code, warehouse, actual_qty
					FROM tabBin
					WHERE warehouse = %s
				""",(self.warehouse), as_dict = 1
			)
			
			self.items.clear()
			for i in items :
				self.append('items',{
						"item": i.item_code,
						"initial_stock": i.actual_qty,
						"final_stock": 0,
						"sales": i.actual_qty,
					}
				)
		else:
			frappe.throw("Enter a Warehouse!")
