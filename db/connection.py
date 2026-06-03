"""
GestiÃ³n de conexiones a base de datos.
Soporta SQLite (local) y Turso (nube) segÃºn la configuraciÃ³n.
"""

import sqlite3
import pandas as pd
from contextlib import contextmanager
from config import DB_PATH, USE_TURSO, TURSO_DB_URL, TURSO_AUTH_TOKEN


def read_sql(con, sql, params=None):
    """
    Ejecuta SQL y retorna un DataFrame.
    Funciona tanto con SQLite como con Turso.
    """
    if USE_TURSO:
        # TursoConnection tiene su propio método read_sql
        return con.read_sql(sql, params)
    # SQLite usa pandas directamente
    return pd.read_sql_query(sql, con, params=params)


def _get_sqlite_connection():
    """Crea una conexiÃ³n SQLite local."""
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def _get_turso_connection():
    """Crea una conexiÃ³n Turso (nube)."""
    from db.turso import TursoConnection
    return TursoConnection(TURSO_DB_URL, TURSO_AUTH_TOKEN)


if USE_TURSO:
    @contextmanager
    def get_db():
        """
        Context manager para conexiones Turso (nube).
        Cada execute() es auto-commit. commit/rollback son no-ops.
        """
        con = _get_turso_connection()
        try:
            yield con
        except Exception:
            raise
        finally:
            con.close()
else:
    @contextmanager
    def get_db():
        """
        Context manager para conexiones SQLite (local).
        Hace commit al salir si no hubo errores, rollback si los hubo.
        """
        con = _get_sqlite_connection()
        try:
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

