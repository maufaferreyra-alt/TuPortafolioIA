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
)
from .universo_instrumentos import (
    buscar_activos,
    get_activo_por_ticker,
)


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
    st.subheader("💼 Tu portafolio actual")
    st.caption(
        "Agregá cada activo que tenés. Podés cargar de a uno y ver cómo "
        "queda armado todo junto."
    )

    # ─── Lista de activos cargados (si los hay) ──────────
    if activos:
        totales = total_portafolio(activos)

        signo_pct = '+' if totales['pnl_total_pct'] >= 0 else ''

        with st.container(border=True):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric(
                "Total invertido",
                f"${totales['total_invertido']:,.0f}",
                help="Lo que realmente pusiste, en pesos.",
            )
            c2.metric(
                "Valor actual",
                f"${totales['valor_total_actual']:,.0f}",
                help="Cuánto vale hoy tu cartera.",
            )
            c3.metric(
                "Ganancia / Pérdida",
                f"${totales['pnl_total_ars']:,.0f}",
                delta=f"{signo_pct}{totales['pnl_total_pct']:.2f}%",
            )
            c4.metric("Activos cargados", str(totales['cantidad_activos']))

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

        st.markdown("### Activos en tu cartera")

        for activo in activos:
            _render_activo_card(activo)
    else:
        st.info(
            "📥 Todavía no cargaste ningún activo. "
            "Empezá agregando el primero abajo."
        )

    st.markdown("---")

    # ─── Form para agregar nuevo activo ───────────────────
    st.markdown("### ➕ Agregar un activo")

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
    st.markdown("---")
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

    monto_simple = 0.0
    cantidad_unidades = 0.0
    precio_actual = 0.0
    precio_compra = 0.0

    if es_modo_simple:
        # ──── MODO SIMPLE: solo monto, sin ganancia/pérdida ────
        st.markdown(
            '<p class="upf-form-hint">'
            'Ingresá cuánta plata (en pesos) tenés hoy en este activo. '
            'Lo encontrás en tu broker como "valor actual" o "tenencia".'
            '</p>',
            unsafe_allow_html=True,
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
        # Mensaje explícito al usuario.
        st.markdown(
            '<p class="upf-form-note">'
            '⓵ En este modo no calculamos ganancia o pérdida — solo registramos '
            'el valor que pusiste. Si querés saber tu ganancia, elegí el modo '
            '"sé cuántas unidades tengo".'
            '</p>',
            unsafe_allow_html=True,
        )

        # NO mostrar expander "Modo avanzado" en modo simple

    else:
        # ──── MODO UNIDADES: cantidad + precio del día ────
        st.markdown(
            '<p class="upf-form-hint">'
            'Si conocés cuántas unidades tenés y a qué precio cotiza hoy, '
            'calculamos por vos cuánto vale.'
            '</p>',
            unsafe_allow_html=True,
        )

        col_unid, col_precio = st.columns(2)

        with col_unid:
            cantidad_unidades = st.number_input(
                "📊 Cantidad de unidades que tenés",
                min_value=0.0,
                step=1.0,
                value=0.0,
                key=f"upf_cantidad_{activo_elegido['ticker']}_{tipo_seleccionado['id']}",
                help="La cantidad exacta que dice tu broker",
            )

        with col_precio:
            precio_actual = st.number_input(
                "💲 Precio del día (ARS)",
                min_value=0.0,
                step=10.0,
                value=0.0,
                key=f"upf_precio_actual_{activo_elegido['ticker']}_{tipo_seleccionado['id']}",
                help="A qué precio cotiza hoy una unidad. Lo ves en tu broker o en BYMA.",
            )

        # Calculo automático en vivo
        if cantidad_unidades > 0 and precio_actual > 0:
            valor_calc = cantidad_unidades * precio_actual
            st.markdown(
                f'<div class="upf-monto-calculado">'
                f'💡 <strong>Valor actual estimado:</strong> '
                f'${valor_calc:,.0f} ARS '
                f'<span class="upf-monto-calc-detail">'
                f'({cantidad_unidades:.2f} unidades × ${precio_actual:,.2f})'
                f'</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

        # SOLO en modo unidades aparece el modo avanzado
        with st.expander("🔧 Modo avanzado: quiero saber ganancia/pérdida"):
            st.markdown(
                '<p class="upf-form-hint">'
                'Si recordás a qué precio compraste una unidad, podemos '
                'calcular cuánto ganaste o perdiste. Si no lo recordás, '
                'no pasa nada — el resto funciona igual.'
                '</p>',
                unsafe_allow_html=True,
            )

            precio_compra = st.number_input(
                "💼 Precio al que compraste una unidad (ARS, opcional)",
                min_value=0.0,
                step=10.0,
                value=0.0,
                key=f"upf_precio_compra_{activo_elegido['ticker']}_{tipo_seleccionado['id']}",
                help="Si no lo recordás, dejalo en 0",
            )

        # Warning de supuesto cae (solo en modo unidades)
        if precio_actual > 0 and precio_compra > 0:
            diferencia_pct = ((precio_compra - precio_actual) / precio_compra) * 100
            if diferencia_pct > 5:
                st.warning(
                    f"⚠️ **Heads up:** el precio actual está {diferencia_pct:.1f}% por "
                    f"debajo de cuando compraste. La proyección de tu cartera "
                    f"sugerida estaba pensada con otros números — vale la pena "
                    f"hablar esto con tu asesor."
                )

    # ─── Botón de agregar ───
    st.markdown("")

    if st.button(
        "➕ Agregar a mi portafolio",
        type="primary",
        use_container_width=True,
        key=f"upf_add_btn_{activo_elegido['ticker']}_{tipo_seleccionado['id']}",
    ):
        if es_modo_simple:
            # Modo simple: SOLO monto, sin precio_actual ni precio_compra
            if monto_simple <= 0:
                st.error("Tenés que poner cuánta plata tenés en este activo.")
            else:
                nuevo_activo = crear_activo(
                    tipo=tipo_seleccionado["id"],
                    ticker=activo_elegido["ticker"],
                    nombre=activo_elegido["nombre"],
                    monto_invertido_ars=monto_simple,
                    precio_actual_ars=None,    # ← CLAVE: None en modo simple
                    precio_compra_ars=None,    # ← CLAVE: None en modo simple
                )
                st.session_state["user_portfolio_activos"].append(nuevo_activo)
                _persistir_portafolio()
                st.success(f"✅ {activo_elegido['nombre']} agregado a tu cartera")
                st.rerun()
        else:
            # Modo unidades: validación de cantidad y precio_actual
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
            st.markdown(f"**{icono}  {activo['nombre']}**")
            st.caption(f"{activo['ticker']} · {tipo_label}")

        with col_action:
            if st.button("🗑️", key=f"upf_del_{activo['id']}", help="Eliminar activo"):
                st.session_state["user_portfolio_activos"] = [
                    a for a in st.session_state["user_portfolio_activos"]
                    if a["id"] != activo["id"]
                ]
                _persistir_portafolio()
                st.rerun()

        n1, n2, n3 = st.columns(3)
        n1.metric("Invertido", f"${invertido:,.0f}")
        n2.metric("Valor actual", f"${pnl['valor_actual']:,.0f}")

        if pnl["pnl_ars"] is not None:
            signo = "+" if pnl["pnl_ars"] >= 0 else ""
            n3.metric(
                "Ganancia / Pérdida",
                f"${pnl['pnl_ars']:,.0f}",
                delta=f"{signo}{pnl['pnl_pct']:.2f}%",
            )
        else:
            n3.metric(
                "Ganancia / Pérdida",
                "—",
                help="Sin datos de compra — cargá el activo con precio de compra para verlo.",
            )


def _render_action_buttons(activos: list):
    """Botones de acción al final del form."""
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "← Volver a mi cartera sugerida",
            use_container_width=True,
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
                # En el 6C abrirá la comparación. Por ahora placeholder.
                st.info(
                    "🚧 La comparación lado a lado va a estar disponible "
                    "muy pronto. Por ahora tu portafolio queda guardado."
                )
