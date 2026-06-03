"""Router de páginas — mapea opciones del menú a funciones render."""

import streamlit as st
from config import MENU_OPTIONS

from pages.login import render_login
from pages.dashboard import render as render_dashboard
from pages.cashbox_usa import render as render_cashbox_usa
from pages.purchase_usa import render as render_purchase_usa
from pages.warehouse_usa import render as render_warehouse_usa
from pages.shipments import render as render_shipments
from pages.cashbox_colombia import render as render_cashbox_colombia
from pages.purchase_colombia import render as render_purchase_colombia
from pages.warehouse_colombia import render as render_warehouse_colombia
from pages.sales import render as render_sales
from pages.warehouse_repuestos import render as render_warehouse_repuestos
from pages.repairs import render as render_repairs
from pages.transfers import render as render_transfers
from pages.expenses import render as render_expenses
from pages.voids import render as render_voids
from pages.users import render as render_users
from pages.exports import render as render_exports

# Mapa: nombre de página → función render
_PAGE_MAP = {
    "Dashboard ganancias": render_dashboard,
    "Caja USA": render_cashbox_usa,
    "Compra USA": render_purchase_usa,
    "Bodega USA": render_warehouse_usa,
    "Envíos USA": render_shipments,
    "Caja Colombia": render_cashbox_colombia,
    "Compra Colombia": render_purchase_colombia,
    "Bodega Colombia": render_warehouse_colombia,
    "Venta Colombia": render_sales,
    "Bodega Repuestos": render_warehouse_repuestos,
    "Taller Reparaciones": render_repairs,
    "Transferencia con tasa": render_transfers,
    "Gastos por caja": render_expenses,
    "Borrar / anular registros": render_voids,
    "Usuarios": render_users,
    "Importar / Exportar": render_exports,
}


def render_page():
    """Renderiza la página seleccionada en el menú lateral."""
    page = st.session_state.get("page", "Dashboard ganancias")
    render_func = _PAGE_MAP.get(page)
    if render_func:
        render_func()
    else:
        st.error(f"Página no encontrada: {page}")
