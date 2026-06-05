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

            st.caption("Atributos / variantes (opcional):")
            ca1, ca2, ca3 = st.columns(3)
            attr1_key = ca1.text_input("Atributo 1", value="Modelo", key="attr1k")
            attr1_val = ca1.text_input("Valor", placeholder="Fat, Slim, Pro", key="attr1v")
            attr2_key = ca2.text_input("Atributo 2", value="Almacenamiento", key="attr2k")
            attr2_val = ca2.text_input("Valor", placeholder="500GB, 1TB", key="attr2v")
            attr3_key = ca3.text_input("Atributo 3", value="Programable", key="attr3k")
            attr3_val = ca3.text_input("Valor", placeholder="Si, No", key="attr3v")

            if st.form_submit_button("Agregar al catalogo"):
                if not cat_name.strip():
                    st.error("El nombre es obligatorio.")
                else:
                    attrs = {}
                    if attr1_key.strip() and attr1_val.strip():
                        attrs[attr1_key.strip()] = attr1_val.strip()
                    if attr2_key.strip() and attr2_val.strip():
                        attrs[attr2_key.strip()] = attr2_val.strip()
                    if attr3_key.strip() and attr3_val.strip():
                        attrs[attr3_key.strip()] = attr3_val.strip()
                    add_product_to_catalog("Colombia", cat_name, cat_category, attrs if attrs else None, st.session_state.user["username"])
                    st.success(f"'{cat_name}' agregado al catalogo.")
                    st.rerun()
