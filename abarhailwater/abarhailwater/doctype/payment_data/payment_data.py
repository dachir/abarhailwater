# Copyright (c) 2023, Kossivi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class PaymentData(Document):
	
	def on_submit(self):
		try:
			for d in self.details:
				args = frappe._dict(
					{
						"doctype": "Payment Entry",
						"payment_type": "Receive",
						"company": self.company,
						"posting_date": frappe.utils.getdate(d.receipt_date),
						#"currency": self.currency,
						"mode_of_payment": "Cash",
						"paid_to": self.paid_to,
						"party_type": "Customer",
						"party": d.customer_code,
						"paid_amount":d.paid_amount,
						"received_amount":d.paid_amount,
						"branch":self.branch,
						"reference_no": d.receipt_no,
						"reference_date": frappe.utils.getdate(d.receipt_date),
						"payment_data": self.name,
					}
				)
				payment = frappe.get_doc(args)
				payment.insert()
		except Exception as e:
			#frappe.msgprint("Error: " + str(e))
			#frappe.msgprint("Data: " +str(args))
			frappe.throw("Error: " + str(e) + "\n" + "Data: " +str(args) + "\n" + "Error occurred during Payment Entry insertion. All records are rejected.")

	def on_cancel(self):
        #self.ignore_linked_doctypes = "GL Entry"

		frappe.delete_doc(
			"Payment Entry",
			frappe.db.sql_list(
				"""select name from `tabPayment Entry`
			where payment_data=%s """,
				(self.name),
			),
		)
        #self.db_set("salary_slips_created", 0)
        #self.db_set("salary_slips_submitted", 0)
        #self.set_status(update=True, status="Cancelled")
