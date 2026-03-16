import frappe


def execute(filters=None):

    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns():

    return [

        {"label": "Month", "fieldname": "month", "fieldtype": "Data", "width": 120},

        {"label": "Item Group", "fieldname": "item_group", "fieldtype": "Data", "width": 140},

        {"label": "Item", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 200},

        {"label": "Warehouse", "fieldname": "warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 160},

        {"label": "Voucher", "fieldname": "voucher_no", "fieldtype": "Dynamic Link", "options": "voucher_type", "width": 180},

        {"label": "Opening", "fieldname": "opening", "fieldtype": "Float", "width": 120},

        {"label": "Stock In", "fieldname": "stock_in", "fieldtype": "Float", "width": 120},

        {"label": "Stock Out", "fieldname": "stock_out", "fieldtype": "Float", "width": 120},

        {"label": "Sales Return", "fieldname": "sales_return", "fieldtype": "Float", "width": 120},

        {"label": "Repair", "fieldname": "repair", "fieldtype": "Float", "width": 120},

        {"label": "Advance", "fieldname": "advance", "fieldtype": "Float", "width": 120},

        {"label": "Closing", "fieldname": "closing", "fieldtype": "Float", "width": 120},

    ]


def get_data(filters):

    conditions = ""

    if filters.get("warehouse"):
        conditions += " AND sle.warehouse = %(warehouse)s "

    data = frappe.db.sql("""

        SELECT

            DATE_FORMAT(sle.posting_date,'%%Y-%%m') as month,

            item.item_group,

            sle.item_code,

            sle.warehouse,

            sle.voucher_type,

            sle.voucher_no,

            SUM(CASE
                WHEN sle.posting_date < %(from_date)s
                THEN sle.actual_qty
                ELSE 0
            END) as opening,

            SUM(CASE
                WHEN sle.posting_date BETWEEN %(from_date)s AND %(to_date)s
                AND sle.actual_qty > 0
                THEN sle.actual_qty
                ELSE 0
            END) as stock_in,

            SUM(CASE
                WHEN sle.posting_date BETWEEN %(from_date)s AND %(to_date)s
                AND sle.actual_qty < 0
                THEN ABS(sle.actual_qty)
                ELSE 0
            END) as stock_out,

            SUM(CASE
                WHEN sle.voucher_type = 'Sales Invoice'
                AND sle.actual_qty > 0
                THEN sle.actual_qty
                ELSE 0
            END) as sales_return

        FROM `tabStock Ledger Entry` sle

        LEFT JOIN `tabItem` item
        ON item.name = sle.item_code

        WHERE sle.posting_date <= %(to_date)s

        {conditions}

        GROUP BY
            sle.item_code,
            sle.warehouse,
            month

    """.format(conditions=conditions), filters, as_dict=True)


    result = []

    total_open = total_in = total_out = total_return = total_close = 0

    for row in data:

        closing = row.opening + row.stock_in - row.stock_out

        result.append({

            "month": row.month,

            "item_group": row.item_group,

            "item_code": row.item_code,

            "warehouse": row.warehouse,

            "voucher_type": row.voucher_type,

            "voucher_no": row.voucher_no,

            "opening": row.opening,

            "stock_in": row.stock_in,

            "stock_out": row.stock_out,

            "sales_return": row.sales_return,

            "repair": 0,

            "advance": 0,

            "closing": closing

        })

        total_open += row.opening
        total_in += row.stock_in
        total_out += row.stock_out
        total_return += row.sales_return
        total_close += closing


    result.append({

        "item_code": "Grand Total",

        "opening": total_open,

        "stock_in": total_in,

        "stock_out": total_out,

        "sales_return": total_return,

        "repair": 0,

        "advance": 0,

        "closing": total_close

    })


    return result