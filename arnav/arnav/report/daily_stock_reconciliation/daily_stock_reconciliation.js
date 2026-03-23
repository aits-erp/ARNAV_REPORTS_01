frappe.query_reports["Daily Stock Reconciliation"] = {

    filters: [
        {
            fieldname: "date",
            label: "Date",
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
            reqd: 1
        },
        {
            fieldname: "warehouse",
            label: "Warehouse",
            fieldtype: "Link",
            options: "Warehouse",
            reqd: 1
        },
        {
            fieldname: "item_group",
            label: "Item Group",
            fieldtype: "Link",
            options: "Item Group"
        }
    ]

};