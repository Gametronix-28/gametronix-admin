"""Taller Reparaciones — 6 tabs: Nueva orden, Órdenes, Abonos, Entrega, Pendientes, Historial."""

import streamlit as st
from components.layout import header
from utils.format import money
from utils.pdf import create_repair_order_pdf
from db.product import list_inventory
from db.repair import (
    register_repair, add_repair_payment, deliver_repair,
    update_repair_status, mark_repair_paid,
    get_repair, list_repairs, list_repair_parts, list_repair_external_parts,
    list_repair_payments, list_pending_repairs, list_repairs_by_client,
)


def render():
    header("Taller Reparaciones",
           "Órdenes de reparación, abonos, repuestos de bodega y repuestos comprados por fuera.")

    parts = list_inventory("Repuestos")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Nueva orden", "Ordenes y pagos", "Historial de pagos",
        "Entrega", "Pendientes", "Historial de servicio",
    ])

    with tab1:
        _render_new_order(parts)
    with tab2:
        _render_orders_list()
    with tab3:
        _render_payments_history()
    with tab4:
        _render_delivery()
    with tab5:
        _render_pending()
    with tab6:
        _render_client_history()


# ── Tab 1: Nueva orden ──────────────────────────────────

def _render_new_order(parts):
    st.subheader("Registrar nueva orden de reparacion")

    # Control de cantidad de equipos (fuera del form para que reaccione)
    if "num_devices" not in st.session_state:
        st.session_state.num_devices = 1

    num_devices = st.number_input(
        "Cantidad de equipos en esta orden",
        min_value=1, max_value=10, step=1,
        value=st.session_state.num_devices,
        key="num_devices",
    )

    with st.form("repair_advanced"):
        c1, c2, c3 = st.columns(3)
        client = c1.text_input("Cliente")
        phone = c2.text_input("Telefono / WhatsApp")
        technician = c3.text_input("Tecnico responsable")

        warranty_days = st.number_input("Garantia en dias", min_value=0, step=1, value=30)

        accessories = st.text_input("Accesorios recibidos", placeholder="Cable, caja, joystick, tapas, etc.")
        received_condition = st.text_area(
            "Estado en que se reciben los equipos",
            placeholder="Rayones, golpes, botones danados, no prende, etc.",
        )

        # ── Equipos (dinamicos) ────────────────────────
        st.divider()
        st.subheader(f"Equipos ({num_devices})")

        devices_list = []
        individual_total = 0.0
        for i in range(1, num_devices + 1):
            with st.expander(f"Equipo {i}", expanded=(i == 1)):
                dc1, dc2, dc3 = st.columns([2, 1, 1])
                dev_name = dc1.text_input(f"Equipo {i}", placeholder="Control PS5, Xbox, consola, etc.", key=f"dev_name_{i}")
                dev_serial = dc2.text_input(f"Serial {i}", key=f"dev_serial_{i}")
                dev_cost = dc3.number_input(f"Valor arreglo {i} COP", min_value=0.0, step=1000.0, key=f"dev_cost_{i}")
                dev_issue = st.text_area(f"Falla reportada equipo {i}", key=f"dev_issue_{i}")
                dev_diag = st.text_input(f"Diagnostico tecnico equipo {i}", key=f"dev_diag_{i}")
                dev_sol = st.text_input(f"Solucion / trabajo equipo {i}", key=f"dev_sol_{i}")
                if dev_name.strip():
                    devices_list.append({
                        "device": dev_name.strip(),
                        "serial": dev_serial.strip(),
                        "cost": float(dev_cost),
                        "issue": dev_issue.strip(),
                        "diagnostic": dev_diag.strip(),
                        "solution": dev_sol.strip(),
                    })
                    individual_total += float(dev_cost)

        # Si no se lleno ningun equipo, usar campos legacy
        if not devices_list:
            devices_list = [{"device": "", "serial": "", "issue": "", "diagnostic": "", "solution": ""}]

        # ── Precio y pago ──────────────────────────────
        st.divider()
        # Total calculado de los costos individuales
        labor_price = individual_total
        st.metric("Total a cobrar (suma de equipos)", money(labor_price, "COP"))
        if labor_price == 0:
            st.caption("Asigna valores de arreglo a cada equipo arriba o ingresa un total manual abajo.")
            labor_price = st.number_input("Valor total manual COP", min_value=0.0, step=1000.0, key="manual_total")

        c8, c9 = st.columns(2)
        amount_paid = c8.number_input("Abono / pago inicial COP", min_value=0.0, step=1000.0)
        payment = c9.selectbox(
            "Medio de pago del abono",
            ["Pendiente", "Efectivo", "Transferencia - Bancolombia",
             "Transferencia - Nequi", "Tarjeta", "Otro"],
        )

        c10, c11 = st.columns(2)
        status = c10.selectbox(
            "Estado",
            ["Recibido", "En proceso", "Esperando repuesto", "Terminado", "Pagado", "Entregado"],
        )
        notes = c11.text_area("Notas internas")

        # Repuestos de bodega
        st.divider()
        st.subheader("Repuestos usados desde Bodega Repuestos")
        used_parts = []

        if not parts.empty:
            for i in range(1, 6):
                pc1, pc2 = st.columns([3, 1])
                label = pc1.selectbox(
                    f"Repuesto de bodega {i}",
                    ["No usar"] + list(parts.apply(
                        lambda r: f"{r['id']} - {r['sku']} - {r['name']} - Stock {r['stock']} - Costo {r['cost']}",
                        axis=1,
                    )),
                    key=f"repair_stock_part_{i}",
                )
                qty = pc2.number_input(
                    f"Cantidad bodega {i}", min_value=0, step=1, key=f"repair_stock_qty_{i}",
                )
                if label != "No usar" and qty > 0:
                    used_parts.append((int(label.split(" - ")[0]), int(qty)))
        else:
            st.info("No hay repuestos cargados en Bodega Repuestos.")

        # Repuestos externos
        st.divider()
        st.subheader("Repuestos comprados por fuera")
        st.caption(
            "Estos repuestos NO se descuentan de bodega. Solo se suman como costo "
            "y reducen la ganancia de la reparación."
        )
        external_parts = []

        for i in range(1, 6):
            with st.expander(f"Repuesto externo {i}", expanded=(i == 1)):
                ec1, ec2, ec3 = st.columns(3)
                part_name = ec1.text_input(f"Nombre repuesto externo {i}", key=f"external_part_name_{i}")
                ext_qty = ec2.number_input(f"Cantidad externa {i}", min_value=0, step=1, key=f"external_part_qty_{i}")
                ext_cost = ec3.number_input(f"Costo unitario externo COP {i}", min_value=0.0, step=1000.0, key=f"external_part_cost_{i}")
                ec4, ec5 = st.columns(2)
                supplier = ec4.text_input(f"Proveedor externo {i}", key=f"external_supplier_{i}")
                ext_notes = ec5.text_input(f"Nota repuesto externo {i}", key=f"external_notes_{i}")

                if part_name.strip() and ext_qty > 0:
                    external_parts.append({
                        "part_name": part_name, "qty": int(ext_qty),
                        "unit_cost": float(ext_cost), "supplier": supplier, "notes": ext_notes,
                    })

        # Vista previa de costos
        stock_cost_preview = 0.0
        if not parts.empty:
            for part_id, qty in used_parts:
                row = parts[parts["id"] == part_id]
                if not row.empty:
                    stock_cost_preview += float(row.iloc[0]["cost"] or 0) * qty

        external_cost_preview = sum(p["qty"] * p["unit_cost"] for p in external_parts)
        total_cost_preview = stock_cost_preview + external_cost_preview
        profit_preview = float(labor_price or 0) - total_cost_preview
        balance_preview = float(labor_price or 0) - float(amount_paid or 0)

        p1, p2, p3, p4 = st.columns(4)
        p1.metric("Costo repuestos bodega", money(stock_cost_preview, "COP"))
        p2.metric("Costo repuestos externos", money(external_cost_preview, "COP"))
        p3.metric("Ganancia estimada", money(profit_preview, "COP"))
        p4.metric("Saldo pendiente", money(balance_preview, "COP"))

        if st.form_submit_button("Guardar orden de reparacion"):
            try:
                # Primer equipo como principal
                main = devices_list[0] if devices_list else {"device": "", "serial": "", "issue": "", "diagnostic": "", "solution": ""}
                repair_id = register_repair(
                    client, phone, main["device"], main["serial"], accessories, received_condition,
                    main["issue"], main["diagnostic"], main["solution"], technician, int(warranty_days),
                    float(labor_price), status, payment, float(amount_paid),
                    used_parts, external_parts, notes, st.session_state.user["username"],
                    additional_devices=devices_list[1:] if len(devices_list) > 1 else [],
                )
                st.success(f"Orden de reparacion registrada: REP-{repair_id:05d}")
                st.rerun()
            except Exception as e:
                st.error(str(e))


