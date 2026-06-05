"""
Schema de base de datos unificado.
Define TODAS las tablas y columnas en UN solo lugar.
Se llama UNA vez al iniciar la app. Ninguna función CRUD llama a migración.
"""

import hashlib
from datetime import datetime
from config import DEFAULT_USERS, DEFAULT_CASHBOXES
from db.connection import get_db


# ── Helpers internos ───────────────────────────────────────

def _now():
    return datetime.now().isoformat(timespec="seconds")


def _hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# ── Definición central de TODAS las tablas ─────────────────
# Cada entrada = nombre_tabla → sentencia CREATE TABLE IF NOT EXISTS

TABLES = {
    "users": """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'caja',
            permissions TEXT,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        )
    """,
    "cashboxes": """
        CREATE TABLE IF NOT EXISTS cashboxes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            currency TEXT NOT NULL,
            balance REAL NOT NULL DEFAULT 0
        )
    """,
    "cashbox_movements": """
        CREATE TABLE IF NOT EXISTS cashbox_movements (
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
        )
    """,
    "products": """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT,
            name TEXT NOT NULL,
            category TEXT,
            stock INTEGER NOT NULL DEFAULT 0,
            min_stock INTEGER NOT NULL DEFAULT 2,
            cost REAL NOT NULL DEFAULT 0,
            price REAL NOT NULL DEFAULT 0,
            currency TEXT NOT NULL DEFAULT 'COP',
            location TEXT,
            warehouse TEXT NOT NULL DEFAULT 'Colombia',
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        )
    """,
    "purchases": """
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            warehouse TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            sku TEXT,
            product_name TEXT NOT NULL,
            qty INTEGER NOT NULL,
            unit_cost REAL NOT NULL,
            total REAL NOT NULL,
            currency TEXT NOT NULL,
            cashbox TEXT NOT NULL,
            supplier TEXT,
            notes TEXT,
            user TEXT,
            active INTEGER NOT NULL DEFAULT 1
        )
    """,
    "sales": """
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            sku TEXT,
            product_name TEXT NOT NULL,
            qty INTEGER NOT NULL,
            unit_cost REAL NOT NULL,
            unit_price REAL NOT NULL,
            total REAL NOT NULL,
            cost_total REAL NOT NULL,
            profit REAL NOT NULL,
            currency TEXT NOT NULL,
            cashbox TEXT NOT NULL,
            client TEXT,
            payment_method TEXT,
            notes TEXT,
            user TEXT,
            active INTEGER NOT NULL DEFAULT 1
        )
    """,
    "invoices": """
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            client TEXT,
            payment_method TEXT,
            total REAL NOT NULL DEFAULT 0,
            cost_total REAL NOT NULL DEFAULT 0,
            profit REAL NOT NULL DEFAULT 0,
            currency TEXT NOT NULL DEFAULT 'COP',
            cashbox TEXT NOT NULL DEFAULT 'Caja Colombia',
            notes TEXT,
            user TEXT,
            active INTEGER NOT NULL DEFAULT 1
        )
    """,
    "invoice_items": """
        CREATE TABLE IF NOT EXISTS invoice_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            sku TEXT,
            product_name TEXT NOT NULL,
            qty INTEGER NOT NULL,
            unit_cost REAL NOT NULL DEFAULT 0,
            unit_price REAL NOT NULL DEFAULT 0,
            total REAL NOT NULL DEFAULT 0,
            cost_total REAL NOT NULL DEFAULT 0,
            profit REAL NOT NULL DEFAULT 0,
            serial TEXT,
            notes TEXT,
            active INTEGER NOT NULL DEFAULT 1
        )
    """,
    "expenses": """
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            concept TEXT NOT NULL,
            amount REAL NOT NULL,
            currency TEXT NOT NULL,
            cashbox TEXT NOT NULL,
            category TEXT,
            notes TEXT,
            user TEXT,
            active INTEGER NOT NULL DEFAULT 1
        )
    """,
    "transfers": """
        CREATE TABLE IF NOT EXISTS transfers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            origin_cashbox TEXT NOT NULL,
            dest_cashbox TEXT NOT NULL,
            amount_origin REAL NOT NULL,
            rate REAL NOT NULL,
            amount_converted REAL NOT NULL,
            notes TEXT,
            user TEXT,
            active INTEGER NOT NULL DEFAULT 1
        )
    """,
    "usa_shipments": """
        CREATE TABLE IF NOT EXISTS usa_shipments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            usa_product_id INTEGER NOT NULL,
            colombia_product_id INTEGER,
            sku TEXT,
            product_name TEXT NOT NULL,
            qty INTEGER NOT NULL,
            stock_before INTEGER NOT NULL,
            stock_after INTEGER NOT NULL,
            rate REAL NOT NULL,
            destination TEXT,
            status TEXT NOT NULL DEFAULT 'Enviado',
            received_in_colombia INTEGER NOT NULL DEFAULT 0,
            received_at TEXT,
            status_notes TEXT,
            notes TEXT,
            user TEXT,
            active INTEGER NOT NULL DEFAULT 1
        )
    """,
    "repairs": """
        CREATE TABLE IF NOT EXISTS repairs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            order_code TEXT,
            client TEXT,
            phone TEXT,
            device TEXT NOT NULL,
            serial TEXT,
            accessories TEXT,
            received_condition TEXT,
            issue TEXT,
            diagnostic TEXT,
            repair_solution TEXT,
            technician TEXT,
            warranty_days INTEGER NOT NULL DEFAULT 0,
            labor_price REAL NOT NULL DEFAULT 0,
            parts_cost REAL NOT NULL DEFAULT 0,
            external_parts_cost REAL NOT NULL DEFAULT 0,
            total REAL NOT NULL DEFAULT 0,
            profit REAL NOT NULL DEFAULT 0,
            amount_paid REAL NOT NULL DEFAULT 0,
            balance_due REAL NOT NULL DEFAULT 0,
            status TEXT,
            payment_method TEXT,
            delivered_at TEXT,
            notes TEXT,
            additional_devices TEXT,
            user TEXT,
            active INTEGER NOT NULL DEFAULT 1
        )
    """,
    "repair_parts": """
        CREATE TABLE IF NOT EXISTS repair_parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repair_id INTEGER NOT NULL,
            part_product_id INTEGER NOT NULL,
            sku TEXT,
            part_name TEXT NOT NULL,
            qty INTEGER NOT NULL,
            unit_cost REAL NOT NULL,
            total_cost REAL NOT NULL,
            active INTEGER NOT NULL DEFAULT 1
        )
    """,
    "repair_external_parts": """
        CREATE TABLE IF NOT EXISTS repair_external_parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repair_id INTEGER NOT NULL,
            part_name TEXT NOT NULL,
            qty INTEGER NOT NULL DEFAULT 1,
            unit_cost REAL NOT NULL DEFAULT 0,
            total_cost REAL NOT NULL DEFAULT 0,
            supplier TEXT,
            notes TEXT,
            active INTEGER NOT NULL DEFAULT 1
        )
    """,
    "repair_payments": """
        CREATE TABLE IF NOT EXISTS repair_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repair_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            payment_method TEXT,
            notes TEXT,
            user TEXT,
            active INTEGER NOT NULL DEFAULT 1
        )
    """,
    "cash_closings": """
        CREATE TABLE IF NOT EXISTS cash_closings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            cashbox TEXT NOT NULL,
            balance REAL NOT NULL,
            user TEXT NOT NULL,
            notes TEXT
        )
    """,
    "debts": """
        CREATE TABLE IF NOT EXISTS debts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            supplier TEXT NOT NULL,
            concept TEXT,
            amount REAL NOT NULL,
            currency TEXT NOT NULL DEFAULT 'COP',
            cashbox TEXT NOT NULL,
            paid INTEGER NOT NULL DEFAULT 0,
            paid_date TEXT,
            notes TEXT,
            user TEXT,
            active INTEGER NOT NULL DEFAULT 1
        )
    """,
    "customers": """
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            notes TEXT,
            created_at TEXT NOT NULL
        )
    """,
    "voids": """
        CREATE TABLE IF NOT EXISTS voids (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            record_type TEXT NOT NULL,
            record_id INTEGER NOT NULL,
            reason TEXT NOT NULL,
            user TEXT NOT NULL
        )
    """,
}

