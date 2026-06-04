"""Caja USA — saldo, movimientos con filtro de fecha y conciliacion."""

import streamlit as st
import pandas as pd
from datetime import date
from components.layout import header
from utils.format import money
from db.cashbox import get_cashbox_balance, list_cashbox_movements


def render():
    header("Caja USA", "Movimientos, saldo y conciliacion en USD.")

    saldo_actual = get_cashbox_balance("Caja USA")
    st.metric("Saldo Caja USA", money(saldo_actual, "USD"))

    # ── Filtro de fecha ──────────────────────────────────
    c1, c2 = st.columns(2)
    start = c1.date_input("Desde", value=date.today().replace(day=1), key="usa_start")
    end = c2.date_input("Hasta", value=date.today(), key="usa_end")

    df = list_cashbox_movements("Caja USA")
    if not df.empty and "date" in df.columns:
        df["date_clean"] = pd.to_datetime(df["date"]).dt.date
        mask = (df["date_clean"] >= start) & (df["date_clean"] <= end)
        filtered = df[mask]
        ingresos = filtered[filtered["amount"] > 0]["amount"].sum()
        egresos = abs(filtered[filtered["amount"] < 0]["amount"].sum())
        c1, c2, c3 = st.columns(3)
        c1.metric("Ingresos del periodo", money(ingresos, "USD"))
        c2.metric("Egresos del periodo", money(egresos, "USD"))
        c3.metric("Neto del periodo", money(ingresos - egresos, "USD"))
        st.dataframe(filtered, use_container_width=True, hide_index=True)
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

    # ── Conciliacion ─────────────────────────────────────
    st.divider()
    with st.expander("🔍 Conciliar caja USA", expanded=True):
        st.markdown("""
        ### Paso a paso para conciliar:
        1. **Saldo inicial**: dinero que ya estaba en la caja al empezar
        2. **+ Capital inyectado**: dinero agregado manualmente
        3. **- Compras**: compras de productos en USA
        4. **- Gastos**: gastos registrados en USD
        5. **-/+ Transferencias**: dinero movido entre cajas
        6. **= Saldo actual**: debe coincidir con lo que hay fisicamente
        """)

        if not df.empty:
            df["amount_f"] = df["amount"].astype(float)
            tipos = {
                "compra": "Compras USA",
                "gasto": "Gastos",
                "inyeccion_capital": "Capital inyectado",
                "transferencia_entrada": "Transferencias (entrada)",
                "transferencia_salida": "Transferencias (salida)",
                "anulacion_compra": "Anulaciones compra",
                "anulacion_gasto": "Anulaciones gasto",
                "anulacion_transferencia": "Anulaciones transferencia",
            }
            df["tipo_legible"] = df["type"].map(tipos).fillna(df["type"])

            summary = df.groupby("tipo_legible")["amount_f"].sum().reset_index()
            summary.columns = ["Tipo de movimiento", "Total"]
            summary = summary.sort_values("Total", ascending=False)

            st.write("**Desglose por tipo de movimiento:**")
            for _, row in summary.iterrows():
                total = row["Total"]
                signo = "+" if total > 0 else ""
                st.write(f"{signo}{money(total, 'USD')} → {row['Tipo de movimiento']}")

            gran_total = summary["Total"].sum()
            st.metric("Saldo total segun movimientos", money(gran_total, "USD"))
            st.metric("Saldo actual en caja", money(saldo_actual, "USD"))

            if abs(gran_total - saldo_actual) < 0.01:
                st.success("✅ La caja USA cuadra perfectamente.")
            else:
                diff = saldo_actual - gran_total
                st.warning(f"⚠️ Diferencia: {money(diff, 'USD')}. Revisa los movimientos.")

    # ── Saldo inicial ────────────────────────────────────
    with st.expander("🏁 Saldo inicial de caja USA", expanded=False):
        st.caption("El saldo inicial es el dinero que habia en caja antes de registrar movimientos.")
        if not df.empty:
            # El primer movimiento de tipo inyeccion_capital marca el inicio
            first = df[df["type"] == "inyeccion_capital"]
            if not first.empty:
                inicial = first.iloc[-1]  # el mas antiguo
                st.metric("Primer capital registrado", money(float(inicial["amount"]), "USD"))
                st.caption(f"Fecha: {inicial['date']}")
            else:
                st.info("No hay inyeccion de capital registrada. El saldo inicial es $0.")
                st.caption("Para registrar el saldo inicial, usa Dashboard → Inyectar capital → Caja USA.")
        else:
            st.info("Sin movimientos. El saldo inicial es $0.")
