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
    st.markdown(
        """
        <div class="upf-header">
            <h2>💼 Tu portafolio actual</h2>
            <p>
                Agregá cada activo que tenés. Podés cargar de a uno y ver cómo
                queda armado todo junto.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ─── Lista de activos cargados (si los hay) ──────────
    if activos:
        totales = total_portafolio(activos)

        st.markdown(
            f"""
            <div class="upf-totals-card">
                <div class="upf-totals-row">
                    <div class="upf-total-item">
                        <div class="upf-total-label">Total invertido</div>
                        <div class="upf-total-value">${totales['total_invertido']:,.0f}</div>
                        <div class="upf-total-sub">ARS</div>
                    </div>
                    <div class="upf-total-item">
                        <div class="upf-total-label">Valor actual</div>
                        <div class="upf-total-value upf-total-value-actual">${totales['valor_total_actual']:,.0f}</div>
                        <div class="upf-total-sub">ARS</div>
                    </div>
                    <div class="upf-total-item">
                        <div class="upf-total-label">Ganancia / Pérdida</div>
                        <div class="upf-total-value {'upf-total-pnl-positive' if totales['pnl_total_ars'] >= 0 else 'upf-total-pnl-negative'}">
                            {'+' if totales['pnl_total_ars'] >= 0 else ''}${totales['pnl_total_ars']:,.0f}
                        </div>
                        <div class="upf-total-sub">
                            {'+' if totales['pnl_total_pct'] >= 0 else ''}{totales['pnl_total_pct']:.2f}%
                        </div>
                    </div>
                    <div class="upf-total-item">
                        <div class="upf-total-label">Activos cargados</div>
                        <div class="upf-total-value">{totales['cantidad_activos']}</div>
                        <div class="upf-total-sub">en cartera</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### Activos en tu cartera")

        for activo in activos:
            _render_activo_card(activo)
    else:
        st.markdown(
            """
            <div class="upf-empty-state">
                <div class="upf-empty-icon">📥</div>
                <div class="upf-empty-text">
                    Todavía no cargaste ningún activo.<br>
                    Empezá agregando el primero abajo.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
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
    query = st.text_input(
        "Buscar activo (por ticker o nombre)",
        key=f"upf_query_input_{tipo_seleccionado['id']}",  # ← key dinámica
        placeholder="Ej: AAPL, Apple, AL30...",
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

    monto_invertido = 0.0
    precio_actual = 0.0
    cantidad_unidades = 0.0

    if modo_carga.startswith("💵"):
        # Modo simple: solo monto
        st.markdown(
            '<p class="upf-form-hint">'
            'Ingresá cuánta plata (en pesos) tenés en este activo hoy. '
            'Lo encontrás en tu cuenta del broker como "valor actual" o "tenencia".'
            '</p>',
            unsafe_allow_html=True,
        )

        monto_invertido = st.number_input(
            "💵 Plata que tenés en este activo (ARS)",
            min_value=0.0,
            step=1000.0,
            value=0.0,
            key=f"upf_monto_simple_{activo_elegido['ticker']}",
            help="Por ejemplo: si en tu broker dice 'Apple: $50.000', poné 50000",
        )

        # Para el modo simple, asumimos que monto = valor actual
        # No tenemos precio compra, así que P&L queda en None
        precio_actual = 0.0  # Lo derivamos del monto, no lo pedimos

    else:
        # Modo con unidades: necesitamos precio del día también
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
                key=f"upf_cantidad_{activo_elegido['ticker']}",
                help="La cantidad exacta que dice tu broker",
            )

        with col_precio:
            precio_actual = st.number_input(
                "💲 Precio del día (ARS)",
                min_value=0.0,
                step=10.0,
                value=0.0,
                key=f"upf_precio_actual_{activo_elegido['ticker']}",
                help="A qué precio cotiza hoy una unidad. Lo ves en tu broker o en BYMA.",
            )

        # Calculamos automáticamente el monto invertido
        if cantidad_unidades > 0 and precio_actual > 0:
            monto_invertido = cantidad_unidades * precio_actual
            st.markdown(
                f'<div class="upf-monto-calculado">'
                f'💡 <strong>Valor actual estimado:</strong> '
                f'${monto_invertido:,.0f} ARS '
                f'<span class="upf-monto-calc-detail">'
                f'({cantidad_unidades:.2f} unidades × ${precio_actual:,.2f})'
                f'</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # ─── Toggle de modo avanzado (P&L con precio de compra) ───
    with st.expander("🔧 Modo avanzado: quiero saber ganancia/pérdida"):
        st.markdown(
            '<p class="upf-form-hint">'
            'Si recordás a qué precio compraste, podemos calcular cuánto ganaste o perdiste. '
            'Si no lo recordás, no pasa nada — el resto funciona igual.'
            '</p>',
            unsafe_allow_html=True,
        )

        precio_compra = st.number_input(
            "💼 Precio al que compraste (ARS, opcional)",
            min_value=0.0,
            step=10.0,
            value=0.0,
            key=f"upf_precio_compra_{activo_elegido['ticker']}",
            help="Si no lo recordás, dejalo en 0",
        )

    # ─── Warning de supuesto cae ───
    if precio_actual > 0 and precio_compra > 0:
        diferencia_pct = ((precio_compra - precio_actual) / precio_compra) * 100
        if diferencia_pct > 5:
            st.warning(
                f"⚠️ **Heads up:** el precio actual está {diferencia_pct:.1f}% por "
                f"debajo de cuando compraste. La proyección de tu cartera sugerida "
                f"estaba pensada con otros números — vale la pena hablar esto con "
                f"tu asesor."
            )

    # ─── Botón de agregar ───
    st.markdown("")

    if st.button(
        "➕ Agregar a mi portafolio",
        type="primary",
        use_container_width=True,
        key=f"upf_add_btn_{activo_elegido['ticker']}",
    ):
        # Validación según modo
        if modo_carga.startswith("💵"):
            # Modo simple
            if monto_invertido <= 0:
                st.error("Tenés que poner cuánta plata tenés en este activo.")
            else:
                # En modo simple, asumimos precio_actual=monto y cantidad implícita=1
                # Esto deja el activo sin posibilidad de P&L (a menos que después
                # rellenen precio_compra)
                nuevo_activo = crear_activo(
                    tipo=tipo_seleccionado["id"],
                    ticker=activo_elegido["ticker"],
                    nombre=activo_elegido["nombre"],
                    monto_invertido_ars=monto_invertido,
                    precio_actual_ars=monto_invertido,  # 1 "unidad virtual" = monto total
                    precio_compra_ars=precio_compra if precio_compra > 0 else None,
                )
                st.session_state["user_portfolio_activos"].append(nuevo_activo)
                _persistir_portafolio()
                st.success(f"✅ {activo_elegido['nombre']} agregado a tu cartera")
                st.rerun()
        else:
            # Modo con unidades
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
    """Card de un activo individual en la lista."""
    tipo_info = get_tipo_info(activo["tipo"])
    pnl = calcular_pnl(activo)

    pnl_class = ""
    pnl_text = "Sin datos de compra"
    if pnl["pnl_ars"] is not None:
        pnl_class = "upf-pnl-positive" if pnl["pnl_ars"] >= 0 else "upf-pnl-negative"
        signo = "+" if pnl["pnl_ars"] >= 0 else ""
        pnl_text = f"{signo}${pnl['pnl_ars']:,.0f} ({signo}{pnl['pnl_pct']:.2f}%)"

    col_data, col_action = st.columns([5, 1])

    with col_data:
        st.markdown(
            f"""
            <div class="upf-activo-card">
                <div class="upf-activo-header">
                    <span class="upf-activo-icono">{tipo_info['icono'] if tipo_info else '📊'}</span>
                    <div class="upf-activo-titles">
                        <div class="upf-activo-nombre">{activo['nombre']}</div>
                        <div class="upf-activo-ticker">{activo['ticker']} · {tipo_info['label'] if tipo_info else activo['tipo']}</div>
                    </div>
                </div>
                <div class="upf-activo-numbers">
                    <div class="upf-activo-num">
                        <span class="upf-activo-num-label">Invertido</span>
                        <span class="upf-activo-num-value">${activo['monto_invertido_ars']:,.0f}</span>
                    </div>
                    <div class="upf-activo-num">
                        <span class="upf-activo-num-label">Valor actual</span>
                        <span class="upf-activo-num-value">${pnl['valor_actual']:,.0f}</span>
                    </div>
                    <div class="upf-activo-num">
                        <span class="upf-activo-num-label">Ganancia/Pérdida</span>
                        <span class="upf-activo-num-value {pnl_class}">{pnl_text}</span>
                    </div>
                </div>
            </div>
            """,
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
