"""Bodega Colombia — inventario con historial de compras en tabs."""

import streamlit as st
from components.layout import header
from db.product import list_inventory
from db.purchase import list_purchases


def render():
    header("Bodega Colombia", "Inventario disponible para venta en Colombia.")

    tab1, tab2 = st.tabs(["📦 Inventario", "📋 Historial de compras"])

    with tab1:
        q = st.text_input("Buscar en Bodega Colombia")
        st.dataframe(list_inventory("Colombia", q), use_container_width=True, hide_index=True)

    with tab2:
        st.dataframe(list_purchases("Colombia"), use_container_width=True, hide_index=True)
