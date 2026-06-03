"""
Capa de datos de GAMETRONIX Admin Pro.
Funciones puras — sin dependencia de Streamlit.
"""

from db.connection import get_db

# Schema
from db.schema import initialize_database

# Auth
from db.auth import authenticate, list_users, add_user

# Cashbox
from db.cashbox import get_cashbox_balance, list_cashboxes, list_cashbox_movements, cashbox_add, inject_capital

# Product
from db.product import add_or_update_product, list_inventory

# Purchase
from db.purchase import register_purchase, list_purchases

# Invoice
from db.invoice import (
    register_invoice_colombia, get_invoice,
    list_invoices, list_invoices_between, list_invoice_items,
)

# Sales legacy
from db.sales_legacy import register_sale, list_sales, list_sales_between

# Shipment
from db.shipment import (
    register_usa_shipment, update_usa_shipment_status,
    list_usa_shipments,
)

# Repair
from db.repair import (
    register_repair, add_repair_payment, deliver_repair,
    get_repair, list_repairs, list_repairs_between,
    list_repair_parts, list_repair_external_parts,
    list_repair_payments, list_pending_repairs, list_repairs_by_client,
)

# Expense
from db.expense import register_expense, list_expenses, list_expenses_by_cashbox

# Transfer
from db.transfer import calculate_transfer, register_transfer, list_transfers

# Dashboard
from db.dashboard import profit_dashboard, payment_method_summary

# Admin
from db.admin import void_record, list_voids, export_to_excel
