"""Autenticacion y gestion de usuarios con permisos."""

import hashlib
import json
from db.connection import get_db
from utils.format import now
from config import ROLE_PERMISSIONS


def _hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def authenticate(username, password):
    """
    Valida credenciales. Retorna dict con id, username, role, permissions o None.
    permissions es una lista de menus permitidos (vacia = admin/todo).
    """
    with get_db() as con:
        row = con.execute(
            "SELECT id, username, role, permissions FROM users "
            "WHERE username = ? AND password_hash = ? AND active = 1",
            (username, _hash_password(password)),
        ).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "username": row["username"],
            "role": row["role"],
            "permissions": _parse_permissions(row["role"], row["permissions"]),
        }


def _parse_permissions(role, stored_permissions):
    """
    Convierte los permisos almacenados (JSON o None) en una lista de menus.
    Si el rol es admin, retorna lista vacia (significa acceso total).
    Si el rol es personalizado, usa los permisos almacenados.
    Para otros roles, usa los predefinidos en ROLE_PERMISSIONS.
    """
    if role == "admin":
        return []  # vacio = todo

    if role == "personalizado":
        if stored_permissions:
            try:
                return json.loads(stored_permissions)
            except Exception:
                pass
        return []

    # Roles predefinidos
    return ROLE_PERMISSIONS.get(role, [])


def get_user_permissions(user):
    """Retorna la lista de menus que el usuario puede ver."""
    perms = user.get("permissions", [])
    return perms


def list_users():
    """Lista todos los usuarios activos con sus permisos."""
    with get_db() as con:
        rows = con.execute(
            "SELECT id, username, role, permissions, active, created_at FROM users ORDER BY id"
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["permissions"] = _parse_permissions(d["role"], d.get("permissions"))
            result.append(d)
        return result


def add_user(username, password, role, permissions=None):
    """
    Crea un nuevo usuario.
    permissions: lista de menus (solo para rol 'personalizado').
    """
    perms_json = json.dumps(permissions) if permissions else None
    with get_db() as con:
        con.execute(
            "INSERT INTO users(username, password_hash, role, permissions, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (username, _hash_password(password), role, perms_json, now()),
        )