# ── Tab 2: Órdenes ──────────────────────────────────────

def _render_orders_list():
    st.subheader("Ordenes de reparacion")
    repairs_df = list_repairs(300)

    if repairs_df.empty:
        st.info("No hay ordenes registradas.")
        return

    # Encabezado de la tabla
    st.caption(f"Total: {len(repairs_df)} ordenes")

    # ── Tabla interactiva con acciones inline ─────────────
    status_options = ["Recibido", "En proceso", "Esperando repuesto", "Terminado", "Pagado", "Entregado"]

    for idx, row in repairs_df.iterrows():
        rid = int(row["id"])
        order = row.get("order_code", f"REP-{rid:05d}")
        client = row.get("client") or "-"
        phone = row.get("phone") or "-"
        device = row.get("device") or "-"
        current_status = row.get("status") or "Recibido"
        balance = float(row.get("balance_due") or 0)
        total = float(row.get("total") or 0)

        # Fila principal: info + estado + acciones
        c1, c2, c3, c4, c5, c6, c7, c8 = st.columns([0.9, 1.2, 1.1, 1.1, 0.8, 1.1, 1.8, 0.5])

        with c1:
            st.write(f"**{order}**")
        with c2:
            st.write(client)
        with c3:
            st.write(phone)
        with c4:
            st.write(device)
        with c5:
            st.write(money(total, "COP"))

        # Estado editable
        with c6:
            status_idx = status_options.index(current_status) if current_status in status_options else 0
            new_status = st.selectbox(
                "Estado",
                status_options,
                index=status_idx,
                key=f"status_{rid}",
                label_visibility="collapsed",
            )

        # Pago / abono inline
        with c7:
            if balance > 0:
                st.caption(f"Pend: {money(balance, 'COP')}")
                ab1, ab2 = st.columns([1, 1])
                with ab1:
                    pay_method = st.selectbox(
                        "Metodo",
                        ["Efectivo", "Transferencia - Bancolombia", "Transferencia - Nequi", "Tarjeta", "Otro"],
                        key=f"paymethod_{rid}",
                        label_visibility="collapsed",
                    )
                with ab2:
                    pay_amount = st.number_input(
                        "Monto",
                        min_value=0.0,
                        max_value=balance,
                        value=balance,
                        step=1000.0,
                        key=f"payamount_{rid}",
                        label_visibility="collapsed",
                    )
                # Botones de pago
                ab3, ab4 = st.columns([1, 1])
                with ab3:
                    if st.button("Abonar", key=f"abbtn_{rid}"):
                        try:
                            add_repair_payment(rid, pay_amount, pay_method, "Abono", st.session_state.user["username"])
                            st.success(f"Abono {money(pay_amount, 'COP')} registrado.")
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))
                with ab4:
                    if st.button("Pagar todo", key=f"payallbtn_{rid}"):
                        try:
                            mark_repair_paid(rid, pay_method, st.session_state.user["username"])
                            st.success(f"{order} PAGADA. Dinero en Caja Colombia.")
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))
            else:
                st.success("Pagado")

        # PDF
        with c8:
            if st.button("PDF", key=f"pdfbtn_{rid}"):
                try:
                    repair = get_repair(rid)
                    if repair:
                        stock_parts_df = list_repair_parts(300)
                        ext_df = list_repair_external_parts(300)
                        pay_df = list_repair_payments(300)
                        pdf_path = create_repair_order_pdf(
                            repair,
                            stock_parts_df.to_dict("records"),
                            ext_df.to_dict("records"),
                            pay_df.to_dict("records"),
                        )
                        with open(pdf_path, "rb") as f:
                            st.download_button(
                                f"Descargar {order}",
                                data=f,
                                file_name=f"Orden_{order}.pdf",
                                mime="application/pdf",
                                key=f"dl_{rid}",
                            )
                except Exception as e:
                    st.error(str(e))

        # Aplicar cambio de estado
        if new_status != current_status:
            try:
                update_repair_status(rid, new_status)
                st.success(f"{order} → {new_status}")
                st.rerun()
            except Exception as e:
                st.error(str(e))

        st.divider()


