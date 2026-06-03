"""
Script de migración: copia la DB local (SQLite) a Turso (nube).
Uso:
  1. Crea tu cuenta gratis en https://turso.tech
  2. Crea una base de datos (ej: "gametronix")
  3. Copia la URL y el token desde el dashboard
  4. Ejecuta: python migrar_a_turso.py

Variables de entorno:
  TURSO_DB_URL  = libsql://tu-db.turso.io
  TURSO_AUTH_TOKEN = token-de-acceso
"""

import os
import sys
import sqlite3
import asyncio
import libsql_client

# ── Configuración ─────────────────────────────────────────

DB_URL = os.getenv("TURSO_DB_URL", "").strip()
AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN", "").strip()
LOCAL_DB = "gametronix.db"

if not DB_URL or not AUTH_TOKEN:
    print("ERROR: Debes configurar las variables de entorno:")
    print("  TURSO_DB_URL=libsql://tu-db.turso.io")
    print("  TURSO_AUTH_TOKEN=tu-token")
    print()
    print("Obtén estas credenciales en https://turso.tech → Dashboard")
    sys.exit(1)

# ── Tablas en orden de creación (respetando dependencias) ─

TABLES_SQL = [
    # Sin dependencias
    """CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'caja',
        active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS cashboxes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        currency TEXT NOT NULL,
        balance REAL NOT NULL DEFAULT 0
    )""",
    """CREATE TABLE IF NOT EXISTS cashbox_movements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        cashbox TEXT NOT NULL,
        type TEXT NOT NULL,
        reference_table TEXT,
        reference_id INTEGER,
        amount REAL NOT NULL,
        currency TEXT NOT NULL,
        description TEXT,
        user TEXT,
        active INTEGER NOT NULL DEFAULT 1
    )""",
    """CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sku TEXT, name TEXT NOT NULL, category TEXT,
        stock INTEGER NOT NULL DEFAULT 0,
        min_stock INTEGER NOT NULL DEFAULT 2,
        cost REAL NOT NULL DEFAULT 0,
        price REAL NOT NULL DEFAULT 0,
        currency TEXT NOT NULL DEFAULT 'COP',
        location TEXT,
        warehouse TEXT NOT NULL DEFAULT 'Colombia',
        active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL, warehouse TEXT NOT NULL,
        product_id INTEGER NOT NULL, sku TEXT,
        product_name TEXT NOT NULL, qty INTEGER NOT NULL,
        unit_cost REAL NOT NULL, total REAL NOT NULL,
        currency TEXT NOT NULL, cashbox TEXT NOT NULL,
        supplier TEXT, notes TEXT, user TEXT,
        active INTEGER NOT NULL DEFAULT 1
    )""",
    """CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL, product_id INTEGER NOT NULL,
        sku TEXT, product_name TEXT NOT NULL,
        qty INTEGER NOT NULL, unit_cost REAL NOT NULL,
        unit_price REAL NOT NULL, total REAL NOT NULL,
        cost_total REAL NOT NULL, profit REAL NOT NULL,
        currency TEXT NOT NULL, cashbox TEXT NOT NULL,
        client TEXT, payment_method TEXT, notes TEXT,
        user TEXT, active INTEGER NOT NULL DEFAULT 1
    )""",
    """CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL, client TEXT,
        payment_method TEXT, total REAL NOT NULL DEFAULT 0,
        cost_total REAL NOT NULL DEFAULT 0,
        profit REAL NOT NULL DEFAULT 0,
        currency TEXT NOT NULL DEFAULT 'COP',
        cashbox TEXT NOT NULL DEFAULT 'Caja Colombia',
        notes TEXT, user TEXT, active INTEGER NOT NULL DEFAULT 1
    )""",
    """CREATE TABLE IF NOT EXISTS invoice_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL, sku TEXT,
        product_name TEXT NOT NULL, qty INTEGER NOT NULL,
        unit_cost REAL NOT NULL DEFAULT 0,
        unit_price REAL NOT NULL DEFAULT 0,
        total REAL NOT NULL DEFAULT 0,
        cost_total REAL NOT NULL DEFAULT 0,
        profit REAL NOT NULL DEFAULT 0,
        serial TEXT, notes TEXT, active INTEGER NOT NULL DEFAULT 1
    )""",
    """CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL, concept TEXT NOT NULL,
        amount REAL NOT NULL, currency TEXT NOT NULL,
        cashbox TEXT NOT NULL, category TEXT,
        notes TEXT, user TEXT, active INTEGER NOT NULL DEFAULT 1
    )""",
    """CREATE TABLE IF NOT EXISTS transfers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL, origin_cashbox TEXT NOT NULL,
        dest_cashbox TEXT NOT NULL, amount_origin REAL NOT NULL,
        rate REAL NOT NULL, amount_converted REAL NOT NULL,
        notes TEXT, user TEXT, active INTEGER NOT NULL DEFAULT 1
    )""",
    """CREATE TABLE IF NOT EXISTS usa_shipments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL, usa_product_id INTEGER NOT NULL,
        colombia_product_id INTEGER, sku TEXT,
        product_name TEXT NOT NULL, qty INTEGER NOT NULL,
        stock_before INTEGER NOT NULL, stock_after INTEGER NOT NULL,
        rate REAL NOT NULL, destination TEXT,
        status TEXT NOT NULL DEFAULT 'Enviado',
        received_in_colombia INTEGER NOT NULL DEFAULT 0,
        received_at TEXT, status_notes TEXT,
        notes TEXT, user TEXT, active INTEGER NOT NULL DEFAULT 1
    )""",
    """CREATE TABLE IF NOT EXISTS repairs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL, order_code TEXT,
        client TEXT, phone TEXT, device TEXT NOT NULL,
        serial TEXT, accessories TEXT, received_condition TEXT,
        issue TEXT, diagnostic TEXT, repair_solution TEXT,
        technician TEXT, warranty_days INTEGER NOT NULL DEFAULT 0,
        labor_price REAL NOT NULL DEFAULT 0,
        parts_cost REAL NOT NULL DEFAULT 0,
        external_parts_cost REAL NOT NULL DEFAULT 0,
        total REAL NOT NULL DEFAULT 0, profit REAL NOT NULL DEFAULT 0,
        amount_paid REAL NOT NULL DEFAULT 0,
        balance_due REAL NOT NULL DEFAULT 0,
        status TEXT, payment_method TEXT, delivered_at TEXT,
        notes TEXT, user TEXT, active INTEGER NOT NULL DEFAULT 1
    )""",
    """CREATE TABLE IF NOT EXISTS repair_parts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        repair_id INTEGER NOT NULL, part_product_id INTEGER NOT NULL,
        sku TEXT, part_name TEXT NOT NULL,
        qty INTEGER NOT NULL, unit_cost REAL NOT NULL,
        total_cost REAL NOT NULL, active INTEGER NOT NULL DEFAULT 1
    )""",
    """CREATE TABLE IF NOT EXISTS repair_external_parts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        repair_id INTEGER NOT NULL, part_name TEXT NOT NULL,
        qty INTEGER NOT NULL DEFAULT 1,
        unit_cost REAL NOT NULL DEFAULT 0,
        total_cost REAL NOT NULL DEFAULT 0,
        supplier TEXT, notes TEXT, active INTEGER NOT NULL DEFAULT 1
    )""",
    """CREATE TABLE IF NOT EXISTS repair_payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        repair_id INTEGER NOT NULL, date TEXT NOT NULL,
        amount REAL NOT NULL, payment_method TEXT,
        notes TEXT, user TEXT, active INTEGER NOT NULL DEFAULT 1
    )""",
    """CREATE TABLE IF NOT EXISTS voids (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL, record_type TEXT NOT NULL,
        record_id INTEGER NOT NULL,
        reason TEXT NOT NULL, user TEXT NOT NULL
    )""",
]

