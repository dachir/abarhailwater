# Copyright (c) 2023, Kossivi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class SalesData(Document):
	
    def on_submit(self):
        abbr = frappe.db.get_value("Company", self.company, "abbr")
        first_item = self.details[0]
        doctype = first_item.get("doctype")
        fieldnames = frappe.get_meta(doctype).get_valid_columns()
        product_names = fieldnames[26:40]
        try:
            for d in self.details:
                invoice_details = []
                for n in product_names:
                    if int(d.get(n)) > 0 :
                        details = frappe._dict({
                            "item_code": frappe.get_meta(doctype).get_label(n), 
                            #"description": n,
                            "qty": int(d.get(n)),
                            #"rate": item.prix,
                            "doctype": "Sales Invoice Item",
                        })
                        invoice_details.append(details)

                args = frappe._dict(
                    {
                        "customer": d.customercode,
                        "company": self.company,
                        "posting_date": d.billdate,
                        "currency": self.currency,
                        "branch": self.branch,
                        "set_warehouse": d.salesman + " - " + abbr,
                        "doctype": "Sales Invoice",
                        "docstatus": 0,
                        "update_stock": 1,
                        "sales_data": self.name,
                        "items":invoice_details,
                    }
                )

                if details :
                    #frappe.throw(str(args))
                    sale = frappe.get_doc(args)
                    sale.insert()
        except Exception as e:
            #frappe.msgprint("Error: " + str(e))
            #frappe.msgprint("Data: " +str(args))
            frappe.throw("Error: " + str(e) + "\n" + "Data: " +str(args) + "\n" + "Error occurred during Sales Invoice insertion. All records are rejected.")

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
	
                    
			
