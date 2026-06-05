"""Bodega Colombia — inventario agrupado, historial y catalogo."""

import streamlit as st
import json
import pandas as pd
from components.layout import header
from db.product import list_inventory, get_product_names, add_product_to_catalog, generate_sku
from db.purchase import list_purchases
from utils.format import money


def render():
    header("Bodega Colombia", "Inventario disponible para venta en Colombia.")

    tab1, tab2, tab3 = st.tabs(["📦 Inventario", "📋 Historial de compras", "🏷️ Catalogo"])

    with tab1:
        _render_inventory()

    with tab2:
        st.dataframe(list_purchases("Colombia"), use_container_width=True, hide_index=True)

    with tab3:
        _render_catalog()


def _render_inventory():
    """Inventario agrupado por nombre con variantes en tabla detallada."""
    df = list_inventory("Colombia")

    if df.empty:
        st.info("No hay productos en Bodega Colombia.")
        return

    # Agrupar por nombre
    grouped = df.groupby("name")
    st.caption(f"{len(grouped)} productos diferentes | {int(df['stock'].sum())} unidades en stock")

    # ── Tabla unificada con botones para expandir ──────
    for name, group in sorted(grouped, key=lambda x: x[0]):
        total_stock = int(group["stock"].sum())
        cat = group.iloc[0].get("category") or "-"
        variants_count = len(group)

        c1, c2, c3, c4 = st.columns([2.5, 1, 1, 1])
        c1.write(f"**{name}**")
        c2.write(f"{cat}")
        c3.write(f"Stock: {total_stock}")
        if c4.button(f"🔍 {variants_count} variantes", key=f"det_{name}"):
            st.session_state[f"expanded_{name}"] = not st.session_state.get(f"expanded_{name}", False)

        # Mostrar detalle si esta expandido
        if st.session_state.get(f"expanded_{name}", False):
            rows = []
            for _, row in group.iterrows():
                attrs_parts = []
                raw = row.get("attributes")
                if raw and str(raw) not in ("None", "", "null", "{}"):
                    try:
                        a = json.loads(str(raw))
                        attrs_parts = [f"{k}: {v}" for k, v in a.items()]
                    except Exception:
                        pass
                rows.append({
                    "SKU": row["sku"],
                    "Variantes": " | ".join(attrs_parts) if attrs_parts else "—",
                    "Stock": int(row["stock"]),
                    "Costo": money(float(row["cost"]), "COP"),
                })
            detail_df = pd.DataFrame(rows)
            st.dataframe(detail_df, use_container_width=True, hide_index=True)

        st.divider()


def _render_catalog():
    """Gestion de catalogo de productos con atributos dinamicos."""
    st.subheader("Gestionar catalogo de productos")
    st.caption("Define nombres de productos y sus variantes. Sirven como plantillas para las compras.")

    # Lista actual
    products = get_product_names("Colombia")
    if products:
        for p in products:
            attrs = ""
            raw = p.get("attributes")
            if raw and str(raw) not in ("None", "", "null"):
                try:
                    a = json.loads(str(raw))
                    attrs = " | ".join(f"{k}: {v}" for k, v in a.items())
                except Exception:
                    pass
            st.write(f"- **{p['name']}** ({p.get('category', '-')}) {attrs}")

    st.divider()

    # Selector de cantidad de atributos FUERA del form (reactivo)
    num_attrs = st.number_input("Cantidad de atributos para este producto", min_value=0, max_value=10, value=1, step=1, key="cat_num_attrs")

    with st.form("catalog_form"):
        c1, c2 = st.columns(2)
        cat_name = c1.text_input("Nombre del producto", placeholder="Ej: PlayStation 4")
        cat_category = c2.text_input("Categoria", placeholder="Ej: Consola")

        attrs = {}
        if num_attrs > 0:
            st.caption("Define los atributos de este producto:")
            for i in range(1, int(num_attrs) + 1):
                ck, cv = st.columns(2)
                key_name = ck.text_input(f"Atributo {i} - Nombre", placeholder="Ej: Modelo", key=f"cat_ak_{i}")
                key_vals = cv.text_input(f"Opciones (coma)", placeholder="Fat, Slim, Pro", key=f"cat_av_{i}")
                if key_name.strip() and key_vals.strip():
                    attrs[key_name.strip()] = key_vals.strip()

        if st.form_submit_button("Agregar al catalogo"):
            if not cat_name.strip():
                st.error("El nombre es obligatorio.")
            else:
                add_product_to_catalog("Colombia", cat_name, cat_category, attrs if attrs else None, st.session_state.user["username"])
                st.success(f"'{cat_name}' agregado al catalogo con {len(attrs)} atributos.")
                st.rerun()
