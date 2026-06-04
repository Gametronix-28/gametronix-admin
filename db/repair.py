"""Taller de reparaciones: Ã³rdenes, repuestos, abonos, entregas."""

from db.connection import get_db, read_sql
from db.cashbox import cashbox_add
from utils.format import now


def register_repair(client, phone, device, serial, accessories, received_condition, issue,
                    diagnostic, repair_solution, technician, warranty_days,
                    labor_price, status, payment_method, amount_paid,
                    used_parts, external_parts, notes, user,
                    additional_devices=None):
    if not device.strip() and not (additional_devices and len(additional_devices) > 0):
        raise ValueError("El equipo es obligatorio.")

    with get_db() as con:
        cur = con.cursor()

        stock_parts_cost = 0.0
        part_rows = []
        for part_id, qty in used_parts:
            p = cur.execute(
                "SELECT * FROM products WHERE id = ? AND warehouse = 'Repuestos' AND active = 1",
                (part_id,),
            ).fetchone()
            if not p:
                raise ValueError("Repuesto de bodega no encontrado.")
            if p["stock"] < qty:
                raise ValueError(f"Stock insuficiente para repuesto: {p['name']}")
            unit_cost = p["cost"] or 0
            total_cost = unit_cost * qty
            stock_parts_cost += total_cost
            part_rows.append((p, qty, unit_cost, total_cost))

        external_cost_total = 0.0
        external_rows = []
        for ext in external_parts:
            name = str(ext.get("part_name", "")).strip()
            qty = int(ext.get("qty", 0) or 0)
            unit_cost = float(ext.get("unit_cost", 0) or 0)
            supplier = str(ext.get("supplier", "") or "")
            ext_notes = str(ext.get("notes", "") or "")
            if name and qty > 0:
                total_cost = qty * unit_cost
                external_cost_total += total_cost
                external_rows.append((name, qty, unit_cost, total_cost, supplier, ext_notes))

        total_parts_cost = stock_parts_cost + external_cost_total
        total = float(labor_price or 0)
        profit = total - total_parts_cost
        amount_paid = float(amount_paid or 0)
        balance_due = total - amount_paid

        if amount_paid > total:
            raise ValueError("El abono/pago no puede ser mayor al total de la reparaciÃ³n.")

        import json
        extra_json = json.dumps(additional_devices) if additional_devices else None

        cur.execute(
            "INSERT INTO repairs(date, client, phone, device, serial, accessories, "
            "received_condition, issue, diagnostic, repair_solution, technician, "
            "warranty_days, labor_price, parts_cost, external_parts_cost, total, profit, "
            "amount_paid, balance_due, status, payment_method, notes, user, additional_devices) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (now(), client, phone, device, serial, accessories, received_condition,
             issue, diagnostic, repair_solution, technician, warranty_days,
             labor_price, stock_parts_cost, external_cost_total, total, profit,
             amount_paid, balance_due, status, payment_method, notes, user, extra_json),
        )
        repair_id = cur.lastrowid
        order_code = f"REP-{repair_id:05d}"
        cur.execute("UPDATE repairs SET order_code = ? WHERE id = ?", (order_code, repair_id))

        for p, qty, unit_cost, total_cost in part_rows:
            cur.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (qty, p["id"]))
            cur.execute(
                "INSERT INTO repair_parts(repair_id, part_product_id, sku, part_name, qty, "
                "unit_cost, total_cost) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (repair_id, p["id"], p["sku"], p["name"], qty, unit_cost, total_cost),
            )

        for name, qty, unit_cost, total_cost, supplier, ext_notes in external_rows:
            cur.execute(
                "INSERT INTO repair_external_parts(repair_id, part_name, qty, unit_cost, "
                "total_cost, supplier, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (repair_id, name, qty, unit_cost, total_cost, supplier, ext_notes),
            )

        if amount_paid > 0:
            cashbox_add(
                cur, "Caja Colombia", amount_paid, "COP", "abono_reparacion",
                "repairs", repair_id, f"Abono reparaciÃ³n {order_code}: {device}", user,
            )
            cur.execute(
                "INSERT INTO repair_payments(repair_id, date, amount, payment_method, notes, user) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (repair_id, now(), amount_paid, payment_method, "Pago inicial / abono", user),
            )

        return repair_id


