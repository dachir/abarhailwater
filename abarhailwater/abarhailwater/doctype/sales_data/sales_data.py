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

        for d in self.details:
            args = frappe._dict(
                {
                    "doctype": "Sales Invoice",
                    "company": self.company,
                    "date": d.billdate,
                    "customer": d.customercode,
                    "branch": self.branch,
                    "set_warehouse": d.salesman + " - " + abbr,
                    "update_stock": 0, #todo 1
                    "sales_data": self.name,
                }
            )
            details = []
            for n in product_names:
                if d.get(n) :
                    args_sub = frappe._dict({
                        "item": n, 
                        "qty": d.get(n), 
                    })
                    details.append(args_sub)

            args.update(
                {
                    "details": details, 
                }
            )

            if details :
                sale = frappe.get_doc(args)
                sale.insert()

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
	
                    
			
