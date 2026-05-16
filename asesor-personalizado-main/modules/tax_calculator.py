"""
Calculador de haircut (descuento) para proyecciones netas.

Aplica costos realistas del mercado argentino 2026:
- Comisiones de operación (escalonado por capital)
- Spread bid/ask (ponderado por composición de cartera)
- Impuestos vigentes 2026 (cedular suspendido, retenciones marginales)
- Bienes Personales (solo si capital > $384M ARS - target retail no aplica)

NOTA: las tablas de comisiones y el mínimo de Bienes Personales están
calibrados en ARS. El caller debe pasar `capital_inicial` en pesos.
"""

# ── Tabla de comisiones efectivas (Argentina 2026) ──
# Promedio del mercado: IOL, Cocos, Balanz, Bull Market, PPI
_COMISION_POR_CAPITAL = [
    (500_000,      0.010),   # < $500K: 1.0% (mínimo por op pesa más)
    (2_000_000,    0.007),   # $500K - $2M: 0.7%
    (10_000_000,   0.005),   # $2M - $10M: 0.5%
    (float("inf"), 0.004),   # > $10M: 0.4%
]

# ── Spread bid/ask por bucket de activo ──
_SPREAD_POR_CATEGORIA = {
    "money_market":  0.000,  # FCI / liquidez: se opera a valor cuota, sin spread
    "mep":           0.003,  # 0.3% en AL30 48hs
    "bonos_sob":     0.003,  # Bonos soberanos / CER
    "bonos_corp":    0.008,  # ONs corporativas
    "cedear_etf":    0.005,  # SPY, QQQ, GLD, VTI, EEM
    "cedear_accion": 0.010,  # CEDEARs de acciones líquidas
    "accion_arg":    0.012,  # Acciones argentinas
}

# ── Mapeo categoría real del ASSET_UNIVERSE → bucket de spread ──
# Las categorías del universo son limpias y distintas, así que el mapeo
# es directo por categoría (no por substring difuso).
_CATEGORY_TO_SPREAD_BUCKET = {
    "Pesos ARS":    "money_market",
    "Fondos ARS":   "money_market",   # FCI: valor cuota, sin spread bid/ask
    "Fondos USD":   "money_market",   # idem
    "Dólar MEP":    "mep",
    "Bonos CER":    "bonos_sob",
    "ETFs":         "cedear_etf",
    "CEDEARs":      "cedear_accion",
    "Acciones ARG": "accion_arg",
    # "Bonos USD" se resuelve aparte: depende del sub (Corporativo vs Soberano)
}

# ── Impuestos 2026 (estimados anuales sobre AUM) ──
# Régimen 2026: impuesto cedular suspendido para retail
_IMPUESTOS_2026 = {
    "dividendos_cedear":      0.001,  # 0.1% (estimado promedio)
    "intereses_ons":          0.0005, # 0.05% después de retención
    "bienes_personales_min":  384_000_000,  # Mínimo no imponible 2026 (ARS)
}

# ── Rebalanceos anuales (estimado) ──
_REBALANCEOS_POR_ANIO = 2


def _comision_segun_capital(capital: float) -> float:
    """Devuelve la comisión % efectiva según el capital (en ARS)."""
    for tope, comision in _COMISION_POR_CAPITAL:
        if capital < tope:
            return comision
    return _COMISION_POR_CAPITAL[-1][1]


def _categorizar_activo_para_spread(category: str, sub: str = "") -> str:
    """Mapea la categoría real del ASSET_UNIVERSE a un bucket de spread.

    Las 9 categorías del universo (Pesos ARS, Dólar MEP, Bonos USD/CER,
    CEDEARs, ETFs, Acciones ARG, Fondos ARS/USD) son distintas y limpias,
    así que el mapeo es directo. Único caso con ambigüedad: "Bonos USD",
    que puede ser corporativo (ON) o soberano según el sub.
    """
    if category == "Bonos USD":
        return "bonos_corp" if (sub or "").strip().lower() == "corporativo" else "bonos_sob"
    return _CATEGORY_TO_SPREAD_BUCKET.get(category, "cedear_etf")  # default conservador


