"""Registro y consulta de gastos por caja."""

from db.connection import get_db, read_sql
from db.cashbox import cashbox_add
from utils.format import now


def register_expense(concept, amount, currency, cashbox, category, notes, user):
    with get_db() as con:
        cur = con.cursor()
        cur.execute(
            "INSERT INTO expenses(date, concept, amount, currency, cashbox, category, notes, user) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (now(), concept, amount, currency, cashbox, category, notes, user),
        )
        expense_id = cur.lastrowid
        cashbox_add(
            cur, cashbox, -amount, currency, "gasto", "expenses",
            expense_id, f"Gasto: {concept}", user,
        )
        return expense_id


def list_expenses():
    with get_db() as con:
        return read_sql(con, 
            "SELECT id, date, concept, amount, currency, cashbox, category, user "
            "FROM expenses WHERE active = 1 ORDER BY id DESC LIMIT 300"
        )


def list_expenses_by_cashbox(cashbox):
    with get_db() as con:
        return read_sql(con, 
            "SELECT id, date, concept, amount, currency, cashbox, category, notes, user "
            "FROM expenses WHERE active = 1 AND cashbox = ? ORDER BY id DESC LIMIT 300",
            (cashbox,),
        )

