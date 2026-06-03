"""Borrar / anular registros con reversión automática (solo admin)."""

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
from db.admin import void_record, list_voids

# Mapa: tipo de registro → función que lista + título de columna ID
_RECORD_SOURCES = {
    "factura": ("Facturas", list_invoices),
    "venta": ("Ventas directas (legacy)", list_sales),
    "compra": ("Compras", list_purchases),
    "envio_usa": ("Envíos USA", list_usa_shipments),
    "reparacion": ("Reparaciones", list_repairs),
    "transferencia": ("Transferencias", list_transfers),
    "gasto": ("Gastos", list_expenses),
    "producto": ("Productos", list_inventory),
}


def render():
    header("Borrar / anular registros",
           "Anula registros y revierte automáticamente stock y caja. Solo admin.")

    user = st.session_state.user
    if user["role"] != "admin":
        st.warning("Solo administrador puede anular registros.")
        return

    record_type = st.selectbox("Tipo de registro", list(_RECORD_SOURCES.keys()))

    # Cargar datos según tipo
    label, list_fn = _RECORD_SOURCES[record_type]
    if record_type == "factura":
        df = list_fn(200)
    elif record_type == "venta":
        df = list_fn(200)
    elif record_type == "envio_usa":
        df = list_fn(200)
    elif record_type == "reparacion":
        df = list_fn(200)
    elif record_type == "producto":
        df = list_fn()  # sin límite ni warehouse
    else:
        df = list_fn()

    st.caption(f"Mostrando: {label}")
    st.dataframe(df, use_container_width=True, hide_index=True)

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
                    st.success("Registro anulado y valores actualizados automáticamente.")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

    st.subheader("Historial de anulaciones")
    st.dataframe(list_voids(), use_container_width=True, hide_index=True)
