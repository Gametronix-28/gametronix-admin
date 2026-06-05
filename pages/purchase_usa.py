"""Compra USA — registro de compras en USD con selector de productos."""

import streamlit as st
from components.layout import header
from db.product import list_inventory, generate_sku
from db.purchase import register_purchase


def render():
    header("Compra USA", "Registra compras en USD, suma inventario a Bodega USA y descuenta Caja USA.")

    inventory = list_inventory("USA")

    if inventory.empty:
        modo = "Crear nuevo producto"
    else:
        modo = st.radio("Modo", ["Agregar a producto existente", "Crear nuevo producto"], horizontal=True)

    with st.form("purchase_usa"):
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
            auto_sku = generate_sku("USA")
            c1, c2, c3 = st.columns(3)
            sku = c1.text_input("SKU / Codigo", value=auto_sku)
            name = c2.text_input("Producto")
            category = c3.text_input("Categoria")

        c4, c5, c6 = st.columns(3)
        qty = c4.number_input("Cantidad", min_value=1, step=1, value=1)
        unit_cost = c5.number_input("Costo unitario USD", min_value=0.0, step=1.0)
        supplier = c6.text_input("Proveedor")
        fiado = st.checkbox("💳 Fiado / a credito (no descuenta caja, registra deuda)", value=False)
        notes = st.text_area("Notas")

        if st.form_submit_button("Registrar compra USA"):
            register_purchase(
                "USA", sku, name, category, qty, unit_cost, "USD",
                "Caja USA", supplier, notes, st.session_state.user["username"],
                fiado=fiado,
            )
            if fiado:
                st.success("Compra USA registrada A CREDITO. La deuda queda pendiente por pagar.")
            else:
                st.success("Compra USA registrada. Se desconto de Caja USA.")
            st.rerun()

    # El historial de compras ahora esta en Bodega USA → Historial de compras
