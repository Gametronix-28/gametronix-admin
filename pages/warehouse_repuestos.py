"""Bodega Repuestos — inventario de repuestos para taller."""

import streamlit as st
from components.layout import header
from db.product import list_inventory
from db.purchase import register_purchase


def render():
    header("Bodega Repuestos", "Inventario de repuestos para taller.")
    q = st.text_input("Buscar repuesto")
    st.dataframe(
        list_inventory("Repuestos", q),
        use_container_width=True,
        hide_index=True,
    )

    with st.expander("Agregar / comprar repuesto"):
        with st.form("purchase_part"):
            c1, c2, c3 = st.columns(3)
            sku = c1.text_input("SKU / Código repuesto")
            name = c2.text_input("Repuesto")
            category = c3.text_input("Categoría", value="Repuesto")
            c4, c5, c6 = st.columns(3)
            qty = c4.number_input("Cantidad", min_value=1, step=1)
            unit_cost = c5.number_input("Costo unitario COP", min_value=0.0, step=1000.0)
            supplier = c6.text_input("Proveedor")
            notes = st.text_area("Notas")

            if st.form_submit_button("Guardar repuesto"):
                register_purchase(
                    "Repuestos", sku, name, category, qty, unit_cost, "COP",
                    "Caja Colombia", supplier, notes, st.session_state.user["username"],
                )
                st.success("Repuesto agregado.")
                st.rerun()
