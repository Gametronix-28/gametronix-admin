"""Base de datos de clientes."""

from db.connection import get_db, read_sql
from utils.format import now


def add_customer(name, phone="", email="", notes=""):
    """Agrega un cliente nuevo. Retorna el ID."""
    if not name.strip():
        raise ValueError("El nombre es obligatorio.")
    with get_db() as con:
        # Si ya existe con ese nombre y telefono, retornar el existente
        existing = con.execute(
            "SELECT id FROM customers WHERE name = ? AND phone = ?",
            (name.strip(), phone.strip()),
        ).fetchone()
        if existing:
            return existing[0]
        con.execute(
            "INSERT INTO customers(name, phone, email, notes, created_at) VALUES (?, ?, ?, ?, ?)",
            (name.strip(), phone.strip(), email.strip(), notes.strip(), now()),
        )
        return con.cursor().lastrowid


def search_customers(query=""):
    """Busca clientes por nombre o telefono."""
    with get_db() as con:
        if query:
            like = f"%{query}%"
            return read_sql(con,
                "SELECT id, name, phone FROM customers "
                "WHERE name LIKE ? OR phone LIKE ? ORDER BY name LIMIT 20",
                (like, like),
            )
        return read_sql(con,
            "SELECT id, name, phone FROM customers ORDER BY name LIMIT 50"
        )


def get_customer_history(customer_id):
    """Historial de reparaciones de un cliente."""
    with get_db() as con:
        return read_sql(con,
            "SELECT id, order_code, date, device, total, status "
            "FROM repairs WHERE client = (SELECT name FROM customers WHERE id = ?) AND active = 1 "
            "ORDER BY id DESC LIMIT 50",
            (customer_id,),
        )
