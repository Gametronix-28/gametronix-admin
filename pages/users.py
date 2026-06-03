"""Gestion de usuarios con roles y permisos (solo admin)."""

import streamlit as st
import pandas as pd
from components.layout import header
from config import ROLES, ROLE_PERMISSIONS, MENU_OPTIONS
from db.auth import list_users, add_user


def render():
    header("Usuarios", "Crear usuarios con roles y permisos personalizados.")

    user = st.session_state.user
    if user["role"] != "admin":
        st.warning("Solo administrador.")
        return

    # Mostrar usuarios existentes
    users_list = list_users()
    if users_list:
        df = pd.DataFrame(users_list)
        col_order = ["id", "username", "role", "permissions", "active", "created_at"]
        df = df[[c for c in col_order if c in df.columns]]
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Crear nuevo usuario")

    # ── Selector de rol FUERA del form (para que reactive al instante) ─
    if "new_user_role" not in st.session_state:
        st.session_state.new_user_role = "admin"

    role = st.selectbox(
        "Rol",
        ROLES,
        key="new_user_role",
        on_change=None,  # se actualiza solo
    )

    # Mostrar info del rol seleccionado
    if role == "admin":
        st.info("Administrador: acceso TOTAL a todos los modulos.")

    elif role == "personalizado":
        st.caption("Marca los modulos a los que tendra acceso:")

    else:
        preset = ROLE_PERMISSIONS.get(role, [])
        st.info(f"Modulos permitidos ({len(preset)}): {', '.join(preset)}")

    # ── Formulario de creacion ────────────────────────────
    with st.form("new_user"):
        c1, c2 = st.columns(2)
        username = c1.text_input("Nombre de usuario")
        password = c2.text_input("Contrasena", type="password")

        # Checkboxes solo si es personalizado
        selected_perms = []
        if role == "personalizado":
            selected_perms = _render_module_checkboxes()

        if st.form_submit_button("Crear usuario"):
            if not username or not password:
                st.error("Usuario y contrasena son obligatorios.")
            elif role == "personalizado" and not selected_perms:
                st.error("Selecciona al menos un modulo.")
            else:
                perms_to_save = selected_perms if role == "personalizado" else None
                add_user(username, password, role, perms_to_save)
                st.success(f"Usuario '{username}' creado con rol '{role}'.")
                st.rerun()


def _render_module_checkboxes():
    """Renderiza checkboxes para cada modulo del menu. Retorna lista de seleccionados."""
    selected = []
    cols_per_row = 4

    for i in range(0, len(MENU_OPTIONS), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            idx = i + j
            if idx >= len(MENU_OPTIONS):
                break
            module = MENU_OPTIONS[idx]
            if col.checkbox(module, key=f"perm_{idx}"):
                selected.append(module)

    return selected
