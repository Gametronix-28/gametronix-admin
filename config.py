"""
GAMETRONIX Admin Pro — Configuración central.
Constantes, estilos, credenciales default y configuración de la app.
"""

import os

# ── Base de datos ──────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), "gametronix.db")

# ── Configuración de Streamlit ─────────────────────────────
APP_CONFIG = {
    "page_title": "GAMETRONIX Admin Pro",
    "page_icon": "🎮",
    "layout": "wide",
}

# ── Estilos CSS globales ───────────────────────────────────
CSS_STYLES = """
<style>
.block-container {padding-top: 1rem;}
.gt-title {font-size: 32px; font-weight: 900; color: #111827;}
.gt-subtitle {color:#6b7280; font-size:14px; margin-bottom:18px;}
div[data-testid="metric-container"] {
    background: #111827;
    border-radius: 18px;
    padding: 16px;
    color: white;
}
div[data-testid="metric-container"] label {color: #d1d5db !important;}
@media print {
    .stApp header, .stApp footer, .stSidebar, button, [data-testid="stSidebar"] {display: none !important;}
    .stApp {margin: 0 !important; padding: 0 !important;}
}
</style>

<!-- PWA Manifest -->
<link rel="manifest" href="/static/manifest.json">
<meta name="theme-color" content="#111827">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black">
<meta name="apple-mobile-web-app-title" content="GAMETRONIX">
"""

# ── Credenciales por defecto ───────────────────────────────
DEFAULT_USERS = [
    {"username": "admin", "password": "admin123", "role": "admin"},
]

DEFAULT_CASHBOXES = [
    {"name": "Caja Colombia", "currency": "COP", "balance": 0},
    {"name": "Caja USA", "currency": "USD", "balance": 0},
]

# ── Monedas y tasas ────────────────────────────────────────
CURRENCY_SYMBOLS = {"COP": "COP", "USD": "USD"}
DEFAULT_RATE = 4000.0

# ── Menú de la aplicación ──────────────────────────────────
MENU_OPTIONS = [
    "Dashboard ganancias",
    "Caja USA",
    "Compra USA",
    "Bodega USA",
    "Envíos USA",
    "Caja Colombia",
    "Compra Colombia",
    "Bodega Colombia",
    "Venta Colombia",
    "Bodega Repuestos",
    "Taller Reparaciones",
    "Transferencia con tasa",
    "Gastos por caja",
    "Borrar / anular registros",
    "Usuarios",
    "Importar / Exportar",
]

# ── Roles del sistema ──────────────────────────────────────
ROLES = ["admin", "caja_colombia", "caja_usa", "inventario", "consulta", "personalizado"]

# Permisos predefinidos por rol (menús que puede ver)
ROLE_PERMISSIONS = {
    "admin": [],  # vacío = acceso total
    "caja_colombia": [
        "Dashboard ganancias",
        "Caja Colombia",
        "Compra Colombia",
        "Bodega Colombia",
        "Venta Colombia",
        "Gastos por caja",
        "Transferencia con tasa",
        "Importar / Exportar",
    ],
    "caja_usa": [
        "Dashboard ganancias",
        "Caja USA",
        "Compra USA",
        "Bodega USA",
        "Envíos USA",
        "Transferencia con tasa",
        "Importar / Exportar",
    ],
    "inventario": [
        "Dashboard ganancias",
        "Bodega USA",
        "Bodega Colombia",
        "Bodega Repuestos",
        "Importar / Exportar",
    ],
    "consulta": [
        "Dashboard ganancias",
        "Bodega USA",
        "Bodega Colombia",
        "Bodega Repuestos",
        "Caja Colombia",
        "Caja USA",
        "Taller Reparaciones",
    ],
}

# ── Turso (nube) ──────────────────────────────────────────
# Para usar la DB en la nube, cambia USE_TURSO a True
# y configura TURSO_DB_URL y TURSO_AUTH_TOKEN desde st.secrets o variables de entorno.
import os

USE_TURSO = os.getenv("USE_TURSO", "").lower() in ("true", "1", "yes")
TURSO_DB_URL = os.getenv("TURSO_DB_URL", "")
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN", "")

# Intentar cargar desde st.secrets si existe (Streamlit Cloud)
try:
    import streamlit as st
    if st.secrets.get("TURSO_DB_URL"):
        TURSO_DB_URL = st.secrets["TURSO_DB_URL"]
        TURSO_AUTH_TOKEN = st.secrets.get("TURSO_AUTH_TOKEN", "")
        USE_TURSO = True
except Exception:
    pass
