"""Ventas directas legacy â€” compatibilidad hacia atrÃ¡s."""

from db.connection import get_db, read_sql
from db.cashbox import cashbox_add
from utils.format import now


def register_sale(product_id, qty, unit_price, currency, cashbox, client, payment_method, notes, user):
    with get_db() as con:
        cur = con.cursor()
        p = cur.execute(
            "SELECT * FROM products WHERE id = ? AND active = 1", (product_id,)
        ).fetchone()
        if not p:
            raise ValueError("Producto no encontrado.")
        if p["stock"] < qty:
            raise ValueError("Stock insuficiente.")

        total = qty * unit_price
        unit_cost = p["cost"] or 0
        cost_total = qty * unit_cost
        profit = total - cost_total

        cur.execute(
            "INSERT INTO sales(date, product_id, sku, product_name, qty, unit_cost, "
            "unit_price, total, cost_total, profit, currency, cashbox, client, "
            "payment_method, notes, user) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (now(), product_id, p["sku"], p["name"], qty, unit_cost, unit_price,
             total, cost_total, profit, currency, cashbox, client, payment_method, notes, user),
        )
        sale_id = cur.lastrowid
        cur.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (qty, product_id))
        cashbox_add(
            cur, cashbox, total, currency, "venta", "sales",
            sale_id, f"Venta: {p['name']} x {qty}", user,
        )
        return sale_id


def list_sales(limit=100):
    with get_db() as con:
        return read_sql(con, 
            "SELECT id, date, sku, product_name, qty, unit_cost, unit_price, total, "
            "cost_total, profit, currency, cashbox, client, payment_method, notes, user "
            "FROM sales WHERE active = 1 ORDER BY id DESC LIMIT ?",
            (limit,),
        )


def list_sales_between(start, end):
    with get_db() as con:
        return read_sql(con, 
            "SELECT id, date, sku, product_name, qty, unit_price, total, cost_total, "
            "profit, client, payment_method, notes, user FROM sales "
            "WHERE active = 1 AND date(date) BETWEEN date(?) AND date(?) ORDER BY id DESC",
            (start, end),
        )

