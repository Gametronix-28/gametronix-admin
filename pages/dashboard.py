"""Dashboard de ganancias con filtros de fecha."""

import streamlit as st
from components.layout import header
from components.forms import filter_date_range
from utils.format import money
from db.dashboard import profit_dashboard, payment_method_summary


def render():
    header("Dashboard de ganancias", "Filtra por día, semana, mes o rango personalizado.")

    start, end = filter_date_range()
    data = profit_dashboard(start, end)

    # Métricas principales
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Ventas Colombia", money(data["sales_cop"], "COP"))
    c2.metric("Reparaciones", money(data["repairs_income_cop"], "COP"))
    c3.metric("Costo vendido/usado", money(data["cost_cop"], "COP"))
    c4.metric("Gastos Colombia", money(data["expenses_cop"], "COP"))
    c5.metric("Ganancia neta", money(data["net_profit_cop"], "COP"))

    c6, c7, c8, c9 = st.columns(4)
    c6.metric("En tránsito USA", data["shipments_sent"])
    c7.metric("Perdidos USA", data["shipments_lost"])
    c8.metric("Recibidos Colombia", data["shipments_received"])
    c9.metric("Stock Repuestos", data["parts_stock"])

    st.subheader("Saldos por medio de pago")
    payment_df = payment_method_summary(start, end)
    st.dataframe(payment_df, use_container_width=True, hide_index=True)
