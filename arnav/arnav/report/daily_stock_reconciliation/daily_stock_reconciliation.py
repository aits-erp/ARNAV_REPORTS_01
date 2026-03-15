import frappe


def execute(filters=None):

    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns():

    return [
        {
            "label": "Item",
            "fieldname": "item_code",
            "fieldtype": "Link",
            "options": "Item",
            "width": 250
        },
        {
            "label": "Opening",
            "fieldname": "opening",
            "fieldtype": "Float",
            "width": 120
        },
        {
            "label": "Stock In",
            "fieldname": "stock_in",
            "fieldtype": "Float",
            "width": 120
        },
        {
            "label": "Stock Out",
            "fieldname": "stock_out",
            "fieldtype": "Float",
            "width": 120
        },
        {
            "label": "Sold",
            "fieldname": "sold",
            "fieldtype": "Float",
            "width": 120
        },
        {
            "label": "Sales Return",
            "fieldname": "sales_return",
            "fieldtype": "Float",
            "width": 130
        },
        {
            "label": "Closing",
            "fieldname": "closing",
            "fieldtype": "Float",
            "width": 120
        }
    ]


def get_data(filters):

    date = filters.get("date")
    warehouse = filters.get("warehouse")

    items = frappe.db.sql("""
        SELECT name
        FROM `tabItem`
        WHERE disabled = 0
    """, as_dict=True)

    data = []

    for item in items:

        item_code = item.name

        # Opening Stock
        opening = frappe.db.sql("""
            SELECT SUM(actual_qty)
            FROM `tabStock Ledger Entry`
            WHERE item_code=%s
            AND warehouse=%s
            AND posting_date < %s
        """, (item_code, warehouse, date))[0][0] or 0


        # Stock In
        stock_in = frappe.db.sql("""
            SELECT SUM(actual_qty)
            FROM `tabStock Ledger Entry`
            WHERE item_code=%s
            AND warehouse=%s
            AND posting_date=%s
            AND actual_qty > 0
        """, (item_code, warehouse, date))[0][0] or 0


        # Stock Out
        stock_out = frappe.db.sql("""
            SELECT SUM(ABS(actual_qty))
            FROM `tabStock Ledger Entry`
            WHERE item_code=%s
            AND warehouse=%s
            AND posting_date=%s
            AND actual_qty < 0
        """, (item_code, warehouse, date))[0][0] or 0


        # SOLD
        sold = frappe.db.sql("""
            SELECT SUM(sii.qty)
            FROM `tabSales Invoice Item` sii
            INNER JOIN `tabSales Invoice` si
                ON sii.parent = si.name
            WHERE sii.item_code=%s
            AND si.docstatus=1
            AND si.is_return=0
            AND si.posting_date=%s
        """, (item_code, date))[0][0] or 0


        # SALES RETURN
        sales_return = frappe.db.sql("""
            SELECT SUM(sii.qty)
            FROM `tabSales Invoice Item` sii
            INNER JOIN `tabSales Invoice` si
                ON sii.parent = si.name
            WHERE sii.item_code=%s
            AND si.docstatus=1
            AND si.is_return=1
            AND si.posting_date=%s
        """, (item_code, date))[0][0] or 0


        closing = opening + stock_in - stock_out - sold + sales_return


        if opening or stock_in or stock_out or sold or sales_return:
            data.append({
                "item_code": item_code,
                "opening": opening,
                "stock_in": stock_in,
                "stock_out": stock_out,
                "sold": sold,
                "sales_return": sales_return,
                "closing": closing
            })

    return data