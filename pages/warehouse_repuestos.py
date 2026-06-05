"""Bodega Repuestos — inventario de repuestos para taller."""

import streamlit as st
from components.layout import header
from db.product import list_inventory, generate_sku
from db.purchase import register_purchase


def render():
    header("Bodega Repuestos", "Inventario de repuestos para taller.")
    q = st.text_input("Buscar repuesto")
    st.dataframe(
        list_inventory("Repuestos", q),
        use_container_width=True,
        hide_index=True,
    )

    inventory = list_inventory("Repuestos")

    with st.expander("Agregar / comprar repuesto"):
        if not inventory.empty:
            modo = st.radio("Modo", ["Agregar a repuesto existente", "Crear nuevo repuesto"], horizontal=True)
        else:
            modo = "Crear nuevo repuesto"

        with st.form("purchase_part"):
            if modo == "Agregar a repuesto existente":
                product_label = st.selectbox(
                    "Repuesto en bodega",
                    inventory.apply(
                        lambda r: f"{r['id']} - {r['sku']} - {r['name']} - Stock {r['stock']} - Costo {r['cost']}",
                        axis=1,
                    ),
                )
                pid = int(product_label.split(" - ")[0])
                row = inventory[inventory["id"] == pid].iloc[0]
                sku = row["sku"]
                name = row["name"]
                category = row.get("category") or "Repuesto"
                st.info(f"SKU: {sku} | Stock actual: {row['stock']} | Costo: {row['cost']}")
            else:
                auto_sku = generate_sku("Repuestos")
                c1, c2, c3 = st.columns(3)
                sku = c1.text_input("SKU / Codigo repuesto", value=auto_sku)
                name = c2.text_input("Repuesto")
                category = c3.text_input("Categoria", value="Repuesto")

            c4, c5, c6 = st.columns(3)
            qty = c4.number_input("Cantidad", min_value=1, step=1)
            unit_cost = c5.number_input("Costo unitario COP", min_value=0.0, step=1000.0)
            supplier = c6.text_input("Proveedor")
            fiado = st.checkbox("💳 Fiado / a credito", value=False)
            notes = st.text_area("Notas")

            if st.form_submit_button("Guardar repuesto"):
                register_purchase(
                    "Repuestos", sku, name, category, qty, unit_cost, "COP",
                    "Caja Colombia", supplier, notes, st.session_state.user["username"],
                    fiado=fiado,
                )
                msg = "A CREDITO. Deuda registrada." if fiado else "Se desconto de Caja Colombia."
                st.success(f"Repuesto agregado. {msg}")
                st.rerun()
