"""Dashboard de ganancias con filtros, alertas y notificaciones."""

import streamlit as st
from components.layout import header
from components.forms import filter_date_range
from utils.format import money
from db.cashbox import get_cashbox_balance, inject_capital
from db.dashboard import profit_dashboard, payment_method_summary
from db.product import list_inventory
from db.repair import list_pending_repairs


def render():
    header("Dashboard de ganancias", "Filtra por dia, semana, mes o rango personalizado.")

    # ── Notificaciones / Alertas ─────────────────────────
    _render_alerts()

    start, end = filter_date_range()
    data = profit_dashboard(start, end)

    # ── Metricas principales ─────────────────────────────
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

    # ── Saldos cajas ─────────────────────────────────────
    sc1, sc2 = st.columns(2)
    sc1.metric("Saldo Caja Colombia", money(get_cashbox_balance("Caja Colombia"), "COP"))
    sc2.metric("Saldo Caja USA", money(get_cashbox_balance("Caja USA"), "USD"))

    with st.expander("💳 Saldos por medio de pago"):
        payment_df = payment_method_summary(start, end)
        _render_payment_cards(payment_df)


def _render_payment_cards(df):
    """Muestra los saldos por medio de pago como tarjetas modernas."""
    icons = {
        "Efectivo": "💵",
        "Bancolombia": "🏦",
        "Nequi": "📱",
        "Tarjeta": "💳",
        "Otro": "🪙",
        "Pendiente": "⏳",
        "Sin especificar": "❓",
    }
    # CSS para tarjetas
    st.markdown("""
    <style>
    .payment-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border-radius: 14px;
        padding: 18px 22px;
        margin: 6px 0;
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-left: 4px solid #3b82f6;
    }
    .payment-card .icon {
        font-size: 28px;
        margin-right: 16px;
    }
    .payment-card .name {
        color: #e2e8f0;
        font-size: 15px;
        font-weight: 600;
    }
    .payment-card .amount {
        color: #60a5fa;
        font-size: 18px;
        font-weight: 700;
        text-align: right;
    }
    </style>
    """, unsafe_allow_html=True)

    for _, row in df.iterrows():
        medio = str(row.get("medio_pago", ""))
        saldo = float(row.get("saldo", 0))
        icon = icons.get(medio, "💰")
        st.markdown(f"""
        <div class="payment-card">
            <div style="display:flex;align-items:center;">
                <span class="icon">{icon}</span>
                <span class="name">{medio}</span>
            </div>
            <span class="amount">{money(saldo, 'COP')}</span>
        </div>
        """, unsafe_allow_html=True)

    # ── Reparaciones pendientes ─────────────────────────
    pending = list_pending_repairs(20)
    pending_count = len(pending) if not pending.empty else 0
    with st.expander(f"🔧 Reparaciones pendientes ({pending_count})"):
        if pending.empty:
            st.success("No hay reparaciones con saldo pendiente.")
        else:
            st.dataframe(pending, use_container_width=True, hide_index=True)

    # ── Inyectar capital ─────────────────────────────────
    with st.expander("💵 Inyectar capital"):
        st.caption("Agrega dinero directamente a una caja.")
        saldo_col = get_cashbox_balance("Caja Colombia")
        saldo_usa = get_cashbox_balance("Caja USA")

        sc1, sc2 = st.columns(2)
        sc1.metric("Saldo Caja Colombia", money(saldo_col, "COP"))
        sc2.metric("Saldo Caja USA", money(saldo_usa, "USD"))

        with st.form("inject_capital"):
            c1, c2, c3 = st.columns(3)
            cashbox = c1.selectbox("Caja destino", ["Caja Colombia", "Caja USA"])
            currency = "COP" if cashbox == "Caja Colombia" else "USD"
            step_val = 10000.0 if currency == "COP" else 10.0
            amount = c2.number_input(f"Monto ({currency})", min_value=0.0, step=step_val)
            payment_method = c3.selectbox(
                "Medio de pago / banco",
                ["Efectivo", "Transferencia - Bancolombia", "Transferencia - Nequi", "Tarjeta", "Otro"],
            )
            notes = st.text_input("Concepto", placeholder="Ej: Capital inicial, inversion...")
            if st.form_submit_button("💵 Inyectar capital"):
                if amount <= 0:
                    st.error("El monto debe ser mayor a cero.")
                else:
                    inject_capital(cashbox, amount, payment_method, notes, st.session_state.user["username"])
                    st.success(f"Capital inyectado: {money(amount, currency)} a {cashbox} via {payment_method}.")
                    st.rerun()


def _render_alerts():
    """Muestra alertas: stock bajo, equipos listos para entregar."""
    low_stock = list_inventory()
    if not low_stock.empty:
        low = low_stock[low_stock["stock"] < low_stock["min_stock"]]
        if not low.empty:
            items = ", ".join(f"{r['name']} ({r['stock']}/{r['min_stock']})" for _, r in low.head(5).iterrows())
            st.warning(f"⚠️ Stock bajo: {items}")

    from db.repair import list_repairs
    repairs = list_repairs(100)
    if not repairs.empty:
        ready = repairs[(repairs["balance_due"] <= 0) & (repairs["status"] != "Entregado")]
        if not ready.empty:
            st.info(f"📦 {len(ready)} equipos listos para entregar. Ve a Taller → Entrega.")
