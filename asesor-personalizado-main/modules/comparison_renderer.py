"""
Renderer de la pantalla de comparación: cartera real vs sugerida.
Bloque 6C — Feature core del pitch.
"""

import streamlit as st
import plotly.graph_objects as go

from .user_portfolio import (
    get_alocacion_por_categoria,
    get_rentabilidad_anual_estimada,
    get_nivel_riesgo_cartera,
    detectar_gaps_simples,
    total_portafolio,
    NOMBRES_CATEGORIA,
)


# Paleta de colores para los donuts (consistente con dark theme)
COLORES_CATEGORIA = {
    "accion_arg": "#60a5fa",   # azul accent
    "cedear":     "#a78bfa",   # violeta
    "bono":       "#34d399",   # verde
    "on":         "#fbbf24",   # amarillo
    "letra":      "#f472b6",   # rosa
    "fci":        "#22d3ee",   # cyan
    "mep":        "#fb923c",   # naranja
}


# Mapeo de la "category" del portfolio sugerido (build_portfolio) a los
# tipo_id que usa user_portfolio (NOMBRES_CATEGORIA / RENTABILIDAD / etc).
# build_portfolio() devuelve {"positions": [{weight, category, ...}]} con
# categories como "Acciones ARG", "CEDEARs", "Bonos USD". No hay buckets
# separados para ONs ni letras: caen en "bono", y el cash ("Pesos ARS")
# se asimila a fondo money market ("fci").
_CATEGORIA_SUGERIDA_A_TIPO = {
    "Acciones ARG":   "accion_arg",
    "CEDEARs":        "cedear",
    "ETFs":           "cedear",
    "ETFs Globales":  "cedear",
    "Bonos USD":      "bono",
    "Bonos CER":      "bono",
    "Dólar MEP":      "mep",
    "Fondos ARS":     "fci",
    "Fondos USD":     "fci",
    "Pesos ARS":      "fci",
}


# Resultados y Comparación mostraban la MISMA cartera sugerida con
# categorías distintas (Resultados: Liquidez/Cobertura/Renta fija/...;
# Comparación: CEDEARs/ONs/Bonos/...). Eso confunde. La comparación
# ahora re-agrupa todo a las 5 categorías de la pantalla de Resultados.
# Mapeo tipo_id (cartera del usuario) -> categoría unificada.
_TIPO_A_CAT_UNIF = {
    "accion_arg": "Renta variable",
    "cedear":     "Renta variable",
    "bono":       "Renta fija",
    "on":         "Renta fija",
    "letra":      "Renta fija",
    "fci":        "Liquidez",
    "mep":        "Cobertura cambiaria",
}

# Colores de las 5 categorías unificadas (los mismos de la pantalla de
# Resultados — charts._CATEGORY_META).
_COLOR_CAT_UNIF = {
    "Liquidez":            "#60a5fa",
    "Cobertura cambiaria": "#f59e0b",
    "Renta fija":          "#22c55e",
    "Fondos globales":     "#4fa3ff",
    "Renta variable":      "#a78bfa",
}


def _unificar(allocation_tipo: dict) -> dict:
    """Re-agrupa una allocation {tipo: %} a {categoría unificada: %}."""
    salida = {}
    for tipo, peso in allocation_tipo.items():
        cat = _TIPO_A_CAT_UNIF.get(tipo, "Renta variable")
        salida[cat] = salida.get(cat, 0) + peso
    return salida


# CEDEARs que en realidad son ETFs (fondos globales), no acciones
# sueltas. Sin esto, un usuario que carga SPY como CEDEAR caía en
# "Renta variable" y la comparación le decía "te falta Fondos
# globales" cuando en realidad lo tiene.
_ETF_TICKERS = {
    "SPY", "VOO", "QQQ", "EEM", "EWZ", "GLD", "IAU", "SLV",
    "XLE", "XLF", "XLK", "ARKK", "DIA", "IWM",
}


def _categoria_unif_activo(activo: dict) -> str:
    """
    Categoría unificada (las 5 de Resultados) de UN activo del usuario.
    Mira tipo + ticker: los CEDEARs de ETFs van a 'Fondos globales',
    los CEDEARs de empresas a 'Renta variable'.
    """
    tipo = activo.get("tipo")
    ticker = (activo.get("ticker") or "").upper().strip()
    if tipo == "cedear" and ticker in _ETF_TICKERS:
        return "Fondos globales"
    return _TIPO_A_CAT_UNIF.get(tipo, "Renta variable")


