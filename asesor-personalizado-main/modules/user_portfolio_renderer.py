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
            # Columnas con proporción [1, 1.5, 1, 1]: "Valor actual" gana
            # 50% más ancho como métrica principal (jerarquía visual sin CSS).
            c1, c2, c3, c4 = st.columns([1, 1.5, 1, 1])
            c1.metric(
                "Total invertido",
                f"${totales['total_invertido']:,.0f}",
                help=(
                    "Lo que realmente pusiste, sumando el costo de cada activo. "
                    "Si cargaste con precio de compra, usamos ese costo real; "
                    "si cargaste en modo simple, usamos el monto que indicaste."
                ),
            )
            c2.metric(
                "💎 Valor actual",
                f"${totales['valor_total_actual']:,.0f}",
                help=(
                    "Cuánto vale hoy tu cartera al precio actual de cada activo. "
                    "Para los activos cargados en modo simple (sin precio del día), "
                    "asumimos que valen lo mismo que pusiste."
                ),
            )
            c3.metric(
                "Ganancia / Pérdida",
                f"${totales['pnl_total_ars']:,.0f}",
                delta=f"{signo_pct}{totales['pnl_total_pct']:.2f}%",
                help=(
                    "Diferencia entre lo que pusiste y lo que vale hoy. "
                    "Verde si ganaste, rojo si perdiste. Los activos sin precio "
                    "de compra no suman al cálculo individual."
                ),
            )
            c4.metric(
                "Activos cargados",
                str(totales['cantidad_activos']),
                help=(
                    "Cantidad de posiciones distintas en tu cartera. "
                    "Si cargaste el mismo activo dos veces, cuenta como dos."
                ),
            )

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
            # Un solo espacio entre ícono y nombre (era doble)
            st.markdown(f"**{icono} {activo['nombre']}**")
            # Ticker en bold para mejor escaneabilidad con múltiples activos
            st.caption(f"**{activo['ticker']}** · {tipo_label}")

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
    st.markdown("---")

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
                # En el 6C abrirá la comparación. Por ahora placeholder.
                st.info(
                    "🚧 La comparación lado a lado va a estar disponible "
                    "muy pronto. Por ahora tu portafolio queda guardado."
                )
