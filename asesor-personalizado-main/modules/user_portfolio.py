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
        "descripcion": "Acciones de empresas extranjeras desde Argentina (AAPL, MSFT, etc.)",
        "icono": "🌎",
    },
    {
        # Los ETFs se compran como CEDEARs en Argentina, pero los
        # listamos aparte: agrupan muchas empresas/activos en una sola
        # compra y en la cartera sugerida figuran como "Fondos globales".
        # Tenerlos separados evita la incoherencia de cargarlos como
        # CEDEAR y verlos después clasificados como fondo.
        "id": "etf",
        "label": "ETFs (fondos del exterior)",
        "descripcion": "Fondos que reúnen muchas empresas o activos en una sola compra (SPY, QQQ, etc.)",
        "icono": "🌐",
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


# Tipos cuyo precio se sigue EN VIVO (tienen cotización en la API del 6B).
# El resto (bonos, ONs, FCIs, letras) se cargan/editan a mano.
TIPOS_VIVO = {"accion_arg", "cedear", "etf", "mep"}


def crear_activo(
    tipo: str,
    ticker: str,
    nombre: str,
    monto_invertido_ars: float,
    modo: str = "manual",
    precio_compra_ars: float | None = None,
    precio_actual_ars: float | None = None,
    valor_actual_directo: float | None = None,
) -> dict:
    """
    Crea el dict de un activo nuevo para agregar al portafolio.

    modo="vivo" (acciones / CEDEARs / MEP):
        monto_invertido_ars  = lo que el usuario PUSO (costo total).
        precio_compra_ars    = precio unitario al que compró.
        Las unidades se derivan (monto / precio_compra) y el valor de
        hoy se calcula con precio_actual_ars (refrescado desde la API).
    modo="manual" (bonos / ONs / FCIs / letras):
        monto_invertido_ars  = lo que puso.
        valor_actual_directo = lo que vale hoy (cargado a mano, editable).

    En CUALQUIER modo, monto_invertido_ars representa el costo — lo que
    el usuario realmente puso.
    """
    return {
        "id": str(uuid.uuid4())[:8],
        "tipo": tipo,
        "ticker": ticker,
        "nombre": nombre,
        "modo": modo,
        "monto_invertido_ars": float(monto_invertido_ars),
        "precio_compra_ars": float(precio_compra_ars) if precio_compra_ars else None,
        "precio_actual_ars": float(precio_actual_ars) if precio_actual_ars else None,
        "valor_actual_directo": float(valor_actual_directo) if valor_actual_directo else None,
        "agregado_en": datetime.now().isoformat(),
    }


def cantidad_unidades(activo: dict) -> float:
    """
    Unidades que tiene el usuario en un activo modo 'vivo':
    costo total / precio de compra unitario.
    Devuelve 0 si no es modo vivo o falta el precio de compra.
    """
    if activo.get("modo") != "vivo":
        return 0.0
    monto = activo.get("monto_invertido_ars", 0) or 0
    precio_compra = activo.get("precio_compra_ars")
    if precio_compra and precio_compra > 0:
        return monto / precio_compra
    return 0.0


def calcular_valor_actual(activo: dict) -> float:
    """
    Valor de HOY del activo en ARS.

    modo 'vivo':   unidades × precio actual de mercado. Si todavía no
                   hay precio actual (la API no respondió), vale lo que
                   se puso.
    modo 'manual': el valor cargado a mano; si no se cargó, lo que se
                   puso.
    Activos viejos sin campo 'modo' caen al camino manual (compatibles).
    """
    monto = activo.get("monto_invertido_ars", 0) or 0

    if activo.get("modo") == "vivo":
        precio_compra = activo.get("precio_compra_ars")
        precio_actual = activo.get("precio_actual_ars")
        if precio_compra and precio_compra > 0 and precio_actual and precio_actual > 0:
            unidades = monto / precio_compra
            return unidades * precio_actual
        return monto

    valor_directo = activo.get("valor_actual_directo")
    if valor_directo is not None and valor_directo > 0:
        return float(valor_directo)
    return monto


def calcular_pnl(activo: dict) -> dict:
    """
    Ganancia/pérdida del activo.

    modo 'vivo':   valor de hoy − costo (requiere precio actual cargado).
    modo 'manual': valor cargado a mano − costo (si se cargó el valor).
    pnl_ars / pnl_pct vienen en None cuando no se puede calcular.
    """
    valor_actual = calcular_valor_actual(activo)
    monto = activo.get("monto_invertido_ars", 0) or 0
    sin_pnl = {
        "valor_actual": valor_actual,
        "monto_invertido": monto,
        "pnl_ars": None,
        "pnl_pct": None,
    }

    if activo.get("modo") == "vivo":
        precio_compra = activo.get("precio_compra_ars")
        precio_actual = activo.get("precio_actual_ars")
        if monto > 0 and precio_compra and precio_compra > 0 and precio_actual and precio_actual > 0:
            pnl_ars = valor_actual - monto
            return {
                "valor_actual": valor_actual,
                "monto_invertido": monto,
                "pnl_ars": pnl_ars,
                "pnl_pct": (pnl_ars / monto) * 100,
            }
        return sin_pnl

    valor_directo = activo.get("valor_actual_directo")
    if valor_directo is not None and valor_directo > 0 and monto > 0:
        pnl_ars = float(valor_directo) - monto
        return {
            "valor_actual": valor_actual,
            "monto_invertido": monto,
            "pnl_ars": pnl_ars,
            "pnl_pct": (pnl_ars / monto) * 100,
        }
    return sin_pnl


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
        valor_total_actual += calcular_valor_actual(a)
        # monto_invertido_ars siempre es el costo en el modelo actual.
        total_invertido_costo += costo_invertido(a)

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
    Lo que el usuario REALMENTE puso en este activo.

    En el modelo actual, monto_invertido_ars siempre es el costo —
    tanto en modo 'vivo' como en 'manual'.
    """
    return activo.get("monto_invertido_ars", 0) or 0


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
# Descripciones educativas breves por categoría
# Una frase clara por categoría, sin jerga financiera, para mostrar
# debajo del título de la categoría en las cards del portafolio.
DESCRIPCIONES_CATEGORIA = {
    "accion_arg": "Empresas argentinas que cotizan en la bolsa local",
    "cedear":     "Acciones de empresas extranjeras compradas en pesos",
    "etf":        "Fondos que reúnen muchas empresas o activos del exterior en una sola compra",
    "bono":       "Préstamos al gobierno que pagan interés en plazos fijos",
    "on":         "Préstamos a empresas privadas con interés fijo",
    "letra":      "Bonos cortos del Tesoro, menores a un año",
    "fci":        "Fondos administrados por profesionales — entrada y salida flexibles",
    "mep":        "Dólares legales comprados a través de la bolsa",
    "cash":       "Plata disponible sin invertir",
}

NOMBRES_CATEGORIA = {
    "accion_arg": "Acciones argentinas",
    "cedear":     "CEDEARs (acciones del exterior)",
    "etf":        "ETFs (fondos del exterior)",
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
    "etf":        0.08,  # 8% real anual (índices diversificados, conservador)
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
    "etf":        "medio",
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


# Puntaje numérico de riesgo por categoría (1 = bajo, 3 = alto).
_RIESGO_SCORE = {"bajo": 1.0, "medio": 2.0, "alto": 3.0}


def get_nivel_riesgo_cartera(activos: list) -> str:
    """
    Devuelve 'bajo' / 'medio' / 'alto'.

    Combina DOS cosas (la versión vieja solo miraba la categoría
    dominante, así que una cartera 100% en algo y otra diversificada
    podían dar el mismo nivel — incorrecto):

    1. Riesgo propio de las categorías, ponderado por cuánta plata hay
       en cada una (las acciones pesan más que un plazo fijo).
    2. Concentración: estar metido en pocas canastas es más riesgoso
       que repartir. Se mide con el índice HHI (Herfindahl: suma de
       los pesos al cuadrado) — 1.0 = todo en una categoría, ~0.2 =
       bien repartido. A más concentración, el riesgo se multiplica.

    Así una cartera concentrada nunca puede leerse igual que la misma
    plata diversificada.
    """
    allocation = get_alocacion_por_categoria(activos)
    if not allocation:
        return "bajo"

    # 1. Riesgo base ponderado (rango 1.0 a 3.0).
    score_base = sum(
        (peso / 100) * _RIESGO_SCORE.get(
            RIESGO_POR_CATEGORIA.get(tipo, "medio"), 2.0
        )
        for tipo, peso in allocation.items()
    )

    # 2. Factor de concentración vía HHI.
    hhi = sum((peso / 100) ** 2 for peso in allocation.values())
    if hhi >= 0.60:      # muy concentrada (1-2 categorías dominan todo)
        factor = 1.4
    elif hhi >= 0.35:    # algo concentrada
        factor = 1.2
    else:                # bien diversificada
        factor = 1.0

    score = score_base * factor

    if score >= 2.5:
        return "alto"
    if score >= 1.6:
        return "medio"
    return "bajo"


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
                "categoria": tipo,
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
            # NOTA: la comparación pasa las allocations ya unificadas a
            # las 5 categorías de Resultados, así que acá 'tipo' es el
            # nombre de categoría (Liquidez, Renta fija, etc.).
            explicacion_extra = ""
            if tipo == "Cobertura cambiaria":
                explicacion_extra = " Te protege si el peso pierde valor."
            elif tipo == "Liquidez":
                explicacion_extra = " Sirve como reserva para emergencias o para aprovechar oportunidades."
            elif tipo == "Renta fija":
                explicacion_extra = " Te da estabilidad y un ingreso más predecible."
            elif tipo == "Fondos globales":
                explicacion_extra = " Te da acceso a las empresas más grandes del mundo."
            gaps.append({
                "icon": "🧩",
                "categoria": tipo,
                "titulo": f"Te falta {nombre}",
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
                    "icon": "⚖️",
                    "categoria": tipo,
                    "titulo": f"Tenés más {nombre} de lo recomendado",
                    "explicacion": (
                        f"Vos: {peso_real:.0f}%. Sugerido: {peso_sug:.0f}%. "
                        "Reducir un poco y diversificar a otras categorías baja el riesgo."
                    ),
                })

    return gaps[:3]


def agrupar_activos_por_categoria(activos: list) -> list:
    """
    Agrupa los activos por su categoría (tipo) y ordena por valor
    total descendente.

    Returns: lista de dicts con la forma:
        [
            {
                "tipo": "accion_arg",
                "activos": [activo1, activo2, ...],
                "valor_total": 250000.0,
                "invertido_total": 200000.0,
                "porcentaje_cartera": 12.5,
                "cantidad": 2,
            },
            ...
        ]
    Ordenado por valor_total descendente (categoría más grande primero).
    """
    if not activos:
        return []

    # Valor total de toda la cartera (para calcular % por categoría)
    valor_cartera_total = sum(calcular_valor_actual(a) or 0 for a in activos)
    if valor_cartera_total <= 0:
        valor_cartera_total = 1  # Evitar div by zero

    grupos = {}
    for activo in activos:
        tipo = activo.get("tipo")
        if not tipo:
            continue
        if tipo not in grupos:
            grupos[tipo] = {
                "tipo": tipo,
                "activos": [],
                "valor_total": 0,
                "invertido_total": 0,
                "porcentaje_cartera": 0,
                "cantidad": 0,
            }
        valor = calcular_valor_actual(activo) or 0
        invertido = costo_invertido(activo) or 0
        grupos[tipo]["activos"].append(activo)
        grupos[tipo]["valor_total"] += valor
        grupos[tipo]["invertido_total"] += invertido
        grupos[tipo]["cantidad"] += 1

    # Calcular % de cartera y ordenar
    for grupo in grupos.values():
        grupo["porcentaje_cartera"] = (grupo["valor_total"] / valor_cartera_total) * 100

    return sorted(
        grupos.values(),
        key=lambda g: g["valor_total"],
        reverse=True,
    )
