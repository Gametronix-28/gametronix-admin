"""Autenticación y gestión de usuarios."""

import hashlib
from db.connection import get_db
from utils.format import now


def _hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def authenticate(username, password):
    """Valida credenciales. Retorna dict con id, username, role o None."""
    with get_db() as con:
        row = con.execute(
            "SELECT id, username, role FROM users "
            "WHERE username = ? AND password_hash = ? AND active = 1",
            (username, _hash_password(password)),
        ).fetchone()
        return dict(row) if row else None


def list_users():
    """Lista todos los usuarios activos."""
    with get_db() as con:
        rows = con.execute(
            "SELECT id, username, role, active, created_at FROM users ORDER BY id"
        ).fetchall()
        return [dict(r) for r in rows]


def add_user(username, password, role):
    """Crea un nuevo usuario."""
    with get_db() as con:
        con.execute(
            "INSERT INTO users(username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
            (username, _hash_password(password), role, now()),
        )
