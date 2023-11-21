import frappe
import frappe.defaults
from frappe import _, qb, throw

from erpnext.accounts.utils import get_held_invoices, QueryPaymentLedger

def get_outstanding_invoices(
	party_type,
	party,
	account,
	common_filter=None,
	posting_date=None,
	min_outstanding=None,
	max_outstanding=None,
	accounting_dimensions=None,
    branch=None,
):

	ple = qb.DocType("Payment Ledger Entry")
	outstanding_invoices = []
	precision = frappe.get_precision("Sales Invoice", "outstanding_amount") or 2

	if account:
		root_type, account_type = frappe.get_cached_value(
			"Account", account, ["root_type", "account_type"]
		)
		party_account_type = "Receivable" if root_type == "Asset" else "Payable"
		party_account_type = account_type or party_account_type
	else:
		party_account_type = erpnext.get_party_account_type(party_type)

	held_invoices = get_held_invoices(party_type, party)

	common_filter = common_filter or []
	common_filter.append(ple.account_type == party_account_type)
	common_filter.append(ple.account == account)
	common_filter.append(ple.party_type == party_type)
	common_filter.append(ple.party == party)


	ple_query = QueryPaymentLedger()
    invoice_list = []
    if branch:
        invoice_list = ple_query.get_voucher_outstandings(
            common_filter=common_filter,
            posting_date=posting_date,
            min_outstanding=min_outstanding,
            max_outstanding=max_outstanding,
            get_invoices=True,
            accounting_dimensions=accounting_dimensions or [],
            branch = branch,
        )
    else :
        invoice_list = ple_query.get_voucher_outstandings(
            common_filter=common_filter,
            posting_date=posting_date,
            min_outstanding=min_outstanding,
            max_outstanding=max_outstanding,
            get_invoices=True,
            accounting_dimensions=accounting_dimensions or [],
        )

	for d in invoice_list:
		payment_amount = d.invoice_amount_in_account_currency - d.outstanding_in_account_currency
		outstanding_amount = d.outstanding_in_account_currency
		if outstanding_amount > 0.5 / (10**precision):
			if (
				min_outstanding
				and max_outstanding
				and not (outstanding_amount >= min_outstanding and outstanding_amount <= max_outstanding)
			):
				continue

			if not d.voucher_type == "Purchase Invoice" or d.voucher_no not in held_invoices:
				outstanding_invoices.append(
					frappe._dict(
						{
							"voucher_no": d.voucher_no,
							"voucher_type": d.voucher_type,
							"posting_date": d.posting_date,
							"invoice_amount": flt(d.invoice_amount_in_account_currency),
							"payment_amount": payment_amount,
							"outstanding_amount": outstanding_amount,
							"due_date": d.due_date,
							"currency": d.currency,
						}
					)
				)

	outstanding_invoices = sorted(
		outstanding_invoices, key=lambda k: k["due_date"] or getdate(nowdate())
	)
	return outstanding_invoices
    


