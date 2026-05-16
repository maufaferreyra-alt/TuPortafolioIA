"""
Manejo del portafolio CARGADO POR EL USUARIO (no la sugerida).

A diferencia de la cartera sugerida (estática, snapshot del test),
la cartera del usuario es viva: se carga activo por activo y se
actualiza con precios del día (en el 6B con APIs).

Estructura de cada activo cargado:
{
    "id": "ABC123",                # uuid corto para borrar
    "tipo": "cedear",              # filtro del universo
    "ticker": "AAPL",
    "nombre": "Apple Inc.",
    "monto_invertido_ars": 50000,  # cuánto puso en pesos
    "precio_compra_ars": None,     # opcional
    "precio_actual_ars": 580,      # precio del día (manual en 6A,
                                   # API en 6B)
    "agregado_en": "2026-05-16T...",
}
"""

import uuid
from datetime import datetime


# Tipos de instrumentos disponibles (con labels human-friendly)
TIPOS_INSTRUMENTO = [
    {
        "id": "bono",
        "label": "Bonos",
        "descripcion": "Préstamos al Estado o empresas (AL30, GD30, etc.)",
        "icono": "📜",
    },
    {
        "id": "cedear",
        "label": "CEDEARs",
        "descripcion": "Acciones de empresas extranjeras desde Argentina (AAPL, SPY, etc.)",
        "icono": "🌎",
    },
    {
        "id": "accion_arg",
        "label": "Acciones argentinas",
        "descripcion": "Empresas que cotizan en BYMA (YPFD, GGAL, etc.)",
        "icono": "🇦🇷",
    },
    {
        "id": "on",
        "label": "Obligaciones Negociables (ONs)",
        "descripcion": "Bonos emitidos por empresas argentinas (YPFDS, TGS, etc.)",
        "icono": "🏢",
    },
    {
        "id": "fci",
        "label": "Fondos Comunes (FCIs)",
        "descripcion": "Fondos administrados por gerentes — incluye Money Market",
        "icono": "💰",
    },
    {
        "id": "letra",
        "label": "Letras del Tesoro",
        "descripcion": "Préstamos al Estado a corto plazo (LECAPs, etc.)",
        "icono": "📄",
    },
    {
        "id": "mep",
        "label": "Dólar MEP",
        "descripcion": "Dólares legales obtenidos vía bonos (AL30D, GD30D)",
        "icono": "💵",
    },
]


def crear_activo(
    tipo: str,
    ticker: str,
    nombre: str,
    monto_invertido_ars: float,
    precio_actual_ars: float,
    precio_compra_ars: float | None = None,
) -> dict:
    """Crea el dict de un activo nuevo para agregar al portafolio."""
    return {
        "id": str(uuid.uuid4())[:8],
        "tipo": tipo,
        "ticker": ticker,
        "nombre": nombre,
        "monto_invertido_ars": float(monto_invertido_ars),
        "precio_compra_ars": float(precio_compra_ars) if precio_compra_ars else None,
        "precio_actual_ars": float(precio_actual_ars),
        "agregado_en": datetime.now().isoformat(),
    }


def calcular_valor_actual(activo: dict) -> float:
    """
    Calcula el valor actual de un activo según precio_actual / precio_compra.
    Si no hay precio_compra, asumimos que monto_invertido = monto_actual.
    """
    if not activo.get("precio_compra_ars"):
        return activo["monto_invertido_ars"]

    # cantidad implícita = monto_invertido / precio_compra
    cantidad = activo["monto_invertido_ars"] / activo["precio_compra_ars"]
    valor_actual = cantidad * activo["precio_actual_ars"]
    return valor_actual


def calcular_pnl(activo: dict) -> dict:
    """
    Calcula ganancia/pérdida vs precio de compra.
    Returns dict con valor_actual, monto_invertido, pnl_ars, pnl_pct.
    Si no hay precio compra, pnl es None.
    """
    valor_actual = calcular_valor_actual(activo)
    monto_invertido = activo["monto_invertido_ars"]

    if not activo.get("precio_compra_ars"):
        return {
            "valor_actual": valor_actual,
            "monto_invertido": monto_invertido,
            "pnl_ars": None,
            "pnl_pct": None,
        }

    pnl_ars = valor_actual - monto_invertido
    pnl_pct = (pnl_ars / monto_invertido) * 100 if monto_invertido > 0 else 0

    return {
        "valor_actual": valor_actual,
        "monto_invertido": monto_invertido,
        "pnl_ars": pnl_ars,
        "pnl_pct": pnl_pct,
    }


def total_portafolio(activos: list[dict]) -> dict:
    """Suma totales del portafolio del usuario."""
    if not activos:
        return {
            "valor_total_actual": 0,
            "total_invertido": 0,
            "pnl_total_ars": 0,
            "pnl_total_pct": 0,
            "cantidad_activos": 0,
        }

    valor_total_actual = sum(calcular_valor_actual(a) for a in activos)
    total_invertido = sum(a["monto_invertido_ars"] for a in activos)
    pnl_total_ars = valor_total_actual - total_invertido
    pnl_total_pct = (pnl_total_ars / total_invertido * 100) if total_invertido > 0 else 0

    return {
        "valor_total_actual": valor_total_actual,
        "total_invertido": total_invertido,
        "pnl_total_ars": pnl_total_ars,
        "pnl_total_pct": pnl_total_pct,
        "cantidad_activos": len(activos),
    }


def get_tipo_info(tipo_id: str) -> dict | None:
    """Devuelve info del tipo de instrumento por id."""
    for tipo in TIPOS_INSTRUMENTO:
        if tipo["id"] == tipo_id:
            return tipo
    return None
