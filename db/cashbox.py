"""GestiÃ³n de cajas y movimientos."""

import pandas as pd
from db.connection import get_db, read_sql
from utils.format import now


def get_cashbox_balance(cashbox):
    with get_db() as con:
        row = con.execute(
            "SELECT balance FROM cashboxes WHERE name = ?", (cashbox,)
        ).fetchone()
        return row["balance"] if row else 0


def list_cashboxes():
    with get_db() as con:
        rows = con.execute(
            "SELECT id, name, currency, balance FROM cashboxes ORDER BY id"
        ).fetchall()
        return [dict(r) for r in rows]


def list_cashbox_movements(cashbox):
    with get_db() as con:
        return read_sql(con, 
            "SELECT id, date, type, amount, currency, description, user "
            "FROM cashbox_movements WHERE cashbox = ? AND active = 1 "
            "ORDER BY id DESC LIMIT 300",
            (cashbox,),
        )


def cashbox_add(cur, cashbox, amount, currency, type_, table, rid, desc, user):
    cur.execute(
        "UPDATE cashboxes SET balance = balance + ? WHERE name = ?",
        (amount, cashbox),
    )
    cur.execute(
        "INSERT INTO cashbox_movements(date, cashbox, type, reference_table, "
        "reference_id, amount, currency, description, user) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (now(), cashbox, type_, table, rid, amount, currency, desc, user),
    )


def inject_capital(cashbox, amount, notes, user):
    """
    Inyecta capital directamente a una caja.
    No tiene contrapartida de compra/venta — es plata que entra al negocio.
    """
    currency = "COP" if cashbox == "Caja Colombia" else "USD"
    with get_db() as con:
        cur = con.cursor()
        cashbox_add(
            cur, cashbox, amount, currency, "inyeccion_capital",
            "cashboxes", 0, f"Inyeccion de capital: {notes}", user,
        )

