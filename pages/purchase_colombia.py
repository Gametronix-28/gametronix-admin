"""Compra Colombia — registro de compras en COP con selector de productos."""

import streamlit as st
from components.layout import header
from utils.format import money
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

    # ── Ensamblar producto ──────────────────────────────
    st.divider()
    st.subheader("🔧 Ensamblar producto")
    st.caption("Combina partes de bodega + compras externas en un solo producto para la venta. Las partes se descuentan del inventario y el costo se suma al producto final.")

    bodega_col = list_inventory("Colombia")

    with st.form("assemble_product"):
        # Producto final
        st.markdown("**Producto final**")
        auto_sku = generate_sku("Colombia")
        c1, c2 = st.columns(2)
        final_name = c1.text_input("Nombre del producto armado", placeholder="Ej: Xbox 360 Completa")
        final_sku = c2.text_input("SKU producto final", value=auto_sku, key="assemble_sku")

        # Partes desde Bodega Colombia (se descuentan del stock)
        st.markdown("**Partes desde Bodega Colombia (se descuentan del stock)**")
        used_parts = []
        if not bodega_col.empty:
            for i in range(1, 7):
                pc1, pc2 = st.columns([3, 1])
                label = pc1.selectbox(
                    f"Producto {i}",
                    ["No usar"] + list(bodega_col.apply(
                        lambda r: f"{r['id']} - {r['sku']} - {r['name']} - Stock {r['stock']} - Costo {r['cost']}",
                        axis=1,
                    )),
                    key=f"assemble_part_{i}",
                )
                qty = pc2.number_input(f"Cant {i}", min_value=0, step=1, key=f"assemble_qty_{i}")
                if label != "No usar" and qty > 0:
                    used_parts.append((int(label.split(" - ")[0]), int(qty)))
        else:
            st.info("No hay productos en Bodega Colombia.")

        # Compras externas
        st.markdown("**Partes compradas por fuera (se suman al costo)**")
        external_parts = []
        for i in range(1, 4):
            with st.expander(f"Compra externa {i}", expanded=(i == 1)):
                ec1, ec2 = st.columns(2)
                part_name = ec1.text_input(f"Nombre parte externa {i}", key=f"assemble_ext_name_{i}")
                ext_cost = ec2.number_input(f"Costo externo COP {i}", min_value=0.0, step=1000.0, key=f"assemble_ext_cost_{i}")
                if part_name.strip() and ext_cost > 0:
                    external_parts.append({"part_name": part_name.strip(), "unit_cost": float(ext_cost)})

        # Vista previa
        stock_cost = 0.0
        all_inventories = list_inventory()
        for pid, qty in used_parts:
            row = all_inventories[all_inventories["id"] == pid]
            if not row.empty:
                stock_cost += float(row.iloc[0]["cost"] or 0) * qty
        ext_cost = sum(p["unit_cost"] for p in external_parts)
        total_cost = stock_cost + ext_cost

        p1, p2, p3 = st.columns(3)
        p1.metric("Costo partes bodega", money(stock_cost, "COP"))
        p2.metric("Costo partes externas", money(ext_cost, "COP"))
        p3.metric("Costo total producto", money(total_cost, "COP"))

        if st.form_submit_button("🔧 Ensamblar producto"):
            if not final_name.strip():
                st.error("El nombre del producto es obligatorio.")
            else:
                try:
                    # 1. Descontar partes de bodega
                    from db.connection import get_db
                    with get_db() as con:
                        cur = con.cursor()
                        for pid, qty in used_parts:
                            p = cur.execute("SELECT * FROM products WHERE id=? AND active=1", (pid,)).fetchone()
                            if p and p["stock"] >= qty:
                                cur.execute("UPDATE products SET stock=stock-? WHERE id=?", (qty, pid))

                    # 2. Registrar el producto ensamblado como compra
                    register_purchase(
                        "Colombia", final_sku, final_name.strip(), "Ensamblado",
                        1, total_cost, "COP", "Caja Colombia", "Ensamblaje",
                        f"Partes bodega: {stock_cost}, Partes externas: {ext_cost}",
                        st.session_state.user["username"],
                    )
                    st.success(f"Producto '{final_name}' ensamblado. Costo total: {money(total_cost, 'COP')}")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
