"""
Renderer de la página de carga de portafolio del usuario.

Estados:
- "intro": pantalla de bienvenida con copy empático
- "loading": form de carga + lista de activos
"""

import streamlit as st
from .user_portfolio import (
    TIPOS_INSTRUMENTO,
    TIPOS_VIVO,
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
    "etf":        "unidades",
    "bono":       "bonos",
    "on":         "ONs",
    "letra":      "letras",
    "mep":        "dólares",
}

NOMBRES_SINGULAR_POR_TIPO = {
    "accion_arg": "acción",
    "cedear":     "CEDEAR",
    "etf":        "unidad",
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

    # ── Header (hero centrado, HTML inline premium) ──────────────
    # No usamos las clases .upf-intro-* (están duplicadas en
    # ui_config.py y se pisan entre sí). CSS inline = render confiable.
    st.markdown(
        '<div style="max-width:600px; margin:1.5rem auto 1.5rem auto; '
        'text-align:center;">'
        # ícono en badge circular indigo
        '<div style="width:4.5rem; height:4.5rem; margin:0 auto 1.25rem auto; '
        'border-radius:50%; background:rgba(96,165,250,0.12); '
        'border:1px solid rgba(96,165,250,0.28); display:flex; '
        'align-items:center; justify-content:center; font-size:2.2rem;">💼</div>'
        # título
        '<h1 style="font-size:1.9rem; font-weight:700; color:#f5f5f7; '
        'line-height:1.25; letter-spacing:-0.02em; margin:0 0 0.85rem 0;">'
        '¿Querés practicar o armar tu portafolio?'
        '</h1>'
        # subtítulo (max-width chico para que envuelva parejo)
        '<p style="font-size:1.02rem; color:rgba(255,255,255,0.6); '
        'line-height:1.6; max-width:480px; margin:0 auto;">'
        'Sabemos que da nervios. Por eso te vamos a acompañar paso por paso. '
        'No hay apuro, no hay decisiones definitivas — solo estamos viendo qué tenés hoy.'
        '</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Bullets (card con cada punto en su fila) ─────────────────
    _bullets = [
        ("⏱️", "Te va a tomar menos de 5 minutos"),
        ("🔓", "Podés cargar cuando quieras, en cualquier momento"),
        ("🔒", "Lo que cargues queda solo en tu navegador, nadie más lo ve"),
        ("💪", "No es decisión definitiva — es ver qué tenés para hablarlo con tu asesor"),
    ]
    _filas_html = ""
    for _i, (_ic, _txt) in enumerate(_bullets):
        _borde = (
            "" if _i == len(_bullets) - 1
            else "border-bottom:1px solid rgba(255,255,255,0.05);"
        )
        _filas_html += (
            f'<div style="display:flex; align-items:center; gap:0.85rem; '
            f'padding:0.7rem 0; {_borde}">'
            f'<div style="flex-shrink:0; width:2.15rem; height:2.15rem; '
            f'border-radius:8px; background:rgba(96,165,250,0.1); '
            f'display:flex; align-items:center; justify-content:center; '
            f'font-size:1.1rem;">{_ic}</div>'
            f'<div style="font-size:0.95rem; color:rgba(255,255,255,0.82); '
            f'line-height:1.45;">{_txt}</div>'
            f'</div>'
        )
    st.markdown(
        '<div style="max-width:560px; margin:0 auto 1.75rem auto; '
        'background:rgba(255,255,255,0.025); '
        'border:1px solid rgba(255,255,255,0.07); '
        'border-radius:14px; padding:0.35rem 1.35rem;">'
        + _filas_html +
        '</div>',
        unsafe_allow_html=True,
    )

    # Botones
    # El label de arrancar depende de si ya hay activos cargados:
    # cartera en 0 → "empezar"; ya empezó → "seguir".
    _tiene_activos = len(st.session_state.get("user_portfolio_activos", [])) > 0
    _label_arrancar = (
        "💪 Seguir con el armado de mi portafolio" if _tiene_activos
        else "💪 Empezar el armado de mi portafolio"
    )
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button(
            _label_arrancar,
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


def _paso_badge(numero: str, titulo: str, subtitulo: str = "") -> str:
    """
    HTML de un encabezado de paso numerado para el form de carga.
    Círculo indigo con el número + título + subtítulo guía. Pensado
    para que un usuario novato sepa en qué parte del proceso está.
    """
    sub = (
        f'<div style="font-size:0.8rem;color:rgba(255,255,255,0.5);'
        f'margin-top:0.1rem;line-height:1.4;">{subtitulo}</div>'
        if subtitulo else ''
    )
    return (
        f'<div style="display:flex;align-items:center;gap:0.7rem;'
        f'margin:1.75rem 0 0.9rem 0;">'
        f'<div style="flex-shrink:0;width:1.7rem;height:1.7rem;'
        f'border-radius:50%;background:#60a5fa;color:#ffffff;'
        f'display:flex;align-items:center;justify-content:center;'
        f'font-weight:700;font-size:0.9rem;line-height:1;">{numero}</div>'
        f'<div>'
        f'<div style="font-size:1.05rem;font-weight:600;color:#ffffff;'
        f'letter-spacing:-0.005em;">{titulo}</div>'
        f'{sub}'
        f'</div>'
        f'</div>'
    )


def _refrescar_precios_vivos(activos: list) -> bool:
    """
    Para los activos modo 'vivo' (acciones / CEDEARs / MEP) vuelve a
    pedir el precio de mercado y actualiza precio_actual_ars. Así el
    valor del portafolio se mueve con el mercado sin que el usuario
    haga nada.

    Usa la caché de 1h de market_data, así que llamarlo en cada run no
    satura la API. Devuelve True si hay al menos un activo en vivo.
    """
    if not activos:
        return False
    try:
        from .market_data import get_precio_dia
    except Exception:
        return False
    hay_vivos = False
    for a in activos:
        if a.get("modo") != "vivo":
            continue
        hay_vivos = True
        try:
            precio = get_precio_dia(a.get("ticker", ""), a.get("tipo", ""))
            if precio and precio > 0:
                a["precio_actual_ars"] = float(precio)
        except Exception as e:
            print(f"[user_portfolio] refresh precio falló para {a.get('ticker')}: {e}")
    return hay_vivos


def _render_loading():
    """Pantalla principal de carga: lista de activos + form."""

    activos = st.session_state.get("user_portfolio_activos", [])

    # Refresco automático de precios para los activos en vivo (6C):
    # el valor del portafolio se mueve con el mercado sin tocar nada.
    _hay_activos_vivos = _refrescar_precios_vivos(activos)

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

        if _hay_activos_vivos:
            st.caption(
                "🟢 Precios de acciones, CEDEARs y MEP actualizados con el "
                "mercado de hoy. Los bonos, ONs y fondos los actualizás vos."
            )

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
            st.plotly_chart(fig_cartera, use_container_width=True, config={"staticPlot": True})

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

        # ── Vista de activos ─────────────────────────────────────
        # Normal: HTML puro estilo "Composición de su cartera"
        #   (categorías en <details> nativos, sub-cards anidadas).
        # Editar: cards Streamlit con el botón 🗑️ de borrar — el
        #   borrar es un widget y no puede vivir en el HTML puro.
        if st.session_state.get("_upf_modo_editar", False):
            _render_modo_editar(activos)
        else:
            _render_portafolio_html(activos)
            _, _col_editar = st.columns([3, 2])
            with _col_editar:
                if st.button(
                    "✏️ Editar / eliminar activos",
                    key="_upf_btn_modo_editar",
                    use_container_width=True,
                    type="tertiary",
                ):
                    st.session_state["_upf_modo_editar"] = True
                    st.rerun()

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
        '<div style="font-size: 1.3rem; font-weight: 600; color: #ffffff; margin-bottom: 0.25rem;">'
        '➕ Agregar un activo'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Paso 1: identificar el activo ─────────────────────
    st.markdown(
        _paso_badge(
            "1",
            "¿Qué activo tenés?",
            "Elegí primero el tipo y después buscá el activo puntual. "
            "Si no sabés alguno, no pasa nada — andá probando.",
        ),
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

    # Nota para ETFs: técnicamente se compran como CEDEARs, pero los
    # mostramos aparte para que la cartera del usuario quede alineada
    # con la sugerida (donde figuran como "Fondos globales").
    if tipo_seleccionado["id"] == "etf":
        st.info(
            "Sí, un ETF se compra como CEDEAR en tu broker. Lo separamos "
            "acá para que se entienda mejor: un ETF es un fondo que junta "
            "muchas empresas o activos, así que en tu cartera lo vas a ver "
            "como fondo, igual que en la cartera que te sugerimos.",
            icon="ℹ️",
        )

    # PASO 2: Buscar activo del universo filtrado
    # Placeholder adaptado al tipo elegido
    PLACEHOLDERS_POR_TIPO = {
        "bono":       "Ej: AL30, GD30, AE38, Bonar...",
        "cedear":     "Ej: AAPL, Apple, MSFT, MELI...",
        "etf":        "Ej: SPY, QQQ, S&P 500, Nasdaq...",
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

    # ─── Paso 2: cuánto tiene el usuario ───
    st.markdown(
        _paso_badge(
            "2",
            "¿Cuánto tenés?",
            "Cargá lo que tenés hoy de este activo. El resto de las "
            "cuentas las hacemos nosotros.",
        ),
        unsafe_allow_html=True,
    )

    tipo_id = tipo_seleccionado["id"]
    tk = activo_elegido["ticker"]
    nombre_plural = NOMBRES_PLURAL_POR_TIPO.get(tipo_id, "unidades")
    nombre_singular = NOMBRES_SINGULAR_POR_TIPO.get(tipo_id, "unidad")
    es_vivo_tipo = tipo_id in TIPOS_VIVO

    # Para acciones / CEDEARs / MEP el camino es "vivo": seguimos el
    # precio de mercado. El usuario puede tildar "no sé el precio" y
    # entonces ese activo se carga como manual.
    no_sabe_precio = False
    if es_vivo_tipo:
        no_sabe_precio = st.checkbox(
            "No sé a qué precio compré este activo",
            key=f"upf_nosabe_{tk}_{tipo_id}",
            help=(
                "Si no te acordás del precio de compra, igual lo podés "
                "cargar — lo registramos con el valor que tenga hoy, pero "
                "no vamos a poder seguir tu ganancia automáticamente."
            ),
        )

    modo_carga = "vivo" if (es_vivo_tipo and not no_sabe_precio) else "manual"

    # Variables del form (las completa el camino que corresponda)
    monto_puesto = 0.0
    precio_compra = 0.0
    valor_hoy_manual = 0.0

    if modo_carga == "vivo":
        # ─────────── CAMINO EN VIVO: monto + precio de compra ───────────
        st.caption(
            f"Decinos cuánto pusiste y a qué precio estaba {nombre_singular} "
            f"cuando compraste. Con eso seguimos solos cuánto vale hoy."
        )

        col_monto, col_pcompra = st.columns(2)
        with col_monto:
            monto_puesto = st.number_input(
                "💵 ¿Cuánto pusiste en total? (ARS)",
                min_value=0.0,
                step=1000.0,
                value=0.0,
                key=f"upf_vivo_monto_{tk}_{tipo_id}",
                help=(
                    "La plata total que pusiste cuando compraste este "
                    "activo. Lo ves en el comprobante de tu broker."
                ),
            )
        with col_pcompra:
            precio_compra = st.number_input(
                f"🏷️ ¿A qué precio estaba una {nombre_singular}? (ARS)",
                min_value=0.0,
                step=10.0,
                value=0.0,
                key=f"upf_vivo_pcompra_{tk}_{tipo_id}",
                help=(
                    f"El precio de UNA {nombre_singular} el día que "
                    f"compraste — no el total. Lo necesitamos para saber "
                    f"cuántas {nombre_plural} tenés."
                ),
            )

        # Preview en vivo: unidades + cuánto valdría hoy
        if monto_puesto > 0 and precio_compra > 0:
            unidades_prev = monto_puesto / precio_compra
            from .market_data import get_precio_dia
            precio_hoy_prev = get_precio_dia(tk, tipo_id)
            if precio_hoy_prev and precio_hoy_prev > 0:
                valor_hoy_prev = unidades_prev * precio_hoy_prev
                pnl_prev = valor_hoy_prev - monto_puesto
                pnl_pct_prev = (pnl_prev / monto_puesto) * 100
                signo_prev = "+" if pnl_prev >= 0 else ""
                msg_prev = (
                    f"💡 Tendrías **{unidades_prev:,.2f} {nombre_plural}**. "
                    f"Hoy valdrían **${valor_hoy_prev:,.0f}** — "
                    f"{signo_prev}${pnl_prev:,.0f} "
                    f"({signo_prev}{pnl_pct_prev:.2f}%)."
                )
                (st.success if pnl_prev >= 0 else st.error)(msg_prev)
            else:
                st.info(
                    f"💡 Serían **{unidades_prev:,.2f} {nombre_plural}**. "
                    "Todavía no tenemos el precio de hoy de este activo — "
                    "lo vas a ver apenas esté disponible."
                )

    else:
        # ─────────── CAMINO MANUAL: monto + valor de hoy editable ───────────
        st.caption(
            "Decinos cuánto pusiste y, si lo sabés, cuánto vale hoy. "
            "Ese valor lo podés editar vos cuando quieras."
        )

        col_monto, col_hoy = st.columns(2)
        with col_monto:
            monto_puesto = st.number_input(
                "💵 ¿Cuánto pusiste? (ARS)",
                min_value=0.0,
                step=1000.0,
                value=0.0,
                key=f"upf_man_monto_{tk}_{tipo_id}",
                help="Lo que pusiste cuando compraste este activo.",
            )
        with col_hoy:
            valor_hoy_manual = st.number_input(
                "💎 ¿Cuánto vale hoy? (ARS, opcional)",
                min_value=0.0,
                step=1000.0,
                value=0.0,
                key=f"upf_man_hoy_{tk}_{tipo_id}",
                help=(
                    "Lo que ves en tu broker como 'valor actual' o "
                    "'tenencia'. Si no lo sabés, dejalo en 0 — asumimos "
                    "que vale lo que pusiste."
                ),
            )

        # Si cargó ambos, mostrar ganancia/pérdida
        if monto_puesto > 0 and valor_hoy_manual > 0:
            pnl_man = valor_hoy_manual - monto_puesto
            pnl_pct_man = (pnl_man / monto_puesto) * 100
            signo_man = "+" if pnl_man >= 0 else ""
            msg_man = (
                f"💡 **Ganancia / pérdida:** {signo_man}${pnl_man:,.0f} "
                f"({signo_man}{pnl_pct_man:.2f}%)"
            )
            (st.success if pnl_man >= 0 else st.error)(msg_man)

    # ─── SANITY CHECK DE MAGNITUD ────────────────────────────────
    # Chequeo sobre lo que el usuario dice que puso. En el camino vivo
    # el valor de hoy lo da el mercado (no se bloquea por eso); en el
    # manual chequeamos también el valor de hoy cargado a mano.
    if modo_carga == "vivo":
        valor_para_check = monto_puesto
    else:
        valor_para_check = valor_hoy_manual if valor_hoy_manual > 0 else monto_puesto

    bloqueado_por_sanity = False
    mensaje_bloqueo = ""

    if valor_para_check > HARD_BLOCK_ARS:
        bloqueado_por_sanity = True
        mensaje_bloqueo = (
            f"🚫 Estás cargando ${valor_para_check:,.0f} ARS en un solo activo. "
            f"Valores arriba de ${HARD_BLOCK_ARS:,.0f} ARS son muy raros — "
            f"revisá si se te corrió la coma."
        )
    elif valor_para_check > SOFT_WARNING_ARS:
        st.warning(
            f"⚠️ **Ojo:** estás cargando ${valor_para_check:,.0f} ARS en este "
            f"activo. Si es correcto, seguí — si no, revisá los números."
        )

    # Ratio check del camino manual: el valor de hoy no puede ser un
    # múltiplo absurdo de lo que se puso (señal de error de tipeo).
    if (modo_carga == "manual" and monto_puesto > 0 and valor_hoy_manual > 0
            and valor_hoy_manual / monto_puesto > RATIO_VALOR_MONTO_MAX):
        bloqueado_por_sanity = True
        multiplicador = valor_hoy_manual / monto_puesto
        mensaje_bloqueo = (
            f"🚫 Estás cargando que este activo multiplicó por "
            f"{multiplicador:.0f}x lo que pusiste. Eso es muy raro — "
            f"revisá los montos."
        )

    if bloqueado_por_sanity:
        st.error(mensaje_bloqueo)

    # ─── Botón de agregar ────────────────────────────────────────
    st.markdown("")

    if st.button(
        "➕ Agregar a mi portafolio",
        type="primary",
        use_container_width=True,
        key=f"upf_add_btn_{tk}_{tipo_id}",
        disabled=bloqueado_por_sanity,
    ):
        if modo_carga == "vivo":
            if monto_puesto <= 0:
                st.error("Tenés que poner cuánto pusiste en este activo.")
            elif precio_compra <= 0:
                st.error(
                    "Tenés que poner a qué precio compraste — lo necesitamos "
                    "para seguir cuánto vale hoy. Si no lo sabés, tildá "
                    "'No sé a qué precio compré este activo'."
                )
            else:
                from .market_data import get_precio_dia
                precio_hoy = get_precio_dia(tk, tipo_id)
                nuevo_activo = crear_activo(
                    tipo=tipo_id,
                    ticker=tk,
                    nombre=activo_elegido["nombre"],
                    monto_invertido_ars=monto_puesto,
                    modo="vivo",
                    precio_compra_ars=precio_compra,
                    precio_actual_ars=precio_hoy if (precio_hoy and precio_hoy > 0) else None,
                )
                st.session_state["user_portfolio_activos"].append(nuevo_activo)
                _persistir_portafolio()
                st.success(f"✅ {activo_elegido['nombre']} agregado a tu cartera")
                st.rerun()
        else:
            if monto_puesto <= 0:
                st.error("Tenés que poner cuánto pusiste en este activo.")
            else:
                nuevo_activo = crear_activo(
                    tipo=tipo_id,
                    ticker=tk,
                    nombre=activo_elegido["nombre"],
                    monto_invertido_ars=monto_puesto,
                    modo="manual",
                    valor_actual_directo=valor_hoy_manual if valor_hoy_manual > 0 else None,
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

    # Agrupar por ticker primero — si el mismo ticker está cargado
    # múltiples veces (ej. 2 compras de la misma ON en momentos
    # distintos), sumamos sus valores para mostrar UN solo slice
    # con el peso total de ese ticker.
    valores_por_ticker = {}
    for a in activos:
        valor = calcular_valor_actual(a) or 0
        if valor > 0:
            ticker = a.get("ticker", "?")
            valores_por_ticker[ticker] = valores_por_ticker.get(ticker, 0) + valor

    # Si después de agrupar queda 1 solo ticker, el donut sería
    # "TICKER 100%" — no agrega información, mejor no mostrarlo.
    if len(valores_por_ticker) < 2:
        return

    labels = list(valores_por_ticker.keys())
    values = list(valores_por_ticker.values())

    # Paleta de azules/violetas para variantes dentro de UNA categoría
    # (no usar la paleta del 6C porque esos colores son por categoría,
    # acá necesitamos diferenciación dentro de la misma categoría)
    PALETA_INTRA = [
        "#60a5fa",  # azul
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
    st.plotly_chart(fig, use_container_width=True, config={"staticPlot": True})


def _user_asset_card_html(activo: dict, color: str) -> str:
    """
    HTML de la sub-card de UN activo del usuario, con el mismo estilo
    (clases .asset-detail-card / .adc-*) que las cards de la pantalla
    "Composición de su cartera". Muestra valor actual + invertido + P&L.
    """
    from .user_portfolio import calcular_pnl, costo_invertido
    from .universo_instrumentos import get_descripcion

    pnl = calcular_pnl(activo)
    invertido = costo_invertido(activo)
    valor = pnl["valor_actual"]
    nombre = activo.get("nombre", "?")
    ticker = activo.get("ticker", "")
    descripcion = get_descripcion(ticker)
    desc_html = (
        f'<div class="adc-desc">{descripcion}</div>' if descripcion else ''
    )

    if pnl["pnl_ars"] is not None:
        signo = "+" if pnl["pnl_ars"] >= 0 else ""
        pnl_col = "#22c55e" if pnl["pnl_ars"] >= 0 else "#ef4444"
        pnl_html = (
            f' &nbsp;·&nbsp; <span style="color:{pnl_col};font-weight:600;">'
            f'{signo}${pnl["pnl_ars"]:,.0f} ({signo}{pnl["pnl_pct"]:.2f}%)</span>'
        )
    else:
        pnl_html = (
            ' &nbsp;·&nbsp; <span style="color:rgba(255,255,255,0.4);">'
            'sin dato de ganancia</span>'
        )

    return (
        f'<div class="asset-detail-card" style="border-left-color:{color};">'
        f'  <div class="adc-top">'
        f'    <div class="adc-title-wrap">'
        f'      <div class="adc-title">{nombre}'
        f'        <span class="adc-ticker-badge">{ticker}</span>'
        f'      </div>'
        f'    </div>'
        f'    <div class="adc-right">'
        f'      <div class="adc-pct">${valor:,.0f}</div>'
        f'      <div class="adc-amt">valor actual</div>'
        f'    </div>'
        f'  </div>'
        f'  {desc_html}'
        f'  <div class="adc-meta" style="margin-top:0.4rem;">'
        f'Invertido ${invertido:,.0f}{pnl_html}</div>'
        f'</div>'
    )


def _render_portafolio_html(activos: list):
    """
    Renderiza el portafolio del usuario como HTML puro estilo
    "Composición de su cartera": cada categoría es un <details> nativo
    con border accent, % gigante y sub-cards de activos anidadas.

    Categoría abierta por default si tiene 2+ activos o si es la única.
    """
    from .user_portfolio import (
        agrupar_activos_por_categoria,
        NOMBRES_CATEGORIA,
        DESCRIPCIONES_CATEGORIA,
        get_tipo_info,
    )
    from .comparison_renderer import COLORES_CATEGORIA

    grupos = agrupar_activos_por_categoria(activos)
    if not grupos:
        return

    html_parts = []
    for grupo in grupos:
        tipo_id = grupo["tipo"]
        cantidad = grupo["cantidad"]
        pct = grupo["porcentaje_cartera"]

        tipo_info = get_tipo_info(tipo_id)
        icono = tipo_info.get("icono", "📦") if tipo_info else "📦"
        nombre_categoria = NOMBRES_CATEGORIA.get(tipo_id) or (
            tipo_info.get("label", tipo_id) if tipo_info else tipo_id
        )
        descripcion = DESCRIPCIONES_CATEGORIA.get(tipo_id, "")
        color = COLORES_CATEGORIA.get(tipo_id, "#60a5fa")

        sufijo = f"{cantidad} {'activo' if cantidad == 1 else 'activos'}"
        desc_line = f"{descripcion}  ·  {sufijo}" if descripcion else sufijo

        abierto = " open" if (cantidad >= 2 or len(grupos) == 1) else ""
        cards = "".join(_user_asset_card_html(a, color) for a in grupo["activos"])

        html_parts.append(
            f'<details class="cat-exp"{abierto}>'
            f'<summary class="cat-exp-summary">'
            f'  <div class="cat-l1-card" style="border-left-color:{color};">'
            f'    <div class="cat-l1-body">'
            f'      <div class="cat-l1-name">{icono}&nbsp; {nombre_categoria}</div>'
            f'      <div class="cat-l1-desc">{desc_line}</div>'
            f'    </div>'
            f'    <div class="cat-l1-right">'
            f'      <div class="cat-l1-pct" style="color:{color};">{pct:.1f}%</div>'
            f'      <div class="cat-l1-pct-sub">de tu cartera</div>'
            f'    </div>'
            f'    <span class="cat-exp-chevron">›</span>'
            f'  </div>'
            f'</summary>'
            f'<div class="cat-exp-body" style="border-left-color:{color};">'
            f'  {cards}'
            f'</div>'
            f'</details>'
        )

    st.markdown("\n".join(html_parts), unsafe_allow_html=True)


def _render_modo_editar(activos: list):
    """
    Modo edición: cada activo se muestra con la MISMA card linda de la
    vista normal (HTML) + un botón 🗑️ al costado para sacarlo. El
    borrar es un widget de Streamlit y no puede ir dentro del HTML, por
    eso va en una columna aparte.
    """
    from .comparison_renderer import COLORES_CATEGORIA

    st.caption(
        "Tocá el 🗑️ de un activo para sacarlo de tu cartera. "
        "Cuando termines, volvé a la vista normal."
    )
    for activo in activos:
        color = COLORES_CATEGORIA.get(activo.get("tipo"), "#60a5fa")
        col_card, col_del = st.columns([11, 1], vertical_alignment="center")
        with col_card:
            st.markdown(_user_asset_card_html(activo, color), unsafe_allow_html=True)
        with col_del:
            if st.button(
                "🗑️",
                key=f"upf_del_{activo['id']}",
                help="Sacar este activo de tu cartera",
            ):
                st.session_state["user_portfolio_activos"] = [
                    a for a in st.session_state["user_portfolio_activos"]
                    if a["id"] != activo["id"]
                ]
                _persistir_portafolio()
                st.rerun()
        st.markdown('<div style="margin-bottom:0.6rem;"></div>', unsafe_allow_html=True)

    st.markdown('<div style="margin-top: 0.5rem;"></div>', unsafe_allow_html=True)
    _, col_listo = st.columns([3, 2])
    with col_listo:
        if st.button(
            "✓ Terminar de editar",
            key="_upf_btn_fin_editar",
            use_container_width=True,
            type="primary",
        ):
            st.session_state["_upf_modo_editar"] = False
            st.rerun()


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
    color_accent = COLORES_CATEGORIA.get(tipo_id, "#60a5fa")

    sufijo_count = f"{cantidad} {'activo' if cantidad == 1 else 'activos'}"

    # State del toggle de expandido en session_state
    clave_estado = f"_cat_card_expandida_{tipo_id}"
    if clave_estado not in st.session_state:
        st.session_state[clave_estado] = cantidad >= 2

    expandida = st.session_state[clave_estado]

    # ── HEADER DECORATIVO: border accent + título + descripción + % ──
    # Layout flex: izquierda título/descripción, derecha % gigante.
    # margin-bottom 0 para conectarse visualmente con el botón toggle
    # que viene debajo (CSS del tertiary neutraliza el botón a estilo
    # link, así que se ve como un caption clickeable al pie de la card).
    st.markdown(
        f'<div style="border-left: 3px solid {color_accent}; '
        f'background: rgba(255,255,255,0.025); '
        f'border-radius: 10px; '
        f'padding: 1rem 1.25rem 0.875rem 1.25rem; '
        f'margin-bottom: 0; '
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
                f'<span style="color: #60a5fa; font-weight: 600; font-family: ui-monospace, monospace;">{activo["ticker"]}</span>'
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
            type="secondary",
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
