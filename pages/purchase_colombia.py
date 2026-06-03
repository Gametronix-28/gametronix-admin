"""Compra Colombia — registro de compras en COP."""

import streamlit as st
from components.layout import header
from db.purchase import register_purchase, list_purchases


def render():
    header("Compra Colombia", "Registra compras en COP, suma inventario a Bodega Colombia y descuenta Caja Colombia.")

    with st.form("purchase_colombia"):
        c1, c2, c3 = st.columns(3)
        sku = c1.text_input("SKU / Código")
        name = c2.text_input("Producto")
        category = c3.text_input("Categoría")
        c4, c5, c6 = st.columns(3)
        qty = c4.number_input("Cantidad", min_value=1, step=1)
        unit_cost = c5.number_input("Costo unitario COP", min_value=0.0, step=1000.0)
        supplier = c6.text_input("Proveedor")
        notes = st.text_area("Notas")

        if st.form_submit_button("Registrar compra Colombia"):
            register_purchase(
                "Colombia", sku, name, category, qty, unit_cost, "COP",
                "Caja Colombia", supplier, notes, st.session_state.user["username"],
            )
            st.success("Compra Colombia registrada.")
            st.rerun()

    st.dataframe(
        list_purchases("Colombia"),
        use_container_width=True,
        hide_index=True,
    )
