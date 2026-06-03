"""Venta Colombia — carrito de facturación con PDF."""

import streamlit as st
import pandas as pd
from components.layout import header
from utils.format import money
from utils.pdf import create_invoice_pdf
from db.cashbox import get_cashbox_balance
from db.product import list_inventory
from db.invoice import register_invoice_colombia, list_invoices, get_invoice, list_invoice_items


def render():
    header("Venta Colombia", "Agrega productos a la factura y luego confirma con Registrar venta.")

    # Inicializar carrito
    if "invoice_cart" not in st.session_state:
        st.session_state.invoice_cart = []

    saldo = get_cashbox_balance("Caja Colombia")
    st.metric("Saldo actual Caja Colombia", money(saldo, "COP"))

    inv = list_inventory("Colombia")
    if inv.empty:
        st.warning("No hay productos en Bodega Colombia.")
    else:
        _render_add_product_form(inv)
        _render_cart()
        _render_confirm_sale()

    st.divider()
    st.subheader("Facturas Colombia")
    st.caption("Presiona 'Generar PDF' en la factura que quieras enviar al cliente.")
    _render_invoice_history()


# ── Sub-componentes ──────────────────────────────────────

def _render_add_product_form(inv):
    st.subheader("1. Agregar producto a la factura")
    with st.form("add_product_to_invoice"):
        product_label = st.selectbox(
            "Producto de Bodega Colombia",
            inv.apply(
                lambda r: f"{r['id']} - {r['sku']} - {r['name']} - "
                          f"Stock {r['stock']} - Costo {r['cost']} - Precio {r['price']}",
                axis=1,
            ),
        )
        product_id = int(product_label.split(" - ")[0])
        product_row = inv[inv["id"] == product_id].iloc[0]

        c1, c2, c3 = st.columns(3)
        qty = c1.number_input("Cantidad", min_value=1, step=1)
        unit_price = c2.number_input(
            "Precio unitario COP",
            min_value=0.0,
            value=float(product_row.get("price") or 0),
            step=1000.0,
        )
        c3.metric("Subtotal", money(qty * unit_price, "COP"))

        c4, c5 = st.columns(2)
        serial = c4.text_input("Serial del producto", placeholder="Serial / IMEI / código")
        line_note = c5.text_input("Nota del producto", placeholder="Garantía, estado, accesorios...")

        if st.form_submit_button("Agregar producto a la factura"):
            current_qty_in_cart = sum(
                item["qty"] for item in st.session_state.invoice_cart
                if item["product_id"] == product_id
            )
            stock_available = int(product_row.get("stock") or 0)

            if current_qty_in_cart + qty > stock_available:
                st.error(
                    f"No puedes agregar esa cantidad. Stock disponible: {stock_available}. "
                    f"Ya tienes {current_qty_in_cart} en la factura."
                )
            else:
                st.session_state.invoice_cart.append({
                    "product_id": product_id,
                    "sku": product_row.get("sku"),
                    "name": product_row.get("name"),
                    "qty": int(qty),
                    "unit_price": float(unit_price),
                    "serial": serial,
                    "notes": line_note,
                })
                st.success("Producto agregado a la factura.")
                st.rerun()


def _render_cart():
    st.divider()
    st.subheader("2. Factura actual")

    if not st.session_state.invoice_cart:
        st.info("Todavía no hay productos agregados a la factura.")
        return

    cart_df = pd.DataFrame(st.session_state.invoice_cart)
    cart_df["subtotal"] = cart_df["qty"] * cart_df["unit_price"]
    st.dataframe(cart_df, use_container_width=True, hide_index=True)

    total_factura = float(cart_df["subtotal"].sum())
    st.metric("TOTAL FACTURA", money(total_factura, "COP"))

    c_remove, c_clear = st.columns(2)
    with c_remove:
        remove_index = st.number_input(
            "Número de línea a quitar",
            min_value=1,
            max_value=max(len(st.session_state.invoice_cart), 1),
            step=1,
        )
        if st.button("Quitar producto seleccionado"):
            st.session_state.invoice_cart.pop(remove_index - 1)
            st.success("Producto quitado de la factura.")
            st.rerun()

    with c_clear:
        st.write("")
        st.write("")
        if st.button("Vaciar factura"):
            st.session_state.invoice_cart = []
            st.success("Factura vaciada.")
            st.rerun()


def _render_confirm_sale():
    if not st.session_state.invoice_cart:
        return

    st.divider()
    st.subheader("3. Registrar venta")
    st.caption("Primero agrega todos los productos a la factura. Luego confirma la venta total.")

    c1, c2 = st.columns(2)
    client = c1.text_input("Cliente", key="invoice_client")
    payment = c2.selectbox(
        "Medio de pago",
        ["Efectivo", "Transferencia", "Tarjeta", "Otro"],
        key="invoice_payment",
    )

    payment_final = payment
    if payment == "Transferencia":
        bank = st.selectbox(
            "Banco / cuenta de transferencia",
            ["Bancolombia", "Nequi"],
            key="invoice_transfer_bank",
        )
        payment_final = f"Transferencia - {bank}"

    invoice_notes = st.text_area("Nota general de la factura", key="invoice_notes")

    if st.button("Registrar venta", type="primary"):
        try:
            items = [
                {
                    "product_id": item["product_id"],
                    "qty": item["qty"],
                    "unit_price": item["unit_price"],
                    "serial": item.get("serial", ""),
                    "notes": item.get("notes", ""),
                }
                for item in st.session_state.invoice_cart
            ]
            invoice_id = register_invoice_colombia(
                items, client, payment_final, invoice_notes,
                st.session_state.user["username"],
            )
            st.session_state.invoice_cart = []
            st.success(
                f"Venta registrada correctamente. Factura #{invoice_id}. "
                "Se descontó Bodega Colombia y se sumó el total a Caja Colombia."
            )
            st.rerun()
        except Exception as e:
            st.error(str(e))


def _render_invoice_history():
    invoices_df = list_invoices(300)
    if invoices_df.empty:
        st.info("Todavía no hay facturas registradas.")
        return

    st.dataframe(invoices_df, use_container_width=True, hide_index=True)
    st.subheader("Generar PDF por factura")

    for _, invoice_row in invoices_df.iterrows():
        invoice_id = int(invoice_row["id"])
        col1, col2, col3, col4 = st.columns([1, 2, 2, 2])
        col1.write(f"#{invoice_id}")
        col2.write(str(invoice_row.get("client") or "Cliente no especificado"))
        col3.write(money(invoice_row.get("total") or 0, "COP"))

        with col4:
            if st.button("Generar PDF", key=f"pdf_invoice_{invoice_id}"):
                try:
                    invoice = get_invoice(invoice_id)
                    items_df = list_invoice_items(invoice_id=invoice_id)
                    items = items_df.to_dict("records")
                    pdf_path = create_invoice_pdf(invoice, items)
                    with open(pdf_path, "rb") as pdf_file:
                        st.download_button(
                            "Descargar PDF",
                            data=pdf_file,
                            file_name=f"Factura_GAMETRONIX_{invoice_id}.pdf",
                            mime="application/pdf",
                            key=f"download_invoice_{invoice_id}",
                        )
                except Exception as e:
                    st.error(str(e))
