"""EnvÃ­os USA: registro, actualizaciÃ³n de estado, consultas."""

from db.connection import get_db, read_sql
from db.product import add_or_update_product
from utils.format import now


def _receive_shipment_in_colombia(cur, shipment):
    if shipment["received_in_colombia"]:
        return shipment["colombia_product_id"]

    usa = cur.execute(
        "SELECT * FROM products WHERE id = ?", (shipment["usa_product_id"],)
    ).fetchone()
    cost_cop = float(usa["cost"] or 0) * float(shipment["rate"] or 0)

    col_id = add_or_update_product(
        cur, "Colombia", shipment["sku"], shipment["product_name"],
        usa["category"], shipment["qty"], cost_cop, "COP",
        shipment["destination"] or "Bodega Colombia",
    )

    cur.execute(
        "UPDATE usa_shipments SET colombia_product_id = ?, received_in_colombia = 1, "
        "received_at = ?, status = 'Bodega Colombia' WHERE id = ?",
        (col_id, now(), shipment["id"]),
    )
    return col_id


def register_usa_shipment(usa_product_id, qty, rate, destination, status, notes, user):
    if status not in ("Enviado", "Perdido", "Bodega Colombia"):
        raise ValueError("Estado invÃ¡lido.")

    with get_db() as con:
        cur = con.cursor()
        p = cur.execute(
            "SELECT * FROM products WHERE id = ? AND warehouse = 'USA' AND active = 1",
            (usa_product_id,),
        ).fetchone()
        if not p:
            raise ValueError("Producto USA no encontrado.")
        if p["stock"] < qty:
            raise ValueError("NO ENVIAR - SIN STOCK USA")

        stock_before = p["stock"]
        stock_after = stock_before - qty
        cur.execute("UPDATE products SET stock = ? WHERE id = ?", (stock_after, usa_product_id))

        cur.execute(
            "INSERT INTO usa_shipments(date, usa_product_id, colombia_product_id, sku, "
            "product_name, qty, stock_before, stock_after, rate, destination, status, "
            "received_in_colombia, notes, user) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (now(), usa_product_id, None, p["sku"], p["name"], qty, stock_before,
             stock_after, rate, destination, status, 0, notes, user),
        )
        shipment_id = cur.lastrowid

        if status == "Bodega Colombia":
            shipment = cur.execute(
                "SELECT * FROM usa_shipments WHERE id = ?", (shipment_id,)
            ).fetchone()
            _receive_shipment_in_colombia(cur, shipment)

        return shipment_id


def update_usa_shipment_status(shipment_id, new_status, status_notes, user):
    if new_status not in ("Enviado", "Perdido", "Bodega Colombia"):
        raise ValueError("Estado invÃ¡lido.")

    with get_db() as con:
        cur = con.cursor()
        shipment = cur.execute(
            "SELECT * FROM usa_shipments WHERE id = ? AND active = 1", (shipment_id,)
        ).fetchone()
        if not shipment:
            raise ValueError("EnvÃ­o no encontrado o anulado.")

        old_status = shipment["status"]
        if old_status == "Bodega Colombia" and new_status != "Bodega Colombia":
            raise ValueError(
                "Este envÃ­o ya entrÃ³ a Bodega Colombia. Para corregirlo debes anular el envÃ­o."
            )

        if new_status == "Bodega Colombia":
            _receive_shipment_in_colombia(cur, shipment)
        else:
            cur.execute(
                "UPDATE usa_shipments SET status = ?, status_notes = ? WHERE id = ?",
                (new_status, status_notes, shipment_id),
            )


def list_usa_shipments(limit=100):
    with get_db() as con:
        return read_sql(con, 
            "SELECT id, date, sku, product_name, qty, stock_before, stock_after, "
            "rate, status, received_in_colombia, received_at, destination, user, "
            "notes, status_notes FROM usa_shipments WHERE active = 1 "
            "ORDER BY id DESC LIMIT ?",
            (limit,),
        )

