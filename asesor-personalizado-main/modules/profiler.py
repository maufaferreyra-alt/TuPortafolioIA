"""
Cuestionario de perfil de inversor — rediseñado para principiantes reales.
Lenguaje cotidiano, situaciones concretas, sin tecnicismos.
"""

import streamlit as st
import urllib.request
import json as _json


@st.cache_data(ttl=300)
def _get_mep_rate() -> tuple[float, bool]:
    """Obtiene el dólar MEP en tiempo real desde dolarapi.com. TTL 5 min."""
    try:
        req = urllib.request.Request(
            "https://dolarapi.com/v1/dolares/bolsa",
            headers={"User-Agent": "Mozilla/5.0"},
        )
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = _json.loads(resp.read())
            rate = float(data.get("venta") or data.get("compra") or 0)
            if rate > 0:
                return rate, True
    except Exception:
        pass
    return 1100.0, False


QUESTIONS = [
    {
        "id": "motivation",
        "emoji": "🤔",
        "step": "Sección 1 de 8",
        "title": "¿Qué te trae acá?",
        "hint": "Elegí la opción que mejor refleje tu situación.",
        "options": [
            ("La inflación me come los ahorros, quiero proteger valor", 0),
            ("Tengo plata quieta y quiero que rinda algo", 1),
            ("Quiero hacer crecer mi plata, entiendo el riesgo", 2),
            ("Busco máxima rentabilidad, asumo el riesgo", 3),
        ],
    },
    {
        "id": "loss_reaction",
        "emoji": "📉",
        "step": "Sección 2 de 8",
        "title": "Invertís $500.000 y al mes valen $430.000. ¿Qué hacés?",
        "hint": "Estas caídas son normales. Sé honesto.",
        "options": [
            ("Los saco de inmediato, no puedo verlo", 0),
            ("Saco la mitad para no perder más", 1),
            ("No hago nada, espero la recuperación", 2),
            ("Meto más plata, está más barato", 3),
        ],
    },
    {
        "id": "horizon",
        "emoji": "📅",
        "step": "Sección 3 de 8",
        "title": "¿En cuánto tiempo vas a necesitar la plata?",
        "hint": "Pensá en tus planes (viaje, vivienda, retiro).",
        "options": [
            ("Menos de 1 año, puedo necesitarla pronto", 0),
            ("1 a 3 años, tengo algo planificado", 1),
            ("3 a 7 años, construyo a mediano plazo", 2),
            ("Largo plazo, no la voy a tocar en años", 3),
        ],
    },
    {
        "id": "income_stability",
        "emoji": "💼",
        "step": "Sección 4 de 8",
        "title": "¿Cómo son tus ingresos cada mes?",
        "hint": "Determina tu capacidad de mantener la inversión.",
        "options": [
            ("Irregulares, nunca sé cuánto voy a cobrar", 0),
            ("Varían bastante, dependo de clientes", 1),
            ("Sueldo fijo, estable y predecible", 2),
            ("Muy estables, varias fuentes de ingreso", 3),
        ],
    },
    {
        "id": "emergency_fund",
        "emoji": "🛡️",
        "step": "Sección 5 de 8",
        "title": "Si surgiera un gasto inesperado, ¿podrías cubrirlo sin tocar esta inversión?",
        "hint": "El fondo de emergencia es la base de toda estrategia.",
        "options": [
            ("No, no tengo nada extra guardado", 0),
            ("Algo, alcanza para 1 o 2 meses", 1),
            ("Sí, tengo 3 a 6 meses guardados", 2),
            ("Sí, tengo más de 6 meses cubiertos", 3),
        ],
    },
    {
        "id": "risk_appetite",
        "emoji": "🎲",
        "step": "Sección 6 de 8",
        "title": "Si tuvieras que elegir, ¿con cuál te quedás?",
        "hint": "No hay respuesta correcta. Reflexioná sobre tu tolerancia real.",
        "options": [
            ("Ganar 5% fijo al año, sin sorpresas", 0),
            ("Hasta 15%, aceptando perder 5% algún año", 1),
            ("Hasta 30%, aceptando perder 20% algún año", 2),
            ("Hasta 60%, aceptando perder 40% algún año", 3),
        ],
    },
    {
        "id": "experience",
        "emoji": "📚",
        "step": "Sección 7 de 8",
        "title": "¿Cuánto sabés de inversiones?",
        "hint": "No hay respuesta incorrecta — solo nos ayuda a personalizar.",
        "options": [
            ("Prácticamente nada, nunca invertí", 0),
            ("Solo conozco el plazo fijo o Mercado Pago", 1),
            ("Algo: escuché de CEDEARs, MEP, fondos", 2),
            ("Bastante: operé acciones, bonos o cripto", 3),
        ],
    },
    {
        "id": "mindset",
        "emoji": "🧠",
        "step": "Sección 8 de 8",
        "title": "¿Con cuál frase te identificás más?",
        "hint": "Elegí la que mejor represente tu filosofía.",
        "options": [
            ("Prefiero dormir tranquilo que ganar más", 0),
            ("Busco equilibrio: seguridad con crecimiento", 1),
            ("Pienso a largo plazo, no me asustan las caídas", 2),
            ("Maximizar patrimonio, el riesgo es parte", 3),
        ],
    },
]

