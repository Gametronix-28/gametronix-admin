"""Importar / Exportar respaldo Excel."""

import streamlit as st
from components.layout import header
from db.admin import export_to_excel


def render():
    header("Importar / Exportar", "Respalda la información en Excel.")
    if st.button("Crear respaldo Excel"):
        path = export_to_excel()
        with open(path, "rb") as f:
            st.download_button(
                "Descargar respaldo",
                f,
                file_name="gametronix_respaldo.xlsx",
            )
