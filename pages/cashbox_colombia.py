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

    # ── Conciliacion ─────────────────────────────────────
    st.divider()
    with st.expander("🔍 Conciliar caja - Ver de donde viene el saldo", expanded=True):
        st.markdown("""
        ### Paso a paso para conciliar:
        1. **Saldo inicial**: dinero que ya estaba en caja antes de empezar a usar el sistema
        2. **+ Ventas**: facturas registradas en Venta Colombia
        3. **+ Reparaciones**: abonos y pagos de taller
        4. **+ Capital inyectado**: dinero agregado manualmente
        5. **- Compras**: compras de productos en Colombia
        6. **- Gastos**: gastos registrados
        7. **-/+ Transferencias**: dinero movido entre cajas
        8. **= Saldo actual**: debe coincidir con lo que hay en caja fisicamente
        """)

        # Desglose por tipo de movimiento
        if not df.empty:
            df["amount_f"] = df["amount"].astype(float)
            tipos = {
                "factura_venta": "Ventas (facturas)",
                "abono_reparacion": "Reparaciones (abonos)",
                "pago_reparacion": "Reparaciones (pagos)",
                "inyeccion_capital": "Capital inyectado",
                "compra": "Compras",
                "gasto": "Gastos",
                "transferencia_entrada": "Transferencias (entrada)",
                "transferencia_salida": "Transferencias (salida)",
                "anulacion_factura": "Anulaciones",
                "anulacion_venta": "Anulaciones venta",
                "anulacion_compra": "Anulaciones compra",
                "anulacion_reparacion": "Anulaciones reparacion",
                "anulacion_abono": "Anulaciones abono",
                "anulacion_gasto": "Anulaciones gasto",
                "anulacion_transferencia": "Anulaciones transferencia",
            }
            df["tipo_legible"] = df["type"].map(tipos).fillna(df["type"])

            # Agrupar por tipo
            summary = df.groupby("tipo_legible")["amount_f"].sum().reset_index()
            summary.columns = ["Tipo de movimiento", "Total"]
            summary = summary.sort_values("Total", ascending=False)

            st.write("**Desglose por tipo de movimiento:**")
            for _, row in summary.iterrows():
                tipo = row["Tipo de movimiento"]
                total = row["Total"]
                color = "green" if total > 0 else "red"
                signo = "+" if total > 0 else ""
                st.write(f"{signo}{money(total, 'COP')} → {tipo}")

            # Total
            gran_total = summary["Total"].sum()
            st.metric("Saldo total segun movimientos", money(gran_total, "COP"))
            st.metric("Saldo actual en caja", money(get_cashbox_balance("Caja Colombia"), "COP"))

            if abs(gran_total - get_cashbox_balance("Caja Colombia")) < 1:
                st.success("✅ La caja cuadra perfectamente.")
            else:
                diff = get_cashbox_balance("Caja Colombia") - gran_total
                st.warning(f"⚠️ Diferencia: {money(diff, 'COP')}. Revisa los movimientos.")
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)

    # ── Saldo inicial ────────────────────────────────────
    with st.expander("🏁 Saldo inicial de caja", expanded=False):
        st.caption("El saldo inicial es el dinero que habia en caja antes de registrar movimientos. Usa Dashboard → Inyectar capital para registrarlo.")
        if not df.empty:
            first_injections = df[df["type"] == "inyeccion_capital"]
            if not first_injections.empty:
                inicial = first_injections.iloc[-1]
                st.metric("Primer capital registrado", money(float(inicial["amount"]), "COP"))
                st.caption(f"Fecha: {inicial['date']} | {inicial['description']}")
            else:
                st.info("No hay inyeccion de capital registrada.")
        else:
            st.info("Sin movimientos.")
