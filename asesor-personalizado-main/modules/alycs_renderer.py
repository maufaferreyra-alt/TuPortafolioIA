"""
Renderizado de la sección comparativa de ALyCs.
Aparece al final del flujo, después de los próximos pasos.

Cada broker es un st.expander colapsable — arranca cerrado para no
saturar al usuario con información; se abre el que le interese. El
header del expander ya muestra un preview escaneable (nombre, tagline,
si tiene asesor humano).
"""

import streamlit as st
from .alycs_data import ALYCS, generar_mensaje_para_asesor


def _alyc_detail_html(alyc: dict) -> str:
    """HTML del contenido interno de cada card (dentro del expander).

    Se devuelve como string concatenado SIN indentación: si las líneas
    arrancaran con 4+ espacios, Markdown lo trataría como bloque de
    código y lo mostraría como texto crudo.
    """
    ventajas_html = "".join(f"<li>{v}</li>" for v in alyc["ventajas"])
    desventajas_html = "".join(f"<li>{d}</li>" for d in alyc["desventajas"])

    return (
        '<div class="alyc-card-body">'
        # ── Specs tipo tabla ──
        '<div class="alyc-specs-table">'
        '<div class="alyc-spec-row">'
        '<span class="alyc-spec-label">Comisión CEDEARs</span>'
        f'<span class="alyc-spec-value">{alyc["comision_cedears"]}</span></div>'
        '<div class="alyc-spec-row">'
        '<span class="alyc-spec-label">Comisión bonos</span>'
        f'<span class="alyc-spec-value">{alyc["comision_bonos"]}</span></div>'
        '<div class="alyc-spec-row">'
        '<span class="alyc-spec-label">Custodia (lo que te cobran por tener tu plata ahí)</span>'
        f'<span class="alyc-spec-value">{alyc["custodia"]}</span></div>'
        '<div class="alyc-spec-row">'
        '<span class="alyc-spec-label">Mínimo para empezar</span>'
        f'<span class="alyc-spec-value">{alyc["minimo_apertura"]}</span></div>'
        '<div class="alyc-spec-row">'
        '<span class="alyc-spec-label">Plataforma</span>'
        f'<span class="alyc-spec-value">{alyc["plataforma"]}</span></div>'
        '</div>'
        # ── Pros / Cons ──
        '<div class="alyc-pros-cons-grid">'
        '<div class="alyc-pros-box">'
        '<div class="alyc-section-title alyc-pros-title">'
        '<span class="alyc-section-icon">✓</span> Lo bueno</div>'
        f'<ul>{ventajas_html}</ul></div>'
        '<div class="alyc-cons-box">'
        '<div class="alyc-section-title alyc-cons-title">'
        '<span class="alyc-section-icon">!</span> A tener en cuenta</div>'
        f'<ul>{desventajas_html}</ul></div>'
        '</div>'
        # ── Ideal para ──
        '<div class="alyc-mejor-para">'
        '<span class="alyc-mejor-para-label">💡 Ideal para</span>'
        f'<span class="alyc-mejor-para-text">{alyc["mejor_para"]}</span></div>'
        '</div>'
    )


