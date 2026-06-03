"""Página de inicio de sesión."""

import streamlit as st
from components.layout import header
from db.auth import authenticate


def render_login():
    """Renderiza el formulario de login."""
    header(
        "GAMETRONIX Admin Pro",
        "Inventario, cajas, compras, ventas, envíos con estado, repuestos y taller.",
    )
    with st.form("login"):
        username = st.text_input("Usuario", key="login_user")
        password = st.text_input("Contraseña", type="password", key="login_pass")
        if st.form_submit_button("Entrar"):
            user = authenticate(username, password)
            if user:
                st.session_state.user = user
                st.session_state.page = "Dashboard ganancias"
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")