HORIZON_MAP = {
    "Menos de 1 año, puedo necesitarla pronto": 1,
    "1 a 3 años, tengo algo planificado":        2,
    "3 a 7 años, construyo a mediano plazo":     5,
    "Largo plazo, no la voy a tocar en años":   10,
}

PROFILES = {
    "conservador": {
        "emoji": "🟢",
        "label": "Inversor Conservador",
        "color": "#22c55e",
        "tagline": "Su prioridad es la preservación del capital. Una decisión sólida.",
        "explanation": (
            "Usted prioriza la seguridad por encima de la rentabilidad máxima. "
            "No desea exponerse a caídas significativas, lo cual es completamente válido — "
            "especialmente si requiere el capital en el corto plazo o está comenzando. "
            "Una cartera conservadora no es sinónimo de bajo rendimiento: "
            "es la elección de quien tiene claras sus prioridades financieras."
        ),
        "what_means": [
            "📦 La mayor parte del capital se destina a instrumentos de alta seguridad",
            "💵 Protección contra la inflación y la devaluación del peso",
            "🔒 Baja volatilidad — el saldo no presenta oscilaciones significativas",
            "📈 Rendimiento moderado, consistente y predecible",
        ],
        "first_steps": [
            "Comience con un Fondo Money Market en IOL o Mercado Pago (rescate en el día)",
            "Adquiera Dólar MEP para dolarizar una parte de su capital",
            "Incorpore ONs corporativas en USD (Pampa Energía, TGS) para renta dolarizada",
        ],
    },
    "moderado": {
        "emoji": "🟡",
        "label": "Inversor Moderado",
        "color": "#f59e0b",
        "tagline": "Busca un equilibrio inteligente entre seguridad y crecimiento.",
        "explanation": (
            "Usted desea que su capital crezca sin asumir riesgos excesivos. "
            "Está dispuesto a tolerar variaciones temporales si eso implica "
            "mejores resultados a mediano plazo. "
            "Es el perfil más frecuente y, para muchos inversores, el más adecuado: "
            "combina protección con crecimiento real."
        ),
        "what_means": [
            "⚖️ Mezcla de activos seguros y activos de crecimiento",
            "🌎 Diversificación entre pesos, dólares y activos internacionales",
            "📊 Rendimiento superior al plazo fijo con riesgo controlado",
            "📉 Puede haber meses negativos, pero el largo plazo es positivo",
        ],
        "first_steps": [
            "Adquiera Dólar MEP y sume ONs corporativas en USD para la parte dolarizada",
            "Incorpore el CEDEAR del S&P 500 (SPY) para crecimiento en pesos al tipo de cambio",
            "Reserve un fondo de liquidez en Money Market para emergencias",
        ],
    },
    "estable": {
        "emoji": "🔵",
        "label": "Inversor Balanceado",
        "color": "#60a5fa",
        "tagline": "Rendimiento superior al plazo fijo con exposición al riesgo controlada.",
        "explanation": (
            "Usted desea que su capital rinda más que un plazo fijo "
            "sin exponerse a caídas significativas. "
            "Es el punto intermedio ideal: mayor rendimiento que la caja de ahorro "
            "sin la volatilidad del mercado de renta variable. "
            "Recomendado para quien inicia su proceso de diversificación."
        ),
        "what_means": [
            "💵 Mayoría en dólares y bonos de empresas sólidas",
            "📈 Rendimiento esperado superior al plazo fijo tradicional",
            "🛡️ Baja volatilidad — el saldo no presenta variaciones significativas mes a mes",
            "🌎 Exposición moderada al mercado global para potenciar el crecimiento",
        ],
        "first_steps": [
            "Adquiera Dólar MEP en IOL o PPI — operación inmediata, sin límite mensual",
            "Invierta en ONs corporativas de Pampa Energía o MercadoLibre",
            "Incorpore el CEDEAR del S&P 500 (SPY) para crecimiento en pesos",
        ],
    },
    "agresivo": {
        "emoji": "🔴",
        "label": "Inversor Agresivo",
        "color": "#ef4444",
        "tagline": "Horizonte largo plazo con foco en maximizar el rendimiento.",
        "explanation": (
            "Usted comprende que para obtener mayor rentabilidad debe asumir mayor riesgo. "
            "Está dispuesto a tolerar caídas significativas sin reaccionar impulsivamente, "
            "porque su horizonte es extenso y su objetivo es maximizar el crecimiento patrimonial. "
            "Importante: esto no implica especulación — significa invertir "
            "con estrategia en instrumentos de alto potencial."
        ),
        "what_means": [
            "🚀 Alta exposición a acciones argentinas e internacionales",
            "⚡ Mayor volatilidad — caídas de 20-30% son parte del proceso, no una señal de venta",
            "💎 Potencial de rendimiento muy superior al largo plazo",
            "🧩 Incluye tecnología global, mercados emergentes y acciones argentinas de alto potencial",
        ],
        "first_steps": [
            "Adquiera Dólar MEP como base dolarizada antes de comprar renta variable",
            "Incorpore el ETF QQQ para acceso a tecnología global desde Argentina",
            "Agregue acciones argentinas de alto potencial: YPF, Galicia, Vista Energy",
        ],
    },
}


