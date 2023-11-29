# Copyright (c) 2023, Kossivi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class AbarPaymentRequest(Document):
	
	@frappe.whitelist()
	def get_party_name(self):
		_party_name = "title" if self.party_type == "Shareholder" else self.party_type.lower() + "_name"
		if self.party:
			if frappe.db.has_column(self.party_type, _party_name):
				self.party_name = frappe.db.get_value(self.party_type, self.party, _party_name)
			else:
				self.party_name = frappe.db.get_value(self.party_type, self.party, "name")
		else:
			self.party_name = ""

