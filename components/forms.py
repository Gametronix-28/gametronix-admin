"""Componentes de formulario reutilizables."""

import streamlit as st
from datetime import date, timedelta


def filter_date_range():
    """
    Renderiza controles de filtro por fecha.
    Retorna (start, end) como strings en formato YYYY-MM-DD.
    """
    today = date.today()
    mode = st.radio(
        "Filtro", ["Día", "Semana", "Mes", "Rango personalizado"],
        horizontal=True,
    )

    if mode == "Día":
        chosen = st.date_input("Día", value=today)
        return str(chosen), str(chosen)

    elif mode == "Semana":
        start = st.date_input(
            "Inicio semana",
            value=today - timedelta(days=today.weekday()),
        )
        end = start + timedelta(days=6)
        st.caption(f"Semana: {start} a {end}")
        return str(start), str(end)

    elif mode == "Mes":
        start = st.date_input("Inicio mes", value=today.replace(day=1))
        next_month = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
        end = next_month - timedelta(days=1)
        st.caption(f"Mes: {start} a {end}")
        return str(start), str(end)

    else:
        c1, c2 = st.columns(2)
        start = c1.date_input("Desde", value=today.replace(day=1))
        end = c2.date_input("Hasta", value=today)
        return str(start), str(end)


def select_product(inventory_df, label="Producto"):
    """
    Renderiza un selectbox para elegir un producto del inventario.
    Retorna el product_id como int, o None si no hay productos.
    """
    if inventory_df.empty:
        st.warning("No hay productos disponibles.")
        return None

    selected = st.selectbox(
        label,
        inventory_df.apply(
            lambda r: f"{r['id']} - {r['sku']} - {r['name']} - Stock {r['stock']}",
            axis=1,
        ),
    )
    return int(selected.split(" - ")[0])