def _score_to_profile(score: int, max_score: int) -> str:
    ratio = score / max_score
    if ratio < 0.26:       # 0-6 pts: quiere solo seguridad
        return "conservador"
    elif ratio < 0.46:     # 7-11 pts: algo mejor que plazo fijo pero sin sustos
        return "estable"
    elif ratio < 0.68:     # 12-16 pts: equilibrio crecimiento/seguridad
        return "moderado"
    else:                  # 17-24 pts: maximizar crecimiento
        return "agresivo"


def render_profiler() -> dict | None:
    answers     = st.session_state.get("answers", {})
    q_ids       = [q["id"] for q in QUESTIONS]
    answered    = len([k for k in answers if k in q_ids])
    has_capital = "capital" in answers
    has_reveal  = answers.get("_reveal_done", False)
    total_steps = len(QUESTIONS) + 1  # preguntas + capital

    # ── Barra de progreso ──────────────────────────────────────────────────────
    if not has_reveal:
        progress_pct = int(min((answered + (1 if has_capital else 0)) / total_steps, 1.0) * 100)
        st.markdown(f"""<div class="progress-wrap">
<div class="progress-label">Progreso del cuestionario</div>
<div class="progress-track"><div class="progress-fill" style="width:{progress_pct}%"></div></div>
</div>""", unsafe_allow_html=True)

    # ── Preguntas del cuestionario ─────────────────────────────────────────────
    if answered < len(QUESTIONS):
        q = QUESTIONS[answered]

        st.markdown(f"""<div class="profiler-card">
<div class="q-emoji">{q['emoji']}</div>
<h3 class="q-title">{q['title']}</h3>
<p class="hint">{q['hint']}</p>
</div>""", unsafe_allow_html=True)

        col_q, _ = st.columns([2, 1])
        with col_q:
            option_labels = [o[0] for o in q["options"]]
            default_index = 0
            if q["id"] == "experience" and st.session_state.get("pre_experience"):
                pre_exp = st.session_state.get("pre_experience")
                if pre_exp in option_labels:
                    default_index = option_labels.index(pre_exp)
            selected = st.radio(
                label="Opción",
                options=option_labels,
                key=f"radio_{q['id']}",
                index=default_index,
                label_visibility="collapsed",
            )

            col_b1, col_b2 = st.columns([1, 2])
            with col_b1:
                if answered > 0 and st.button("← Atrás", key=f"back_{q['id']}"):
                    prev_id = QUESTIONS[answered - 1]["id"]
                    answers.pop(prev_id, None)
                    st.session_state.answers = answers
                    st.rerun()
            with col_b2:
                label = "Continuar →" if answered < len(QUESTIONS) - 1 else "Última sección →"
                if st.button(label, key=f"next_{q['id']}", use_container_width=True):
                    answers[q["id"]] = selected
                    st.session_state.answers = answers
                    st.rerun()

        return None

    # ── Pregunta de capital ────────────────────────────────────────────────────
    if not has_capital:
        st.markdown("""<div class="profiler-card">
<div class="q-emoji">💵</div>
<h3 class="q-title">¿Con qué capital desea comenzar a invertir?</h3>
<p class="hint">No existe un mínimo perfecto. Con cualquier monto puede invertir de forma inteligente.</p>
</div>""", unsafe_allow_html=True)

        _mep_rate, _mep_live = _get_mep_rate()
        _mep_tag = f"${_mep_rate:,.0f}/USD · tiempo real" if _mep_live else f"~${_mep_rate:,.0f}/USD · estimado"

        col_q, _ = st.columns([2, 1])
        with col_q:
            currency_choice = st.radio(
                "Moneda",
                ["Pesos argentinos (ARS)", "Dólares (USD)"],
                key="currency_choice",
                horizontal=True,
            )

            if "Pesos" in currency_choice:
                amount_ars = st.number_input(
                    "Monto en pesos",
                    min_value=10_000,
                    max_value=500_000_000,
                    value=500_000,
                    step=10_000,
                    format="%d",
                    key="capital_ars",
                    label_visibility="collapsed",
                )
                st.caption(f"💵 Aproximadamente USD {amount_ars / _mep_rate:,.0f} al tipo de cambio MEP ({_mep_tag})")
                capital_usd      = amount_ars / _mep_rate
                capital_display  = f"${amount_ars:,.0f} ARS"
                currency         = "ARS"
                capital_original = float(amount_ars)
            else:
                capital_usd = st.number_input(
                    "Monto en USD",
                    min_value=100,
                    max_value=10_000_000,
                    value=5_000,
                    step=100,
                    key="capital_usd_input",
                    label_visibility="collapsed",
                )
                st.caption(f"💵 USD {capital_usd:,.0f}")
                capital_display  = f"USD {capital_usd:,.0f}"
                currency         = "USD"
                capital_original = float(capital_usd)

            col_b1, col_b2 = st.columns([1, 2])
            with col_b1:
                if st.button("← Atrás", key="back_capital"):
                    prev_id = QUESTIONS[-1]["id"]
                    answers.pop(prev_id, None)
                    st.session_state.answers = answers
                    st.rerun()
            with col_b2:
                if st.button("Ver mi Perfil de Inversor", key="finish_btn", use_container_width=True):
                    answers["capital"]          = float(capital_usd)
                    answers["capital_display"]  = capital_display
                    answers["currency"]         = currency
                    answers["capital_original"] = capital_original
                    st.session_state.answers    = answers
                    st.rerun()

        return None

    # ── Calcular perfil ────────────────────────────────────────────────────────
    total_score = 0
    max_score   = len(QUESTIONS) * 3

    for q in QUESTIONS:
        raw_val   = answers.get(q["id"])
        score_val = next((s for lbl, s in q["options"] if lbl == raw_val), 0)
        total_score += score_val

    risk_profile = _score_to_profile(total_score, max_score)
    p            = PROFILES[risk_profile]

    # ── Pantalla de reveal del perfil ──────────────────────────────────────────
    if not has_reveal:
        pct_score = int((total_score / max_score) * 100)

        st.markdown(f"""<div class="reveal-card">
<div class="reveal-badge" style="border-color:{p['color']};color:{p['color']};">
  {p['emoji']} {p['label']}
</div>
<p class="reveal-tagline">{p['tagline']}</p>
<div class="explain-outer"><p class="reveal-explanation">{p['explanation']}</p></div>
</div>""", unsafe_allow_html=True)

        what_means_html  = "".join(f'<div class="reveal-item">{item}</div>' for item in p['what_means'])
        first_steps_html = "".join(f'<div class="reveal-item">✅ {step}</div>' for step in p['first_steps'])
        st.markdown(f"""<div class="reveal-columns">
<div class="reveal-section">
<div class="reveal-section-title">📋 Implicancias para su cartera</div>
{what_means_html}
</div>
<div class="reveal-section">
<div class="reveal-section-title">📌 Primeros pasos sugeridos</div>
{first_steps_html}
</div>
</div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        _, col_cta, _ = st.columns([1, 2, 1])
        with col_cta:
            if st.button("Ver Cartera Sugerida →", key="to_portfolio", use_container_width=True):
                answers["_reveal_done"] = True
                st.session_state.answers = answers
                st.rerun()
        return None

    # ── Devolver perfil al app principal ──────────────────────────────────────
    horizon_label = answers.get("horizon", "3 a 7 años, construyo a mediano plazo")
    horizon_years = HORIZON_MAP.get(horizon_label, 5)
    capital       = answers.get("capital", 5_000.0)
    p_data        = PROFILES[risk_profile]

    return {
        "risk_profile":       risk_profile,
        "risk_score":         total_score,
        "risk_max":           max_score,
        "horizon":            horizon_years,
        "capital":            capital,
        "capital_display":    answers.get("capital_display", f"USD {capital:,.0f}"),
        "currency":           answers.get("currency", "USD"),
        "capital_original":   answers.get("capital_original", capital),
        "income_stability":   answers.get("income_stability", ""),
        "loss_tolerance":     answers.get("loss_reaction", ""),
        "objective":          answers.get("motivation", ""),
        "experience":         answers.get("experience", ""),
        "emergency_fund":     answers.get("emergency_fund", ""),
        "profile_label":      p_data["label"],
        "profile_tagline":    p_data["tagline"],
        "profile_explanation":p_data["explanation"],
        "raw_answers":        answers,
    }
