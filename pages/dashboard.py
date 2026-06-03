"""Dashboard de ganancias con filtros de fecha e inyeccion de capital."""

import streamlit as st
from components.layout import header
from components.forms import filter_date_range
from utils.format import money
from db.cashbox import get_cashbox_balance, inject_capital
from db.dashboard import profit_dashboard, payment_method_summary


def render():
    header("Dashboard de ganancias", "Filtra por dia, semana, mes o rango personalizado.")

    start, end = filter_date_range()
    data = profit_dashboard(start, end)

    # Metricas principales
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Ventas Colombia", money(data["sales_cop"], "COP"))
    c2.metric("Reparaciones", money(data["repairs_income_cop"], "COP"))
    c3.metric("Costo vendido/usado", money(data["cost_cop"], "COP"))
    c4.metric("Gastos Colombia", money(data["expenses_cop"], "COP"))
    c5.metric("Ganancia neta", money(data["net_profit_cop"], "COP"))

    c6, c7, c8, c9 = st.columns(4)
    c6.metric("En transito USA", data["shipments_sent"])
    c7.metric("Perdidos USA", data["shipments_lost"])
    c8.metric("Recibidos Colombia", data["shipments_received"])
    c9.metric("Stock Repuestos", data["parts_stock"])

    st.subheader("Saldos por medio de pago")
    payment_df = payment_method_summary(start, end)
    st.dataframe(payment_df, use_container_width=True, hide_index=True)

    # ── Inyeccion de capital ──────────────────────────────
    st.divider()
    st.subheader("💵 Inyectar capital")
    st.caption("Agrega dinero directamente a una caja sin necesidad de registrar una venta o compra.")

    saldo_col = get_cashbox_balance("Caja Colombia")
    saldo_usa = get_cashbox_balance("Caja USA")

    sc1, sc2, sc3 = st.columns(3)
    sc1.metric("Saldo Caja Colombia", money(saldo_col, "COP"))
    sc2.metric("Saldo Caja USA", money(saldo_usa, "USD"))

    with st.form("inject_capital"):
        c1, c2, c3 = st.columns(3)
        cashbox = c1.selectbox("Caja destino", ["Caja Colombia", "Caja USA"])
        currency = "COP" if cashbox == "Caja Colombia" else "USD"
        step_val = 10000.0 if currency == "COP" else 10.0
        amount = c2.number_input(
            f"Monto a inyectar ({currency})",
            min_value=0.0, step=step_val,
        )
        payment_method = c3.selectbox(
            "Medio de pago / banco",
            ["Efectivo", "Transferencia - Bancolombia", "Transferencia - Nequi", "Tarjeta", "Otro"],
        )
        notes = st.text_input("Concepto", placeholder="Ej: Capital inicial, inversion del socio...")

        if st.form_submit_button("💵 Inyectar capital"):
            if amount <= 0:
                st.error("El monto debe ser mayor a cero.")
            else:
                inject_capital(
                    cashbox, amount, payment_method, notes,
                    st.session_state.user["username"],
                )
                st.success(
                    f"Capital inyectado: {money(amount, currency)} a {cashbox} via {payment_method}."
                )
                st.rerun()
