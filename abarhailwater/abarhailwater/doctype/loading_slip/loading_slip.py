# Copyright (c) 2023, Kossivi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import traceback

class LoadingSlip(Document):
	
    def on_submit(self):
        abbr = frappe.db.get_value("Company", self.company, "abbr")
        first_item = self.details[0]
        doctype = first_item.get("doctype")
        fieldnames = frappe.get_meta(doctype).get_valid_columns()
        product_names = fieldnames[10:27]
        args = {}
        failed_records = []
        last_num = ''
        
        for d in self.details:
            last_num = d.slipno
            loading_details = []
            for n in product_names:
                if(d.get(n)):
                    if int(d.get(n)) > 0 :
                        max_qty = int(d.get(n))
                        it_code = frappe.get_meta(doctype).get_label(n)
                        item_code = it_code if it_code != 'EMPTY BOTTLE 5 GALLON' else 'EMPTY BOTTLE 5 GALLON - ABAR'
                        batches = frappe.db.get_list("Batch", fields=["name", "batch_qty"], filters={"item":item_code, "batch_qty": [">",0]}, order_by="manufacturing_date asc, batch_qty desc")
                        for b in batches:
                            if b.batch_qty >= max_qty:
                                details = frappe._dict({
                                    "s_warehouse": self.source_warehouse,
                                    "t_warehouse": d.salesman + " - " + abbr,
                                    "item_code": item_code, 
                                    "qty": max_qty,
                                    "doctype": "Stock Entry Detail",
                                })
                                loading_details.append(details)
                                max_qty = 0
                                break
                            else:
                                details = frappe._dict({
                                    "s_warehouse": self.source_warehouse,
                                    "t_warehouse": d.salesman + " - " + abbr,
                                    "item_code": item_code, 
                                    "qty": b.batch_qty,
                                    "doctype": "Stock Entry Detail",
                                })
                                loading_details.append(details)
                                max_qty = max_qty - b.batch_qty

                        if max_qty > 0:
                            details = frappe._dict({
                                "s_warehouse": self.source_warehouse,
                                "t_warehouse": d.salesman + " - " + abbr,
                                "item_code": item_code, 
                                "qty": max_qty,
                                "doctype": "Stock Entry Detail",
                            })
                            loading_details.append(details)

            args = frappe._dict(
                {
                    "stock_entry_type": "Material Transfer",
                    "company": self.company,
                    "set_posting_time" : 1,
                    "posting_date": d.slipdate,
                    "posting_time": "23:50",
                    "from_warehouse": self.source_warehouse,
                    "branch": self.branch,
                    "doctype": "Stock Entry",
                    "docstatus": 0,
                    "loading_slip": self.name,
                    "items":loading_details,
                }
            )

            if details :
                sale = frappe.get_doc(args)
                try:
                    sale.insert()
                    sale.submit()
                except Exception as e:
                    failed_records.append(args)
                    frappe.msgprint(last_num)
                    #frappe.throw("Last Error Number: " + str(last_num) + "\n" + "Data: " +str(args) + "\n" + "Insertion stopped")

                    # Send the error to log
					frappe.log_error(e)

    def on_cancel(self):
        #self.ignore_linked_doctypes = "GL Entry"

        frappe.delete_doc(
            "Stock Entry",
            frappe.db.sql_list(
                """select name from `tabStock Entry`
            where loading_slip=%s """,
                (self.name),
            ),
        )
        #self.db_set("salary_slips_created", 0)
        #self.db_set("salary_slips_submitted", 0)
        #self.set_status(update=True, status="Cancelled")
	
