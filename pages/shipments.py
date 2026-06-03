"""Envíos USA — gestión de envíos con estados."""

import streamlit as st
from components.layout import header
from db.product import list_inventory
from db.shipment import register_usa_shipment, update_usa_shipment_status, list_usa_shipments


def render():
    header(
        "Envíos USA",
        "El producto se descuenta de USA al enviarse, pero solo suma a Colombia "
        "cuando el estado sea Bodega Colombia.",
    )

    usa = list_inventory("USA")

    if usa.empty:
        st.warning("No hay productos en Bodega USA.")
    else:
        with st.form("ship_usa"):
            product_label = st.selectbox(
                "Producto USA",
                usa.apply(
                    lambda r: f"{r['id']} - {r['sku']} - {r['name']} - Stock {r['stock']}",
                    axis=1,
                ),
            )
            product_id = int(product_label.split(" - ")[0])

            c1, c2, c3 = st.columns(3)
            qty = c1.number_input("Cantidad a enviar", min_value=1, step=1)
            rate = c2.number_input("Tasa USD/COP", min_value=0.000001, value=4000.0, step=1.0)
            status = c3.selectbox(
                "Estado inicial", ["Enviado", "Perdido", "Bodega Colombia"]
            )
            destination = st.text_input("Destino", value="Bodega Colombia")
            notes = st.text_area("Notas")

            if st.form_submit_button("Registrar envío USA"):
                try:
                    register_usa_shipment(
                        product_id, qty, rate, destination, status, notes,
                        st.session_state.user["username"],
                    )
                    if status == "Bodega Colombia":
                        st.success("Envío registrado y sumado automáticamente a Bodega Colombia.")
                    else:
                        st.success(
                            "Envío registrado. El stock queda pendiente hasta cambiar "
                            "estado a Bodega Colombia."
                        )
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

    st.divider()
    st.subheader("Actualizar estado de envío")

    shipments = list_usa_shipments(300)
    st.dataframe(shipments, use_container_width=True, hide_index=True)

    if not shipments.empty and "status" in shipments.columns:
        active = shipments[shipments["status"].isin(["Enviado", "Perdido"])]

        if not active.empty:
            with st.form("update_shipment_status"):
                shipment_label = st.selectbox(
                    "Envío",
                    active.apply(
                        lambda r: f"{r['id']} - {r['sku']} - {r['product_name']} - "
                                  f"Cantidad {r['qty']} - Estado {r['status']}",
                        axis=1,
                    ),
                )
                shipment_id = int(shipment_label.split(" - ")[0])
                new_status = st.selectbox(
                    "Nuevo estado", ["Enviado", "Perdido", "Bodega Colombia"]
                )
                reason = st.text_input("Observación del cambio")

                if st.form_submit_button("Actualizar estado"):
                    try:
                        update_usa_shipment_status(
                            shipment_id, new_status, reason,
                            st.session_state.user["username"],
                        )
                        if new_status == "Bodega Colombia":
                            st.success(
                                "Estado actualizado. Producto sumado automáticamente "
                                "a Bodega Colombia."
                            )
                        else:
                            st.success("Estado actualizado.")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
        else:
            st.info("No hay envíos pendientes para actualizar.")
