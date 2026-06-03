"""Formateo de moneda, strings seguros, timestamps."""

from datetime import datetime


def now():
    """Timestamp ISO actual, precisión al segundo."""
    return datetime.now().isoformat(timespec="seconds")


def money(value, cur="COP"):
    """Formatea un valor numérico como moneda legible."""
    try:
        return f"{cur} {float(value):,.2f}"
    except Exception:
        return f"{cur} 0.00"


def safe_str(value):
    """Convierte cualquier valor a string seguro. None → ''."""
    if value is None:
        return ""
    return str(value)
