"""Gastos por caja — registro y visualización."""

import streamlit as st
from components.layout import header
from utils.format import money
from db.cashbox import get_cashbox_balance
from db.expense import register_expense, list_expenses, list_expenses_by_cashbox


def render():
    header("Gastos por caja", "Registra gastos separados: Colombia descuenta Caja Colombia y USA descuenta Caja USA.")

    c1, c2 = st.columns(2)
    c1.metric("Saldo Caja Colombia", money(get_cashbox_balance("Caja Colombia"), "COP"))
    c2.metric("Saldo Caja USA", money(get_cashbox_balance("Caja USA"), "USD"))

    st.divider()

    with st.form("expense_by_cashbox"):
        c1, c2, c3 = st.columns(3)
        cashbox = c1.selectbox("Caja", ["Caja Colombia", "Caja USA"])
        currency = "COP" if cashbox == "Caja Colombia" else "USD"
        step_value = 1000.0 if currency == "COP" else 1.0
        amount = c2.number_input(f"Monto gasto {currency}", min_value=0.0, step=step_value)
        category = c3.selectbox(
            "Categoría",
            ["Arriendo", "Servicios", "Transporte", "Comisiones", "Empaque",
             "Herramientas", "Publicidad", "Nómina", "Compra menor", "Otro"],
        )
        concept = st.text_input("Concepto del gasto")
        notes = st.text_area("Observaciones")

        if st.form_submit_button("Registrar gasto"):
            register_expense(
                concept, amount, currency, cashbox, category, notes,
                st.session_state.user["username"],
            )
            st.success(f"Gasto registrado. Se descontó de {cashbox}.")
            st.rerun()

    st.divider()

    tab1, tab2, tab3 = st.tabs(["Gastos Colombia", "Gastos USA", "Todos"])
    with tab1:
        st.dataframe(
            list_expenses_by_cashbox("Caja Colombia"),
            use_container_width=True, hide_index=True,
        )
    with tab2:
        st.dataframe(
            list_expenses_by_cashbox("Caja USA"),
            use_container_width=True, hide_index=True,
        )
    with tab3:
        st.dataframe(list_expenses(), use_container_width=True, hide_index=True)