# ── Columnas migrables (agregadas en versiones posteriores) ─
# Solo se agregan si no existen. No modifican datos existentes.

MIGRATABLE_COLUMNS = {
    "users": {
        "permissions": "TEXT",
    },
    "usa_shipments": {
        "status": "TEXT NOT NULL DEFAULT 'Enviado'",
        "received_in_colombia": "INTEGER NOT NULL DEFAULT 0",
        "received_at": "TEXT",
        "status_notes": "TEXT",
    },
    "repairs": {
        "order_code": "TEXT",
        "phone": "TEXT",
        "serial": "TEXT",
        "accessories": "TEXT",
        "received_condition": "TEXT",
        "diagnostic": "TEXT",
        "repair_solution": "TEXT",
        "technician": "TEXT",
        "warranty_days": "INTEGER NOT NULL DEFAULT 0",
        "external_parts_cost": "REAL NOT NULL DEFAULT 0",
        "amount_paid": "REAL NOT NULL DEFAULT 0",
        "balance_due": "REAL NOT NULL DEFAULT 0",
        "delivered_at": "TEXT",
        "additional_devices": "TEXT",
    },
    "products": {
        "attributes": "TEXT",
    },
}


# ── Funciones principales ──────────────────────────────────

def initialize_database():
    """
    Inicializa la base de datos: crea tablas faltantes, agrega columnas nuevas,
    indices, y siembra datos por defecto.
    """
    with get_db() as con:
        cur = con.cursor()

        # 1. Crear todas las tablas (si no existen)
        for ddl in TABLES.values():
            cur.execute(ddl)

        # 2. Migrar columnas faltantes
        _migrate_columns(cur)

        # 3. Crear indices (si no existen)
        _create_indexes(cur)

        # 4. Sembrar datos por defecto
        _seed_defaults(cur)

        # 5. Completar order_code en reparaciones antiguas
        _backfill_order_codes(cur)