def _alloc_unif_usuario(activos: list) -> dict:
    """Allocation {categoría unificada: %} de la cartera del usuario,
    decidiendo la categoría activo por activo (ticker + tipo)."""
    from .user_portfolio import calcular_valor_actual
    total = sum((calcular_valor_actual(a) or 0) for a in activos)
    if total <= 0:
        return {}
    out = {}
    for a in activos:
        valor = calcular_valor_actual(a) or 0
        if valor <= 0:
            continue
        cat = _categoria_unif_activo(a)
        out[cat] = out.get(cat, 0) + (valor / total) * 100
    return out


def _emoji_rentabilidad(pct: float) -> str:
    """
    Emoji honesto según nivel de rentabilidad REAL estimada
    (después de inflación). Thresholds calibrados con referencia
    al S&P 500 histórico (~7% real anual) como benchmark de
    "rendimiento bueno".
    """
    if pct >= 7:   return "🚀"   # alta, mejor que S&P histórico
    if pct >= 4:   return "✓"    # buena
    if pct >= 2:   return "⚠️"   # ojo, conviene revisar
    return "📉"                  # baja, casi como banco


def _emoji_riesgo(nivel: str) -> str:
    if nivel == "bajo":  return "✓"
    if nivel == "medio": return "≈"
    return "⚠️"


