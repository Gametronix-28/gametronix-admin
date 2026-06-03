"""Caja Colombia — saldo y movimientos."""

import streamlit as st
from components.layout import header
from utils.format import money
from db.cashbox import get_cashbox_balance, list_cashbox_movements


def render():
    header("Caja Colombia", "Entradas, salidas, ventas, reparaciones, compras, gastos y transferencias en COP.")
    st.metric("Saldo Caja Colombia", money(get_cashbox_balance("Caja Colombia"), "COP"))
    st.dataframe(
        list_cashbox_movements("Caja Colombia"),
        use_container_width=True,
        hide_index=True,
    )
