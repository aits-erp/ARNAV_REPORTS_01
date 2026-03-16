import frappe


def execute(filters=None):

    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns():

    return [
        {"label": "Item", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 250},
        {"label": "Opening", "fieldname": "opening", "fieldtype": "Float", "width": 120},
        {"label": "Stock In", "fieldname": "stock_in", "fieldtype": "Float", "width": 120},
        {"label": "Stock Out", "fieldname": "stock_out", "fieldtype": "Float", "width": 120},
        {"label": "Closing", "fieldname": "closing", "fieldtype": "Float", "width": 120}
    ]


def get_data(filters):

    date = filters.get("date")
    warehouse = filters.get("warehouse")

    items = frappe.get_all("Item", filters={"disabled": 0}, fields=["name"])

    data = []

    total_opening = 0
    total_stock_in = 0
    total_stock_out = 0
    total_closing = 0

    for item in items:

        item_code = item.name

        # Opening Balance
        opening = frappe.db.sql("""
            SELECT COALESCE(SUM(actual_qty),0)
            FROM `tabStock Ledger Entry`
            WHERE item_code=%s
            AND warehouse=%s
            AND posting_date < %s
        """, (item_code, warehouse, date))[0][0]


        # Stock In
        stock_in = frappe.db.sql("""
            SELECT COALESCE(SUM(actual_qty),0)
            FROM `tabStock Ledger Entry`
            WHERE item_code=%s
            AND warehouse=%s
            AND posting_date=%s
            AND actual_qty > 0
        """, (item_code, warehouse, date))[0][0]


        # Stock Out
        stock_out = frappe.db.sql("""
            SELECT COALESCE(SUM(ABS(actual_qty)),0)
            FROM `tabStock Ledger Entry`
            WHERE item_code=%s
            AND warehouse=%s
            AND posting_date=%s
            AND actual_qty < 0
        """, (item_code, warehouse, date))[0][0]


        closing = opening + stock_in - stock_out


        if opening or stock_in or stock_out:

            data.append({
                "item_code": item_code,
                "opening": opening,
                "stock_in": stock_in,
                "stock_out": stock_out,
                "closing": closing
            })


            total_opening += opening
            total_stock_in += stock_in
            total_stock_out += stock_out
            total_closing += closing


    # Grand Total Row
    data.append({
        "item_code": "Grand Total",
        "opening": total_opening,
        "stock_in": total_stock_in,
        "stock_out": total_stock_out,
        "closing": total_closing
    })

    return data