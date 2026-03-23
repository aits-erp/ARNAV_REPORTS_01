import frappe


def execute(filters=None):

    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns():

    return [
        {"label": "Item Group", "fieldname": "item_group", "fieldtype": "Data", "width": 140},
        {"label": "Item", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 240},
        {"label": "Opening", "fieldname": "opening", "fieldtype": "Float", "width": 120},
        {"label": "Stock In", "fieldname": "stock_in", "fieldtype": "Float", "width": 120},
        {"label": "Stock Out", "fieldname": "stock_out", "fieldtype": "Float", "width": 120},
        {"label": "Sold", "fieldname": "sold", "fieldtype": "Float", "width": 120},
        {"label": "Sales Return", "fieldname": "sales_return", "fieldtype": "Float", "width": 140},
        {"label": "Closing", "fieldname": "closing", "fieldtype": "Float", "width": 120}
    ]


def get_data(filters):

    conditions = ""

    if filters.get("warehouse"):
        conditions += " AND sle.warehouse = %(warehouse)s "

    if filters.get("item_group"):
        conditions += " AND item.item_group = %(item_group)s "

    data = frappe.db.sql(f"""

        SELECT
            item.item_group,
            sle.item_code,

            SUM(CASE WHEN sle.posting_date < %(date)s THEN sle.actual_qty ELSE 0 END) as opening,

            SUM(CASE WHEN sle.posting_date = %(date)s AND sle.actual_qty > 0 THEN sle.actual_qty ELSE 0 END) as stock_in,

            SUM(CASE WHEN sle.posting_date = %(date)s AND sle.actual_qty < 0 THEN ABS(sle.actual_qty) ELSE 0 END) as stock_out

        FROM `tabStock Ledger Entry` sle

        LEFT JOIN `tabItem` item
        ON item.name = sle.item_code

        WHERE sle.posting_date <= %(date)s
        {conditions}

        GROUP BY sle.item_code

    """, filters, as_dict=True)


    result = []

    total_open = total_in = total_out = total_sold = total_return = total_close = 0

    for row in data:

        # SOLD
        sold = frappe.db.sql("""
            SELECT COALESCE(SUM(sii.qty),0)
            FROM `tabSales Invoice Item` sii
            INNER JOIN `tabSales Invoice` si
            ON sii.parent = si.name
            WHERE sii.item_code=%s
            AND si.posting_date=%s
            AND si.docstatus=1
            AND si.is_return=0
        """, (row.item_code, filters.get("date")))[0][0]

        # SALES RETURN
        sales_return = frappe.db.sql("""
            SELECT COALESCE(SUM(sii.qty),0)
            FROM `tabSales Invoice Item` sii
            INNER JOIN `tabSales Invoice` si
            ON sii.parent = si.name
            WHERE sii.item_code=%s
            AND si.posting_date=%s
            AND si.docstatus=1
            AND si.is_return=1
        """, (row.item_code, filters.get("date")))[0][0]

        # CORRECT CLOSING (NO DOUBLE COUNT)
        closing = row.opening + row.stock_in - row.stock_out

        if row.opening or row.stock_in or row.stock_out:

            result.append({
                "item_group": row.item_group,
                "item_code": row.item_code,
                "opening": row.opening,
                "stock_in": row.stock_in,
                "stock_out": row.stock_out,
                "sold": sold,
                "sales_return": sales_return,
                "closing": closing
            })

            total_open += row.opening
            total_in += row.stock_in
            total_out += row.stock_out
            total_sold += sold
            total_return += sales_return
            total_close += closing


    # ✅ FIXED GRAND TOTAL
    result.append({
        "item_group": "",
        "item_code": "Grand Total",
        "opening": total_open,
        "stock_in": total_in,
        "stock_out": total_out,
        "sold": total_sold,
        "sales_return": total_return,
        "closing": total_close
    })

    return result