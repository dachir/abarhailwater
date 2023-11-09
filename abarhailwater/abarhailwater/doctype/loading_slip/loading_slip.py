# Copyright (c) 2023, Kossivi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class LoadingSlip(Document):
	
    def on_submit(self):
        abbr = frappe.db.get_value("Company", self.company, "abbr")
        first_item = self.details[0]
        doctype = first_item.get("doctype")
        fieldnames = frappe.get_meta(doctype).get_valid_columns()
        product_names = fieldnames[10:24]
        args = {}
        try:
            for d in self.details:
                loading_details = []
                for n in product_names:
                    if(d.get(n)):
                        if int(d.get(n)) > 0 :
                            details = frappe._dict({
                                "s_warehouse": self.source_warehouse,
                                "t_warehouse": d.salesman + " - " + abbr,
                                "item_code": frappe.get_meta(doctype).get_label(n), 
                                "qty": int(d.get(n)),
                                "doctype": "Stock Entry Detail",
                            })
                            loading_details.append(details)

                args = frappe._dict(
                    {
                        "stock_entry_type": "Material Transfer",
                        "company": self.company,
                        "set_posting_time" : 1,
                        "posting_date": d.slipdate,
                        "from_warehouse": self.source_warehouse,
                        "branch": self.branch,
                        "doctype": "Stock Entry",
                        "docstatus": 0,
                        "loading_slip": self.name,
                        "items":loading_details,
                    }
                )

                if details :
                    #frappe.throw(str(args))
                    sale = frappe.get_doc(args)
                    sale.insert()
        except Exception as e:
            #frappe.msgprint("Error: " + str(e))
            #frappe.msgprint("Data: " +str(args))
            frappe.throw("Error: " + str(e) + "\n" + "Data: " +str(args) + "\n" + "Error occurred during Stock Entry insertion. All records are rejected.")

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
	