def calcular_haircut_anual(
    portfolio: dict,
    capital_inicial: float,
    aporte_mensual: float = 0.0,
) -> dict:
    """
    Calcula el haircut anual estimado para una cartera específica.

    Args:
        portfolio: dict con key "positions" (lista de activos con weight,
                   category, sub).
        capital_inicial: capital en ARS (las tablas están calibradas en pesos).
        aporte_mensual: aporte mensual en ARS (0 si no aporta).

    Returns:
        dict con keys:
        - haircut_total: % anual a descontar del retorno bruto
        - desglose: dict con componentes (comisiones, spread, impuestos)
        - explicacion: texto para mostrar al usuario
    """
    # 1. Comisión de rebalanceos (2 al año del capital total)
    comision_pct = _comision_segun_capital(capital_inicial)
    costo_rebalanceo = comision_pct * _REBALANCEOS_POR_ANIO

    # 2. Comisión de aportes mensuales
    if aporte_mensual > 0:
        comision_aporte = _comision_segun_capital(aporte_mensual * 12)
        aum_promedio = capital_inicial + (aporte_mensual * 6)
        costo_aportes = (
            (aporte_mensual * 12 * comision_aporte) / aum_promedio
            if aum_promedio > 0 else 0.0
        )
    else:
        costo_aportes = 0.0

    # 3. Spread ponderado por composición
    spread_ponderado = 0.0
    positions = portfolio.get("positions", [])
    for pos in positions:
        cat = pos.get("category", "")
        sub = pos.get("sub", "")
        weight = pos.get("weight", 0)
        bucket = _categorizar_activo_para_spread(cat, sub)
        spread = _SPREAD_POR_CATEGORIA.get(bucket, 0.005)
        spread_ponderado += weight * spread
    # Spread se paga 2 veces al año (en rebalanceos)
    costo_spread = spread_ponderado * _REBALANCEOS_POR_ANIO

    # 4. Impuestos 2026 (marginales)
    costo_impuestos = (
        _IMPUESTOS_2026["dividendos_cedear"] + _IMPUESTOS_2026["intereses_ons"]
    )

    # Bienes Personales solo si capital supera mínimo
    bienes_personales = 0.0
    if capital_inicial > _IMPUESTOS_2026["bienes_personales_min"]:
        bienes_personales = 0.005  # 0.5% estimado promedio

    # Total
    haircut_total = (
        costo_rebalanceo + costo_aportes + costo_spread
        + costo_impuestos + bienes_personales
    )

    return {
        "haircut_total": haircut_total,
        "desglose": {
            "comisiones_rebalanceo": costo_rebalanceo,
            "comisiones_aportes":    costo_aportes,
            "spread":                costo_spread,
            "impuestos":             costo_impuestos,
            "bienes_personales":     bienes_personales,
        },
        "explicacion": _generar_explicacion(
            comision_pct, spread_ponderado, costo_impuestos,
            bienes_personales, capital_inicial,
        ),
    }


def _generar_explicacion(comision_pct, spread, impuestos, bp, capital):
    """Genera texto educativo para tooltip."""
    lineas = [
        f"Comisiones del broker: ~{comision_pct*100:.2f}% por operación (2 rebalanceos/año)",
        f"Spread bid/ask ponderado: ~{spread*100:.2f}% por operación",
        f"Impuestos 2026 (dividendos + retención ONs): ~{impuestos*100:.2f}% anual",
    ]
    if bp > 0:
        _min_m = _IMPUESTOS_2026["bienes_personales_min"] / 1e6
        lineas.append(f"Bienes Personales: ~{bp*100:.2f}% anual (capital >{_min_m:.0f}M)")
    else:
        lineas.append("Bienes Personales: exento (capital bajo el mínimo de $384M ARS)")
    lineas.append("Impuesto cedular sobre ganancias: suspendido en 2026")
    return "\n".join(lineas)


def aplicar_haircut(retorno_bruto: float, haircut: float) -> float:
    """Aplica el haircut al retorno bruto, devuelve neto."""
    return retorno_bruto - haircut
