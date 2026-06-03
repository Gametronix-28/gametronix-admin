"""Componentes de tabla y descarga."""

import streamlit as st


def show_dataframe(df, key=None):
    """Muestra un DataFrame con el estilo estándar de la app."""
    if df.empty:
        st.info("No hay datos para mostrar.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)


def pdf_download_button(file_path, label="Descargar PDF", file_name="documento.pdf"):
    """
    Muestra un botón de descarga para un archivo PDF generado.
    Lee el archivo del disco y lo ofrece como descarga.
    """
    try:
        with open(file_path, "rb") as f:
            st.download_button(
                label=label,
                data=f,
                file_name=file_name,
                mime="application/pdf",
            )
    except FileNotFoundError:
        st.error(f"Archivo no encontrado: {file_path}")
    except Exception as e:
        st.error(f"Error al preparar descarga: {e}")
