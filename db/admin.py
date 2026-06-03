"""AdministraciÃ³n: anulaciÃ³n de registros, historial de anulaciones, exportaciÃ³n Excel."""

import pandas as pd
from db.connection import get_db, read_sql
from db.cashbox import cashbox_add
from utils.format import now


# â”€â”€ Estrategias de anulaciÃ³n â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _void_invoice(cur, record_id):
    r = cur.execute(
        "SELECT * FROM invoices WHERE id = ? AND active = 1", (record_id,)
    ).fetchone()
    if not r:
        raise ValueError("Factura no encontrada o ya anulada.")
    items = cur.execute(
        "SELECT * FROM invoice_items WHERE invoice_id = ? AND active = 1", (record_id,)
    ).fetchall()
    for item in items:
        cur.execute(
            "UPDATE products SET stock = stock + ? WHERE id = ?",
            (item["qty"], item["product_id"]),
        )
    cashbox_add(
        cur, r["cashbox"], -r["total"], r["currency"], "anulacion_factura",
        "invoices", record_id, f"AnulaciÃ³n factura {record_id}", "admin",
    )
    cur.execute("UPDATE invoice_items SET active = 0 WHERE invoice_id = ?", (record_id,))
    cur.execute("UPDATE invoices SET active = 0 WHERE id = ?", (record_id,))


def _void_sale(cur, record_id):
    r = cur.execute(
        "SELECT * FROM sales WHERE id = ? AND active = 1", (record_id,)
    ).fetchone()
    if not r:
        raise ValueError("Venta no encontrada o ya anulada.")
    cur.execute("UPDATE products SET stock = stock + ? WHERE id = ?", (r["qty"], r["product_id"]))
    cashbox_add(
        cur, r["cashbox"], -r["total"], r["currency"], "anulacion_venta",
        "sales", record_id, f"AnulaciÃ³n venta {record_id}", "admin",
    )
    cur.execute("UPDATE sales SET active = 0 WHERE id = ?", (record_id,))


def _void_purchase(cur, record_id):
    r = cur.execute(
        "SELECT * FROM purchases WHERE id = ? AND active = 1", (record_id,)
    ).fetchone()
    if not r:
        raise ValueError("Compra no encontrada o ya anulada.")
    product = cur.execute(
        "SELECT stock FROM products WHERE id = ?", (r["product_id"],)
    ).fetchone()
    if product and product["stock"] < r["qty"]:
        raise ValueError("No se puede anular: el stock actual es menor que la compra.")
    cur.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (r["qty"], r["product_id"]))
    cashbox_add(
        cur, r["cashbox"], r["total"], r["currency"], "anulacion_compra",
        "purchases", record_id, f"AnulaciÃ³n compra {record_id}", "admin",
    )
    cur.execute("UPDATE purchases SET active = 0 WHERE id = ?", (record_id,))


def _void_shipment(cur, record_id):
    r = cur.execute(
        "SELECT * FROM usa_shipments WHERE id = ? AND active = 1", (record_id,)
    ).fetchone()
    if not r:
        raise ValueError("EnvÃ­o no encontrado o ya anulado.")
    cur.execute(
        "UPDATE products SET stock = stock + ? WHERE id = ?",
        (r["qty"], r["usa_product_id"]),
    )
    if r["received_in_colombia"] and r["colombia_product_id"]:
        col = cur.execute(
            "SELECT stock FROM products WHERE id = ?", (r["colombia_product_id"],)
        ).fetchone()
        if col and col["stock"] < r["qty"]:
            raise ValueError(
                "No se puede anular: el stock Colombia actual es menor que el envÃ­o recibido."
            )
        cur.execute(
            "UPDATE products SET stock = stock - ? WHERE id = ?",
            (r["qty"], r["colombia_product_id"]),
        )
    cur.execute("UPDATE usa_shipments SET active = 0 WHERE id = ?", (record_id,))


