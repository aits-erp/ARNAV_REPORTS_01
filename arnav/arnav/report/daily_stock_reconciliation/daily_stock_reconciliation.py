import frappe


def execute(filters=None):

    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns():

    return [

        {"label": "Item", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 220},

        {"label": "Opening", "fieldname": "opening", "fieldtype": "Float", "width": 120},

        {"label": "Stock In", "fieldname": "stock_in", "fieldtype": "Float", "width": 120},

        {"label": "Stock Out", "fieldname": "stock_out", "fieldtype": "Float", "width": 120},

        {"label": "Sales Return", "fieldname": "sales_return", "fieldtype": "Float", "width": 120},

        {"label": "Closing", "fieldname": "closing", "fieldtype": "Float", "width": 120},

    ]


def get_data(filters):

    date = filters.get("date")
    warehouse = filters.get("warehouse")

    stock = frappe.db.sql("""

        SELECT

            sle.item_code,

            SUM(CASE
                WHEN sle.posting_date < %(date)s
                THEN sle.actual_qty
                ELSE 0
            END) as opening,

            SUM(CASE
                WHEN sle.posting_date = %(date)s
                AND sle.actual_qty > 0
                THEN sle.actual_qty
                ELSE 0
            END) as stock_in,

            SUM(CASE
                WHEN sle.posting_date = %(date)s
                AND sle.actual_qty < 0
                THEN ABS(sle.actual_qty)
                ELSE 0
            END) as stock_out,

            SUM(CASE
                WHEN sle.posting_date = %(date)s
                AND sle.voucher_type = 'Sales Invoice'
                AND sle.actual_qty > 0
                THEN sle.actual_qty
                ELSE 0
            END) as sales_return

        FROM `tabStock Ledger Entry` sle

        WHERE sle.warehouse = %(warehouse)s

        GROUP BY sle.item_code

    """, filters, as_dict=True)


    data = []

    total_opening = 0
    total_in = 0
    total_out = 0
    total_return = 0
    total_close = 0


    for row in stock:

        closing = row.opening + row.stock_in - row.stock_out

        data.append({

            "item_code": row.item_code,
            "opening": row.opening,
            "stock_in": row.stock_in,
            "stock_out": row.stock_out,
            "sales_return": row.sales_return,
            "closing": closing

        })

        total_opening += row.opening
        total_in += row.stock_in
        total_out += row.stock_out
        total_return += row.sales_return
        total_close += closing


    data.append({

        "item_code": "Grand Total",
        "opening": total_opening,
        "stock_in": total_in,
        "stock_out": total_out,
        "sales_return": total_return,
        "closing": total_close

    })


    return data