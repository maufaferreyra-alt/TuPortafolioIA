"""
Renderer de la página de carga de portafolio del usuario.

Estados:
- "intro": pantalla de bienvenida con copy empático
- "loading": form de carga + lista de activos
"""

import streamlit as st
from .user_portfolio import (
    TIPOS_INSTRUMENTO,
    crear_activo,
    calcular_pnl,
    total_portafolio,
    costo_invertido,
    get_tipo_info,
    SOFT_WARNING_ARS,
    HARD_BLOCK_ARS,
    RATIO_VALOR_MONTO_MAX,
)
from .universo_instrumentos import (
    buscar_activos,
    get_activo_por_ticker,
)


# ── Nombres en lenguaje natural por tipo de activo ────────────────
# Usados en labels del form para que el usuario novato encuentre
# las palabras que ve en su broker (acciones, CEDEARs, bonos)
# en vez del genérico "unidades".

NOMBRES_PLURAL_POR_TIPO = {
    "accion_arg": "acciones",
    "cedear":     "CEDEARs",
    "bono":       "bonos",
    "on":         "ONs",
    "letra":      "letras",
    "mep":        "dólares",
}

NOMBRES_SINGULAR_POR_TIPO = {
    "accion_arg": "acción",
    "cedear":     "CEDEAR",
    "bono":       "bono",
    "on":         "ON",
    "letra":      "letra",
    "mep":        "dólar",
}


def _persistir_portafolio():
    """Guarda el portafolio del usuario en localStorage junto con la cartera."""
    try:
        from .storage import guardar_estado
        guardar_estado(
            answers=st.session_state.get("answers", {}),
            profile=st.session_state.get("profile", {}),
            portfolio=st.session_state.get("portfolio", {}),
            user_portfolio_activos=st.session_state.get("user_portfolio_activos", []),
        )
    except Exception as e:
        print(f"[user_portfolio] Error persistiendo: {e}")


def render_user_portfolio_page():
    """Punto de entrada de la página de carga."""

    # Inicializar estado si no existe
    if "user_portfolio_step" not in st.session_state:
        st.session_state["user_portfolio_step"] = "intro"
    if "user_portfolio_activos" not in st.session_state:
        st.session_state["user_portfolio_activos"] = []

    step = st.session_state["user_portfolio_step"]

    if step == "intro":
        _render_intro()
    elif step == "loading":
        _render_loading()


