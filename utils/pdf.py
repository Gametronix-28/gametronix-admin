"""
Generación de PDFs: facturas de venta y órdenes de reparación.
Usa ReportLab para crear documentos profesionales listos para enviar al cliente.
"""

from pathlib import Path
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


# ── Helpers ───────────────────────────────────────────────

def _money(value):
    try:
        return f"$ {float(value):,.0f} COP"
    except Exception:
        return "$ 0 COP"


def _safe(value):
    if value is None:
        return ""
    return str(value)


# ── PDF de factura ────────────────────────────────────────

def create_invoice_pdf(invoice, items, output_dir="facturas_pdf"):
    """
    Crea un PDF de factura para el cliente.
    invoice: dict con id, date, client, payment_method, total, notes, user.
    items: lista de dicts con product_name, sku, qty, unit_price, total, serial, notes.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    invoice_id = invoice.get("id", "sin_id")
    pdf_path = out_dir / f"Factura_GAMETRONIX_{invoice_id}.pdf"

    doc = SimpleDocTemplate(
        str(pdf_path), pagesize=letter,
        rightMargin=16 * mm, leftMargin=16 * mm,
        topMargin=14 * mm, bottomMargin=14 * mm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "GTTitle", parent=styles["Title"], fontName="Helvetica-Bold",
        fontSize=22, leading=26, textColor=colors.HexColor("#111827"),
        alignment=1, spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "GTSubtitle", parent=styles["Normal"], fontName="Helvetica",
        fontSize=9, leading=12, textColor=colors.HexColor("#4B5563"),
        alignment=1, spaceAfter=12,
    )
    section_style = ParagraphStyle(
        "Section", parent=styles["Heading2"], fontName="Helvetica-Bold",
        fontSize=11, leading=14, textColor=colors.HexColor("#111827"),
        spaceBefore=8, spaceAfter=6,
    )
    normal = ParagraphStyle(
        "NormalSmall", parent=styles["Normal"], fontName="Helvetica",
        fontSize=9, leading=12, textColor=colors.HexColor("#111827"),
    )
    small = ParagraphStyle(
        "Small", parent=styles["Normal"], fontName="Helvetica",
        fontSize=8, leading=10, textColor=colors.HexColor("#374151"),
    )

    story = []

    # Encabezado
    story.append(Paragraph("GAMETRONIX", title_style))
    story.append(Paragraph("Factura de venta - Servicio administrativo interno", subtitle_style))

    invoice_date = _safe(invoice.get("date"))
    client = _safe(invoice.get("client")) or "Cliente no especificado"
    payment_method = _safe(invoice.get("payment_method"))
    user = _safe(invoice.get("user"))

    # Tabla de datos generales
    header_data = [
        [Paragraph("<b>Factura No.</b>", normal), Paragraph(str(invoice_id), normal),
         Paragraph("<b>Fecha</b>", normal), Paragraph(invoice_date, normal)],
        [Paragraph("<b>Cliente</b>", normal), Paragraph(client, normal),
         Paragraph("<b>Medio de pago</b>", normal), Paragraph(payment_method, normal)],
        [Paragraph("<b>Vendedor/usuario</b>", normal), Paragraph(user, normal),
         Paragraph("<b>Moneda</b>", normal), Paragraph("COP", normal)],
    ]

    header_table = Table(header_data, colWidths=[32 * mm, 55 * mm, 35 * mm, 55 * mm])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F9FAFB")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E5E7EB")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 8))

    # Productos
    story.append(Paragraph("Productos", section_style))

    table_data = [[
        Paragraph("<b>Producto</b>", small), Paragraph("<b>SKU</b>", small),
        Paragraph("<b>Serial</b>", small), Paragraph("<b>Cant.</b>", small),
        Paragraph("<b>Precio</b>", small), Paragraph("<b>Total</b>", small),
    ]]

    for row in items:
        table_data.append([
            Paragraph(_safe(row.get("product_name")), small),
            Paragraph(_safe(row.get("sku")), small),
            Paragraph(_safe(row.get("serial")), small),
            Paragraph(_safe(row.get("qty")), small),
            Paragraph(_money(row.get("unit_price")), small),
            Paragraph(_money(row.get("total")), small),
        ])
        item_note = _safe(row.get("notes"))
        if item_note:
            table_data.append([
                Paragraph(f"<b>Nota:</b> {item_note}", small), "", "", "", "", "",
            ])

    products_table = Table(
        table_data,
        colWidths=[55 * mm, 23 * mm, 38 * mm, 14 * mm, 28 * mm, 28 * mm],
        repeatRows=1,
    )
    products_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E5E7EB")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(products_table)
    story.append(Spacer(1, 10))

    # Totales
    totals_data = [
        ["Subtotal", _money(invoice.get("total"))],
        ["Total", _money(invoice.get("total"))],
    ]
    totals_table = Table(totals_data, colWidths=[40 * mm, 45 * mm], hAlign="RIGHT")
    totals_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#111827")),
        ("TEXTCOLOR", (0, 1), (-1, 1), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#111827")),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D1D5DB")),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(totals_table)

    # Notas
    notes = _safe(invoice.get("notes"))
    if notes:
        story.append(Spacer(1, 10))
        story.append(Paragraph("Nota general", section_style))
        story.append(Paragraph(notes, normal))

    story.append(Spacer(1, 16))
    story.append(Paragraph(
        "Gracias por tu compra. Conserva esta factura para soporte, garantía o consultas futuras.",
        subtitle_style,
    ))
    story.append(Paragraph(
        f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        subtitle_style,
    ))

    doc.build(story)
    return str(pdf_path)


# ── PDF de orden de reparación ────────────────────────────

def create_repair_order_pdf(repair, stock_parts, external_parts, payments, output_dir="ordenes_reparacion_pdf"):
    """
    Crea un PDF de orden de reparación con datos del equipo, repuestos y pagos.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    order_code = repair.get("order_code") or f"REP-{repair.get('id')}"
    pdf_path = out_dir / f"Orden_{order_code}.pdf"

    doc = SimpleDocTemplate(
        str(pdf_path), pagesize=letter,
        rightMargin=16 * mm, leftMargin=16 * mm,
        topMargin=14 * mm, bottomMargin=14 * mm,
    )

    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "TitleGT", parent=styles["Title"], fontSize=20,
        textColor=colors.HexColor("#111827"), alignment=1,
    )
    normal = ParagraphStyle(
        "NormalGT", parent=styles["Normal"], fontSize=9, leading=12,
    )

    story = [
        Paragraph("GAMETRONIX", title),
        Paragraph("Orden de reparación", normal),
        Spacer(1, 8),
    ]

    # Datos principales
    data = [
        ["Orden", _safe(order_code), "Fecha", _safe(repair.get("date"))],
        ["Cliente", _safe(repair.get("client")), "Teléfono", _safe(repair.get("phone"))],
        ["Equipo", _safe(repair.get("device")), "Serial", _safe(repair.get("serial"))],
        ["Técnico", _safe(repair.get("technician")), "Estado", _safe(repair.get("status"))],
        ["Garantía", f"{_safe(repair.get('warranty_days'))} días", "Saldo", _money(repair.get("balance_due"))],
    ]
    table = Table(data, colWidths=[28 * mm, 60 * mm, 28 * mm, 60 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F9FAFB")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E5E7EB")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(table)
    story.append(Spacer(1, 8))

    # Campos descriptivos
    for label, key in [
        ("Accesorios recibidos", "accessories"),
        ("Estado recibido", "received_condition"),
        ("Falla reportada", "issue"),
        ("Diagnóstico", "diagnostic"),
        ("Solución", "repair_solution"),
        ("Notas", "notes"),
    ]:
        value = _safe(repair.get(key))
        if value:
            story.append(Paragraph(f"<b>{label}:</b> {value}", normal))
            story.append(Spacer(1, 4))

    # Costos y pagos
    story.append(Spacer(1, 6))
    story.append(Paragraph("<b>Costos y pagos</b>", normal))
    totals = [
        ["Valor reparación", _money(repair.get("total"))],
        ["Costo repuestos bodega", _money(repair.get("parts_cost"))],
        ["Costo repuestos externos", _money(repair.get("external_parts_cost"))],
        ["Ganancia", _money(repair.get("profit"))],
        ["Abonado", _money(repair.get("amount_paid"))],
        ["Saldo pendiente", _money(repair.get("balance_due"))],
    ]
    totals_table = Table(totals, colWidths=[60 * mm, 60 * mm])
    totals_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#111827")),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D1D5DB")),
        ("BACKGROUND", (0, 5), (-1, 5), colors.HexColor("#111827")),
        ("TEXTCOLOR", (0, 5), (-1, 5), colors.white),
    ]))
    story.append(totals_table)

    doc.build(story)
    return str(pdf_path)
