"""
GAMETRONIX Admin Pro — Entry Point.
App Streamlit para gestión de inventario, ventas y reparaciones.
"""

import streamlit as st
from config import APP_CONFIG, CSS_STYLES
from db.schema import initialize_database
from components.layout import render_topbar
from pages import MENU_OPTIONS, render_page
from pages.login import render_login

# ── Configuración inicial ──────────────────────────────────
st.set_page_config(**APP_CONFIG)
st.markdown(CSS_STYLES, unsafe_allow_html=True)

# ── Inicializar base de datos ──────────────────────────────
initialize_database()

# ── Autenticación ──────────────────────────────────────────
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "Dashboard ganancias"

if not st.session_state.user:
    render_login()
    st.stop()

# ── Barra superior + menú horizontal ───────────────────────
user = st.session_state.user


def on_logout():
    st.session_state.user = None
    st.session_state.page = "Dashboard ganancias"


selected_page = render_topbar(user, MENU_OPTIONS, on_logout)
if selected_page is not None:
    st.session_state.page = selected_page
    st.rerun()

# ── Renderizar página actual ───────────────────────────────
render_page()
