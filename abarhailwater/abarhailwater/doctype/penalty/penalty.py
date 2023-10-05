# Copyright (c) 2023, Kossivi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

class Penalty(Document):

	def on_submit(self):
		if len(self.penalty_line) > 30 or frappe.flags.enqueue_penalty_line:
				self.db_set("status", "Queued")
				frappe.enqueue(
					self.submit_penalty,
					timeout=600,
					lines=self.penalty_line,
					args=frappe._dict(),
					publish_progress=False,
				)
				frappe.msgprint(
					_("Penalties is queued. It may take a few minutes"),
					alert=True,
					indicator="blue",
				)
		else:
			self.submit_penalty(self.penalty_line, frappe._dict(), publish_progress=False)
			# since this method is called via frm.call this doc needs to be updated manually
			#self.reload()
	
	def submit_penalty(self, lines, args, publish_progress=True) :
		count = 0
		#frappe.msgprint("OK")
		for l in lines:
			#frappe.msgprint(e.employee)
			emp = frappe.get_doc('Employee', l.employee)
			emp.penalty = l.amount
			emp.save()

			count += 1
			if publish_progress:
				frappe.publish_progress(
					count * 100 / len(set(lines)),
					title=_("Updating Penalties..."),
				)
