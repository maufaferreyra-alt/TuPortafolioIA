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
    "monto_invertido_ars": 50000,  # cuánto PUSO en pesos (costo)
    "precio_compra_ars": None,     # opcional (modo unidades)
    "precio_actual_ars": 580,      # precio del día (modo unidades)
    "valor_actual_directo": None,  # FCIs: valor hoy sin cuotapartes
    "agregado_en": "2026-05-16T...",
}

Tres formas de cargar un activo:
1. Modo simple: solo monto_invertido. valor_actual = monto. Sin P&L.
2. Modo unidades (CEDEARs, acciones, bonos, ONs, letras, MEP):
   cantidad × precio. monto_invertido = cantidad × precio_actual;
   costo se reconstruye con precio_compra si está disponible.
3. Modo FCI: monto_invertido (lo que entregó) + valor_actual_directo
   opcional (lo que vale hoy, lo lee del broker). Sin cuotapartes.
"""

import uuid
from datetime import datetime


# ── Umbrales de sanity check de magnitud ───────────────────────────
# Soft warning: aviso amarillo, NO bloquea. Pensado para usuarios con
# mucha plata genuinamente.
# Hard block: bloquea el botón "Agregar". Pensado para typos.
# Ratio max: en modo unidades con compra, valor_actual no puede ser
# >10x el costo invertido (señal de error de coma en algún precio).
SOFT_WARNING_ARS      = 500_000_000     # $500M ARS por activo individual
HARD_BLOCK_ARS        = 5_000_000_000   # $5.000M ARS por activo individual
RATIO_VALOR_MONTO_MAX = 10              # valor_actual / costo_invertido


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
    valor_actual_directo: float | None = None,
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
        "valor_actual_directo": float(valor_actual_directo) if valor_actual_directo else None,
        "agregado_en": datetime.now().isoformat(),
    }


def calcular_valor_actual(activo: dict) -> float:
    """
    Calcula el valor actual de un activo.

    Casos:
    0. FCI con valor_actual_directo cargado: valor = valor_actual_directo
    1. Modo simple (precio_actual=None): valor = monto_invertido (sin P&L)
    2. Modo unidades sin compra: valor = monto_invertido = unidades × precio_actual
       (ya están multiplicados en monto_invertido al guardarse)
    3. Modo unidades con compra: valor = unidades × precio_actual = monto_invertido
       (el P&L se calcula aparte en calcular_pnl)
    """
    monto_invertido = activo.get("monto_invertido_ars", 0)

    # Caso 0: FCI cargó valor actual directo (sin cuotapartes)
    valor_directo = activo.get("valor_actual_directo")
    if valor_directo is not None and valor_directo > 0:
        return float(valor_directo)

    precio_actual = activo.get("precio_actual_ars")
    precio_compra = activo.get("precio_compra_ars")

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

    Modo FCI con valor_actual_directo: pnl = valor_directo - monto_invertido.
    Modo simple (precio_actual=None y sin valor_directo): pnl = None.
    Modo unidades sin compra: pnl = None.
    Modo unidades con compra: pnl = (precio_actual - precio_compra) × cantidad
    """
    valor_actual = calcular_valor_actual(activo)
    monto_invertido = activo.get("monto_invertido_ars", 0)
    precio_actual = activo.get("precio_actual_ars")
    precio_compra = activo.get("precio_compra_ars")
    valor_directo = activo.get("valor_actual_directo")

    # Caso FCI: P&L directo = valor_directo - monto_invertido
    if valor_directo is not None and valor_directo > 0 and monto_invertido > 0:
        pnl_ars = valor_directo - monto_invertido
        pnl_pct = (pnl_ars / monto_invertido) * 100
        return {
            "valor_actual": valor_actual,
            "monto_invertido": monto_invertido,
            "pnl_ars": pnl_ars,
            "pnl_pct": pnl_pct,
        }

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
        valor_directo = a.get("valor_actual_directo")
        monto = a.get("monto_invertido_ars", 0)

        # FCI con valor directo: costo = monto invertido (lo que puso)
        if valor_directo is not None and valor_directo > 0:
            total_invertido_costo += monto
        elif precio_actual is None or precio_compra is None or precio_compra <= 0:
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


# ═══════════════════════════════════════════════════════════════════
# FUNCIONES DE ANÁLISIS PARA COMPARACIÓN REAL VS SUGERIDA (Bloque 6C)
# ═══════════════════════════════════════════════════════════════════
#
# Lenguaje humano: estas funciones devuelven datos que después se
# muestran al usuario. NO usar términos técnicos en docstrings que
# después puedan filtrar a la UI.


# Mapeo tipo_id → nombre human-friendly para mostrar
NOMBRES_CATEGORIA = {
    "accion_arg": "Acciones argentinas",
    "cedear":     "CEDEARs (acciones del exterior)",
    "bono":       "Bonos del gobierno",
    "on":         "ONs (deuda de empresas)",
    "letra":      "Letras del Tesoro",
    "fci":        "Fondos comunes",
    "mep":        "Dólar MEP",
}


# Rentabilidad anual REAL estimada por categoría (después de
# inflación). Tasas conservadoras para no inflar expectativas.
# Estos números son la base — si en el futuro tenemos scores
# específicos por ticker (finviz_scores.json, bond_scores.json),
# podemos reemplazar la categoría por el promedio ponderado real.
RENTABILIDAD_ANUAL_REAL_POR_CATEGORIA = {
    "accion_arg": 0.08,  # 8% real anual (acciones ARG históricamente)
    "cedear":     0.10,  # 10% real anual (S&P 500 histórico USD)
    "bono":       0.06,  # 6% real anual (soberanos ARG estable)
    "on":         0.08,  # 8% real anual (ONs corporativas)
    "letra":      0.04,  # 4% real anual (LECAPs corto plazo)
    "fci":        0.03,  # 3% real anual (Money Market en términos reales)
    "mep":        0.00,  # 0% (cobertura de devaluación, no rinde)
}


