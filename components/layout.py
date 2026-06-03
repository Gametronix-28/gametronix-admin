"""Componentes de layout: header, sidebar, estilos."""

import streamlit as st


def header(title, subtitle=""):
    """Renderiza un título y subtítulo con el estilo GAMETRONIX."""
    st.markdown(f'<div class="gt-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="gt-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def render_sidebar(user, menu_options, on_logout):
    """
    Renderiza la barra lateral con menú de navegación.
    user: dict con username y role.
    menu_options: lista de strings con las opciones del menú.
    on_logout: callback para cerrar sesión.
    Retorna la página seleccionada.
    """
    with st.sidebar:
        st.markdown("## 🎮 GAMETRONIX")
        st.write(f"Usuario: **{user['username']}**")
        st.caption(f"Rol: {user['role']}")
        page = st.radio("Menú", menu_options)
        if st.button("Cerrar sesión"):
            on_logout()
        return page
