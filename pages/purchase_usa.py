"""Compra USA — registro de compras en USD."""

import streamlit as st
from components.layout import header
from db.purchase import register_purchase, list_purchases


def render():
    header("Compra USA", "Registra compras en USD, suma inventario a Bodega USA y descuenta Caja USA.")

    with st.form("purchase_usa"):
        c1, c2, c3 = st.columns(3)
        sku = c1.text_input("SKU / Código")
        name = c2.text_input("Producto")
        category = c3.text_input("Categoría")
        c4, c5, c6 = st.columns(3)
        qty = c4.number_input("Cantidad", min_value=1, step=1)
        unit_cost = c5.number_input("Costo unitario USD", min_value=0.0, step=1.0)
        supplier = c6.text_input("Proveedor")
        notes = st.text_area("Notas")

        if st.form_submit_button("Registrar compra USA"):
            register_purchase(
                "USA", sku, name, category, qty, unit_cost, "USD",
                "Caja USA", supplier, notes, st.session_state.user["username"],
            )
            st.success("Compra USA registrada.")
            st.rerun()

    st.dataframe(
        list_purchases("USA"),
        use_container_width=True,
        hide_index=True,
    )
