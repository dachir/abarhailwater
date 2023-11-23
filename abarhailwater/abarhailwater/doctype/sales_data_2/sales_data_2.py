# Copyright (c) 2023, Kossivi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.exceptions import LinkValidationError
import traceback
import csv
import os
from erpnext.stock.doctype.batch.batch import get_batch_qty

class SalesData2(Document):
	
	def on_submit(self):
		abbr = frappe.db.get_value("Company", self.company, "abbr")
		failed_records = []
		last_num = ''
		last_billdate = ''	
		last_customername = ''
		invoice_details = []
		temp_batches = []
		
		for d in self.details:
			
			if last_num != d.custno:
				if invoice_details:
					customer_names = last_customername.split()
					code = last_customername
					if customer_names[0].isnumeric():
						code = customer_names[0]
						
						args = frappe._dict(
							{
								"customer": code,
								"company": self.company,
								"set_posting_time": 1,
								"posting_date": frappe.utils.getdate(last_billdate),
								"posting_time": "23:50",
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
					else:
						args = frappe._dict(
							{
								"customer": code,
								"company": self.company,
								"set_posting_time": 1,
								"posting_date": frappe.utils.getdate(last_billdate),
								"posting_time": "23:50",
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

					tax = frappe._dict({
						"charge_type": "On Net Total",
						"account_head": "VAT 15% - AHW",
						"description": "VAT 15% @ 15.0",
						"rate": 15.0,
						"doctype": "Sales Taxes and Charges",
					})
					args.update({"taxes": [tax]})
					sale = frappe.get_doc(args)
					try:
						sale.insert()
						sale.submit()
					except Exception as e:
						# Add the failed record to the list
						failed_records.append(args)
						frappe.msgprint(last_num)

						# Send the error to log
						frappe.log_error(e)

				invoice_details = []
				
			last_num = d.custno	
			last_billdate = d.billdate	
			last_customername = d.customername

			max_qty = int(d.quantity)
			#batches = frappe.db.get_list("Batch", fields=["name", "batch_qty"], filters={"item":d.productname, "batch_qty": [">",0]}, order_by="manufacturing_date asc, batch_qty desc")
			batches = get_batch_qty(warehouse=self.warehouse, item_code = d.productname, posting_date = frappe.utils.getdate(last_billdate), posting_time = "23:50")
			for b in batches:
				t_batch = frappe._dict({"batch_no" : b.batch_no,"item_code":d.productname, "batch_qty": b.qty})
				temp_batches.append(t_batch)

			filtered_batches = [d for d in temp_batches if d["item_code"] == d.productname]

			for b in filtered_batches:
				if not b.qty:
					continue
				if b.qty <= 0:
					continue

				if b.qty >= max_qty:
					details = frappe._dict({
						"item_code": d.productname,
						"qty": max_qty,
						"rate" : float(d.grossamount) / float(d.quantity),
						"doctype": "Sales Invoice Item",
					})
					invoice_details.append(details)
					b.qty -= max_qty
					max_qty = 0
					temp_batches[temp_batches.index(b)] = b
					break
				else:
					details = frappe._dict({
						"item_code": d.productname,
						"qty": b.qty,
						"rate" : float(d.grossamount) / float(d.quantity),
						"doctype": "Sales Invoice Item",
					})
					invoice_details.append(details)
					max_qty = max_qty - b.qty
					b.qty = 0
					temp_batches[temp_batches.index(b)] = b

			if max_qty > 0:
				details = frappe._dict({
					"item_code": d.productname,
					"qty": max_qty,
					"rate" : float(d.grossamount) / float(d.quantity),
					"doctype": "Sales Invoice Item",
				})
				invoice_details.append(details)

		if invoice_details:
			customer_names = last_customername.split()
			code = last_customername
			if customer_names[0].isnumeric():
				code = customer_names[0]
				
			args = frappe._dict(
				{
					"customer": code,
					"company": self.company,
					"set_posting_time": 1,
					"posting_date": frappe.utils.getdate(last_billdate),
					"posting_time": "23:00",
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
			#try:
				#sale.insert()
				#sale.submit()
			#except Exception as e:
				# Add the failed record to the list
				#failed_records.append({"Sales Data" : last_num, "Customer Name": last_customername})
				#frappe.msgprint(last_num)

				# Send the error to log
				#frappe.log_error(e)
				#frappe.throw(e)
			#finally:
			#	frappe.msgprint(str(failed_records))
				
