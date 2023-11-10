# Copyright (c) 2023, Kossivi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.exceptions import LinkValidationError
import traceback
import csv
import os

class SalesData2(Document):
	
	def on_submit(self):
		abbr = frappe.db.get_value("Company", self.company, "abbr")
		failed_records = []
		last_num = ''
		last_billdate = ''	
		last_customername = ''
		invoice_details = []
		
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
			batches = frappe.db.get_list("Batch", fields=["name", "batch_qty"], filters={"item":d.productname, "batch_qty": [">",0]}, order_by="batch_qty desc")
			
			for b in batches:
				if b.batch_qty >= max_qty:
					details = frappe._dict({
						"item_code": d.productname,
						"qty": max_qty,
						"rate" : d.grossamount / int(d.quantity),
						"doctype": "Sales Invoice Item",
					})
					invoice_details.append(details)
					max_qty = 0
					break
				else:
					details = frappe._dict({
						"item_code": d.productname,
						"qty": b.batch_qty,
						"rate" : d.grossamount / int(d.quantity),
						"doctype": "Sales Invoice Item",
					})
					invoice_details.append(details)
					max_qty = max_qty - b.batch_qty

			if max_qty > 0:
				details = frappe._dict({
					"item_code": d.productname,
					"qty": max_qty,
					"rate" : d.grossamount / int(d.quantity),
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
