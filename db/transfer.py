"""Transferencias entre cajas con tasa de cambio."""

from db.connection import get_db, read_sql
from db.cashbox import cashbox_add
from utils.format import now


def calculate_transfer(origin, dest, amount, rate):
    if origin == dest:
        return 0
    if origin == "Caja Colombia" and dest == "Caja USA":
        return amount / rate if rate else 0
    if origin == "Caja USA" and dest == "Caja Colombia":
        return amount * rate
    return amount


def register_transfer(origin, dest, amount_origin, rate, notes, user):
    if origin == dest:
        raise ValueError("La caja origen y destino no pueden ser iguales.")

    amount_converted = calculate_transfer(origin, dest, amount_origin, rate)
    origin_currency = "COP" if origin == "Caja Colombia" else "USD"
    dest_currency = "COP" if dest == "Caja Colombia" else "USD"

    with get_db() as con:
        cur = con.cursor()
        cur.execute(
            "INSERT INTO transfers(date, origin_cashbox, dest_cashbox, amount_origin, "
            "rate, amount_converted, notes, user) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (now(), origin, dest, amount_origin, rate, amount_converted, notes, user),
        )
        tid = cur.lastrowid

        cashbox_add(
            cur, origin, -amount_origin, origin_currency, "transferencia_salida",
            "transfers", tid, f"Transferencia a {dest}", user,
        )
        cashbox_add(
            cur, dest, amount_converted, dest_currency, "transferencia_entrada",
            "transfers", tid, f"Transferencia desde {origin}", user,
        )
        return tid


def list_transfers():
    with get_db() as con:
        return read_sql(con, 
            "SELECT id, date, origin_cashbox, dest_cashbox, amount_origin, rate, "
            "amount_converted, notes, user FROM transfers WHERE active = 1 "
            "ORDER BY id DESC LIMIT 300"
        )

