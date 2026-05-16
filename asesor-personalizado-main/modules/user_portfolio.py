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
    precio_actual_ars: float | None = None,
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
        "precio_actual_ars": float(precio_actual_ars) if precio_actual_ars else None,
        "agregado_en": datetime.now().isoformat(),
    }


def calcular_valor_actual(activo: dict) -> float:
    """
    Calcula el valor actual de un activo.

    Casos:
    1. Modo simple (precio_actual=None): valor = monto_invertido (sin P&L)
    2. Modo unidades sin compra: valor = monto_invertido = unidades × precio_actual
       (ya están multiplicados en monto_invertido al guardarse)
    3. Modo unidades con compra: valor = unidades × precio_actual = monto_invertido
       (el P&L se calcula aparte en calcular_pnl)
    """
    precio_actual = activo.get("precio_actual_ars")
    precio_compra = activo.get("precio_compra_ars")
    monto_invertido = activo.get("monto_invertido_ars", 0)

    # Caso 1: modo simple, no se puede calcular valor distinto
    if precio_actual is None:
        return monto_invertido

    # Caso 2: modo unidades sin compra — monto_invertido ya es el valor actual
    if precio_compra is None or precio_compra <= 0:
        return monto_invertido

    # Caso 3: modo unidades con precio de compra.
    # monto_invertido al guardarse en modo unidades YA ES el valor actual
    # (cantidad × precio_actual). El P&L se calcula en calcular_pnl().
    return monto_invertido


def calcular_pnl(activo: dict) -> dict:
    """
    Calcula ganancia/pérdida del activo.

    Modo simple (precio_actual=None): pnl es None (no se puede calcular).
    Modo unidades sin compra: pnl es None.
    Modo unidades con compra: pnl = (precio_actual - precio_compra) × cantidad
    """
    valor_actual = calcular_valor_actual(activo)
    monto_invertido = activo.get("monto_invertido_ars", 0)
    precio_actual = activo.get("precio_actual_ars")
    precio_compra = activo.get("precio_compra_ars")

    # Sin precio_actual (modo simple) → no se calcula P&L
    if precio_actual is None:
        return {
            "valor_actual": valor_actual,
            "monto_invertido": monto_invertido,
            "pnl_ars": None,
            "pnl_pct": None,
        }

    # Sin precio_compra → no se calcula P&L
    if precio_compra is None or precio_compra <= 0:
        return {
            "valor_actual": valor_actual,
            "monto_invertido": monto_invertido,
            "pnl_ars": None,
            "pnl_pct": None,
        }

    # Con ambos precios: calcular P&L real
    cantidad_estimada = monto_invertido / precio_actual
    costo_total = cantidad_estimada * precio_compra
    pnl_ars = monto_invertido - costo_total
    pnl_pct = (pnl_ars / costo_total * 100) if costo_total > 0 else 0

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

    valor_total_actual = 0
    total_invertido_costo = 0  # lo que realmente PUSO el usuario

    for a in activos:
        valor_actual = calcular_valor_actual(a)
        valor_total_actual += valor_actual

        precio_actual = a.get("precio_actual_ars")
        precio_compra = a.get("precio_compra_ars")
        monto = a.get("monto_invertido_ars", 0)

        if precio_actual is None or precio_compra is None or precio_compra <= 0:
            # No hay precio compra: el "invertido" es el monto que puso
            total_invertido_costo += monto
        else:
            # Con precio compra: el costo real es cantidad × precio_compra
            cantidad = monto / precio_actual
            total_invertido_costo += cantidad * precio_compra

    pnl_total_ars = valor_total_actual - total_invertido_costo
    pnl_total_pct = (pnl_total_ars / total_invertido_costo * 100) if total_invertido_costo > 0 else 0

    return {
        "valor_total_actual": valor_total_actual,
        "total_invertido": total_invertido_costo,
        "pnl_total_ars": pnl_total_ars,
        "pnl_total_pct": pnl_total_pct,
        "cantidad_activos": len(activos),
    }


def costo_invertido(activo: dict) -> float:
    """
    Devuelve lo que el usuario REALMENTE puso en este activo.

    En modo unidades con compra, monto_invertido_ars guarda el valor
    actual (cantidad × precio_actual), no el costo. El costo real es
    cantidad × precio_compra.
    """
    precio_actual = activo.get("precio_actual_ars")
    precio_compra = activo.get("precio_compra_ars")
    monto = activo.get("monto_invertido_ars", 0)

    if precio_actual is None or precio_compra is None or precio_compra <= 0:
        return monto

    cantidad = monto / precio_actual
    return cantidad * precio_compra


def get_tipo_info(tipo_id: str) -> dict | None:
    """Devuelve info del tipo de instrumento por id."""
    for tipo in TIPOS_INSTRUMENTO:
        if tipo["id"] == tipo_id:
            return tipo
    return None
