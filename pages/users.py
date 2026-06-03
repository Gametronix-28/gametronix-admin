"""Gestión de usuarios (solo admin)."""

import streamlit as st
import pandas as pd
from components.layout import header
from config import ROLES
from db.auth import list_users, add_user


def render():
    header("Usuarios", "Crear usuarios y roles.")
    user = st.session_state.user

    if user["role"] != "admin":
        st.warning("Solo administrador.")
        return

    st.dataframe(
        pd.DataFrame(list_users()),
        use_container_width=True,
        hide_index=True,
    )

    with st.form("new_user"):
        username = st.text_input("Nuevo usuario")
        password = st.text_input("Contraseña", type="password")
        role = st.selectbox("Rol", ROLES)
        if st.form_submit_button("Crear usuario"):
            add_user(username, password, role)
            st.success("Usuario creado.")
            st.rerun()