def _construir_donut(allocation: dict, titulo: str):
    """Construye un donut chart de Plotly a partir del dict allocation."""
    if not allocation:
        return None
    labels = list(allocation.keys())
    values = list(allocation.values())
    colors = [_COLOR_CAT_UNIF.get(c, "#888") for c in allocation.keys()]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.55,
        marker=dict(colors=colors, line=dict(color="#0e1117", width=2)),
        texttemplate="%{percent:.0%}",
        textposition="inside",
        textfont=dict(size=13, color="#ffffff"),
        hovertemplate="<b>%{label}</b><br>%{percent}<extra></extra>",
    )])
    fig.update_layout(
        # Sin leyenda propia: hay una leyenda única compartida abajo de
        # los dos donuts (evita repetir las categorías dos veces).
        showlegend=False,
        margin=dict(t=10, b=10, l=10, r=10),
        height=210,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def _leyenda_compartida(allocation_real: dict, allocation_sugerida: dict) -> str:
    """
    HTML de una leyenda única para los dos donuts: un color + nombre
    por cada categoría presente en cualquiera de las dos carteras.
    """
    tipos = list(dict.fromkeys(
        list(allocation_real.keys()) + list(allocation_sugerida.keys())
    ))
    items = ""
    for t in tipos:
        color = _COLOR_CAT_UNIF.get(t, "#888")
        nombre = t
        items += (
            f'<span style="display:inline-flex; align-items:center; '
            f'gap:0.4rem; margin:0.25rem 0.7rem;">'
            f'<span style="width:0.7rem; height:0.7rem; border-radius:3px; '
            f'background:{color}; display:inline-block; flex-shrink:0;"></span>'
            f'<span style="font-size:0.8rem; color:rgba(255,255,255,0.7);">'
            f'{nombre}</span>'
            f'</span>'
        )
    return (
        '<div style="display:flex; flex-wrap:wrap; justify-content:center; '
        'margin:0.25rem 0 0.75rem 0;">' + items + '</div>'
    )


def _metrica_comparada(label: str, val_tuya: str, val_sug: str, sublabel: str) -> str:
    """HTML de una métrica en formato comparativo: tu cartera vs sugerida."""
    return (
        f'<div style="flex:1; min-width:220px;">'
        f'<div style="font-size:0.8rem; color:rgba(255,255,255,0.55); '
        f'margin-bottom:0.4rem;">{label}</div>'
        f'<div style="display:flex; gap:1.1rem; align-items:baseline;">'
        f'<div><div style="font-size:1.35rem; font-weight:700; color:#ffffff;">'
        f'{val_tuya}</div>'
        f'<div style="font-size:0.7rem; color:rgba(255,255,255,0.4);">tu cartera</div></div>'
        f'<div style="color:rgba(255,255,255,0.3); font-size:0.9rem;">vs</div>'
        f'<div><div style="font-size:1.35rem; font-weight:700; '
        f'color:rgba(255,255,255,0.7);">{val_sug}</div>'
        f'<div style="font-size:0.7rem; color:rgba(255,255,255,0.4);">sugerida</div></div>'
        f'</div>'
        f'<div style="font-size:0.7rem; color:rgba(255,255,255,0.35); '
        f'margin-top:0.4rem;">{sublabel}</div>'
        f'</div>'
    )


def render_comparison_page():
    """Punto de entrada de la pantalla de comparación (step='comparison')."""

    # ── Header empático ──────────────────────────────────────────
    st.markdown(
        '<div style="font-size: 1.75rem; font-weight: 700; color: #ffffff; '
        'margin-bottom: 0.5rem; letter-spacing: -0.01em;">'
        '🔍 Tu cartera vs la que te sugerimos'
        '</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Acá podés ver lado a lado lo que tenés hoy y lo que el modelo "
        "te recomienda según tu perfil. Tomalo como un mapa, no como una "
        "orden — vos decidís qué hacer."
    )

    # ── Datos ────────────────────────────────────────────────────
    activos_real = st.session_state.get("user_portfolio_activos", [])
    cartera_sugerida = st.session_state.get("portfolio", {})

    if not activos_real:
        st.warning(
            "Todavía no cargaste activos en tu cartera. "
            "Volvé al paso anterior y cargá al menos uno para ver la comparación."
        )
        if st.button("← Volver a cargar mi cartera", type="primary"):
            st.session_state["step"] = "user_portfolio"
            st.rerun()
        return

    allocation_real = get_alocacion_por_categoria(activos_real)

    # La cartera sugerida (build_portfolio) tiene estructura
    # {"positions": [{weight: 0.x, category: "Acciones ARG", ...}], ...}.
    # Construimos allocation_sugerida agregando weight por categoría y
    # mapeando la category a los tipo_id de user_portfolio.
    allocation_sugerida = {}
    positions_sug = []
    if isinstance(cartera_sugerida, dict):
        positions_sug = cartera_sugerida.get("positions", []) or []
    for pos in positions_sug:
        if not isinstance(pos, dict):
            continue
        categoria = pos.get("category", "")
        tipo = _CATEGORIA_SUGERIDA_A_TIPO.get(categoria)
        if tipo is None:
            continue
        try:
            # weight viene como fracción 0-1 → lo pasamos a porcentaje
            peso_num = float(pos.get("weight", 0)) * 100
        except (ValueError, TypeError):
            continue
        if peso_num <= 0:
            continue
        allocation_sugerida[tipo] = allocation_sugerida.get(tipo, 0) + peso_num

    # Si por algún motivo no hay sugerida, fallback educativo
    if not allocation_sugerida:
        st.info(
            "No encontramos tu cartera sugerida en esta sesión. "
            "Probá completar el test de perfil primero y después volver acá."
        )
        if st.button("← Volver al test", type="primary"):
            st.session_state["step"] = "questions"
            st.rerun()
        return

    rent_real = get_rentabilidad_anual_estimada(activos_real)
    riesgo_real = get_nivel_riesgo_cartera(activos_real)

    # La rentabilidad de la sugerida la calculamos con la misma función
    # construyendo una lista de "activos sintéticos" desde allocation_sugerida.
    activos_sugerida_sinteticos = [
        {
            "tipo": tipo,
            "monto_invertido_ars": peso * 1000,  # base normalizada
            "precio_actual_ars": None,
            "precio_compra_ars": None,
        }
        for tipo, peso in allocation_sugerida.items()
    ]
    rent_sugerida = get_rentabilidad_anual_estimada(activos_sugerida_sinteticos)
    riesgo_sugerido = get_nivel_riesgo_cartera(activos_sugerida_sinteticos)

    # ── Allocations para el DISPLAY, unificadas a las 5 categorías de
    # la pantalla de Resultados (donuts + leyenda + gaps coinciden).
    # La sugerida se re-agrupa con la MISMA función que Resultados
    # (_asset_to_user_category) para que matchee 1:1. La rentabilidad y
    # el riesgo de arriba no se tocan — siguen sobre el sistema de tipos.
    from .charts import _asset_to_user_category
    alloc_real_disp = _alloc_unif_usuario(activos_real)
    alloc_sug_disp = {}
    for pos in positions_sug:
        if not isinstance(pos, dict):
            continue
        cat = _asset_to_user_category(pos)
        try:
            peso = float(pos.get("weight", 0)) * 100
        except (ValueError, TypeError):
            continue
        if peso > 0:
            alloc_sug_disp[cat] = alloc_sug_disp.get(cat, 0) + peso

    # Diferencia anual en $ (la línea VENDEDORA)
    totales_real = total_portafolio(activos_real)
    valor_real = totales_real["valor_total_actual"]
    diferencia_pct_anual = rent_sugerida - rent_real
    diferencia_ars_anual = valor_real * (diferencia_pct_anual / 100)

    # ── 2 COLUMNAS LADO A LADO ───────────────────────────────────
    col_real, col_sug = st.columns(2)

    with col_real:
        st.markdown(
            '<div style="font-size: 1.1rem; font-weight: 600; color: #ffffff; '
            'margin-bottom: 0.5rem;">📂 Tu cartera</div>',
            unsafe_allow_html=True,
        )
        fig_real = _construir_donut(alloc_real_disp, "Real")
        if fig_real:
            st.plotly_chart(fig_real, use_container_width=True, config={"staticPlot": True})

    with col_sug:
        st.markdown(
            '<div style="font-size: 1.1rem; font-weight: 600; color: #ffffff; '
            'margin-bottom: 0.5rem;">⭐ La que te sugerimos</div>',
            unsafe_allow_html=True,
        )
        fig_sug = _construir_donut(alloc_sug_disp, "Sugerida")
        if fig_sug:
            st.plotly_chart(fig_sug, use_container_width=True, config={"staticPlot": True})

    # ── Leyenda única compartida por los dos donuts ──────────────
    st.markdown(
        _leyenda_compartida(alloc_real_disp, alloc_sug_disp),
        unsafe_allow_html=True,
    )

    # ── Tira comparativa: rentabilidad y riesgo, las dos carteras ─
    # Una sola lectura lado a lado, en vez de cuatro bloques sueltos.
    st.markdown(
        '<div style="display:flex; gap:1.5rem; flex-wrap:wrap; '
        'background:rgba(255,255,255,0.025); '
        'border:1px solid rgba(255,255,255,0.06); border-radius:12px; '
        'padding:1rem 1.25rem;">'
        + _metrica_comparada(
            "Lo que podría rendir al año",
            f"{_emoji_rentabilidad(rent_real)} {rent_real:.1f}%",
            f"{_emoji_rentabilidad(rent_sugerida)} {rent_sugerida:.1f}%",
            "estimación real, después de inflación",
        )
        + _metrica_comparada(
            "Nivel de riesgo",
            f"{_emoji_riesgo(riesgo_real)} {riesgo_real.capitalize()}",
            f"{_emoji_riesgo(riesgo_sugerido)} {riesgo_sugerido.capitalize()}",
            "cuánto puede subir o bajar tu plata",
        )
        + _metrica_comparada(
            "Repartida en",
            f"🧩 {len(alloc_real_disp)} "
            + ("tipo" if len(alloc_real_disp) == 1 else "tipos"),
            f"🧩 {len(alloc_sug_disp)} "
            + ("tipo" if len(alloc_sug_disp) == 1 else "tipos"),
            "más repartida = que a una le vaya mal no te hunde",
        )
        + '</div>',
        unsafe_allow_html=True,
    )

    # ── Si la rentabilidad propia es MÁS alta, explicar por qué ──
    # Sin esto el usuario lee "la mía rinde más" y piensa que es mejor.
    # La causa real es la concentración — y eso ya se ve en el riesgo.
    if rent_real > rent_sugerida + 0.3:
        st.markdown(
            f'<div style="border-left:3px solid #f59e0b; '
            f'background:rgba(245,158,11,0.06); border-radius:0 10px 10px 0; '
            f'padding:0.9rem 1.15rem; margin-top:0.85rem;">'
            f'<div style="font-size:0.95rem; font-weight:600; color:#ffffff; '
            f'margin-bottom:0.3rem;">'
            f'⚠️ ¿Por qué tu cartera muestra un número más alto?</div>'
            f'<div style="font-size:0.875rem; color:rgba(255,255,255,0.72); '
            f'line-height:1.55;">'
            f'No es que sea mejor. Tu cartera está concentrada en pocos '
            f'activos parecidos: eso puede mostrar un número más alto en '
            f'el papel, pero si a ese grupo le va mal te golpea de lleno. '
            f'Por eso tu cartera es de riesgo <strong>{riesgo_real}</strong> '
            f'y la sugerida de riesgo <strong>{riesgo_sugerido}</strong>. '
            f'La sugerida está armada para darte el mejor resultado '
            f'posible sin exponerte de más — es la mejor para tu perfil '
            f'de riesgo y la más repartida.'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Por qué te sugerimos esta — explicación simple ───────────
    # Traduce a lenguaje cero-técnico que la sugerida es el resultado
    # de optimizar (Markowitz) sobre el análisis de cada empresa.
    # Pensado para alguien que nunca invirtió y que no quiere números.
    st.markdown(
        '<div style="border-left:3px solid #60a5fa; '
        'background:rgba(96,165,250,0.05); border-radius:0 10px 10px 0; '
        'padding:0.9rem 1.15rem; margin-top:0.85rem;">'
        '<div style="font-size:0.95rem; font-weight:600; color:#ffffff; '
        'margin-bottom:0.3rem;">⭐ ¿Por qué te sugerimos esta?</div>'
        '<div style="font-size:0.875rem; color:rgba(255,255,255,0.72); '
        'line-height:1.55;">'
        'No es la que más promete en el papel — es la más equilibrada '
        'para vos. La armamos mirando cada empresa una por una y cómo '
        'se mueven sus precios entre sí, para encontrar el mejor punto '
        'entre lo que podés ganar y lo que podés llegar a perder. No '
        'hace falta que entiendas los números: para eso la calculamos '
        'nosotros.'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Diferencia anual destacada (el VENDEDOR del pitch) ────────
    if diferencia_pct_anual > 0.5:  # Solo si hay diferencia material
        st.markdown(
            '<hr style="border: none; border-top: 1px solid rgba(255,255,255,0.08); margin: 1.5rem 0;">',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div style="background: rgba(34,197,94,0.08); border: 1px solid rgba(34,197,94,0.3); '
            f'border-radius: 8px; padding: 1rem 1.25rem;">'
            f'<div style="font-size: 0.875rem; color: rgba(255,255,255,0.7);">'
            f'💡 Con la cartera sugerida, podrías estar ganando aproximadamente</div>'
            f'<div style="font-size: 2rem; font-weight: 700; color: #22c55e; margin-top: 0.25rem; '
            f'letter-spacing: -0.01em;">${diferencia_ars_anual:,.0f} más al año</div>'
            f'<div style="font-size: 0.75rem; color: rgba(255,255,255,0.5); margin-top: 0.5rem;">'
            f'Calculado sobre tus ${valor_real:,.0f} actuales · '
            f'{diferencia_pct_anual:+.1f}% más rentabilidad estimada anual</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Gaps en lenguaje humano ──────────────────────────────────
    gaps = detectar_gaps_simples(alloc_real_disp, alloc_sug_disp)
    if gaps:
        st.markdown(
            '<hr style="border: none; border-top: 1px solid rgba(255,255,255,0.08); margin: 2rem 0 1rem 0;">',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div style="font-size: 1.3rem; font-weight: 600; color: #ffffff; '
            'margin-bottom: 0.75rem;">Lo más importante a revisar</div>',
            unsafe_allow_html=True,
        )
        for gap in gaps:
            # border-left del color de la categoría del gap — lo ata
            # visualmente a su porción en los donuts de arriba.
            color = _COLOR_CAT_UNIF.get(gap.get("categoria"), "#60a5fa")
            st.markdown(
                f'<div style="border-left:3px solid {color}; '
                f'background:rgba(255,255,255,0.03); '
                f'border-radius:0 10px 10px 0; '
                f'padding:0.85rem 1.1rem; margin-bottom:0.55rem;">'
                f'<div style="font-size:1rem; font-weight:600; color:#ffffff; '
                f'margin-bottom:0.3rem;">{gap["icon"]} {gap["titulo"]}</div>'
                f'<div style="font-size:0.875rem; color:rgba(255,255,255,0.72); '
                f'line-height:1.55;">{gap["explicacion"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # ── CTAs finales: handoff a asesor ───────────────────────────
    st.markdown(
        '<hr style="border: none; border-top: 1px solid rgba(255,255,255,0.08); margin: 2rem 0 1rem 0;">',
        unsafe_allow_html=True,
    )
    st.caption(
        "Esto es educativo, no es asesoramiento personalizado. "
        "Para tomar decisiones reales con tu plata, conviene hablar con alguien "
        "que te conozca y pueda mirar tu situación completa."
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button(
            "← Volver a editar mi cartera",
            use_container_width=True,
            key="cmp_back_btn",
        ):
            st.session_state["step"] = "user_portfolio"
            st.rerun()

    with col2:
        if st.button(
            "💬 Quiero hablar con un asesor",
            type="primary",
            use_container_width=True,
            key="cmp_advisor_btn",
        ):
            # Por ahora placeholder. En v2 abre el modal de handoff
            # con la info pre-cargada de la cartera + perfil.
            st.success(
                "Buenísimo. En el próximo paso vas a poder conectarte "
                "con un asesor real que ya ve tu cartera y tu perfil. "
                "Esa parte está casi lista — la integramos esta semana."
            )
