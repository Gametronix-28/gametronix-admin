"""GestiÃ³n de productos e inventario."""

from db.connection import get_db, read_sql
from utils.format import now


def add_or_update_product(cur, warehouse, sku, name, category, qty, unit_cost, currency, location):
    if sku:
        row = cur.execute(
            "SELECT * FROM products WHERE warehouse = ? AND active = 1 AND sku = ? LIMIT 1",
            (warehouse, sku),
        ).fetchone()
    else:
        row = None
    if not row:
        row = cur.execute(
            "SELECT * FROM products WHERE warehouse = ? AND active = 1 AND name = ? LIMIT 1",
            (warehouse, name),
        ).fetchone()

    if row:
        pid = row["id"]
        old_stock = row["stock"]
        old_cost = row["cost"] or 0
        new_stock = old_stock + qty
        avg_cost = ((old_stock * old_cost) + (qty * unit_cost)) / new_stock if new_stock else unit_cost
        cur.execute(
            "UPDATE products SET stock = ?, cost = ?, currency = ? WHERE id = ?",
            (new_stock, avg_cost, currency, pid),
        )
        return pid

    cur.execute(
        "INSERT INTO products(sku, name, category, stock, min_stock, cost, price, "
        "currency, location, warehouse, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (sku or None, name, category, qty, 2, unit_cost, 0, currency, location, warehouse, now()),
    )
    return cur.lastrowid


def list_inventory(warehouse=None, q=""):
    sql = ("SELECT id, sku, name, category, stock, min_stock, cost, price, "
           "currency, location, warehouse FROM products WHERE active = 1")
    params = []

    if warehouse:
        sql += " AND warehouse = ?"
        params.append(warehouse)
    if q:
        sql += " AND (sku LIKE ? OR name LIKE ? OR category LIKE ? OR location LIKE ?)"
        like = f"%{q}%"
        params += [like, like, like, like]

    sql += " ORDER BY name"

    with get_db() as con:
        return read_sql(con, sql, params)


def generate_sku(warehouse):
    """Genera el siguiente SKU automatico: GTX-001, GTX-002, ..."""
    with get_db() as con:
        row = con.execute(
            "SELECT sku FROM products WHERE warehouse = ? AND sku LIKE 'GTX-%' "
            "ORDER BY id DESC LIMIT 1", (warehouse,)
        ).fetchone()
        if row and row["sku"]:
            try:
                num = int(row["sku"].replace("GTX-", "").replace("-", ""))
                return f"GTX-{num + 1:03d}"
            except Exception:
                pass
        return "GTX-001"

