"""Importacion masiva de productos desde Excel."""

import pandas as pd
from db.purchase import register_purchase


def import_products_from_excel(file_path, user="admin"):
    """
    Lee un archivo Excel con productos y los registra como compras.
    Columnas esperadas: SKU, Nombre, Categoria, Cantidad, Costo_unitario, Moneda, Bodega, Proveedor, Notas
    Retorna (total_registrados, total_costo_compra, errores).
    """
    df = pd.read_excel(file_path)

    # Normalizar nombres de columnas
    col_map = {
        "sku": "SKU", "nombre": "Nombre", "categoria": "Categoria",
        "cantidad": "Cantidad", "costo_unitario": "Costo_unitario",
        "moneda": "Moneda", "bodega": "Bodega", "proveedor": "Proveedor",
        "notas": "Notas",
    }
    df = df.rename(columns={k.lower(): v for k, v in col_map.items()})

    total = 0
    total_cost = 0.0
    errores = []

    for idx, row in df.iterrows():
        try:
            name = str(row.get("Nombre", "")).strip()
            if not name:
                errores.append(f"Fila {idx + 2}: Nombre vacio")
                continue

            sku = str(row.get("SKU", "")).strip() if pd.notna(row.get("SKU")) else ""
            category = str(row.get("Categoria", "")).strip() if pd.notna(row.get("Categoria")) else ""
            qty = int(row.get("Cantidad", 1)) if pd.notna(row.get("Cantidad")) else 1
            unit_cost = float(row.get("Costo_unitario", 0))
            currency = str(row.get("Moneda", "COP")).strip().upper()
            warehouse = str(row.get("Bodega", "Colombia")).strip()
            supplier = str(row.get("Proveedor", "")).strip() if pd.notna(row.get("Proveedor")) else ""
            notes = str(row.get("Notas", "")).strip() if pd.notna(row.get("Notas")) else ""

            if currency not in ("COP", "USD"):
                errores.append(f"Fila {idx + 2}: Moneda invalida '{currency}'. Usar COP o USD")
                continue
            if warehouse not in ("Colombia", "USA", "Repuestos"):
                errores.append(f"Fila {idx + 2}: Bodega invalida '{warehouse}'. Usar Colombia, USA o Repuestos")
                continue

            cashbox = "Caja Colombia" if currency == "COP" else "Caja USA"

            register_purchase(warehouse, sku, name, category, qty, unit_cost, currency, cashbox, supplier, notes, user)
            total += 1
            total_cost += qty * unit_cost

        except Exception as e:
            errores.append(f"Fila {idx + 2}: {e}")

    return total, total_cost, errores
