# Copyright (c) 2023, Kossivi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

class Commission(Document):
	def on_submit(self):
		if len(self.commission_line) > 30 or frappe.flags.enqueue_commission_line:
				self.db_set("status", "Queued")
				frappe.enqueue(
					self.submit_Commission,
					timeout=600,
					lines=self.commission_line,
					args=frappe._dict(),
					publish_progress=False,
				)
				frappe.msgprint(
					_("Commissions is queued. It may take a few minutes"),
					alert=True,
					indicator="blue",
				)
		else:
			self.submit_Commission(self.commission_line, frappe._dict(), publish_progress=False)
			# since this method is called via frm.call this doc needs to be updated manually
			#self.reload()
	
	def submit_Commission(self, lines, args, publish_progress=True) :
		count = 0
		#frappe.msgprint("OK")
		for l in lines:
			#frappe.msgprint(e.employee)
			emp = frappe.get_doc('Employee', l.employee)
			emp.commission = l.amount
			emp.save()

			count += 1
			if publish_progress:
				frappe.publish_progress(
					count * 100 / len(set(lines)),
					title=_("Updating Commissions..."),
				)
