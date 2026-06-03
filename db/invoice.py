"""FacturaciÃ³n Colombia: registro de facturas multi-item, consulta y detalle."""

from db.connection import get_db, read_sql
from db.cashbox import cashbox_add
from utils.format import now


def register_invoice_colombia(items, client, payment_method, invoice_notes, user):
    if not items:
        raise ValueError("Debes agregar al menos un producto a la factura.")

    with get_db() as con:
        cur = con.cursor()
        total_invoice = 0.0
        cost_invoice = 0.0
        prepared = []

        for item in items:
            product_id = int(item["product_id"])
            qty = int(item["qty"])
            unit_price = float(item["unit_price"])
            serial = item.get("serial", "")
            line_notes = item.get("notes", "")

            if qty <= 0:
                raise ValueError("La cantidad debe ser mayor a cero.")

            p = cur.execute(
                "SELECT * FROM products WHERE id = ? AND warehouse = 'Colombia' AND active = 1",
                (product_id,),
            ).fetchone()
            if not p:
                raise ValueError("Producto no encontrado en Bodega Colombia.")
            if p["stock"] < qty:
                raise ValueError(
                    f"Stock insuficiente para {p['name']}. Stock actual: {p['stock']}"
                )

            unit_cost = p["cost"] or 0
            line_total = qty * unit_price
            line_cost = qty * unit_cost
            line_profit = line_total - line_cost

            total_invoice += line_total
            cost_invoice += line_cost
            prepared.append((p, qty, unit_cost, unit_price, line_total, line_cost, line_profit, serial, line_notes))

        profit_invoice = total_invoice - cost_invoice

        cur.execute(
            "INSERT INTO invoices(date, client, payment_method, total, cost_total, profit, "
            "currency, cashbox, notes, user) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (now(), client, payment_method, total_invoice, cost_invoice, profit_invoice,
             "COP", "Caja Colombia", invoice_notes, user),
        )
        invoice_id = cur.lastrowid

        for p, qty, unit_cost, unit_price, line_total, line_cost, line_profit, serial, line_notes in prepared:
            cur.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (qty, p["id"]))
            cur.execute(
                "INSERT INTO invoice_items(invoice_id, product_id, sku, product_name, qty, "
                "unit_cost, unit_price, total, cost_total, profit, serial, notes) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (invoice_id, p["id"], p["sku"], p["name"], qty, unit_cost, unit_price,
                 line_total, line_cost, line_profit, serial, line_notes),
            )

        cashbox_add(
            cur, "Caja Colombia", total_invoice, "COP", "factura_venta",
            "invoices", invoice_id, f"Factura venta Colombia #{invoice_id}", user,
        )

        return invoice_id


def get_invoice(invoice_id):
    with get_db() as con:
        row = con.execute(
            "SELECT id, date, client, payment_method, total, cost_total, profit, "
            "currency, cashbox, notes, user FROM invoices WHERE active = 1 AND id = ?",
            (invoice_id,),
        ).fetchone()
        return dict(row) if row else None


def list_invoices(limit=100):
    with get_db() as con:
        return read_sql(con, 
            "SELECT id, date, client, payment_method, total, cost_total, profit, "
            "currency, cashbox, notes, user FROM invoices WHERE active = 1 "
            "ORDER BY id DESC LIMIT ?",
            (limit,),
        )


def list_invoices_between(start, end):
    with get_db() as con:
        return read_sql(con, 
            "SELECT id, date, client, payment_method, total, cost_total, profit, "
            "currency, cashbox, notes, user FROM invoices "
            "WHERE active = 1 AND date(date) BETWEEN date(?) AND date(?) "
            "ORDER BY id DESC",
            (start, end),
        )


def list_invoice_items(limit=300, invoice_id=None):
    with get_db() as con:
        if invoice_id:
            return read_sql(con, 
                "SELECT ii.id, ii.invoice_id, i.date, i.client, ii.sku, ii.product_name, "
                "ii.qty, ii.unit_price, ii.total, ii.serial, ii.notes "
                "FROM invoice_items ii LEFT JOIN invoices i ON i.id = ii.invoice_id "
                "WHERE ii.active = 1 AND ii.invoice_id = ? ORDER BY ii.id DESC",
                (invoice_id,),
            )
        return read_sql(con, 
            "SELECT ii.id, ii.invoice_id, i.date, i.client, ii.sku, ii.product_name, "
            "ii.qty, ii.unit_price, ii.total, ii.serial, ii.notes "
            "FROM invoice_items ii LEFT JOIN invoices i ON i.id = ii.invoice_id "
            "WHERE ii.active = 1 ORDER BY ii.id DESC LIMIT ?",
            (limit,),
        )

