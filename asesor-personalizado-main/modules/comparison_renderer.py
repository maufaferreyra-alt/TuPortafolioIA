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


def _emoji_rentabilidad(pct: float) -> str:
    """Emoji honesto según nivel de rentabilidad estimada."""
    if pct >= 9:   return "🚀"
    if pct >= 6:   return "✓"
    if pct >= 3:   return "⚠️"
    return "📉"


def _emoji_riesgo(nivel: str) -> str:
    if nivel == "bajo":  return "✓"
    if nivel == "medio": return "≈"
    return "⚠️"


def _construir_donut(allocation: dict, titulo: str):
    """Construye un donut chart de Plotly a partir del dict allocation."""
    if not allocation:
        return None
    labels = [NOMBRES_CATEGORIA.get(t, t) for t in allocation.keys()]
    values = list(allocation.values())
    colors = [COLORES_CATEGORIA.get(t, "#888") for t in allocation.keys()]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.55,
        marker=dict(colors=colors, line=dict(color="#0e1117", width=2)),
        textinfo="percent",
        textposition="inside",
        textfont=dict(size=13, color="#ffffff"),
        hovertemplate="<b>%{label}</b><br>%{percent}<extra></extra>",
    )])
    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.05,
            font=dict(size=11, color="rgba(255,255,255,0.75)"),
        ),
        margin=dict(t=10, b=10, l=10, r=10),
        height=280,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


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
        fig_real = _construir_donut(allocation_real, "Real")
        if fig_real:
            st.plotly_chart(fig_real, use_container_width=True, config={"displayModeBar": False})
        st.markdown(
            f'<div style="padding: 0.5rem 0;">'
            f'<div style="font-size: 0.875rem; color: rgba(255,255,255,0.6);">Lo que podría rendir al año</div>'
            f'<div style="font-size: 1.5rem; font-weight: 700; color: #ffffff; margin-top: 0.15rem;">'
            f'{_emoji_rentabilidad(rent_real)} {rent_real:.1f}%</div>'
            f'<div style="font-size: 0.75rem; color: rgba(255,255,255,0.4); margin-top: 0.25rem;">'
            f'estimación real, después de inflación</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div style="padding: 0.5rem 0;">'
            f'<div style="font-size: 0.875rem; color: rgba(255,255,255,0.6);">Nivel de riesgo</div>'
            f'<div style="font-size: 1.25rem; font-weight: 600; color: #ffffff; margin-top: 0.15rem;">'
            f'{_emoji_riesgo(riesgo_real)} {riesgo_real.capitalize()}</div>'
            f'<div style="font-size: 0.75rem; color: rgba(255,255,255,0.4); margin-top: 0.25rem;">'
            f'cuánto puede subir o bajar tu plata</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col_sug:
        st.markdown(
            '<div style="font-size: 1.1rem; font-weight: 600; color: #ffffff; '
            'margin-bottom: 0.5rem;">⭐ La que te sugerimos</div>',
            unsafe_allow_html=True,
        )
        fig_sug = _construir_donut(allocation_sugerida, "Sugerida")
        if fig_sug:
            st.plotly_chart(fig_sug, use_container_width=True, config={"displayModeBar": False})
        st.markdown(
            f'<div style="padding: 0.5rem 0;">'
            f'<div style="font-size: 0.875rem; color: rgba(255,255,255,0.6);">Lo que podría rendir al año</div>'
            f'<div style="font-size: 1.5rem; font-weight: 700; color: #ffffff; margin-top: 0.15rem;">'
            f'{_emoji_rentabilidad(rent_sugerida)} {rent_sugerida:.1f}%</div>'
            f'<div style="font-size: 0.75rem; color: rgba(255,255,255,0.4); margin-top: 0.25rem;">'
            f'estimación real, después de inflación</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div style="padding: 0.5rem 0;">'
            f'<div style="font-size: 0.875rem; color: rgba(255,255,255,0.6);">Nivel de riesgo</div>'
            f'<div style="font-size: 1.25rem; font-weight: 600; color: #ffffff; margin-top: 0.15rem;">'
            f'{_emoji_riesgo(riesgo_sugerido)} {riesgo_sugerido.capitalize()}</div>'
            f'<div style="font-size: 0.75rem; color: rgba(255,255,255,0.4); margin-top: 0.25rem;">'
            f'cuánto puede subir o bajar tu plata</div>'
            f'</div>',
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
    gaps = detectar_gaps_simples(allocation_real, allocation_sugerida)
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
            with st.container(border=True):
                st.markdown(
                    f'<div style="padding: 0.25rem 0;">'
                    f'<div style="font-size: 1rem; font-weight: 600; color: #ffffff; margin-bottom: 0.25rem;">'
                    f'{gap["icon"]} {gap["titulo"]}</div>'
                    f'<div style="font-size: 0.875rem; color: rgba(255,255,255,0.75); line-height: 1.5;">'
                    f'{gap["explicacion"]}</div>'
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
