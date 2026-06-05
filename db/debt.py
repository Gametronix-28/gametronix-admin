"""Gestion de deudas / cuentas por pagar a proveedores."""

import pandas as pd
from db.connection import get_db, read_sql
from db.cashbox import cashbox_add
from utils.format import now, money


def register_debt(supplier, concept, amount, currency, cashbox, notes, user, cur=None):
    """
    Registra una deuda con un proveedor. No descuenta caja.
    Si cur es pasado, se usa esa transaccion activa en vez de abrir una nueva.
    """
    if not supplier.strip():
        raise ValueError("El proveedor es obligatorio.")
    if cur:
        cur.execute(
            "INSERT INTO debts(date, supplier, concept, amount, currency, cashbox, notes, user) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (now(), supplier.strip(), concept.strip(), amount, currency, cashbox, notes, user),
        )
        return cur.lastrowid
    with get_db() as con:
        con.execute(
            "INSERT INTO debts(date, supplier, concept, amount, currency, cashbox, notes, user) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (now(), supplier.strip(), concept.strip(), amount, currency, cashbox, notes, user),
        )
        return con.cursor().lastrowid


def pay_debt(debt_id, user):
    """Paga una deuda: descuenta de caja y la marca como pagada."""
    with get_db() as con:
        cur = con.cursor()
        d = cur.execute(
            "SELECT * FROM debts WHERE id = ? AND active = 1 AND paid = 0", (debt_id,)
        ).fetchone()
        if not d:
            raise ValueError("Deuda no encontrada o ya pagada.")

        # Descontar de caja
        cashbox_add(
            cur, d["cashbox"], -d["amount"], d["currency"], "pago_deuda",
            "debts", debt_id,
            f"Pago deuda a {d['supplier']}: {d['concept']}", user,
        )

        # Marcar como pagada
        cur.execute(
            "UPDATE debts SET paid = 1, paid_date = ? WHERE id = ?",
            (now(), debt_id),
        )


def list_debts(paid=None, limit=100):
    """Lista deudas. paid=None=todas, paid=0=pendientes, paid=1=pagadas."""
    sql = "SELECT id, date, supplier, concept, amount, currency, paid, paid_date, notes FROM debts WHERE active = 1"
    params = []
    if paid is not None:
        sql += " AND paid = ?"
        params.append(paid)
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    with get_db() as con:
        return read_sql(con, sql, params)


def get_total_debt():
    """Total de deuda pendiente."""
    with get_db() as con:
        row = con.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM debts WHERE active = 1 AND paid = 0"
        ).fetchone()
        return float(row[0]) if row else 0.0
