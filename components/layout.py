"""Componentes de layout: header, sidebar, menu horizontal, estilos."""

import streamlit as st


def header(title, subtitle=""):
    """Renderiza un titulo y subtitulo con el estilo GAMETRONIX."""
    st.markdown(f'<div class="gt-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="gt-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def render_topbar(user, menu_options, on_logout):
    """
    Renderiza barra superior con logo, usuario y menu horizontal.
    Retorna la pagina seleccionada.
    """
    st.markdown("""
    <style>
    .gt-topbar {
        background: #111827;
        padding: 0.5rem 1.5rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 0;
    }
    .gt-logo {
        color: white;
        font-size: 20px;
        font-weight: 900;
    }
    .gt-user {
        color: #d1d5db;
        font-size: 13px;
    }
    .gt-user strong {
        color: white;
    }
    .gt-menu-row {
        display: flex;
        flex-wrap: wrap;
        gap: 4px;
        padding: 0.5rem 1rem;
        background: #1f2937;
        margin-bottom: 1rem;
        border-radius: 0 0 8px 8px;
    }
    .gt-menu-item {
        background: #374151;
        color: #d1d5db;
        border: none;
        padding: 6px 14px;
        border-radius: 6px;
        cursor: pointer;
        font-size: 13px;
        white-space: nowrap;
        transition: all 0.2s;
    }
    .gt-menu-item:hover {
        background: #4b5563;
        color: white;
    }
    .gt-menu-item.active {
        background: #2563eb;
        color: white;
        font-weight: 600;
    }
    .gt-logout {
        background: #dc2626;
        color: white;
        border: none;
        padding: 6px 14px;
        border-radius: 6px;
        cursor: pointer;
        font-size: 13px;
        margin-left: auto;
    }
    .gt-logout:hover {
        background: #ef4444;
    }
    </style>
    """, unsafe_allow_html=True)

    # Barra superior con logo y usuario
    st.markdown(f"""
    <div class="gt-topbar">
        <span class="gt-logo">🎮 GAMETRONIX</span>
        <span class="gt-user">Usuario: <strong>{user['username']}</strong> | Rol: {user['role']}</span>
    </div>
    """, unsafe_allow_html=True)

    # Menu horizontal con columnas
    cols_per_row = 8
    n = len(menu_options)
    page_idx = menu_options.index(st.session_state.get("page", menu_options[0]))

    # Generar botones del menu
    selected = None
    for row_start in range(0, n, cols_per_row):
        cols = st.columns(min(cols_per_row, n - row_start))
        for i, col in enumerate(cols):
            idx = row_start + i
            if idx >= n:
                break
            option = menu_options[idx]
            is_active = (idx == page_idx)
            label = f"**{option}**" if is_active else option
            if col.button(label, key=f"menu_{idx}", use_container_width=True,
                          type="primary" if is_active else "secondary"):
                selected = option

    # Boton cerrar sesion
    if st.button("🚪 Cerrar sesion", key="logout_btn"):
        on_logout()
        return None

    return selected


def render_sidebar(user, menu_options, on_logout):
    """
    Renderiza barra lateral con menu de navegacion (modo legacy).
    Mantenida por compatibilidad.
    """
    with st.sidebar:
        st.markdown("## 🎮 GAMETRONIX")
        st.write(f"Usuario: **{user['username']}**")
        st.caption(f"Rol: {user['role']}")
        page = st.radio("Menu", menu_options)
        if st.button("Cerrar sesion"):
            on_logout()
        return page
