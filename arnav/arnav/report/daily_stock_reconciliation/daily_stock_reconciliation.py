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

        {"label": "Closing", "fieldname": "closing", "fieldtype": "Float", "width": 120},

    ]


def get_data(filters):

    date = filters.get("date")
    warehouse = filters.get("warehouse")

    stock = frappe.db.sql("""

        SELECT

            item_code,

            SUM(CASE
                WHEN posting_date < %(date)s
                THEN actual_qty
                ELSE 0
            END) as opening,

            SUM(CASE
                WHEN posting_date = %(date)s AND actual_qty > 0
                THEN actual_qty
                ELSE 0
            END) as stock_in,

            SUM(CASE
                WHEN posting_date = %(date)s AND actual_qty < 0
                THEN ABS(actual_qty)
                ELSE 0
            END) as stock_out

        FROM `tabStock Ledger Entry`

        WHERE warehouse = %(warehouse)s

        GROUP BY item_code

    """, filters, as_dict=True)


    data = []

    total_opening = 0
    total_in = 0
    total_out = 0
    total_close = 0


    for row in stock:

        closing = row.opening + row.stock_in - row.stock_out

        data.append({

            "item_code": row.item_code,
            "opening": row.opening,
            "stock_in": row.stock_in,
            "stock_out": row.stock_out,
            "closing": closing

        })

        total_opening += row.opening
        total_in += row.stock_in
        total_out += row.stock_out
        total_close += closing


    data.append({

        "item_code": "Grand Total",
        "opening": total_opening,
        "stock_in": total_in,
        "stock_out": total_out,
        "closing": total_close

    })


    return data