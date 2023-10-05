// Copyright (c) 2023, Kossivi and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Bank reporting"] = {
	"filters": [
		{
			fieldname:"Company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			reqd: 1
		},
		{
			fieldname:"Branch",
			label: __("Branch"),
			fieldtype: "Link",
			options: "Branch",
			reqd: 0
		},
		{
			fieldname:"Department",
			label: __("Department"),
			fieldtype: "Link",
			options: "Department",
			reqd: 0
		},
		{
			fieldname:"Designation",
			label: __("Designation"),
			fieldtype: "Link",
			options: "Designation",
			reqd: 0
		},
		{
			fieldname:"Payroll Period",
			label: __("Payroll Period"),
			fieldtype: "Link",
			options: "Payroll Period",
			reqd: 1,
		},
	]
};