# ── Historial de pagos ─────────────────────────────────

def _render_payments_history():
    st.subheader("Historial de pagos de taller")
    payments_df = list_repair_payments(300)
    if payments_df.empty:
        st.info("No hay pagos registrados.")
    else:
        st.dataframe(payments_df, use_container_width=True, hide_index=True)


# ── Tab 4: Entrega ──────────────────────────────────────

def _render_delivery():
    st.subheader("Entregar equipo reparado")
    repairs_df = list_repairs(300)

    if repairs_df.empty:
        st.info("No hay reparaciones registradas.")
        return

    ready_df = repairs_df[
        (repairs_df["balance_due"] <= 0) & (repairs_df["status"] != "Entregado")
    ] if not repairs_df.empty else repairs_df

    if ready_df.empty:
        st.info("No hay equipos listos para entrega sin saldo pendiente.")
    else:
        with st.form("deliver_repair_form"):
            repair_label = st.selectbox(
                "Reparación lista para entregar",
                ready_df.apply(
                    lambda r: f"{r['id']} - {r['order_code']} - {r['client']} - "
                              f"{r['device']} - Estado {r['status']}",
                    axis=1,
                ),
            )
            repair_id = int(repair_label.split(" - ")[0])
            delivery_notes = st.text_area("Nota de entrega")

            if st.form_submit_button("Marcar como entregado"):
                try:
                    deliver_repair(
                        repair_id, delivery_notes, st.session_state.user["username"],
                    )
                    st.success("Equipo marcado como entregado.")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))


# ── Tab 5: Pendientes ───────────────────────────────────

def _render_pending():
    st.subheader("Reparaciones con pagos pendientes")
    st.dataframe(list_pending_repairs(300), use_container_width=True, hide_index=True)


# ── Tab 6: Historial cliente ────────────────────────────

def _render_client_history():
    st.subheader("Buscar historial por cliente, teléfono, serial o equipo")
    q = st.text_input("Buscar historial")
    if q:
        st.dataframe(
            list_repairs_by_client(q),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Escribe un cliente, teléfono, serial o equipo para buscar.")
