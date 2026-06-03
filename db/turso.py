"""
Adaptador Turso: wrapper sincrono que imita sqlite3.Connection/Cursor
usando libsql-client (async) por debajo con un event loop persistente.
"""

import asyncio
import atexit
import pandas as pd
import libsql_client

# Event loop persistente (nunca se cierra hasta que salga el proceso)
_LOOP = asyncio.new_event_loop()


def _run(coro):
    """Ejecuta una corrutina en el loop persistente y retorna el resultado."""
    return _LOOP.run_until_complete(coro)


def _cleanup():
    """Cierra el loop al salir del proceso."""
    try:
        _LOOP.close()
    except Exception:
        pass


atexit.register(_cleanup)


class TursoRow:
    """Wrapper que imita sqlite3.Row para compatibilidad con dict(row)."""

    def __init__(self, data, columns=None):
        self._data = data
        self._columns = columns or []

    def keys(self):
        return self._columns

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._data[key]
        if isinstance(key, str) and self._columns:
            idx = self._columns.index(key)
            return self._data[idx]
        return self._data[key]

    def __iter__(self):
        # Soporte para dict(row): itera sobre (key, value)
        return iter(zip(self._columns, self._data))

    def __len__(self):
        return len(self._data)


class TursoCursor:
    """Imita sqlite3.Cursor usando el cliente async de Turso."""

    def __init__(self, client):
        self._client = client
        self.lastrowid = None
        self.rowcount = 0
        self._last_result = None
        self._rows = []
        self._columns = []

    def execute(self, sql, params=None):
        self._last_result = _run(self._client.execute(sql, params or []))
        self.lastrowid = self._last_result.last_insert_rowid
        self.rowcount = self._last_result.rows_affected or 0
        cols = self._last_result.columns
        if cols:
            self._columns = [c if isinstance(c, str) else c.name for c in cols]
        else:
            self._columns = []
        self._rows = [TursoRow(r, self._columns) for r in self._last_result.rows] if self._last_result.rows else []
        return self

    def fetchone(self):
        if self._rows:
            return self._rows[0]
        return None

    def fetchall(self):
        return self._rows

    def __iter__(self):
        return iter(self._rows)


class TursoConnection:
    """
    Imita sqlite3.Connection usando Turso/libsql por debajo.
    - Cada execute() es auto-commit (HTTP).
    - commit() y rollback() son no-ops.
    """

    def __init__(self, url, auth_token):
        self.url = url
        self.auth_token = auth_token
        self._async_client = None

    def _get_client(self):
        if self._async_client is None:
            async def _create():
                return libsql_client.create_client(
                    url=self.url, auth_token=self.auth_token,
                )
            self._async_client = _run(_create())
        return self._async_client

    def cursor(self):
        return TursoCursor(self._get_client())

    def execute(self, sql, params=None):
        cur = self.cursor()
        cur.execute(sql, params)
        return cur

    def commit(self):
        pass  # auto-commit mode

    def rollback(self):
        pass

    def close(self):
        if self._async_client:
            try:
                _run(self._async_client.close())
            except Exception:
                pass
            self._async_client = None

    def batch(self, statements):
        stmts = []
        for s in statements:
            if isinstance(s, tuple):
                stmts.append(libsql_client.Statement(s[0], s[1]))
            else:
                stmts.append(s)
        _run(self._get_client().batch(stmts))

    def read_sql(self, sql, params=None):
        cur = self.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
        if rows:
            return pd.DataFrame(rows, columns=cur._columns)
        return pd.DataFrame()
