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
</style>
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

# ── Roles del sistema ──────────────────────────────────────
ROLES = ["admin", "caja", "inventario", "consulta"]

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
