"""Importar / Exportar respaldo Excel con filtro de fecha."""

import streamlit as st
from datetime import date
from components.layout import header
from db.admin import export_to_excel


def render():
    header("Importar / Exportar", "Respalda la informacion en Excel. Opcional: filtra por fecha.")

    c1, c2 = st.columns(2)
    start = c1.date_input("Desde (opcional)", value=None, key="exp_start")
    end = c2.date_input("Hasta (opcional)", value=None, key="exp_end")

    use_filter = start is not None and end is not None

    if st.button("Crear respaldo Excel"):
        if use_filter:
            path = export_to_excel(str(start), str(end))
            st.caption(f"Filtrado: {start} a {end}")
        else:
            path = export_to_excel()
            st.caption("Export completo (sin filtro de fecha)")
        with open(path, "rb") as f:
            st.download_button("Descargar respaldo", f, file_name="gametronix_respaldo.xlsx")
