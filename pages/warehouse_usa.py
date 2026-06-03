"""Bodega USA — inventario."""

import streamlit as st
from components.layout import header
from db.product import list_inventory


def render():
    header("Bodega USA", "Inventario disponible en USA.")
    q = st.text_input("Buscar en Bodega USA")
    st.dataframe(
        list_inventory("USA", q),
        use_container_width=True,
        hide_index=True,
    )
