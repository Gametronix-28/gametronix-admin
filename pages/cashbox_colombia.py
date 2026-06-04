"""Caja Colombia — saldo, movimientos con filtro de fecha y cierre diario."""

import streamlit as st
import pandas as pd
from datetime import date
from components.layout import header
from utils.format import money
from db.cashbox import get_cashbox_balance, list_cashbox_movements


def render():
    header("Caja Colombia", "Movimientos, saldo y cierre diario en COP.")

    st.metric("Saldo Caja Colombia", money(get_cashbox_balance("Caja Colombia"), "COP"))

    # ── Filtro de fecha ──────────────────────────────────
    c1, c2 = st.columns(2)
    start = c1.date_input("Desde", value=date.today().replace(day=1), key="cc_start")
    end = c2.date_input("Hasta", value=date.today(), key="cc_end")

    df = list_cashbox_movements("Caja Colombia")
    if not df.empty and "date" in df.columns:
        df["date_clean"] = pd.to_datetime(df["date"]).dt.date
        mask = (df["date_clean"] >= start) & (df["date_clean"] <= end)
        filtered = df[mask]
        # Totales del periodo
        ingresos = filtered[filtered["amount"] > 0]["amount"].sum()
        egresos = abs(filtered[filtered["amount"] < 0]["amount"].sum())
        c1, c2, c3 = st.columns(3)
        c1.metric("Ingresos del periodo", money(ingresos, "COP"))
        c2.metric("Egresos del periodo", money(egresos, "COP"))
        c3.metric("Neto del periodo", money(ingresos - egresos, "COP"))
        st.dataframe(filtered, use_container_width=True, hide_index=True)
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)
