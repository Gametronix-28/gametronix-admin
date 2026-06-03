"""Transferencia con tasa — entre cajas con conversión USD/COP."""

import streamlit as st
import pandas as pd
from components.layout import header
from db.cashbox import list_cashboxes
from db.transfer import calculate_transfer, register_transfer, list_transfers


def render():
    header("Transferencia con tasa corregida", "Colombia → USA: COP / tasa. USA → Colombia: USD * tasa.")

    st.dataframe(
        pd.DataFrame(list_cashboxes()),
        use_container_width=True,
        hide_index=True,
    )

    with st.form("transfer"):
        c1, c2 = st.columns(2)
        origin = c1.selectbox("Caja origen", ["Caja Colombia", "Caja USA"])
        dest = c2.selectbox("Caja destino", ["Caja USA", "Caja Colombia"])
        c3, c4, c5 = st.columns(3)
        amount = c3.number_input("Monto origen", min_value=0.0, step=1000.0)
        rate = c4.number_input(
            "Tasa USD/COP", min_value=0.000001, value=4000.0,
            step=1.0, format="%.6f",
        )
        converted = calculate_transfer(origin, dest, amount, rate)
        c5.metric("Monto convertido", f"{converted:,.2f}")
        notes = st.text_input("Observaciones")

        if st.form_submit_button("Registrar transferencia"):
            register_transfer(
                origin, dest, amount, rate, notes,
                st.session_state.user["username"],
            )
            st.success("Transferencia registrada.")
            st.rerun()

    st.dataframe(
        list_transfers(),
        use_container_width=True,
        hide_index=True,
    )
