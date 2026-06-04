"""
GAMETRONIX Admin Pro — Entry Point.
App Streamlit para gestion de inventario, ventas y reparaciones.
"""

import streamlit as st
from config import APP_CONFIG, CSS_STYLES, MENU_OPTIONS
from db.schema import initialize_database
from components.layout import render_topbar
from pages import render_page
from pages.login import render_login


def get_allowed_menu(user):
    """
    Retorna la lista de menus que el usuario puede ver segun sus permisos.
    Si permissions es vacio (admin) → ve todo.
    """
    permissions = user.get("permissions", [])
    if not permissions:
        return MENU_OPTIONS  # admin: acceso total
    return [m for m in MENU_OPTIONS if m in permissions]


# ── Configuracion inicial ──────────────────────────────────
st.set_page_config(**APP_CONFIG)
st.markdown(CSS_STYLES, unsafe_allow_html=True)

# ── Inicializar base de datos ──────────────────────────────
initialize_database()

# ── Backup diario ──────────────────────────────────────────
from utils.backup import run_backup
run_backup()

# ── Autenticacion ──────────────────────────────────────────
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "Dashboard ganancias"

if not st.session_state.user:
    render_login()
    st.stop()

# ── Barra superior + menu horizontal filtrado ──────────────
user = st.session_state.user
allowed_menu = get_allowed_menu(user)

# Si la pagina actual no esta permitida, redirigir al dashboard
if st.session_state.page not in allowed_menu:
    st.session_state.page = allowed_menu[0] if allowed_menu else "Dashboard ganancias"


def on_logout():
    st.session_state.user = None
    st.session_state.page = "Dashboard ganancias"


selected_page = render_topbar(user, allowed_menu, on_logout)
if selected_page is not None and selected_page in allowed_menu:
    st.session_state.page = selected_page
    st.rerun()

# ── Proteger pagina ────────────────────────────────────────
if st.session_state.page not in allowed_menu:
    st.error("No tienes permiso para acceder a esta pagina.")
    st.stop()

# ── Renderizar pagina actual ───────────────────────────────
render_page()
