"""GestiÃ³n de productos e inventario."""

import json
from db.connection import get_db, read_sql
from utils.format import now


def add_or_update_product(cur, warehouse, sku, name, category, qty, unit_cost, currency, location, attributes=None):
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

    attrs_json = json.dumps(attributes) if attributes else None

    if row:
        # Si el producto tiene los MISMOS atributos (o ambos sin atributos), aumentar stock
        existing_attrs = row["attributes"]
        same_attrs = _same_attributes(existing_attrs, attrs_json)

        if same_attrs:
            pid = row["id"]
            old_stock = row["stock"]
            old_cost = row["cost"] or 0
            new_stock = old_stock + qty
            avg_cost = ((old_stock * old_cost) + (qty * unit_cost)) / new_stock if new_stock else unit_cost
            cur.execute(
                "UPDATE products SET stock = ?, cost = ?, currency = ?, attributes = COALESCE(?, attributes) WHERE id = ?",
                (new_stock, avg_cost, currency, attrs_json, pid),
            )
            return pid
        # Si atributos son diferentes, no usar este row - buscar otro o crear nuevo

    # Buscar por nombre + atributos exactos (sin importar SKU)
    if attrs_json:
        match = cur.execute(
            "SELECT * FROM products WHERE warehouse = ? AND active = 1 AND name = ? AND attributes = ? LIMIT 1",
            (warehouse, name, attrs_json),
        ).fetchone()
        if match:
            pid = match["id"]
            old_stock = match["stock"]
            old_cost = match["cost"] or 0
            new_stock = old_stock + qty
            avg_cost = ((old_stock * old_cost) + (qty * unit_cost)) / new_stock if new_stock else unit_cost
            cur.execute(
                "UPDATE products SET stock = ?, cost = ?, currency = ? WHERE id = ?",
                (new_stock, avg_cost, currency, pid),
            )
            return pid

    # Crear nuevo producto (auto-generar SKU si no se paso uno)
    if not sku:
        new_sku = generate_sku(warehouse)
    else:
        new_sku = sku
    cur.execute(
        "INSERT INTO products(sku, name, category, stock, min_stock, cost, price, "
        "currency, location, warehouse, attributes, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (new_sku, name, category, qty, 2, unit_cost, 0, currency, location, warehouse, attrs_json, now()),
    )
    return cur.lastrowid


def _same_attributes(existing, new_json):
    """Compara dos atributos JSON. Retorna True si son iguales o ambos nulos/vacios."""
    import json
    if existing == new_json:
        return True
    if not existing and not new_json:
        return True
    if (not existing or str(existing) in ("None", "", "null", "{}")) and \
       (not new_json or str(new_json) in ("None", "", "null", "{}")):
        return True
    try:
        e = json.loads(str(existing)) if existing else {}
        n = json.loads(str(new_json)) if new_json else {}
        return e == n
    except Exception:
        return False


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


def get_product_names(warehouse):
    """Lista de nombres unicos de productos en una bodega (para catalogo)."""
    with get_db() as con:
        rows = con.execute(
            "SELECT DISTINCT name, category, attributes FROM products "
            "WHERE warehouse = ? AND active = 1 ORDER BY name",
            (warehouse,),
        ).fetchall()
        return [dict(r) for r in rows]


def add_product_to_catalog(warehouse, name, category, attributes, user):
    """
    Agrega un producto al catalogo CON stock 0 (solo como plantilla).
    attributes: dict con variantes (ej: {'modelo': 'Fat', 'capacidad': '500GB'})
    """
    import json
    with get_db() as con:
        cur = con.cursor()
        sku = generate_sku(warehouse)
        cur.execute(
            "INSERT INTO products(sku, name, category, stock, min_stock, cost, price, "
            "currency, warehouse, attributes, created_at) "
            "VALUES (?, ?, ?, 0, 1, 0, 0, ?, ?, ?, ?)",
            (sku, name.strip(), category, "COP" if warehouse != "USA" else "USD",
             warehouse, json.dumps(attributes) if attributes else None, now()),
        )
        return cur.lastrowid


def generate_sku(warehouse):
    """
    Genera el siguiente SKU automatico segun la bodega:
    - Colombia: GTX-001, GTX-002, ...
    - USA: USA-001, USA-002, ...
    - Repuestos: RPT-001, RPT-002, ...
    """
    prefixes = {
        "Colombia": "GTX",
        "USA": "USA",
        "Repuestos": "RPT",
    }
    prefix = prefixes.get(warehouse, "GTX")

    with get_db() as con:
        row = con.execute(
            "SELECT sku FROM products WHERE warehouse = ? AND sku LIKE ? "
            "ORDER BY id DESC LIMIT 1", (warehouse, f"{prefix}-%"),
        ).fetchone()
        if row and row["sku"]:
            try:
                num = int(row["sku"].replace(f"{prefix}-", "").replace("-", ""))
                return f"{prefix}-{num + 1:03d}"
            except Exception:
                pass
        return f"{prefix}-001"

