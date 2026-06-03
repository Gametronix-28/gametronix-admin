"""Bodega Colombia — inventario."""

import streamlit as st
from components.layout import header
from db.product import list_inventory


def render():
    header("Bodega Colombia", "Inventario disponible para venta en Colombia.")
    q = st.text_input("Buscar en Bodega Colombia")
    st.dataframe(
        list_inventory("Colombia", q),
        use_container_width=True,
        hide_index=True,
    )