def _void_repair(cur, record_id):
    r = cur.execute(
        "SELECT * FROM repairs WHERE id = ? AND active = 1", (record_id,)
    ).fetchone()
    if not r:
        raise ValueError("ReparaciÃ³n no encontrada o ya anulada.")
    parts = cur.execute(
        "SELECT * FROM repair_parts WHERE repair_id = ? AND active = 1", (record_id,)
    ).fetchall()
    for part in parts:
        cur.execute(
            "UPDATE products SET stock = stock + ? WHERE id = ?",
            (part["qty"], part["part_product_id"]),
        )
    paid = float(r["amount_paid"] or 0)
    if paid > 0:
        cashbox_add(
            cur, "Caja Colombia", -paid, "COP", "anulacion_reparacion",
            "repairs", record_id, f"AnulaciÃ³n reparaciÃ³n {record_id}", "admin",
        )
    cur.execute("UPDATE repair_parts SET active = 0 WHERE repair_id = ?", (record_id,))
    cur.execute("UPDATE repair_external_parts SET active = 0 WHERE repair_id = ?", (record_id,))
    cur.execute("UPDATE repair_payments SET active = 0 WHERE repair_id = ?", (record_id,))
    cur.execute("UPDATE repairs SET active = 0 WHERE id = ?", (record_id,))


def _void_transfer(cur, record_id):
    r = cur.execute(
        "SELECT * FROM transfers WHERE id = ? AND active = 1", (record_id,)
    ).fetchone()
    if not r:
        raise ValueError("Transferencia no encontrada o ya anulada.")
    origin_currency = "COP" if r["origin_cashbox"] == "Caja Colombia" else "USD"
    dest_currency = "COP" if r["dest_cashbox"] == "Caja Colombia" else "USD"
    cashbox_add(
        cur, r["origin_cashbox"], r["amount_origin"], origin_currency,
        "anulacion_transferencia", "transfers", record_id,
        f"AnulaciÃ³n transferencia {record_id}", "admin",
    )
    cashbox_add(
        cur, r["dest_cashbox"], -r["amount_converted"], dest_currency,
        "anulacion_transferencia", "transfers", record_id,
        f"AnulaciÃ³n transferencia {record_id}", "admin",
    )
    cur.execute("UPDATE transfers SET active = 0 WHERE id = ?", (record_id,))


def _void_expense(cur, record_id):
    r = cur.execute(
        "SELECT * FROM expenses WHERE id = ? AND active = 1", (record_id,)
    ).fetchone()
    if not r:
        raise ValueError("Gasto no encontrado o ya anulado.")
    cashbox_add(
        cur, r["cashbox"], r["amount"], r["currency"], "anulacion_gasto",
        "expenses", record_id, f"AnulaciÃ³n gasto {record_id}", "admin",
    )
    cur.execute("UPDATE expenses SET active = 0 WHERE id = ?", (record_id,))


def _void_product(cur, record_id):
    r = cur.execute(
        "SELECT * FROM products WHERE id = ? AND active = 1", (record_id,)
    ).fetchone()
    if not r:
        raise ValueError("Producto no encontrado o ya eliminado.")
    cur.execute("UPDATE products SET active = 0 WHERE id = ?", (record_id,))


_VOID_STRATEGIES = {
    "factura": _void_invoice,
    "venta": _void_sale,
    "compra": _void_purchase,
    "envio_usa": _void_shipment,
    "reparacion": _void_repair,
    "transferencia": _void_transfer,
    "gasto": _void_expense,
    "producto": _void_product,
}


def void_record(record_type, record_id, reason, user):
    strategy = _VOID_STRATEGIES.get(record_type)
    if not strategy:
        raise ValueError(f"Tipo de registro invÃ¡lido: {record_type}")
    with get_db() as con:
        cur = con.cursor()
        strategy(cur, record_id)
        cur.execute(
            "INSERT INTO voids(date, record_type, record_id, reason, user) VALUES (?, ?, ?, ?, ?)",
            (now(), record_type, record_id, reason, user),
        )


def list_voids():
    with get_db() as con:
        return read_sql(con, "SELECT * FROM voids ORDER BY id DESC LIMIT 300")


def export_to_excel():
    out = "gametronix_respaldo.xlsx"
    tables = [
        "products", "purchases", "invoices", "invoice_items", "sales",
        "repairs", "repair_parts", "repair_external_parts", "repair_payments",
        "expenses", "transfers", "usa_shipments", "cashboxes",
        "cashbox_movements", "users", "voids",
    ]
    with get_db() as con:
        with pd.ExcelWriter(out, engine="openpyxl") as writer:
            for table in tables:
                read_sql(con, f"SELECT * FROM {table}").to_excel(
                    writer, sheet_name=table[:31], index=False,
                )
    return out