def _render_intro():
    """Pantalla de bienvenida a la carga del portafolio."""

    # Header centrado
    st.markdown(
        '<div class="upf-intro-header">'
        '<div class="upf-intro-icon">💼</div>'
        '<h1 class="upf-intro-title">¿Estás listo para armar tu primer portafolio?</h1>'
        '<p class="upf-intro-subtitle">'
        'Sabemos que da nervios. Por eso te vamos a acompañar paso por paso. '
        'No hay apuro, no hay decisiones definitivas — solo estamos viendo qué tenés hoy.'
        '</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Bullets en bloque separado, HTML simple
    st.markdown(
        '<div class="upf-intro-bullets">'
        '<div class="upf-intro-bullet">'
        '<span class="upf-intro-bullet-icon">⏱️</span>'
        '<span class="upf-intro-bullet-text">Te va a tomar menos de 5 minutos</span>'
        '</div>'
        '<div class="upf-intro-bullet">'
        '<span class="upf-intro-bullet-icon">🔓</span>'
        '<span class="upf-intro-bullet-text">Podés cargar cuando quieras, en cualquier momento</span>'
        '</div>'
        '<div class="upf-intro-bullet">'
        '<span class="upf-intro-bullet-icon">🔒</span>'
        '<span class="upf-intro-bullet-text">Lo que cargues queda solo en tu navegador, nadie más lo ve</span>'
        '</div>'
        '<div class="upf-intro-bullet">'
        '<span class="upf-intro-bullet-icon">💪</span>'
        '<span class="upf-intro-bullet-text">No es decisión definitiva — es ver qué tenés para hablarlo con tu asesor</span>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Botones
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button(
            "💪 Empezar a cargar mi portafolio",
            use_container_width=True,
            type="primary",
            key="upf_start_btn",
        ):
            st.session_state["user_portfolio_step"] = "loading"
            st.rerun()

        if st.button(
            "⏭️ Saltar por ahora, vuelvo después",
            use_container_width=True,
            key="upf_skip_btn",
        ):
            # Volver al resultado de cartera sugerida
            st.session_state["step"] = "results"
            st.rerun()


def _render_loading():
    """Pantalla principal de carga: lista de activos + form."""

    activos = st.session_state.get("user_portfolio_activos", [])

    # ─── Header ──────────────────────────────────────────
    # NOTA: usamos componentes nativos de Streamlit (st.subheader, st.caption,
    # st.container, st.columns, st.metric) en vez de HTML+CSS custom. El CSS
    # del bloque global de ui_config.py no aplicaba de forma confiable a estas
    # clases .upf-* y las cards salían como texto plano sin estilo. Los
    # componentes nativos renderizan styleados garantizado.
    st.markdown(
        '<div style="font-size: 1.5rem; font-weight: 700; color: #ffffff; margin-bottom: 0.5rem; letter-spacing: -0.01em;">'
        '💼 Tu portafolio actual'
        '</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Agregá cada activo que tenés. Podés cargar de a uno y ver cómo "
        "queda armado todo junto."
    )

    # ─── Lista de activos cargados (si los hay) ──────────
    if activos:
        totales = total_portafolio(activos)

        signo_pct = '+' if totales['pnl_total_pct'] >= 0 else ''

        # ── DONUT GRANDE: composición de la cartera por categoría ──
        # En vez de mostrar el valor total como número gigante, el donut
        # comunica la composición visual (qué tan diversificada está la
        # cartera, qué predomina). El valor total va al resumen chico
        # debajo de los desplegables.
        from .user_portfolio import agrupar_activos_por_categoria, NOMBRES_CATEGORIA
        from .comparison_renderer import COLORES_CATEGORIA

        grupos_para_donut = agrupar_activos_por_categoria(activos)
        if grupos_para_donut:
            import plotly.graph_objects as go

            labels_donut = [NOMBRES_CATEGORIA.get(g["tipo"], g["tipo"]) for g in grupos_para_donut]
            values_donut = [g["valor_total"] for g in grupos_para_donut]
            colors_donut = [COLORES_CATEGORIA.get(g["tipo"], "#888") for g in grupos_para_donut]

            fig_cartera = go.Figure(data=[go.Pie(
                labels=labels_donut,
                values=values_donut,
                hole=0.6,
                marker=dict(colors=colors_donut, line=dict(color="#0f1423", width=2)),
                textinfo="percent",
                textposition="inside",
                textfont=dict(size=14, color="#ffffff"),
                hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<br>%{percent}<extra></extra>",
            )])
            fig_cartera.update_layout(
                showlegend=True,
                legend=dict(
                    orientation="v",
                    yanchor="middle",
                    y=0.5,
                    xanchor="left",
                    x=1.05,
                    font=dict(size=12, color="rgba(255,255,255,0.85)"),
                ),
                margin=dict(t=20, b=20, l=20, r=20),
                height=340,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_cartera, use_container_width=True, config={"displayModeBar": False})

        # Detectar si algún activo está en modo simple (sin valuación de mercado).
        # En modo simple precio_actual_ars queda en None.
        activos_sin_precio_dia = [
            a for a in activos if a.get("precio_actual_ars") is None
        ]

        if activos_sin_precio_dia:
            st.caption(
                "💡 **Valor actual = Total invertido**: para los activos que cargaste sin "
                "precio del día, asumimos que valen lo mismo que pusiste. Cuando conectemos "
                "con precios de mercado, vas a ver el valor real de hoy. "
                "Si querés precisión ahora, recargá el activo con cantidad de unidades + precio del día."
            )

        st.markdown(
            '<div style="font-size: 1.15rem; font-weight: 600; color: #ffffff; margin: 1.5rem 0 0.75rem 0;">'
            'Activos en tu cartera'
            '</div>',
            unsafe_allow_html=True,
        )

        # Si hay solo 1 activo, mantener el render flat (no tiene
        # sentido un expander para una sola cosa)
        if len(activos) == 1:
            _render_activo_card(activos[0])
        else:
            # 2+ activos: agrupar por categoría con cards custom
            # (border accent + % gigante + toggle propio con session_state).
            from .user_portfolio import agrupar_activos_por_categoria as _agrupar_loop
            grupos_loop = _agrupar_loop(activos)
            for grupo in grupos_loop:
                _render_categoria_card(grupo)

        # ── Resumen chico DESPUÉS de los desplegables ────────────
        # El valor total + delta + datos clave en formato compacto.
        # Visualmente discreto (no es el dato protagonista — el donut
        # de arriba lo es), pero la info sigue accesible.
        pnl_color_res = "#22c55e" if totales['pnl_total_pct'] >= 0 else "#ef4444"
        pnl_arrow_res = "↑" if totales['pnl_total_pct'] >= 0 else "↓"

        # Texto de los tooltips (mismo copy que tenían los st.metric
        # antes de pasar a HTML plano).
        tooltip_valor_actual = (
            "Cuánto vale hoy tu cartera, sumando el precio actual de cada activo."
        )
        tooltip_total_invertido = (
            "Lo que realmente pusiste, sumando el costo de cada activo. "
            "Si cargaste con precio de compra, usamos ese costo real; "
            "si cargaste en modo simple, usamos el monto que indicaste."
        )
        tooltip_cantidad_activos = (
            "Cantidad de posiciones distintas en tu cartera. "
            "Si cargaste el mismo activo dos veces, cuenta como dos."
        )

        st.markdown(
            f'<div style="margin: 1.25rem 0 0.5rem 0; padding: 0.875rem 1.125rem; '
            f'background: rgba(255,255,255,0.025); border-radius: 10px; '
            f'border: 1px solid rgba(255,255,255,0.06);">'
            f'<div style="font-size: 0.95rem; color: rgba(255,255,255,0.85); line-height: 1.5;">'
            f'💎 Tu portafolio vale '
            f'<strong style="color: #ffffff; cursor: help;" title="{tooltip_valor_actual}">${totales["valor_total_actual"]:,.0f}</strong>'
            f'  ·  '
            f'<span style="color: {pnl_color_res}; font-weight: 500;">{pnl_arrow_res} {signo_pct}{totales["pnl_total_pct"]:.2f}%</span>'
            f'  ·  Total invertido '
            f'<strong style="color: rgba(255,255,255,0.95); cursor: help;" title="{tooltip_total_invertido}">${totales["total_invertido"]:,.0f}</strong>'
            f'  ·  '
            f'<strong style="color: rgba(255,255,255,0.95); cursor: help;" title="{tooltip_cantidad_activos}">{totales["cantidad_activos"]}</strong>'
            f' {"activo" if totales["cantidad_activos"] == 1 else "activos"}'
            f'</div>'
            f'<div style="font-size: 0.75rem; color: rgba(255,255,255,0.4); margin-top: 0.5rem; line-height: 1.4;">'
            f'ℹ️ Diferencia entre lo que pusiste y lo que vale hoy. Los activos sin precio de compra no suman al cálculo individual.'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        st.info(
            "📥 Todavía no cargaste ningún activo. "
            "Empezá agregando el primero abajo."
        )

    st.markdown(
        '<hr style="border: none; border-top: 1px solid rgba(255,255,255,0.08); margin: 2rem 0;">',
        unsafe_allow_html=True,
    )

    # ─── Form para agregar nuevo activo ───────────────────
    st.markdown(
        '<div style="font-size: 1.3rem; font-weight: 600; color: #ffffff; margin-bottom: 0.75rem;">'
        '➕ Agregar un activo'
        '</div>',
        unsafe_allow_html=True,
    )

    # PASO 1: Tipo de instrumento
    tipo_options = ["— Elegí un tipo... —"] + [
        f"{t['icono']} {t['label']}" for t in TIPOS_INSTRUMENTO
    ]

    tipo_idx = st.selectbox(
        "¿Qué tipo de activo querés agregar?",
        range(len(tipo_options)),
        format_func=lambda i: tipo_options[i],
        key="upf_tipo_selectbox",
    )

    if tipo_idx == 0:
        # No eligió tipo todavía
        st.caption("Elegí primero el tipo de activo para ver las opciones disponibles.")
        _render_action_buttons(activos)
        return

    tipo_seleccionado = TIPOS_INSTRUMENTO[tipo_idx - 1]

    st.caption(f"💡 {tipo_seleccionado['descripcion']}")

    # PASO 2: Buscar activo del universo filtrado
    # Placeholder adaptado al tipo elegido
    PLACEHOLDERS_POR_TIPO = {
        "bono":       "Ej: AL30, GD30, AE38, Bonar...",
        "cedear":     "Ej: AAPL, Apple, SPY, MELI...",
        "accion_arg": "Ej: YPFD, GGAL, Pampa, Macro...",
        "on":         "Ej: YPFDS, ON YPF, Pan American...",
        "fci":        "Ej: Money Market, Cocos, Balanz...",
        "letra":      "Ej: S30Y6, LECAP, BONCAP...",
        "mep":        "Ej: MEP, AL30D, GD30D...",
    }
    placeholder_query = PLACEHOLDERS_POR_TIPO.get(
        tipo_seleccionado["id"],
        "Ej: ticker o nombre del activo...",
    )

    query = st.text_input(
        "Buscar activo (por ticker o nombre)",
        key=f"upf_query_input_{tipo_seleccionado['id']}",  # ← key dinámica
        placeholder=placeholder_query,
    )

    matches = buscar_activos(query, tipo=tipo_seleccionado["id"], limit=8)

    if not matches:
        st.warning(
            f"No encontramos resultados de {tipo_seleccionado['label']} "
            f"con '{query}'. Probá con otro nombre o ticker."
        )
        _render_action_buttons(activos)
        return

    activo_options = [f"{m['ticker']} — {m['nombre']}" for m in matches]

    activo_idx = st.selectbox(
        "Elegí el activo",
        range(len(activo_options)),
        format_func=lambda i: activo_options[i],
        key=f"upf_activo_selectbox_{tipo_seleccionado['id']}",  # ← key dinámica
    )

    activo_elegido = matches[activo_idx]

    # ─── PASO 3: ¿Cómo sabe el usuario cuánto tiene? ───
    st.markdown(
        '<hr style="border: none; border-top: 1px solid rgba(255,255,255,0.08); margin: 2rem 0;">',
        unsafe_allow_html=True,
    )

    es_fci = tipo_seleccionado["id"] == "fci"

    # Variables del form (defaults según corresponda)
    monto_simple = 0.0
    cantidad_unidades = 0.0
    precio_actual = 0.0
    precio_compra = 0.0
    fci_monto_puesto = 0.0
    fci_valor_hoy = 0.0
    es_modo_simple = True  # FCI siempre es modo simple-like

    if es_fci:
        # ─────────── FORM PARA FCIs ───────────
        # Los FCIs no se cargan por cuotapartes. El broker te muestra
        # directamente cuánto vale tu posición en pesos.
        st.markdown("##### 💰 ¿Cuánto tenés en este fondo?")
        st.caption(
            "En los FCIs el broker te muestra directo cuánto vale tu "
            "posición — no hace falta calcular nada."
        )

        col_pusiste, col_hoy = st.columns(2)

        with col_pusiste:
            fci_monto_puesto = st.number_input(
                "💵 ¿Cuánto pusiste? (ARS)",
                min_value=0.0,
                step=1000.0,
                value=0.0,
                key=f"upf_fci_puesto_{activo_elegido['ticker']}",
                help="Lo que entregaste cuando suscribiste el fondo.",
            )

        with col_hoy:
            fci_valor_hoy = st.number_input(
                "💎 ¿Cuánto vale hoy? (ARS, opcional)",
                min_value=0.0,
                step=1000.0,
                value=0.0,
                key=f"upf_fci_hoy_{activo_elegido['ticker']}",
                help=(
                    "Lo que ves en tu broker como 'valor actual' o 'tenencia'. "
                    "Si no lo sabés, dejalo en 0 — asumimos que vale lo que pusiste."
                ),
            )

        # Si cargó ambos, mostrar P&L proyectado en vivo
        if fci_monto_puesto > 0 and fci_valor_hoy > 0:
            pnl_proy = fci_valor_hoy - fci_monto_puesto
            pnl_pct_proy = (pnl_proy / fci_monto_puesto) * 100
            signo = '+' if pnl_proy >= 0 else ''
            if pnl_proy >= 0:
                st.success(
                    f"💡 **Ganancia / pérdida proyectada:** "
                    f"{signo}${pnl_proy:,.0f} ({signo}{pnl_pct_proy:.2f}%)"
                )
            else:
                st.error(
                    f"💡 **Ganancia / pérdida proyectada:** "
                    f"${pnl_proy:,.0f} ({pnl_pct_proy:.2f}%)"
                )

    else:
        # ─────────── FORM PARA RESTO DE TIPOS ───────────
        st.markdown("##### 💰 ¿Cómo querés cargar lo que tenés?")

        modo_carga = st.radio(
            "Elegí la opción que mejor te resulte:",
            options=[
                "💵 Sé cuánta plata tengo en este activo",
                "📊 Sé cuántas unidades tengo (lo veo en mi broker)",
            ],
            key=f"upf_modo_{tipo_seleccionado['id']}_{activo_elegido['ticker']}",
            help="Si dudás, elegí la primera — es la más común.",
        )

        es_modo_simple = modo_carga.startswith("💵")

        if es_modo_simple:
            # ──── MODO SIMPLE: solo monto, sin ganancia/pérdida ────
            st.caption(
                "Ingresá cuánta plata (en pesos) tenés hoy en este activo. "
                "Lo encontrás en tu broker como \"valor actual\" o \"tenencia\"."
            )

            monto_simple = st.number_input(
                "💵 Plata que tenés en este activo (ARS)",
                min_value=0.0,
                step=1000.0,
                value=0.0,
                key=f"upf_monto_simple_{activo_elegido['ticker']}_{tipo_seleccionado['id']}",
                help="Por ejemplo: si en tu broker dice 'Apple: $50.000', poné 50000",
            )

            # En modo simple NO hay manera de calcular ganancia/pérdida.
            st.info(
                "⓵ En este modo no calculamos ganancia o pérdida — solo "
                "registramos el valor que pusiste. Si querés saber tu "
                "ganancia, elegí el modo \"sé cuántas unidades tengo\"."
            )

        else:
            # ──── MODO UNIDADES: cantidad + precio del día ────
            # Nombres dinámicos según tipo (acciones/CEDEARs/bonos/etc)
            tipo_id = tipo_seleccionado["id"]
            nombre_plural = NOMBRES_PLURAL_POR_TIPO.get(tipo_id, "unidades")
            nombre_singular = NOMBRES_SINGULAR_POR_TIPO.get(tipo_id, "unidad")

            st.caption(
                f"Si conocés cuántas {nombre_plural} tenés y a qué precio "
                f"cotiza una hoy, calculamos por vos cuánto vale tu posición."
            )

            # Key del number_input del precio (usado también por el botón
            # de fetch para escribir el valor traído de la API).
            precio_key = f"upf_precio_actual_{activo_elegido['ticker']}_{tipo_seleccionado['id']}"

            # Inicializar si no existe (evita warning de Streamlit por
            # conflicto entre value default y session_state existente).
            if precio_key not in st.session_state:
                st.session_state[precio_key] = 0.0

            # Botón de auto-fill desde API (Bloque 6B). Va arriba de
            # las columnas para que sea visible y opcional. Si la API
            # no tiene el activo, caption discreta y el usuario carga
            # manual abajo.
            col_btn, col_info = st.columns([2, 3])
            with col_btn:
                if st.button(
                    "📡 Traer precio en vivo",
                    key=f"upf_fetch_btn_{activo_elegido['ticker']}_{tipo_seleccionado['id']}",
                    use_container_width=True,
                    help=(
                        "Trae el precio del día desde APIs gratuitas "
                        "(data912 / argentinadatos, ~2h de delay). En "
                        "producción con API paga sería tiempo real."
                    ),
                ):
                    from .market_data import get_precio_dia
                    precio_fetched = get_precio_dia(
                        activo_elegido["ticker"],
                        tipo_seleccionado["id"],
                    )
                    if precio_fetched and precio_fetched > 0:
                        st.session_state[precio_key] = float(precio_fetched)
                        st.session_state[f"_fetch_msg_{precio_key}"] = (
                            f"✅ ${precio_fetched:,.2f} traído de la API"
                        )
                    else:
                        st.session_state[f"_fetch_msg_{precio_key}"] = (
                            "📡 No tenemos precio en vivo para este activo. "
                            "Cargalo a mano abajo."
                        )
                    st.rerun()

            with col_info:
                # Mostrar el último mensaje de fetch (success o no-data)
                msg = st.session_state.get(f"_fetch_msg_{precio_key}")
                if msg:
                    if msg.startswith("✅"):
                        st.success(msg)
                    else:
                        st.caption(msg)

            col_unid, col_precio = st.columns(2)

            with col_unid:
                cantidad_unidades = st.number_input(
                    f"📊 Cantidad de {nombre_plural} que tenés",
                    min_value=0.0,
                    step=1.0,
                    value=0.0,
                    key=f"upf_cantidad_{activo_elegido['ticker']}_{tipo_seleccionado['id']}",
                    help=(
                        f"La cantidad exacta de {nombre_plural} que dice tu "
                        "broker. Si tu broker dice 'tenencia 100', acá va 100."
                    ),
                )

            with col_precio:
                precio_actual = st.number_input(
                    f"💲 Precio actual de una {nombre_singular} (ARS)",
                    min_value=0.0,
                    step=10.0,
                    key=precio_key,
                    help=(
                        f"Lo que vale HOY UNA {nombre_singular} (no el total). "
                        f"Si tenés 100 {nombre_plural} y cada una vale $1.000, "
                        "acá ponés 1000, no 100000. Lo ves en tu broker como "
                        "'cotización' o 'último precio', o usá '📡 Traer precio "
                        "en vivo' arriba."
                    ),
                )

            # Cálculo automático en vivo con componente nativo
            if cantidad_unidades > 0 and precio_actual > 0:
                valor_calc = cantidad_unidades * precio_actual
                st.info(
                    f"💡 **Tu posición vale:** ${valor_calc:,.0f} ARS  "
                    f"_({cantidad_unidades:.0f} {nombre_plural} × "
                    f"${precio_actual:,.2f} cada una)_"
                )

            # SOLO en modo unidades aparece el campo de precio de compra
            with st.expander(f"💡 Sé a qué precio compré cada {nombre_singular} (opcional)"):
                st.caption(
                    f"Si recordás a qué precio compraste cada {nombre_singular}, "
                    f"calculamos cuánto ganaste o perdiste desde ese momento. "
                    "Si no lo recordás, no pasa nada — el resto funciona igual."
                )

                precio_compra = st.number_input(
                    f"💼 Precio al que compraste cada {nombre_singular} (ARS, opcional)",
                    min_value=0.0,
                    step=10.0,
                    value=0.0,
                    key=f"upf_precio_compra_{activo_elegido['ticker']}_{tipo_seleccionado['id']}",
                    help=(
                        f"Lo que pagaste por UNA {nombre_singular} cuando la "
                        "compraste, no el total. Si no lo recordás exacto, "
                        "dejalo en 0 y seguís."
                    ),
                )

            # Banner del supuesto cae — copy NEUTRO (Bug 4)
            if precio_actual > 0 and precio_compra > 0:
                diferencia_pct = ((precio_compra - precio_actual) / precio_compra) * 100
                if diferencia_pct > 5:
                    st.warning(
                        f"⚠️ **Heads up:** el precio actual está "
                        f"{diferencia_pct:.1f}% por debajo de cuando compraste. "
                        f"Puede ser pérdida real, o que cargaste algún número "
                        f"raro — vale la pena revisarlo antes de agregar."
                    )

    # ─── SANITY CHECK DE MAGNITUD (Bug 3) ────────────────────────
    # Se calcula sobre el valor "más reciente" (lo que vale hoy o lo
    # que puso). Bloquea agregar si supera HARD_BLOCK_ARS o si el
    # ratio valor/costo es absurdo en modo unidades con compra.
    if es_fci:
        valor_para_check = fci_valor_hoy if fci_valor_hoy > 0 else fci_monto_puesto
    elif es_modo_simple:
        valor_para_check = monto_simple
    else:
        valor_para_check = cantidad_unidades * precio_actual

    bloqueado_por_sanity = False
    mensaje_bloqueo = ""

    if valor_para_check > HARD_BLOCK_ARS:
        bloqueado_por_sanity = True
        mensaje_bloqueo = (
            f"🚫 Estás cargando ${valor_para_check:,.0f} ARS en un solo activo. "
            f"Valores arriba de ${HARD_BLOCK_ARS:,.0f} ARS son muy raros — "
            f"revisá si se te corrió la coma en cantidad o precio."
        )
    elif valor_para_check > SOFT_WARNING_ARS:
        st.warning(
            f"⚠️ **Ojo:** estás cargando ${valor_para_check:,.0f} ARS en este "
            f"activo. Si es correcto, seguí — si no, revisá los números."
        )

    # Ratio check (solo modo unidades con compra)
    if (not es_fci and not es_modo_simple
            and precio_actual > 0 and precio_compra > 0
            and cantidad_unidades > 0):
        costo_real = cantidad_unidades * precio_compra
        valor_real = cantidad_unidades * precio_actual
        if costo_real > 0 and valor_real / costo_real > RATIO_VALOR_MONTO_MAX:
            bloqueado_por_sanity = True
            multiplicador = valor_real / costo_real
            mensaje_bloqueo = (
                f"🚫 Estás cargando que este activo multiplicó por "
                f"{multiplicador:.0f}x desde que lo compraste. Eso es muy raro — "
                f"revisá precio de compra y precio del día."
            )

    if bloqueado_por_sanity:
        st.error(mensaje_bloqueo)

    # ─── Botón de agregar ────────────────────────────────────────
    st.markdown("")

    if st.button(
        "➕ Agregar a mi portafolio",
        type="primary",
        use_container_width=True,
        key=f"upf_add_btn_{activo_elegido['ticker']}_{tipo_seleccionado['id']}",
        disabled=bloqueado_por_sanity,
    ):
        if es_fci:
            # FCI: monto_invertido obligatorio, valor_actual_directo opcional
            if fci_monto_puesto <= 0:
                st.error("Tenés que poner cuánto pusiste en este fondo.")
            else:
                nuevo_activo = crear_activo(
                    tipo=tipo_seleccionado["id"],
                    ticker=activo_elegido["ticker"],
                    nombre=activo_elegido["nombre"],
                    monto_invertido_ars=fci_monto_puesto,
                    precio_actual_ars=None,
                    precio_compra_ars=None,
                    valor_actual_directo=fci_valor_hoy if fci_valor_hoy > 0 else None,
                )
                st.session_state["user_portfolio_activos"].append(nuevo_activo)
                _persistir_portafolio()
                st.success(f"✅ {activo_elegido['nombre']} agregado a tu cartera")
                st.rerun()
        elif es_modo_simple:
            # Modo simple: SOLO monto
            if monto_simple <= 0:
                st.error("Tenés que poner cuánta plata tenés en este activo.")
            else:
                nuevo_activo = crear_activo(
                    tipo=tipo_seleccionado["id"],
                    ticker=activo_elegido["ticker"],
                    nombre=activo_elegido["nombre"],
                    monto_invertido_ars=monto_simple,
                    precio_actual_ars=None,
                    precio_compra_ars=None,
                )
                st.session_state["user_portfolio_activos"].append(nuevo_activo)
                _persistir_portafolio()
                st.success(f"✅ {activo_elegido['nombre']} agregado a tu cartera")
                st.rerun()
        else:
            # Modo unidades: cantidad + precio_actual obligatorios
            if cantidad_unidades <= 0:
                st.error("Tenés que poner cuántas unidades tenés.")
            elif precio_actual <= 0:
                st.error("Tenés que poner el precio actual del activo.")
            else:
                nuevo_activo = crear_activo(
                    tipo=tipo_seleccionado["id"],
                    ticker=activo_elegido["ticker"],
                    nombre=activo_elegido["nombre"],
                    monto_invertido_ars=cantidad_unidades * precio_actual,
                    precio_actual_ars=precio_actual,
                    precio_compra_ars=precio_compra if precio_compra > 0 else None,
                )
                st.session_state["user_portfolio_activos"].append(nuevo_activo)
                _persistir_portafolio()
                st.success(f"✅ {activo_elegido['nombre']} agregado a tu cartera")
                st.rerun()

    _render_action_buttons(activos)


def _render_mini_donut(grupo: dict):
    """
    Renderiza un mini-donut con el peso de cada activo DENTRO de la
    categoría. Solo tiene sentido cuando hay 2+ activos — el llamador
    debe verificar antes de invocar.

    Usa Plotly con el mismo styling de los donuts del 6C, pero más chico.
    """
    import plotly.graph_objects as go
    from .user_portfolio import calcular_valor_actual

    activos = grupo["activos"]
    if len(activos) < 2:
        return

    # Calcular peso de cada activo dentro del grupo
    valor_grupo = grupo["valor_total"]
    if valor_grupo <= 0:
        return

    labels = []
    values = []
    for a in activos:
        valor = calcular_valor_actual(a) or 0
        if valor > 0:
            ticker = a.get("ticker", "?")
            labels.append(ticker)
            values.append(valor)

    if not labels:
        return

    # Paleta de azules/violetas para variantes dentro de UNA categoría
    # (no usar la paleta del 6C porque esos colores son por categoría,
    # acá necesitamos diferenciación dentro de la misma categoría)
    PALETA_INTRA = [
        "#6366f1",  # azul
        "#a78bfa",  # violeta
        "#34d399",  # verde
        "#fbbf24",  # amarillo
        "#f472b6",  # rosa
        "#22d3ee",  # cyan
        "#fb923c",  # naranja
        "#e879f9",  # magenta
    ]
    colors = [PALETA_INTRA[i % len(PALETA_INTRA)] for i in range(len(labels))]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.6,
        marker=dict(colors=colors, line=dict(color="#1a1f2e", width=2)),
        textinfo="percent",
        textposition="inside",
        textfont=dict(size=11, color="#ffffff"),
        hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<br>%{percent}<extra></extra>",
    )])
    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.05,
            font=dict(size=10, color="rgba(255,255,255,0.75)"),
        ),
        margin=dict(t=5, b=5, l=5, r=5),
        height=180,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _render_categoria_card(grupo: dict):
    """
    Renderiza UN grupo de activos como una card con el estilo de
    "Composición de su cartera" (cartera sugerida): border-left accent
    + título + descripción + % gigante a la derecha. Toggle para
    expandir/colapsar con session_state.

    Estado inicial:
      - 2+ activos: expandido por default
      - 1 activo: colapsado
    """
    from .user_portfolio import (
        DESCRIPCIONES_CATEGORIA,
        NOMBRES_CATEGORIA,
        get_tipo_info,
    )
    from .comparison_renderer import COLORES_CATEGORIA

    tipo_id = grupo["tipo"]
    cantidad = grupo["cantidad"]
    valor_total = grupo["valor_total"]
    pct_cartera = grupo["porcentaje_cartera"]

    tipo_info = get_tipo_info(tipo_id)
    icono = tipo_info.get("icono", "📦") if tipo_info else "📦"
    nombre_categoria = NOMBRES_CATEGORIA.get(tipo_id) or (
        tipo_info.get("label", tipo_id) if tipo_info else tipo_id
    )
    descripcion = DESCRIPCIONES_CATEGORIA.get(tipo_id, "")
    color_accent = COLORES_CATEGORIA.get(tipo_id, "#6366f1")

    sufijo_count = f"{cantidad} {'activo' if cantidad == 1 else 'activos'}"

    # State del toggle de expandido en session_state
    clave_estado = f"_cat_card_expandida_{tipo_id}"
    if clave_estado not in st.session_state:
        st.session_state[clave_estado] = cantidad >= 2

    expandida = st.session_state[clave_estado]

    # ── HEADER DECORATIVO: border accent + título + descripción + % ──
    # Layout flex: izquierda título/descripción, derecha % gigante
    st.markdown(
        f'<div style="border-left: 3px solid {color_accent}; '
        f'background: rgba(255,255,255,0.025); '
        f'border-radius: 10px; '
        f'padding: 1rem 1.25rem 0.875rem 1.25rem; '
        f'margin-bottom: 0.375rem; '
        f'display: flex; align-items: center; justify-content: space-between; gap: 1rem;">'
        f'<div style="flex: 1; min-width: 0;">'
        f'<div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.25rem;">'
        f'<span style="font-size: 1.05rem;">{icono}</span>'
        f'<strong style="color: #ffffff; font-size: 1rem; letter-spacing: -0.005em;">{nombre_categoria}</strong>'
        f'</div>'
        f'<div style="color: rgba(255,255,255,0.6); font-size: 0.825rem; line-height: 1.4;">'
        f'{descripcion}'
        f'{"  ·  " + sufijo_count if descripcion else sufijo_count}'
        f'</div>'
        f'</div>'
        f'<div style="text-align: right; flex-shrink: 0;">'
        f'<div style="color: {color_accent}; font-size: 1.75rem; font-weight: 700; letter-spacing: -0.02em; line-height: 1;">'
        f'{pct_cartera:.1f}%'
        f'</div>'
        f'<div style="color: rgba(255,255,255,0.4); font-size: 0.7rem; letter-spacing: 0.05em; text-transform: uppercase; margin-top: 0.25rem;">'
        f'de tu cartera'
        f'</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── BOTÓN TOGGLE: discreto, alineado a la derecha ──
    # Streamlit no permite envolver el header en un botón clickeable,
    # así que ofrecemos un toggle textual chico debajo. Usamos columnas
    # con peso para alinear a la derecha.
    col_spacer, col_btn = st.columns([5, 2])
    with col_btn:
        label_btn = "Ocultar detalle ⌄" if expandida else "Ver detalle ›"
        if st.button(
            label_btn,
            key=f"_btn_toggle_cat_{tipo_id}",
            use_container_width=True,
            type="tertiary",
        ):
            st.session_state[clave_estado] = not expandida
            st.rerun()

    # ── CONTENIDO EXPANDIDO ──
    if expandida:
        # Mini-donut SOLO si hay 2+ activos
        if cantidad >= 2:
            _render_mini_donut(grupo)
            st.markdown(
                '<hr style="border: none; border-top: 1px solid rgba(255,255,255,0.06); margin: 0.5rem 0 1rem 0;">',
                unsafe_allow_html=True,
            )

        # Cards de los activos del grupo (sin cambios)
        for activo in grupo["activos"]:
            _render_activo_card(activo)

    # Separador visual entre cards de categoría
    st.markdown(
        '<div style="margin-bottom: 1rem;"></div>',
        unsafe_allow_html=True,
    )


def _render_categoria_group(grupo: dict):
    """
    Renderiza UN grupo de activos como un expander.

    El header del expander muestra ícono + nombre human-friendly +
    total $ + cantidad de activos + % de la cartera total.

    Estado inicial:
      - Si hay 2+ activos: expanded=True
      - Si hay 1 activo: expanded=False
    """
    tipo_id = grupo["tipo"]
    cantidad = grupo["cantidad"]
    valor_total = grupo["valor_total"]
    pct_cartera = grupo["porcentaje_cartera"]

    # Ícono y nombre desde el catálogo de tipos
    tipo_info = get_tipo_info(tipo_id)
    icono = tipo_info["icono"] if tipo_info else "📦"
    nombre_categoria = tipo_info["label"] if tipo_info else tipo_id

    # Sufijo: "1 activo" o "N activos"
    sufijo_count = f"{cantidad} {'activo' if cantidad == 1 else 'activos'}"

    # Header del expander (multi-info en una sola línea)
    header_text = (
        f"{icono} {nombre_categoria}  ·  "
        f"${valor_total:,.0f}  ·  "
        f"{sufijo_count}  ·  "
        f"{pct_cartera:.1f}% de tu cartera"
    )

    # Estado inicial: abierto si hay 2+, cerrado si hay 1
    inicialmente_abierto = cantidad >= 2

    with st.expander(header_text, expanded=inicialmente_abierto):
        # Mini-donut SOLO si hay 2+ activos
        if cantidad >= 2:
            _render_mini_donut(grupo)
            st.markdown(
                '<hr style="border: none; border-top: 1px solid rgba(255,255,255,0.06); margin: 0.5rem 0 1rem 0;">',
                unsafe_allow_html=True,
            )

        # Cards de los activos del grupo
        for activo in grupo["activos"]:
            _render_activo_card(activo)


def _render_activo_card(activo: dict):
    """Card de un activo individual — componentes nativos de Streamlit."""
    tipo_info = get_tipo_info(activo["tipo"])
    pnl = calcular_pnl(activo)

    icono = tipo_info['icono'] if tipo_info else '📊'
    tipo_label = tipo_info['label'] if tipo_info else activo['tipo']

    # "Invertido" = lo que el usuario realmente puso. En modo unidades con
    # compra, monto_invertido_ars guarda el valor actual, no el costo.
    invertido = costo_invertido(activo)

    with st.container(border=True):
        col_titulo, col_action = st.columns([8, 1])

        with col_titulo:
            # Header del activo con ticker en accent color (azul marca).
            # CSS inline garantiza que aplique (no depende de clases globales).
            st.markdown(
                f'<div style="font-size: 1.05rem; font-weight: 600; color: #ffffff;">'
                f'{icono} {activo["nombre"]}'
                f'</div>'
                f'<div style="font-size: 0.85rem; color: rgba(255,255,255,0.55); margin-top: 0.15rem;">'
                f'<span style="color: #6366f1; font-weight: 600; font-family: ui-monospace, monospace;">{activo["ticker"]}</span>'
                f' · {tipo_label}'
                f'</div>',
                unsafe_allow_html=True,
            )

        with col_action:
            if st.button("🗑️", key=f"upf_del_{activo['id']}", help="Eliminar activo"):
                st.session_state["user_portfolio_activos"] = [
                    a for a in st.session_state["user_portfolio_activos"]
                    if a["id"] != activo["id"]
                ]
                _persistir_portafolio()
                st.rerun()

        n1, n2, n3 = st.columns(3)
        n1.metric(
            "Invertido",
            f"${invertido:,.0f}",
            help="Lo que realmente pusiste por este activo.",
        )
        n2.metric(
            "Valor actual",
            f"${pnl['valor_actual']:,.0f}",
            help=(
                "Cuánto vale hoy este activo. "
                "Si lo cargaste en modo simple, asumimos que vale lo mismo que pusiste."
            ),
        )

        if pnl["pnl_ars"] is not None:
            signo = "+" if pnl["pnl_ars"] >= 0 else ""
            n3.metric(
                "Ganancia / Pérdida",
                f"${pnl['pnl_ars']:,.0f}",
                delta=f"{signo}{pnl['pnl_pct']:.2f}%",
                help="Diferencia entre lo que pusiste y lo que vale hoy.",
            )
        else:
            n3.metric(
                "Ganancia / Pérdida",
                "—",
                help=(
                    "Sin datos de compra — cargá el activo con cantidad de unidades "
                    "+ precio de compra para verlo."
                ),
            )


def _render_action_buttons(activos: list):
    """Botones de acción al final del form."""
    st.markdown(
        '<hr style="border: none; border-top: 1px solid rgba(255,255,255,0.08); margin: 2rem 0;">',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "← Volver a mi cartera sugerida",
            use_container_width=True,
            type="tertiary",
            key="upf_back_btn",
        ):
            st.session_state["step"] = "results"
            st.rerun()

    with col2:
        if activos:
            if st.button(
                "✅ Listo, ver comparación",
                type="primary",
                use_container_width=True,
                key="upf_finish_btn",
            ):
                st.session_state["step"] = "comparison"
                st.rerun()