# ── Indices para acelerar busquedas ─────────────────────────

_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_products_warehouse ON products(warehouse, active)",
    "CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku, warehouse)",
    "CREATE INDEX IF NOT EXISTS idx_purchases_warehouse ON purchases(warehouse, date)",
    "CREATE INDEX IF NOT EXISTS idx_purchases_product ON purchases(product_id)",
    "CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(date)",
    "CREATE INDEX IF NOT EXISTS idx_invoice_items_invoice ON invoice_items(invoice_id)",
    "CREATE INDEX IF NOT EXISTS idx_repairs_date ON repairs(date)",
    "CREATE INDEX IF NOT EXISTS idx_repairs_status ON repairs(status, active)",
    "CREATE INDEX IF NOT EXISTS idx_repairs_client ON repairs(client, active)",
    "CREATE INDEX IF NOT EXISTS idx_repair_payments_repair ON repair_payments(repair_id, active)",
    "CREATE INDEX IF NOT EXISTS idx_cashbox_movements_cashbox ON cashbox_movements(cashbox, date, active)",
    "CREATE INDEX IF NOT EXISTS idx_cashbox_movements_type ON cashbox_movements(type, active)",
    "CREATE INDEX IF NOT EXISTS idx_usa_shipments_status ON usa_shipments(status, active)",
    "CREATE INDEX IF NOT EXISTS idx_expenses_cashbox ON expenses(cashbox, date)",
    "CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone)",
    "CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(date, active)",
]


def _create_indexes(cur):
    """Crea indices para acelerar las consultas mas frecuentes."""
    for idx_sql in _INDEXES:
        try:
            cur.execute(idx_sql)
        except Exception:
            pass


def _migrate_columns(cur):
    """
    Agrega columnas nuevas a tablas existentes.
    Compara PRAGMA table_info contra MIGRATABLE_COLUMNS.
    Solo agrega — nunca borra ni modifica datos.
    """
    for table, columns in MIGRATABLE_COLUMNS.items():
        existing = {r[1] for r in cur.execute(f"PRAGMA table_info({table})").fetchall()}
        for col_name, col_def in columns.items():
            if col_name not in existing:
                cur.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_def}")


def _seed_defaults(cur):
    """Siembra usuarios y cajas por defecto si la DB está vacía."""
    if cur.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        for u in DEFAULT_USERS:
            cur.execute(
                "INSERT INTO users(username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
                (u["username"], _hash_password(u["password"]), u["role"], _now()),
            )
    if cur.execute("SELECT COUNT(*) FROM cashboxes").fetchone()[0] == 0:
        for cb in DEFAULT_CASHBOXES:
            cur.execute(
                "INSERT INTO cashboxes(name, currency, balance) VALUES (?, ?, ?)",
                (cb["name"], cb["currency"], cb["balance"]),
            )


def _backfill_order_codes(cur):
    """Completa order_code para reparaciones antiguas que no lo tengan."""
    rows = cur.execute(
        "SELECT id FROM repairs WHERE order_code IS NULL OR order_code = ''"
    ).fetchall()
    for row in rows:
        rid = row["id"] if hasattr(row, "keys") else row[0]
        cur.execute(
            "UPDATE repairs SET order_code = ? WHERE id = ?",
            (f"REP-{int(rid):05d}", rid),
        )