def render_alycs_section(portfolio: dict, profile: dict):
    """Renderiza la sección completa de comparación de brokers."""

    # Header con HTML inline en una sola estructura (sin la clase
    # .section-header ni saltos de línea): el HTML multilínea con <p>
    # lo re-envolvía el procesador de Markdown de Streamlit y rompía
    # el centrado. Inline + texto continuo = centrado confiable.
    st.markdown(
        '<div style="text-align:center; max-width:680px; '
        'margin:2.5rem auto 1.25rem auto;">'
        '<div style="font-size:0.9rem; font-weight:600; '
        'color:#60a5fa; margin-bottom:0.4rem;">'
        '💡 Te facilitamos el paso 1, así no pensás tanto'
        '</div>'
        '<div style="font-size:1.75rem; font-weight:700; color:#f5f6fa; '
        'margin-bottom:0.6rem; letter-spacing:-0.01em;">'
        '🏦 ¿Dónde podés invertir tu cartera?'
        '</div>'
        '<div style="font-size:1rem; color:rgba(245,246,250,0.75); '
        'line-height:1.55;">'
        'Sabemos que elegir un broker es confuso. Acá te mostramos las '
        'opciones más usadas en Argentina, con lo bueno y lo no tan bueno '
        'de cada una. No hay una mejor que otra — depende de qué te '
        'conviene a vos.'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Lista de brokers ──────────────────────────────────────────
    # Cada broker es un st.expander colapsable. Para no abrumar a quien
    # nunca invirtió, mostramos solo los primeros y el resto va atrás
    # de un botón "ver más" (reduce estímulos / parálisis de elección).
    # Qué es una ALyC ya está explicado en el Glosario, no hace falta
    # un banner acá.
    _N_VISIBLES = 3
    _mostrar_todas = st.session_state.get("_alycs_mostrar_todas", False)
    _visibles = ALYCS if _mostrar_todas else ALYCS[:_N_VISIBLES]

    for alyc in _visibles:
        # Rótulo sobre Cocos: marca el punto de entrada más fácil para
        # un primerizo. Es sobre facilidad de onboarding, NO un "es el
        # mejor" — todos los brokers son válidos (ver copy del header).
        if alyc["id"] == "cocos":
            st.markdown(
                '<div style="display:inline-block; font-size:0.72rem; '
                'font-weight:600; color:#60a5fa; '
                'background:rgba(96,165,250,0.1); '
                'border:1px solid rgba(96,165,250,0.3); '
                'border-radius:999px; padding:0.15rem 0.7rem; '
                'margin:0.25rem 0 0.35rem 2px;">'
                '✨ Más fácil para arrancar'
                '</div>',
                unsafe_allow_html=True,
            )

        asesor_indicator = (
            "· 👤 con asesor" if alyc.get("tiene_asesor_humano") else "· 💬 solo chat"
        )
        header_label = (
            f"{alyc['logo_emoji']} **{alyc['nombre']}** — "
            f"{alyc['tagline']} {asesor_indicator}"
        )
        with st.expander(header_label):
            st.markdown(_alyc_detail_html(alyc), unsafe_allow_html=True)

            col_a, col_b = st.columns(2)
            with col_a:
                st.link_button(
                    "🌐 Abrir cuenta",
                    alyc["url_apertura"],
                    use_container_width=True,
                )
            with col_b:
                if st.button(
                    "📋 Llevar mi cartera",
                    key=f"llevar_cartera_{alyc['id']}",
                    use_container_width=True,
                ):
                    st.session_state["alyc_seleccionada"] = alyc["id"]
                    st.session_state["mostrar_mensaje_asesor"] = True

    # Toggle ver más / ver menos: el primerizo ve pocas opciones; el
    # que quiere comparar todo, despliega — y puede volver a contraer.
    if len(ALYCS) > _N_VISIBLES:
        if not _mostrar_todas:
            _restantes = len(ALYCS) - _N_VISIBLES
            if st.button(
                f"Ver las demás opciones ({_restantes})",
                key="_alycs_ver_mas_btn",
                use_container_width=True,
            ):
                st.session_state["_alycs_mostrar_todas"] = True
                st.rerun()
        else:
            if st.button(
                "Ver menos opciones",
                key="_alycs_ver_menos_btn",
                use_container_width=True,
            ):
                st.session_state["_alycs_mostrar_todas"] = False
                st.rerun()

    # Mostrar el mensaje pre-armado si se eligió una ALyC
    if st.session_state.get("mostrar_mensaje_asesor"):
        alyc_id = st.session_state.get("alyc_seleccionada")
        alyc = next((a for a in ALYCS if a["id"] == alyc_id), None)

        if alyc:
            st.markdown("---")
            st.markdown(
                f"""<div class="mensaje-asesor-header">
<h3>📨 Tu mensaje para el asesor de {alyc['nombre']}</h3>
<p>
Copiá este texto y pegalo cuando contactes al asesor del broker.
Tiene toda la información de tu cartera para que puedan trabajar juntos.
</p>
</div>""",
                unsafe_allow_html=True,
            )

            mensaje = generar_mensaje_para_asesor(portfolio, profile)
            st.code(mensaje, language=None)

            st.caption(
                "Tip: usá el botoncito de copiar en la esquina derecha del recuadro. "
                "Después abrí la cuenta en el broker, contactá al asesor y pegale este "
                "mensaje. Te va a ahorrar tiempo a vos y al asesor."
            )
