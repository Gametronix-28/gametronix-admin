"""
Adaptador Turso: wrapper síncrono que imita sqlite3.Connection/Cursor
usando libsql-client (async) por debajo con asyncio.run().

Esto permite que los módulos db/ funcionen con cambios mínimos,
simplemente importando desde db.connection (que decide si usa SQLite o Turso).
"""

import asyncio
import pandas as pd
import libsql_client


class TursoCursor:
    """Imita sqlite3.Cursor usando el cliente async de Turso."""

    def __init__(self, client):
        self._client = client
        self.lastrowid = None
        self.rowcount = 0
        self._last_result = None
        self._rows = []

    def execute(self, sql, params=None):
        """Ejecuta una consulta SQL. Retorna self para compatibilidad."""
        coro = self._client.execute(sql, params or [])
        self._last_result = asyncio.run(coro)
        self.lastrowid = self._last_result.last_insert_rowid
        self.rowcount = self._last_result.rows_affected or 0
        self._rows = self._last_result.rows if self._last_result.rows else []
        return self

    def fetchone(self):
        """Retorna la primera fila como Row-like dict, o None."""
        if self._rows:
            return self._rows[0]
        return None

    def fetchall(self):
        """Retorna todas las filas como lista de Row-like dicts."""
        return self._rows

    def __iter__(self):
        return iter(self._rows)


class TursoConnection:
    """
    Imita sqlite3.Connection usando Turso/libsql por debajo.
    - Cada execute() es una transacción auto-committed (HTTP).
    - commit() y rollback() son no-ops (modo auto-commit).
    - Para operaciones atómicas multi-statement, usar batch().
    """

    def __init__(self, url, auth_token):
        self.url = url
        self.auth_token = auth_token
        self._async_client = None

    def _get_client(self):
        """Crea o retorna el cliente async (lazy init)."""
        if self._async_client is None:
            self._async_client = libsql_client.create_client(
                url=self.url, auth_token=self.auth_token,
            )
        return self._async_client

    def cursor(self):
        """Retorna un TursoCursor vinculado a esta conexión."""
        return TursoCursor(self._get_client())

    def execute(self, sql, params=None):
        """Ejecuta SQL directamente. Retorna TursoCursor."""
        cur = self.cursor()
        cur.execute(sql, params)
        return cur

    def commit(self):
        """No-op: cada execute() hace auto-commit."""
        pass

    def rollback(self):
        """No-op en modo auto-commit."""
        pass

    def close(self):
        """Cierra el cliente async."""
        if self._async_client:
            try:
                asyncio.run(self._async_client.close())
            except Exception:
                pass
            self._async_client = None

    def batch(self, statements):
        """
        Ejecuta múltiples statements en una transacción atómica.
        statements: lista de strings SQL o tuplas (sql, params).
        """
        stmts = []
        for s in statements:
            if isinstance(s, tuple):
                stmts.append(libsql_client.Statement(s[0], s[1]))
            else:
                stmts.append(s)

        asyncio.run(self._get_client().batch(stmts))

    def read_sql(self, sql, params=None):
        """
        Reemplazo síncrono de pd.read_sql_query().
        Ejecuta SQL y retorna un DataFrame.
        """
        cur = self.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
        if rows:
            # Extraer nombres de columnas del último resultado
            columns = [c.name for c in cur._last_result.columns]
            return pd.DataFrame(rows, columns=columns)
        return pd.DataFrame()
