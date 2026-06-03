"""Borrar / anular registros con reversion automatica (solo admin)."""

import streamlit as st
from components.layout import header
from db.invoice import list_invoices
from db.sales_legacy import list_sales
from db.purchase import list_purchases
from db.shipment import list_usa_shipments
from db.repair import list_repairs
from db.transfer import list_transfers
from db.expense import list_expenses
from db.product import list_inventory
from db.admin import void_record, list_voids, get_repair_payment_details
from utils.format import money

_RECORD_SOURCES = {
    "factura": ("Facturas", list_invoices),
    "venta": ("Ventas directas (legacy)", list_sales),
    "compra": ("Compras", list_purchases),
    "envio_usa": ("Envios USA", list_usa_shipments),
    "reparacion": ("Reparaciones", list_repairs),
    "abono_reparacion": ("Abonos de taller (individual)", None),
    "transferencia": ("Transferencias", list_transfers),
    "gasto": ("Gastos", list_expenses),
    "producto": ("Productos", list_inventory),
}


def render():
    header("Borrar / anular registros",
           "Anula registros y revierte automaticamente stock y caja. Solo admin.")

    user = st.session_state.user
    if user["role"] != "admin":
        st.warning("Solo administrador puede anular registros.")
        return

    record_type = st.selectbox("Tipo de registro", list(_RECORD_SOURCES.keys()))

    # Cargar datos segun tipo
    label, list_fn = _RECORD_SOURCES[record_type]

    if list_fn:
        if record_type == "factura":
            df = list_fn(200)
        elif record_type == "venta":
            df = list_fn(200)
        elif record_type == "envio_usa":
            df = list_fn(200)
        elif record_type == "reparacion":
            df = list_fn(200)
        elif record_type == "producto":
            df = list_fn()
        else:
            df = list_fn()
        st.caption(f"Mostrando: {label}")
        st.dataframe(df, use_container_width=True, hide_index=True)

    # ── Mostrar detalles de pagos al seleccionar reparacion ─
    if record_type == "reparacion":
        st.divider()
        st.subheader("Consultar abonos de una reparacion")
        lookup_id = st.number_input("ID de reparacion para ver sus abonos", min_value=1, step=1, key="lookup_repair")
        if st.button("Ver abonos", key="btn_lookup"):
            try:
                payments, movements = get_repair_payment_details(int(lookup_id))
                if payments.empty:
                    st.info("Esta reparacion no tiene abonos registrados.")
                else:
                    st.write("**Abonos / pagos:**")
                    st.dataframe(payments, use_container_width=True, hide_index=True)
                    st.write("**Movimientos en caja:**")
                    st.dataframe(movements, use_container_width=True, hide_index=True)
                    st.caption("Para anular un abono individual, usa el tipo 'Abonos de taller (individual)' con el ID del abono.")
            except Exception as e:
                st.error(str(e))

    # ── Mostrar abonos activos al seleccionar abono_reparacion ─
    if record_type == "abono_reparacion":
        st.info("Ingresa el ID del abono (de la tabla repair_payments). Usa la opcion 'reparacion' arriba para consultar los IDs.")
        from db.repair import list_repair_payments
        payments_df = list_repair_payments(300)
        active = payments_df[payments_df["active"] == 1] if not payments_df.empty and "active" in payments_df.columns else payments_df
        st.caption("Abonos activos:")
        st.dataframe(active, use_container_width=True, hide_index=True)

    # ── Formulario de anulacion ─────────────────────────
    with st.form("void"):
        record_id = st.number_input("ID a anular/eliminar", min_value=1, step=1)
        reason = st.text_area("Motivo obligatorio")
        confirm = st.checkbox("Confirmo que quiero anular este registro y revertir sus efectos.")

        if st.form_submit_button("Anular registro"):
            if not confirm or not reason.strip():
                st.error("Debes confirmar y escribir el motivo.")
            else:
                try:
                    void_record(record_type, int(record_id), reason, user["username"])
                    st.success("Registro anulado y valores actualizados automaticamente.")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

    st.subheader("Historial de anulaciones")
    st.dataframe(list_voids(), use_container_width=True, hide_index=True)
