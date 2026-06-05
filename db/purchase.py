"""Registro y consulta de compras."""

from db.connection import get_db, read_sql
from db.product import add_or_update_product
from db.cashbox import cashbox_add
from utils.format import now


def register_purchase(warehouse, sku, name, category, qty, unit_cost, currency, cashbox, supplier, notes, user, fiado=False):
    if not name.strip():
        raise ValueError("El nombre del producto es obligatorio.")
    total = qty * unit_cost

    with get_db() as con:
        cur = con.cursor()
        product_id = add_or_update_product(
            cur, warehouse, sku, name, category, qty, unit_cost, currency, f"Bodega {warehouse}"
        )
        cur.execute(
            "INSERT INTO purchases(date, warehouse, product_id, sku, product_name, qty, "
            "unit_cost, total, currency, cashbox, supplier, notes, user) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (now(), warehouse, product_id, sku, name, qty, unit_cost, total,
             currency, cashbox, supplier, notes, user),
        )
        purchase_id = cur.lastrowid

        if fiado:
            # No descuenta caja, registra deuda (usando el mismo cursor)
            from db.debt import register_debt
            register_debt(
                supplier or "Proveedor", f"Compra {warehouse}: {name} x {qty}",
                total, currency, cashbox, notes, user, cur=cur,
            )
        else:
            cashbox_add(
                cur, cashbox, -total, currency, "compra", "purchases",
                purchase_id, f"Compra {warehouse}: {name} x {qty}", user,
            )
        return purchase_id


def list_purchases(warehouse=None):
    sql = ("SELECT id, date, warehouse, sku, product_name, qty, unit_cost, total, "
           "currency, cashbox, supplier, user FROM purchases WHERE active = 1")
    params = []

    if warehouse:
        sql += " AND warehouse = ?"
        params.append(warehouse)

    sql += " ORDER BY id DESC LIMIT 300"

    with get_db() as con:
        return read_sql(con, sql, params)

