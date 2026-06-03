"""Dashboard de ganancias y resÃºmenes financieros."""

import pandas as pd
from db.connection import get_db, read_sql


def profit_dashboard(start, end):
    with get_db() as con:
        cur = con.cursor()

        sales = cur.execute(
            "SELECT COALESCE(SUM(total), 0), COALESCE(SUM(cost_total), 0), COALESCE(SUM(profit), 0) "
            "FROM sales WHERE active = 1 AND currency = 'COP' "
            "AND date(date) BETWEEN date(?) AND date(?)",
            (start, end),
        ).fetchone()

        invoices = cur.execute(
            "SELECT COALESCE(SUM(total), 0), COALESCE(SUM(cost_total), 0), COALESCE(SUM(profit), 0) "
            "FROM invoices WHERE active = 1 AND currency = 'COP' "
            "AND date(date) BETWEEN date(?) AND date(?)",
            (start, end),
        ).fetchone()

        repairs = cur.execute(
            "SELECT COALESCE(SUM(total), 0), COALESCE(SUM(parts_cost + external_parts_cost), 0), "
            "COALESCE(SUM(profit), 0) FROM repairs "
            "WHERE active = 1 AND date(date) BETWEEN date(?) AND date(?)",
            (start, end),
        ).fetchone()

        expenses_colombia = cur.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM expenses "
            "WHERE active = 1 AND cashbox = 'Caja Colombia' AND currency = 'COP' "
            "AND date(date) BETWEEN date(?) AND date(?)",
            (start, end),
        ).fetchone()[0]

        expenses_usa = cur.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM expenses "
            "WHERE active = 1 AND cashbox = 'Caja USA' AND currency = 'USD' "
            "AND date(date) BETWEEN date(?) AND date(?)",
            (start, end),
        ).fetchone()[0]

        purchases_usa = cur.execute(
            "SELECT COALESCE(SUM(total), 0) FROM purchases "
            "WHERE active = 1 AND warehouse = 'USA' "
            "AND date(date) BETWEEN date(?) AND date(?)",
            (start, end),
        ).fetchone()[0]

        purchases_colombia = cur.execute(
            "SELECT COALESCE(SUM(total), 0) FROM purchases "
            "WHERE active = 1 AND warehouse = 'Colombia' "
            "AND date(date) BETWEEN date(?) AND date(?)",
            (start, end),
        ).fetchone()[0]

        sent = cur.execute(
            "SELECT COUNT(*) FROM usa_shipments WHERE active = 1 AND status = 'Enviado'"
        ).fetchone()[0]
        lost = cur.execute(
            "SELECT COUNT(*) FROM usa_shipments WHERE active = 1 AND status = 'Perdido'"
        ).fetchone()[0]
        received = cur.execute(
            "SELECT COUNT(*) FROM usa_shipments WHERE active = 1 AND status = 'Bodega Colombia'"
        ).fetchone()[0]
        parts_stock = cur.execute(
            "SELECT COALESCE(SUM(stock), 0) FROM products WHERE active = 1 AND warehouse = 'Repuestos'"
        ).fetchone()[0]

    old_sales_cop = float(sales[0] or 0)
    invoice_sales_cop = float(invoices[0] or 0)
    total_sales_cop = old_sales_cop + invoice_sales_cop

    old_cost_cop = float(sales[1] or 0)
    invoice_cost_cop = float(invoices[1] or 0)
    repairs_cost_cop = float(repairs[1] or 0)
    total_cost_cop = old_cost_cop + invoice_cost_cop + repairs_cost_cop

    old_profit_cop = float(sales[2] or 0)
    invoice_profit_cop = float(invoices[2] or 0)
    sales_profit_cop = old_profit_cop + invoice_profit_cop

    repairs_income_cop = float(repairs[0] or 0)
    repairs_profit_cop = float(repairs[2] or 0)

    gross_profit_cop = sales_profit_cop + repairs_profit_cop
    net_profit_cop = gross_profit_cop - float(expenses_colombia or 0)

    return {
        "sales_cop": total_sales_cop,
        "old_sales_cop": old_sales_cop,
        "invoice_sales_cop": invoice_sales_cop,
        "repairs_income_cop": repairs_income_cop,
        "cost_cop": total_cost_cop,
        "profit_cop": sales_profit_cop,
        "repairs_profit_cop": repairs_profit_cop,
        "expenses_cop": float(expenses_colombia or 0),
        "expenses_usd": float(expenses_usa or 0),
        "net_profit_cop": net_profit_cop,
        "purchases_usd": float(purchases_usa or 0),
        "purchases_colombia_cop": float(purchases_colombia or 0),
        "shipments_sent": sent,
        "shipments_lost": lost,
        "shipments_received": received,
        "parts_stock": parts_stock,
    }


def payment_method_summary(start, end):
    with get_db() as con:
        frames = []
        for sql in [
            "SELECT COALESCE(payment_method, 'Sin especificar') AS medio_pago, "
            "COALESCE(SUM(total), 0) AS saldo FROM invoices "
            "WHERE active = 1 AND date(date) BETWEEN date(?) AND date(?) "
            "GROUP BY COALESCE(payment_method, 'Sin especificar')",
            "SELECT COALESCE(payment_method, 'Sin especificar') AS medio_pago, "
            "COALESCE(SUM(total), 0) AS saldo FROM sales "
            "WHERE active = 1 AND date(date) BETWEEN date(?) AND date(?) "
            "GROUP BY COALESCE(payment_method, 'Sin especificar')",
            "SELECT COALESCE(payment_method, 'Sin especificar') AS medio_pago, "
            "COALESCE(SUM(amount), 0) AS saldo FROM repair_payments "
            "WHERE active = 1 AND date(date) BETWEEN date(?) AND date(?) "
            "GROUP BY COALESCE(payment_method, 'Sin especificar')",
        ]:
            try:
                frames.append(read_sql(con, sql, (start, end)))
            except Exception:
                pass

    if not frames:
        return pd.DataFrame({
            "medio_pago": ["Efectivo", "Bancolombia", "Nequi", "Tarjeta", "Otro"],
            "saldo": [0, 0, 0, 0, 0],
        })

    df = pd.concat(frames, ignore_index=True)
    if df.empty:
        return pd.DataFrame({
            "medio_pago": ["Efectivo", "Bancolombia", "Nequi", "Tarjeta", "Otro"],
            "saldo": [0, 0, 0, 0, 0],
        })

    def normalize_payment(value):
        value = str(value or "Sin especificar")
        if "Bancolombia" in value:
            return "Bancolombia"
        if "Nequi" in value:
            return "Nequi"
        return value

    df["medio_pago"] = df["medio_pago"].apply(normalize_payment)
    result = df.groupby("medio_pago", as_index=False)["saldo"].sum()
    order = ["Efectivo", "Bancolombia", "Nequi", "Tarjeta", "Otro", "Pendiente", "Sin especificar"]
    result["orden"] = result["medio_pago"].apply(lambda x: order.index(x) if x in order else 99)
    result = result.sort_values(["orden", "medio_pago"]).drop(columns=["orden"])
    return result