def add_repair_payment(repair_id, amount, payment_method, notes, user):
    amount = float(amount or 0)
    if amount <= 0:
        raise ValueError("El abono debe ser mayor a cero.")

    with get_db() as con:
        cur = con.cursor()
        r = cur.execute(
            "SELECT * FROM repairs WHERE id = ? AND active = 1", (repair_id,)
        ).fetchone()
        if not r:
            raise ValueError("ReparaciÃ³n no encontrada.")
        if amount > float(r["balance_due"] or 0):
            raise ValueError("El abono no puede ser mayor al saldo pendiente.")

        new_paid = float(r["amount_paid"] or 0) + amount
        new_balance = float(r["total"] or 0) - new_paid
        new_status = r["status"]
        if new_balance <= 0 and r["status"] in ("Recibido", "En proceso", "Terminado"):
            new_status = "Pagado"

        cur.execute(
            "UPDATE repairs SET amount_paid = ?, balance_due = ?, status = ? WHERE id = ?",
            (new_paid, new_balance, new_status, repair_id),
        )
        cur.execute(
            "INSERT INTO repair_payments(repair_id, date, amount, payment_method, notes, user) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (repair_id, now(), amount, payment_method, notes, user),
        )
        cashbox_add(
            cur, "Caja Colombia", amount, "COP", "abono_reparacion",
            "repairs", repair_id, f"Abono reparaciÃ³n {r['order_code']}", user,
        )


def update_repair_status(repair_id, new_status):
    """Cambia el estado de una reparacion (sin afectar pagos ni caja)."""
    with get_db() as con:
        cur = con.cursor()
        r = cur.execute(
            "SELECT * FROM repairs WHERE id = ? AND active = 1", (repair_id,)
        ).fetchone()
        if not r:
            raise ValueError("Reparacion no encontrada.")
        cur.execute(
            "UPDATE repairs SET status = ? WHERE id = ?",
            (new_status, repair_id),
        )


def mark_repair_paid(repair_id, payment_method, user):
    """
    Marca una reparacion como totalmente pagada.
    Paga el saldo pendiente completo y lo envia a Caja Colombia.
    """
    with get_db() as con:
        cur = con.cursor()
        r = cur.execute(
            "SELECT * FROM repairs WHERE id = ? AND active = 1", (repair_id,)
        ).fetchone()
        if not r:
            raise ValueError("Reparacion no encontrada.")

        balance = float(r["balance_due"] or 0)
        if balance <= 0:
            raise ValueError("Esta reparacion ya esta totalmente pagada.")

        # Registrar el pago completo del saldo
        cur.execute(
            "UPDATE repairs SET amount_paid = total, balance_due = 0, "
            "status = CASE WHEN status IN ('Recibido','En proceso','Terminado','Esperando repuesto') "
            "THEN 'Pagado' ELSE status END, "
            "payment_method = ? WHERE id = ?",
            (payment_method, repair_id),
        )
        cur.execute(
            "INSERT INTO repair_payments(repair_id, date, amount, payment_method, notes, user) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (repair_id, now(), balance, payment_method, "Pago total del saldo", user),
        )
        cashbox_add(
            cur, "Caja Colombia", balance, "COP", "pago_reparacion",
            "repairs", repair_id, f"Pago total reparacion {r['order_code']}", user,
        )


def deliver_repair(repair_id, notes, user):
    with get_db() as con:
        cur = con.cursor()
        r = cur.execute(
            "SELECT * FROM repairs WHERE id = ? AND active = 1", (repair_id,)
        ).fetchone()
        if not r:
            raise ValueError("Reparacion no encontrada.")
        if float(r["balance_due"] or 0) > 0:
            raise ValueError("No se puede entregar: la reparacion tiene saldo pendiente.")
        cur.execute(
            "UPDATE repairs SET status = 'Entregado', delivered_at = ?, "
            "notes = COALESCE(notes, '') || ? WHERE id = ?",
            (now(), f" | Entrega: {notes}", repair_id),
        )