# Tablas en orden de migración de datos
TABLE_NAMES = [
    "users", "cashboxes", "cashbox_movements", "products",
    "purchases", "sales", "invoices", "invoice_items",
    "expenses", "transfers", "usa_shipments", "repairs",
    "repair_parts", "repair_external_parts", "repair_payments", "voids",
]


async def migrate():
    print(f"Conectando a Turso: {DB_URL}")
    client = libsql_client.create_client(url=DB_URL, auth_token=AUTH_TOKEN)

    # 1. Crear tablas en Turso
    print("\n--- Creando tablas en Turso ---")
    for ddl in TABLES_SQL:
        try:
            await client.execute(ddl)
        except Exception as e:
            print(f"  ⚠ {e}")

    print("Tablas creadas/verificadas.")

    # 2. Migrar datos desde SQLite local
    if not os.path.exists(LOCAL_DB):
        print(f"\n⚠ No se encontró {LOCAL_DB}. Solo se crearon las tablas vacías.")
        print("La DB está lista para usarse con datos nuevos.")
        await client.close()
        return

    local = sqlite3.connect(LOCAL_DB)
    local.row_factory = sqlite3.Row

    print("\n--- Migrando datos ---")
    total_migrated = 0

    for table in TABLE_NAMES:
        # Verificar si la tabla tiene columna 'active'
        cols_info = local.execute(f"PRAGMA table_info({table})").fetchall()
        col_names = [c[1] for c in cols_info]
        has_active = "active" in col_names

        if has_active:
            rows = local.execute(
                f"SELECT * FROM [{table}] WHERE active IS NULL OR active = 1"
            ).fetchall()
        else:
            rows = local.execute(f"SELECT * FROM [{table}]").fetchall()

        if not rows:
            print(f"  {table}: 0 filas")
            continue

        columns = col_names  # usar los nombres de PRAGMA

        # Excluir columnas que no existen en Turso (ej: generated columns)
        placeholders = ", ".join(["?"] * len(columns))
        cols_str = ", ".join(columns)
        sql = f"INSERT OR IGNORE INTO {table} ({cols_str}) VALUES ({placeholders})"

        ok_count = 0
        for row in rows:
            try:
                values = [row[c] for c in columns]
                await client.execute(sql, values)
                ok_count += 1
            except Exception as e:
                print(f"  ⚠ Error en {table} id={row[0] if row else '?'}: {e}")

        total_migrated += ok_count
        print(f"  {table}: {ok_count}/{len(rows)} filas migradas")

    local.close()
    await client.close()

    print(f"\n✅ Migración completada: {total_migrated} registros copiados a Turso")
    print(f"   DB URL: {DB_URL}")
    print()
    print("Ahora configura Streamlit Cloud con estos secrets:")
    print(f'  TURSO_DB_URL = "{DB_URL}"')
    print(f'  TURSO_AUTH_TOKEN = "{AUTH_TOKEN}"')


if __name__ == "__main__":
    asyncio.run(migrate())