class CustomQueryPaymentLedger(QueryPaymentLedger):

    def query_for_outstanding(self):
		"""
		Database query to fetch voucher amount and voucher outstanding using Common Table Expression
		"""

		ple = self.ple

		filter_on_voucher_no = []
		filter_on_against_voucher_no = []
		if self.vouchers:
			voucher_types = set([x.voucher_type for x in self.vouchers])
			voucher_nos = set([x.voucher_no for x in self.vouchers])

			filter_on_voucher_no.append(ple.voucher_type.isin(voucher_types))
			filter_on_voucher_no.append(ple.voucher_no.isin(voucher_nos))

			filter_on_against_voucher_no.append(ple.against_voucher_type.isin(voucher_types))
			filter_on_against_voucher_no.append(ple.against_voucher_no.isin(voucher_nos))

		# build outstanding amount filter
		filter_on_outstanding_amount = []
		if self.min_outstanding:
			if self.min_outstanding > 0:
				filter_on_outstanding_amount.append(
					Table("outstanding").amount_in_account_currency >= self.min_outstanding
				)
			else:
				filter_on_outstanding_amount.append(
					Table("outstanding").amount_in_account_currency <= self.min_outstanding
				)
		if self.max_outstanding:
			if self.max_outstanding > 0:
				filter_on_outstanding_amount.append(
					Table("outstanding").amount_in_account_currency <= self.max_outstanding
				)
			else:
				filter_on_outstanding_amount.append(
					Table("outstanding").amount_in_account_currency >= self.max_outstanding
				)

		# build query for voucher amount
		query_voucher_amount = (
			qb.from_(ple)
			.select(
				ple.account,
				ple.voucher_type,
				ple.voucher_no,
				ple.party_type,
				ple.party,
				ple.posting_date,
				ple.due_date,
				ple.account_currency.as_("currency"),
				Sum(ple.amount).as_("amount"),
				Sum(ple.amount_in_account_currency).as_("amount_in_account_currency"),
			)
			.where(ple.delinked == 0)
            .where(ple.branch.like(self.branch if self.branch else '%'))
			.where(Criterion.all(filter_on_voucher_no))
			.where(Criterion.all(self.common_filter))
			.where(Criterion.all(self.dimensions_filter))
			.where(Criterion.all(self.voucher_posting_date))
			.groupby(ple.voucher_type, ple.voucher_no, ple.party_type, ple.party)
		)

		# build query for voucher outstanding
		query_voucher_outstanding = (
			qb.from_(ple)
			.select(
				ple.account,
				ple.against_voucher_type.as_("voucher_type"),
				ple.against_voucher_no.as_("voucher_no"),
				ple.party_type,
				ple.party,
				ple.posting_date,
				ple.due_date,
				ple.account_currency.as_("currency"),
				Sum(ple.amount).as_("amount"),
				Sum(ple.amount_in_account_currency).as_("amount_in_account_currency"),
			)
			.where(ple.delinked == 0)
            .where(ple.branch.like(self.branch if self.branch else '%'))
			.where(Criterion.all(filter_on_against_voucher_no))
			.where(Criterion.all(self.common_filter))
			.groupby(ple.against_voucher_type, ple.against_voucher_no, ple.party_type, ple.party)
		)

		# build CTE for combining voucher amount and outstanding
		self.cte_query_voucher_amount_and_outstanding = (
			qb.with_(query_voucher_amount, "vouchers")
			.with_(query_voucher_outstanding, "outstanding")
			.from_(AliasedQuery("vouchers"))
			.left_join(AliasedQuery("outstanding"))
			.on(
				(AliasedQuery("vouchers").account == AliasedQuery("outstanding").account)
				& (AliasedQuery("vouchers").voucher_type == AliasedQuery("outstanding").voucher_type)
				& (AliasedQuery("vouchers").voucher_no == AliasedQuery("outstanding").voucher_no)
				& (AliasedQuery("vouchers").party_type == AliasedQuery("outstanding").party_type)
				& (AliasedQuery("vouchers").party == AliasedQuery("outstanding").party)
			)
			.select(
				Table("vouchers").account,
				Table("vouchers").voucher_type,
				Table("vouchers").voucher_no,
				Table("vouchers").party_type,
				Table("vouchers").party,
				Table("vouchers").posting_date,
				Table("vouchers").amount.as_("invoice_amount"),
				Table("vouchers").amount_in_account_currency.as_("invoice_amount_in_account_currency"),
				Table("outstanding").amount.as_("outstanding"),
				Table("outstanding").amount_in_account_currency.as_("outstanding_in_account_currency"),
				(Table("vouchers").amount - Table("outstanding").amount).as_("paid_amount"),
				(
					Table("vouchers").amount_in_account_currency - Table("outstanding").amount_in_account_currency
				).as_("paid_amount_in_account_currency"),
				Table("vouchers").due_date,
				Table("vouchers").currency,
			)
			.where(Criterion.all(filter_on_outstanding_amount))
		)

		# build CTE filter
		# only fetch invoices
		if self.get_invoices:
			self.cte_query_voucher_amount_and_outstanding = (
				self.cte_query_voucher_amount_and_outstanding.having(
					qb.Field("outstanding_in_account_currency") > 0
				)
			)
		# only fetch payments
		elif self.get_payments:
			self.cte_query_voucher_amount_and_outstanding = (
				self.cte_query_voucher_amount_and_outstanding.having(
					qb.Field("outstanding_in_account_currency") < 0
				)
			)

		# execute SQL
		self.voucher_outstandings = self.cte_query_voucher_amount_and_outstanding.run(as_dict=True)


    def get_voucher_outstandings(
		self,
		vouchers=None,
		common_filter=None,
		posting_date=None,
		min_outstanding=None,
		max_outstanding=None,
		get_payments=False,
		get_invoices=False,
		accounting_dimensions=None,
        branch=None,
	):
		"""
		Fetch voucher amount and outstanding amount from Payment Ledger using Database CTE

		vouchers - dict of vouchers to get
		common_filter - array of criterions
		min_outstanding - filter on minimum total outstanding amount
		max_outstanding - filter on maximum total  outstanding amount
		get_invoices - only fetch vouchers(ledger entries with +ve outstanding)
		get_payments - only fetch payments(ledger entries with -ve outstanding)
		"""

		self.reset()
		self.vouchers = vouchers
		self.common_filter = common_filter or []
		self.dimensions_filter = accounting_dimensions or []
		self.voucher_posting_date = posting_date or []
		self.min_outstanding = min_outstanding
		self.max_outstanding = max_outstanding
		self.get_payments = get_payments
		self.get_invoices = get_invoices
        self.branch = branch
		self.query_for_outstanding()

		return self.voucher_outstandings