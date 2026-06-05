"""Bodega Colombia — inventario, historial y catalogo de productos."""

import streamlit as st
import json
from components.layout import header
from db.product import list_inventory, get_product_names, add_product_to_catalog, generate_sku
from db.purchase import list_purchases


def render():
    header("Bodega Colombia", "Inventario disponible para venta en Colombia.")

    tab1, tab2, tab3 = st.tabs(["📦 Inventario", "📋 Historial de compras", "🏷️ Catalogo"])

    with tab1:
        q = st.text_input("Buscar en Bodega Colombia")
        df = list_inventory("Colombia", q)
        # Mostrar atributos si existen
        st.dataframe(df, use_container_width=True, hide_index=True)

    with tab2:
        st.dataframe(list_purchases("Colombia"), use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("Gestionar catalogo de productos")
        st.caption("Agrega nombres de productos al catalogo. Sirven como plantillas para las compras.")

        # Lista actual
        products = get_product_names("Colombia")
        if products:
            st.write(f"**{len(products)} productos en catalogo:**")
            for p in products:
                attrs = ""
                if p.get("attributes"):
                    try:
                        a = json.loads(p["attributes"])
                        attrs = " | ".join(f"{k}: {v}" for k, v in a.items())
                    except Exception:
                        pass
                st.write(f"- {p['name']} ({p.get('category', '-')}) {attrs}")

        st.divider()
        with st.form("catalog_form"):
            c1, c2 = st.columns(2)
            cat_name = c1.text_input("Nombre del producto", placeholder="Ej: PlayStation 4")
            cat_category = c2.text_input("Categoria", placeholder="Ej: Consola")

            st.caption("Atributos / variantes (llena solo los que necesites):")
            num_attrs = st.number_input("Cantidad de atributos", min_value=0, max_value=10, value=1, step=1)

            attrs = {}
            for i in range(1, int(num_attrs) + 1):
                ck, cv = st.columns(2)
                key_name = ck.text_input(f"Nombre del atributo {i}", placeholder="Ej: Modelo, Color, Capacidad...", key=f"cat_ak_{i}")
                key_vals = cv.text_input(f"Opciones (separadas por coma)", placeholder="Ej: Fat, Slim, Pro", key=f"cat_av_{i}")
                if key_name.strip() and key_vals.strip():
                    attrs[key_name.strip()] = key_vals.strip()

            if st.form_submit_button("Agregar al catalogo"):
                if not cat_name.strip():
                    st.error("El nombre es obligatorio.")
                else:
                    add_product_to_catalog("Colombia", cat_name, cat_category, attrs if attrs else None, st.session_state.user["username"])
                    st.success(f"'{cat_name}' agregado al catalogo con {len(attrs)} atributos.")
                    st.rerun()
