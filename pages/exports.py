"""Importar / Exportar respaldo Excel con importacion masiva."""

import streamlit as st
import os
from components.layout import header
from utils.format import money
from db.admin import export_to_excel
from utils.import_excel import import_products_from_excel


def render():
    header("Importar / Exportar", "Respalda la informacion o importa productos masivamente desde Excel.")

    tab1, tab2 = st.tabs(["📥 Importar productos", "📤 Exportar respaldo"])

    # ── Importar ────────────────────────────────────────
    with tab1:
        st.subheader("Importar productos desde Excel")
        st.caption("Descarga la plantilla, llena tus productos y subela aqui.")

        # Boton para descargar plantilla
        template_path = "plantilla_importar_productos.xlsx"
        if os.path.exists(template_path):
            with open(template_path, "rb") as f:
                st.download_button(
                    "📋 Descargar plantilla Excel",
                    data=f,
                    file_name="plantilla_productos.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

        st.markdown("""
        **Columnas de la plantilla:**
        - `SKU` — codigo del producto (vacio = auto GTX-XXX)
        - `Nombre` — obligatorio
        - `Categoria` — ej: Consola, Control, Accesorio
        - `Cantidad` — unidades
        - `Costo_unitario` — lo que te costo cada unidad
        - `Moneda` — COP o USD
        - `Bodega` — Colombia, USA o Repuestos
        - `Proveedor` — opcional
        - `Notas` — opcional
        """)

        uploaded = st.file_uploader("Sube tu archivo Excel (.xlsx)", type=["xlsx"])
        if uploaded:
            # Guardar temporal
            temp_path = "_temp_import.xlsx"
            with open(temp_path, "wb") as f:
                f.write(uploaded.read())

            # Vista previa
            import pandas as pd
            preview = pd.read_excel(temp_path)
            st.write(f"**{len(preview)} productos para importar:**")
            st.dataframe(preview, use_container_width=True, hide_index=True)

            if st.button("🚀 Importar todos los productos", type="primary"):
                with st.spinner("Importando..."):
                    total, costo, errores = import_products_from_excel(temp_path, st.session_state.user["username"])

                if total > 0:
                    st.success(f"✅ {total} productos importados. Costo total: {money(costo, 'COP' if costo > 1000 else 'USD')}")
                    st.info(f"💡 Ahora ve a Dashboard → Inyectar capital y agrega el valor de tu mercancia + plata fisica.")
                if errores:
                    st.warning("Algunos productos no se importaron:")
                    for e in errores:
                        st.write(f"- {e}")

                os.remove(temp_path)

    # ── Exportar ────────────────────────────────────────
    with tab2:
        st.subheader("Exportar respaldo Excel")
        c1, c2 = st.columns(2)
        start = c1.date_input("Desde (opcional)", value=None, key="exp_start")
        end = c2.date_input("Hasta (opcional)", value=None, key="exp_end")
        use_filter = start is not None and end is not None

        if st.button("📤 Crear respaldo Excel"):
            if use_filter:
                path = export_to_excel(str(start), str(end))
                st.caption(f"Filtrado: {start} a {end}")
            else:
                path = export_to_excel()
                st.caption("Export completo (sin filtro de fecha)")
            with open(path, "rb") as f:
                st.download_button("📥 Descargar respaldo", f, file_name="gametronix_respaldo.xlsx")
