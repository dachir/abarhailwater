# Copyright (c) 2023, Kossivi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.exceptions import LinkValidationError
import traceback
import csv
import os

class SalesData(Document):
	
    def on_submit(self):
        abbr = frappe.db.get_value("Company", self.company, "abbr")
        first_item = self.details[0]
        doctype = first_item.get("doctype")
        fieldnames = frappe.get_meta(doctype).get_valid_columns()
        product_names = fieldnames[26:40]

        # Create a list to store the failed records
        failed_records = []
        failed_numbers = []
        num = ''

        for d in self.details:
            try:
                num = d.billno
                invoice_details = []
                for n in product_names:
                    if int(d.get(n)) > 0:
                        max_qty = int(d.get(n))
                        item_code = frappe.get_meta(doctype).get_label(n)
                        batches = frappe.db.get_list("Batch", fields=["name", "batch_qty"], filters={"item":item_code, "batch_qty": [">",0]}, order_by="batch_qty desc")
                        for b in batches:
                            if b.batch_qty >= max_qty:
                                details = frappe._dict({
                                    "item_code": item_code,
                                    "qty": max_qty,
                                    "doctype": "Sales Invoice Item",
                                })
                                invoice_details.append(details)
                                max_qty = 0
                                break
                            else:
                                details = frappe._dict({
                                    "item_code": item_code,
                                    "qty": b.batch_qty,
                                    "doctype": "Sales Invoice Item",
                                })
                                invoice_details.append(details)
                                max_qty = max_qty - b.batch_qty

                        if max_qty > 0:
                            details = frappe._dict({
                                "item_code": item_code,
                                "qty": max_qty,
                                "doctype": "Sales Invoice Item",
                            })
                            invoice_details.append(details)


                args = frappe._dict(
                    {
                        "customer": d.customercode,
                        "company": self.company,
                        "set_posting_time": 1,
                        "posting_date": d.billdate,
                        "currency": self.currency,
                        "branch": self.branch,
                        "set_warehouse": d.salesman + " - " + abbr,
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
                    
            except Exception as e:
                # Add the failed record to the list
                failed_records.append(args)
                frappe.msgprint(num)

                # Send the error to log
                frappe.log_error(e)

        # Create a CSV file to store failed records
        frappe.msgprint(str(failed_records))
        if failed_records:
            csv_file_path = os.path.join(frappe.get_site_path("public", "files"), "failed_sales_data.csv")

            with open(csv_file_path, "w", newline="") as csv_file:
                csv_writer = csv.DictWriter(csv_file, fieldnames=args.keys())
                csv_writer.writeheader()
                csv_writer.writerows(failed_records)

    def on_cancel(self):
        #self.ignore_linked_doctypes = "GL Entry"

        frappe.delete_doc(
            "Sales Invoice",
            frappe.db.sql_list(
                """select name from `tabSales Invoice`
            where sales_data=%s """,
                (self.name),
            ),
        )
        #self.db_set("salary_slips_created", 0)
        #self.db_set("salary_slips_submitted", 0)
        #self.set_status(update=True, status="Cancelled")
	
                    
			