# Mapeo categoría → nivel de riesgo (bajo / medio / alto)
RIESGO_POR_CATEGORIA = {
    "accion_arg": "alto",
    "cedear":     "medio",
    "bono":       "medio",
    "on":         "medio",
    "letra":      "bajo",
    "fci":        "bajo",
    "mep":        "bajo",
}


def get_alocacion_por_categoria(activos: list) -> dict:
    """
    Devuelve dict {categoria: porcentaje} para una lista de activos.
    El porcentaje es sobre el valor ACTUAL total (no el invertido).
    """
    if not activos:
        return {}

    total_valor = sum(calcular_valor_actual(a) or 0 for a in activos)
    if total_valor <= 0:
        return {}

    allocation = {}
    for a in activos:
        tipo = a.get("tipo")
        if not tipo:
            continue
        valor = calcular_valor_actual(a) or 0
        if valor <= 0:
            continue
        peso_pct = (valor / total_valor) * 100
        allocation[tipo] = allocation.get(tipo, 0) + peso_pct

    return allocation


def get_rentabilidad_anual_estimada(activos: list) -> float:
    """
    Estimación de rentabilidad real anual (después de inflación) para
    una cartera, ponderando las tasas de cada categoría por su peso.
    Devuelve porcentaje (ej. 7.3 para 7.3%).
    """
    allocation = get_alocacion_por_categoria(activos)
    if not allocation:
        return 0.0

    suma_ponderada = 0.0
    for tipo, peso_pct in allocation.items():
        tasa = RENTABILIDAD_ANUAL_REAL_POR_CATEGORIA.get(tipo, 0.0)
        suma_ponderada += (peso_pct / 100) * tasa * 100

    return suma_ponderada


def get_nivel_riesgo_cartera(activos: list) -> str:
    """
    Devuelve 'bajo' / 'medio' / 'alto' según la categoría dominante.
    Heurística simple: si más del 60% está en categorías de "alto"
    riesgo, la cartera es "alto". Si más del 60% en "bajo", "bajo".
    Resto: "medio".
    """
    allocation = get_alocacion_por_categoria(activos)
    if not allocation:
        return "bajo"

    peso_alto = sum(p for t, p in allocation.items() if RIESGO_POR_CATEGORIA.get(t) == "alto")
    peso_bajo = sum(p for t, p in allocation.items() if RIESGO_POR_CATEGORIA.get(t) == "bajo")

    if peso_alto > 60:
        return "alto"
    if peso_bajo > 60:
        return "bajo"
    return "medio"


def detectar_gaps_simples(allocation_real: dict, allocation_sugerida: dict) -> list:
    """
    Compara las dos allocations y devuelve una lista de gaps (max 3),
    cada uno con título corto + explicación humana.

    Retorna lista de dicts: {'icon': str, 'titulo': str, 'explicacion': str}
    """
    gaps = []

    # Gap 1: concentración en una sola categoría (real > 60%)
    for tipo, peso in allocation_real.items():
        if peso > 60:
            gaps.append({
                "icon": "🎯",
                "titulo": f"Estás muy concentrado en {NOMBRES_CATEGORIA.get(tipo, tipo)}",
                "explicacion": (
                    f"Tenés el {peso:.0f}% de tu plata en una sola categoría. "
                    "Si a ese sector le va mal, te impacta de lleno. La idea de "
                    "diversificar es tener huevos en distintas canastas."
                ),
            })
            break  # Solo el más concentrado

    # Gap 2: categoría sugerida importante que el usuario no tiene
    for tipo, peso_sug in allocation_sugerida.items():
        peso_real = allocation_real.get(tipo, 0)
        if peso_sug >= 15 and peso_real < 5:
            nombre = NOMBRES_CATEGORIA.get(tipo, tipo)
            explicacion_extra = ""
            if tipo == "cedear":
                explicacion_extra = " Te protege si el peso pierde valor."
            elif tipo == "fci":
                explicacion_extra = " Sirve como reserva para emergencias o aprovechar oportunidades."
            elif tipo == "bono":
                explicacion_extra = " Te dan estabilidad y un ingreso predecible."
            gaps.append({
                "icon": "🎯",
                "titulo": f"Te falta {nombre.lower()}",
                "explicacion": (
                    f"La sugerida tiene un {peso_sug:.0f}% acá y vos tenés "
                    f"un {peso_real:.0f}%.{explicacion_extra}"
                ),
            })
            if len(gaps) >= 3:
                break

    # Gap 3 (si todavía hay espacio): exceso en una categoría
    for tipo, peso_real in allocation_real.items():
        if len(gaps) >= 3:
            break
        peso_sug = allocation_sugerida.get(tipo, 0)
        if peso_real > peso_sug + 20:  # 20% por encima de lo sugerido
            nombre = NOMBRES_CATEGORIA.get(tipo, tipo)
            # Solo si NO es el gap de concentración (evitar repetir)
            if not any(g["titulo"].endswith(f"en {NOMBRES_CATEGORIA.get(tipo, tipo)}") for g in gaps):
                gaps.append({
                    "icon": "🎯",
                    "titulo": f"Tenés más {nombre.lower()} de lo recomendado",
                    "explicacion": (
                        f"Vos: {peso_real:.0f}%. Sugerido: {peso_sug:.0f}%. "
                        "Reducir un poco y diversificar a otras categorías baja el riesgo."
                    ),
                })

    return gaps[:3]
