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

    st.markdown(
        """
        <div class="upf-intro-container">
            <div class="upf-intro-icon">💼</div>
            <h1 class="upf-intro-title">
                ¿Estás listo para armar tu primer portafolio?
            </h1>
            <p class="upf-intro-subtitle">
                Sabemos que da nervios. Por eso te vamos a acompañar paso por paso.
                No hay apuro, no hay decisiones definitivas — solo estamos viendo
                qué tenés hoy.
            </p>

            <div class="upf-intro-bullets">
                <div class="upf-intro-bullet">
                    <span class="upf-intro-bullet-icon">⏱️</span>
                    <span>Te va a tomar menos de 5 minutos</span>
                </div>
                <div class="upf-intro-bullet">
                    <span class="upf-intro-bullet-icon">🔓</span>
                    <span>Podés cargar cuando quieras, en cualquier momento</span>
                </div>
                <div class="upf-intro-bullet">
                    <span class="upf-intro-bullet-icon">🔒</span>
                    <span>Lo que cargues queda solo en tu navegador, nadie más lo ve</span>
                </div>
                <div class="upf-intro-bullet">
                    <span class="upf-intro-bullet-icon">💪</span>
                    <span>No es una decisión final — es ver qué tenés para hablarlo con tu asesor</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

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
        key="upf_query_input",
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
        key="upf_activo_selectbox",
    )

    activo_elegido = matches[activo_idx]

    # PASO 3: Montos
    col1, col2, col3 = st.columns(3)

    with col1:
        monto_invertido = st.number_input(
            "Monto invertido (ARS)",
            min_value=0.0,
            step=1000.0,
            value=0.0,
            key="upf_monto_input",
            help="Cuánto invertiste en pesos cuando compraste este activo",
        )

    with col2:
        precio_actual = st.number_input(
            "Precio del día (ARS por unidad)",
            min_value=0.0,
            step=10.0,
            value=0.0,
            key="upf_precio_actual_input",
            help="El precio actual al que cotiza hoy. Mirá tu broker o el panel del mercado.",
        )

    with col3:
        precio_compra = st.number_input(
            "Precio de compra (opcional, ARS)",
            min_value=0.0,
            step=10.0,
            value=0.0,
            key="upf_precio_compra_input",
            help="A qué precio compraste. Si lo dejás en 0, no calculamos ganancia/pérdida.",
        )

    # ─── Validación: precio actual no puede estar muy abajo del supuesto ───
    profile = st.session_state.get("profile", {})
    supuesto_cae = False

    if precio_actual > 0 and precio_compra > 0:
        # Si el precio actual cayó más del 5% respecto al supuesto del test
        diferencia_pct = ((precio_compra - precio_actual) / precio_compra) * 100
        if diferencia_pct > 5:
            supuesto_cae = True
            st.warning(
                f"⚠️ **Heads up:** el precio actual está {diferencia_pct:.1f}% por "
                f"debajo del precio de compra. Las proyecciones de tu cartera "
                f"sugerida estaban basadas en supuestos que ya no se cumplen — "
                f"vale la pena hablar esto con tu asesor."
            )

    # Botón de agregar
    if st.button(
        "➕ Agregar a mi portafolio",
        type="primary",
        use_container_width=True,
        key="upf_add_btn",
    ):
        if monto_invertido <= 0:
            st.error("Tenés que poner el monto invertido en pesos.")
        elif precio_actual <= 0:
            st.error("Tenés que poner el precio actual del activo.")
        else:
            nuevo_activo = crear_activo(
                tipo=tipo_seleccionado["id"],
                ticker=activo_elegido["ticker"],
                nombre=activo_elegido["nombre"],
                monto_invertido_ars=monto_invertido,
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
