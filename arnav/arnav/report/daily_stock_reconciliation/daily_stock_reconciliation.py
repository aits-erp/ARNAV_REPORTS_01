import frappe


def execute(filters=None):

    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns():

    return [
        {"label": "Item", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 240},
        {"label": "Opening", "fieldname": "opening", "fieldtype": "Float", "width": 120},
        {"label": "Stock In", "fieldname": "stock_in", "fieldtype": "Float", "width": 120},
        {"label": "Stock Out", "fieldname": "stock_out", "fieldtype": "Float", "width": 120},
        {"label": "Sold", "fieldname": "sold", "fieldtype": "Float", "width": 120},
        {"label": "Sales Return", "fieldname": "sales_return", "fieldtype": "Float", "width": 140},
        {"label": "Closing", "fieldname": "closing", "fieldtype": "Float", "width": 120}
    ]


def get_data(filters):

    date = filters.get("date")
    warehouse = filters.get("warehouse")

    items = frappe.get_all("Item", filters={"disabled": 0}, fields=["name"])

    data = []

    total_open = 0
    total_in = 0
    total_out = 0
    total_sold = 0
    total_return = 0
    total_close = 0

    for item in items:

        item_code = item.name

        # Opening
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


        # Sold (using qty NOT weight)
        sold = frappe.db.sql("""
            SELECT COALESCE(SUM(sii.qty),0)
            FROM `tabSales Invoice Item` sii
            INNER JOIN `tabSales Invoice` si
                ON sii.parent = si.name
            WHERE sii.item_code=%s
            AND sii.warehouse=%s
            AND si.docstatus=1
            AND si.is_return=0
            AND si.posting_date=%s
        """, (item_code, warehouse, date))[0][0]


        # Sales Return
        sales_return = frappe.db.sql("""
            SELECT COALESCE(SUM(sii.qty),0)
            FROM `tabSales Invoice Item` sii
            INNER JOIN `tabSales Invoice` si
                ON sii.parent = si.name
            WHERE sii.item_code=%s
            AND sii.warehouse=%s
            AND si.docstatus=1
            AND si.is_return=1
            AND si.posting_date=%s
        """, (item_code, warehouse, date))[0][0]


        # Final Closing Formula
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

            total_open += opening
            total_in += stock_in
            total_out += stock_out
            total_sold += sold
            total_return += sales_return
            total_close += closing


    # Grand Total Row
    data.append({
        "item_code": "Grand Total",
        "opening": total_open,
        "stock_in": total_in,
        "stock_out": total_out,
        "sold": total_sold,
        "sales_return": total_return,
        "closing": total_close
    })


    return data