def get_repair(repair_id):
    with get_db() as con:
        row = con.execute(
            "SELECT * FROM repairs WHERE active = 1 AND id = ?", (repair_id,)
        ).fetchone()
        return dict(row) if row else None


def list_repairs(limit=100):
    with get_db() as con:
        return read_sql(con, 
            "SELECT id, order_code, date, client, phone, device, serial, issue, technician, "
            "labor_price, parts_cost, external_parts_cost, total, profit, amount_paid, balance_due, "
            "status, payment_method, warranty_days, delivered_at, user, notes "
            "FROM repairs WHERE active = 1 ORDER BY id DESC LIMIT ?",
            (limit,),
        )


def list_repairs_between(start, end):
    with get_db() as con:
        return read_sql(con, 
            "SELECT id, order_code, date, client, phone, device, issue, technician, "
            "labor_price, parts_cost, external_parts_cost, total, profit, amount_paid, balance_due, "
            "status, payment_method, warranty_days, user "
            "FROM repairs WHERE active = 1 AND date(date) BETWEEN date(?) AND date(?) "
            "ORDER BY id DESC",
            (start, end),
        )


def list_repair_parts(limit=100):
    with get_db() as con:
        return read_sql(con, 
            "SELECT rp.id, rp.repair_id, r.order_code, r.date, r.client, r.device, "
            "rp.sku, rp.part_name, rp.qty, rp.unit_cost, rp.total_cost "
            "FROM repair_parts rp LEFT JOIN repairs r ON r.id = rp.repair_id "
            "WHERE rp.active = 1 ORDER BY rp.id DESC LIMIT ?",
            (limit,),
        )


def list_repair_external_parts(limit=100, repair_id=None):
    with get_db() as con:
        if repair_id:
            return read_sql(con, 
                "SELECT ep.id, ep.repair_id, r.order_code, r.date, r.client, r.device, "
                "ep.part_name, ep.qty, ep.unit_cost, ep.total_cost, ep.supplier, ep.notes "
                "FROM repair_external_parts ep LEFT JOIN repairs r ON r.id = ep.repair_id "
                "WHERE ep.active = 1 AND ep.repair_id = ? ORDER BY ep.id DESC",
                (repair_id,),
            )
        return read_sql(con, 
            "SELECT ep.id, ep.repair_id, r.order_code, r.date, r.client, r.device, "
            "ep.part_name, ep.qty, ep.unit_cost, ep.total_cost, ep.supplier, ep.notes "
            "FROM repair_external_parts ep LEFT JOIN repairs r ON r.id = ep.repair_id "
            "WHERE ep.active = 1 ORDER BY ep.id DESC LIMIT ?",
            (limit,),
        )


def list_repair_payments(limit=100):
    with get_db() as con:
        return read_sql(con, 
            "SELECT rp.id, rp.repair_id, r.order_code, r.client, r.device, "
            "rp.date, rp.amount, rp.payment_method, rp.notes, rp.user "
            "FROM repair_payments rp LEFT JOIN repairs r ON r.id = rp.repair_id "
            "WHERE rp.active = 1 ORDER BY rp.id DESC LIMIT ?",
            (limit,),
        )


def list_pending_repairs(limit=300):
    with get_db() as con:
        return read_sql(con, 
            "SELECT id, order_code, date, client, phone, device, total, amount_paid, "
            "balance_due, status, technician FROM repairs "
            "WHERE active = 1 AND COALESCE(balance_due, 0) > 0 "
            "ORDER BY id DESC LIMIT ?",
            (limit,),
        )


def list_repairs_by_client(client_query):
    with get_db() as con:
        like = f"%{client_query}%"
        return read_sql(con, 
            "SELECT id, order_code, date, client, phone, device, serial, issue, "
            "total, amount_paid, balance_due, status, technician FROM repairs "
            "WHERE active = 1 AND (client LIKE ? OR phone LIKE ? OR serial LIKE ? OR device LIKE ?) "
            "ORDER BY id DESC LIMIT 300",
            (like, like, like, like),
        )

