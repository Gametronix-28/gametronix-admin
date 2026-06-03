"""Caja USA — saldo y movimientos."""

import streamlit as st
from components.layout import header
from utils.format import money
from db.cashbox import get_cashbox_balance, list_cashbox_movements


def render():
    header("Caja USA", "Entradas, salidas, compras, transferencias y saldo en USD.")
    st.metric("Saldo Caja USA", money(get_cashbox_balance("Caja USA"), "USD"))
    st.dataframe(
        list_cashbox_movements("Caja USA"),
        use_container_width=True,
        hide_index=True,
    )
