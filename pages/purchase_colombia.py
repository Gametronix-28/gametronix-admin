"""Compra Colombia — registro de compras en COP con selector de productos."""

import streamlit as st
from components.layout import header
from db.product import list_inventory, generate_sku
from db.purchase import register_purchase, list_purchases


def render():
    header("Compra Colombia", "Registra compras en COP, suma inventario a Bodega Colombia y descuenta Caja Colombia.")

    inventory = list_inventory("Colombia")

    # Selector de producto existente O nuevo
    if inventory.empty:
        modo = "Crear nuevo producto"
    else:
        modo = st.radio("Modo", ["Agregar a producto existente", "Crear nuevo producto"], horizontal=True)

    with st.form("purchase_colombia"):
        if modo == "Agregar a producto existente":
            product_label = st.selectbox(
                "Producto en bodega",
                inventory.apply(
                    lambda r: f"{r['id']} - {r['sku']} - {r['name']} - Stock {r['stock']} - Costo {r['cost']}",
                    axis=1,
                ),
            )
            pid = int(product_label.split(" - ")[0])
            row = inventory[inventory["id"] == pid].iloc[0]
            sku = row["sku"]
            name = row["name"]
            category = row.get("category") or ""
            st.info(f"SKU: {sku} | Stock actual: {row['stock']} | Costo: {row['cost']}")
        else:
            auto_sku = generate_sku("Colombia")
            c1, c2, c3 = st.columns(3)
            sku = c1.text_input("SKU / Codigo", value=auto_sku)
            name = c2.text_input("Producto")
            category = c3.text_input("Categoria")

        c4, c5, c6 = st.columns(3)
        qty = c4.number_input("Cantidad", min_value=1, step=1, value=1)
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

    st.dataframe(list_purchases("Colombia"), use_container_width=True, hide_index=True)
