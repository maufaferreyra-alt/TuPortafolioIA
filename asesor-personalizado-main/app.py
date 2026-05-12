"""
FinanzasIA — Asesor Financiero Inteligente
"""

import threading

import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
from datetime import datetime
from modules.ui_config import apply_custom_css, render_header, render_footer
from modules.profiler import render_profiler
from modules.portfolio import build_portfolio
from modules.charts import render_pie_chart, render_evolution_chart, render_bar_simulation, render_allocation_table
from modules.simulator import simulate_portfolio, comparar_vs_alternativas, proyectar_con_aportes
from modules.backtest import run_backtest
from modules.ai_advisor import chat_with_advisor
from modules.glossary import render_glossary, tip, wrap_terms as _wrap_terms

import html as _html_lib


def _safe_with_tips(text: str) -> str:
    """Escapa HTML y aplica tooltips a términos del glosario."""
    return _wrap_terms(_html_lib.escape(str(text)))
from modules.costo_no_invertir import render_cost_of_not_investing, render_cost_results
from modules.methodology import render_methodology, render_how_it_works

_SCORES_MAX_AGE_DAYS = 7   # umbral para auto-actualización


# ── Estado de actualización en segundo plano (persiste entre reruns) ──────────
@st.cache_resource
def _update_state():
    return {"thread": None, "last_result": None}


def _run_scores_background():
    """Descarga fundamentals y recalcula scores. Corre en hilo daemon."""
    errors = []
    try:
        from modules.finviz_scorer import run_and_save as _eq
        _eq()
    except Exception as e:
        errors.append(f"equity: {e}")
    try:
        from modules.bond_scorer import run_and_save as _bonds
        _bonds()
    except Exception as e:
        errors.append(f"bonos: {e}")
    _update_state()["last_result"] = "error" if errors else "ok"


def _score_age(path: str):
    import json as _json
    p = Path(path)
    if not p.exists():
        return None, "⚫ No encontrado"
    # Prefer generated_at from JSON over file mtime (more accurate after manual edits)
    try:
        raw = _json.loads(p.read_text())
        ts  = raw.get("generated_at") or raw.get("as_of")
        if ts:
            dt = datetime.fromisoformat(ts) if "T" in ts else datetime.strptime(ts, "%Y-%m-%d")
            delta = datetime.now() - dt
        else:
            raise ValueError("no timestamp in json")
    except Exception:
        delta = datetime.now() - datetime.fromtimestamp(p.stat().st_mtime)
    days  = delta.days
    hours = delta.seconds // 3600
    if days == 0:
        label = f"hace {hours}h" if hours > 0 else "hace menos de 1h"
        icon  = "🟢"
    elif days <= 3:
        label = f"hace {days}d"
        icon  = "🟢"
    elif days <= 7:
        label = f"hace {days}d"
        icon  = "🟡"
    else:
        label = f"hace {days}d — desactualizado"
        icon  = "🔴"
    return days, f"{icon} {label}"


def _auto_update_if_stale() -> bool:
    """Dispara actualización en hilo de fondo si los scores tienen > 7 días. Retorna True si arrancó."""
    eq_days, _ = _score_age("finviz_scores.json")
    if eq_days is None or eq_days > _SCORES_MAX_AGE_DAYS:
        state = _update_state()
        t = state.get("thread")
        if t is None or not t.is_alive():
            thread = threading.Thread(target=_run_scores_background, daemon=True)
            thread.start()
            state["thread"] = thread
            state["last_result"] = None
            return True
    return False

_CELEBRATION_HTML = """<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
@keyframes confettiFall {
    0%   { transform: translateY(-10px) rotate(0deg);   opacity: 1; }
    100% { transform: translateY(110vh) rotate(720deg); opacity: 0; }
}
@keyframes celebFadeIn  { from { opacity:0; transform:scale(0.92); } to { opacity:1; transform:scale(1); } }
@keyframes celebFadeOut { from { opacity:1; } to { opacity:0; } }
</style>
</head><body style="margin:0;background:transparent;">
<script>
(function() {
    var LS_KEY = 'asesor_celebration_v1';
    try { if (window.parent.localStorage.getItem(LS_KEY)) return; } catch(e) {}
    var doc = window.parent.document;
    var overlay = doc.createElement('div');
    overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(5,8,16,0.93);z-index:99999;display:flex;flex-direction:column;align-items:center;justify-content:center;cursor:pointer;overflow:hidden;animation:celebFadeIn 0.4s ease-out both';
    var style = doc.createElement('style');
    style.textContent = '@keyframes confettiFall{0%{transform:translateY(-10px) rotate(0deg);opacity:1}100%{transform:translateY(110vh) rotate(720deg);opacity:0}}@keyframes celebFadeIn{from{opacity:0;transform:scale(0.92)}to{opacity:1;transform:scale(1)}}@keyframes celebFadeOut{from{opacity:1}to{opacity:0}}';
    doc.head.appendChild(style);
    var colors = ['#4fa3ff','#10d98a','#f0b429','#ff4d6a','#a78bfa','#ffffff','#38bdf8'];
    for (var i = 0; i < 70; i++) {
        var p = doc.createElement('div');
        var left = Math.random() * 100;
        var delay = Math.random() * 2.2;
        var dur = 2.2 + Math.random() * 1.8;
        var size = 5 + Math.random() * 9;
        var isRect = Math.random() > 0.5;
        p.style.cssText = 'position:absolute;left:' + left + '%;top:-20px;width:' + size + 'px;height:' + (isRect ? size * 0.4 : size) + 'px;background:' + colors[i % colors.length] + ';border-radius:' + (isRect ? '2px' : '50%') + ';animation:confettiFall ' + dur + 's ' + delay + 's ease-in forwards;pointer-events:none;';
        overlay.appendChild(p);
    }
    var box = doc.createElement('div');
    box.style.cssText = 'text-align:center;padding:2rem;position:relative;z-index:2;';
    box.innerHTML = '<div style="font-size:4rem;margin-bottom:1rem;filter:drop-shadow(0 0 20px rgba(240,180,41,0.6))">🎉</div><h1 style="font-family:Syne,sans-serif;font-size:clamp(1.6rem,4vw,2.4rem);font-weight:800;color:#eef2ff;margin:0 0 0.8rem;line-height:1.2;letter-spacing:-0.02em;">¡Su cartera personalizada está lista!</h1><p style="font-family:DM Sans,sans-serif;font-size:clamp(0.95rem,2vw,1.15rem);color:#94a3b8;margin:0 0 1.5rem;">Análisis completado en menos de 2 minutos.</p><p style="font-size:0.8rem;color:#475569;">Toque en cualquier lugar para continuar</p>';
    overlay.appendChild(box);
    doc.body.appendChild(overlay);
    try { window.parent.localStorage.setItem(LS_KEY, '1'); } catch(e) {}
    function dismiss() {
        overlay.style.animation = 'celebFadeOut 0.4s ease-in forwards';
        setTimeout(function() { overlay.remove(); style.remove(); }, 420);
    }
    overlay.addEventListener('click', dismiss);
    setTimeout(dismiss, 3000);
})();
</script></body></html>"""

st.set_page_config(
    page_title="TuPortafolioIA · Tu asesor financiero",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

def init_state():
    defaults = {
        "step":                  "intro",
        "profile":               None,
        "portfolio":             None,
        "simulation":            None,
        "chat_history":          [],
        "answers":               {},
        "theme":                 "dark",
        "auto_update_checked":   False,
        "scores_refreshed":      False,   # True cuando la actualización en curso termina
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_state()


# ── Auto-actualización de scores (una sola vez por sesión) ───────────────────
if not st.session_state.auto_update_checked:
    st.session_state.auto_update_checked = True
    _auto_update_if_stale()

# Detectar si el hilo de fondo acaba de terminar
_state = _update_state()
_bg_thread = _state.get("thread")
if (_bg_thread is not None
        and not _bg_thread.is_alive()
        and _state.get("last_result") == "ok"
        and not st.session_state.scores_refreshed):
    st.session_state.scores_refreshed = True

apply_custom_css()
render_header()

# ── Sidebar: frescura de scores y botón de actualización ──────────────────────

with st.sidebar:
    st.markdown("### ⚙️ Scores de mercado")
    eq_days,   eq_label   = _score_age("finviz_scores.json")
    bond_days, bond_label = _score_age("bond_scores.json")
    st.markdown(f"**Equity / CEDEARs:** {eq_label}")
    st.markdown(f"**Bonos ARG:** {bond_label}")

    # Tipo de cambio MEP en vivo
    try:
        from modules.market_data import get_mep_rate as _sidebar_mep
        _live_mep = _sidebar_mep()
        st.markdown(f"**MEP (bolsa):** ${_live_mep:,.0f} ARS/USD")
    except Exception:
        pass

    # Riesgo país en vivo
    try:
        from modules.bond_scorer import _get_riesgo_pais_bps as _sidebar_rp
        _rp = _sidebar_rp()
        if _rp is not None:
            _rp_icon = "🟢" if _rp < 500 else ("🟡" if _rp < 800 else "🔴")
            st.markdown(f"**Riesgo país:** {_rp_icon} {_rp:,.0f} bps")
    except Exception:
        pass

    # Estado del hilo de fondo
    _bg = _update_state().get("thread")
    if _bg is not None and _bg.is_alive():
        st.info("⏳ Actualizando scores en segundo plano…")
    elif st.session_state.scores_refreshed:
        st.success("✅ Scores actualizados")

    st.markdown("---")
    st.caption("Los scores se actualizan automáticamente cuando tienen más de 7 días.")
    if st.button("🔄 Actualizar ahora", use_container_width=True):
        with st.spinner("Actualizando scores de equity... (~2 min)"):
            try:
                from modules.finviz_scorer import run_and_save as _run_eq
                _run_eq()
            except Exception as e:
                st.error(f"Error equity scorer: {e}")
        with st.spinner("Actualizando scores de bonos..."):
            try:
                from modules.bond_scorer import run_and_save as _run_bonds
                _run_bonds()
            except Exception as e:
                st.error(f"Error bond scorer: {e}")
        st.session_state.scores_refreshed = True
        st.success("✅ Scores actualizados")
        st.rerun()

    # Modo avanzado — solo para el administrador de la app
    with st.expander("⚙️ Avanzado", expanded=False):
        st.session_state["_modo_avanzado"] = st.checkbox(
            "Modo presentación académica",
            value=st.session_state.get("_modo_avanzado", False),
        )
        if st.session_state.get("_modo_avanzado"):
            if st.button("🎓 Metodología del sistema", use_container_width=True):
                st.session_state._prev_step = st.session_state.get("step", "intro")
                st.session_state.step = "metodologia"
                st.rerun()

step = st.session_state.step

# ── Auto scroll-to-top on navigation ─────────────────────────────────────────
# Detecta cambios de step automáticamente. Si el usuario cambió de pantalla
# (intro → profiling → results, o vuelve al home, o entra al glosario),
# forzamos scroll instantáneo al top. Sin esto, Streamlit a veces preserva
# scroll de la pantalla anterior, o algún widget fuerza scroll al fondo.
# Múltiples intentos con delays escalonados para ganar contra cualquier
# scroll automático que Streamlit dispare después.
_last_step = st.session_state.get("_last_rendered_step")
if _last_step is not None and _last_step != step:
    components.html("""
<script>
(function() {
    let userScrolled = false;
    let initialTop = true;

    function toTop() {
        if (userScrolled) return;  // respetar al usuario si ya scrolleó
        try {
            const doc = window.parent.document;
            window.parent.scrollTo({ top: 0, behavior: 'instant' });
            doc.documentElement.scrollTop = 0;
            doc.body.scrollTop = 0;
        } catch(e) {}
    }

    // Detectar scroll manual: cualquier wheel, touchmove o keydown del usuario
    // aborta el loop de auto-scroll para no pelearlo.
    try {
        const winp = window.parent;
        const onUserScroll = () => { userScrolled = true; };
        winp.addEventListener('wheel',     onUserScroll, { passive: true, once: true });
        winp.addEventListener('touchmove', onUserScroll, { passive: true, once: true });
        winp.addEventListener('keydown',   onUserScroll, { once: true });
    } catch(e) {}

    // Reintentos hasta 1s solamente (antes 4s era demasiado y peleaba con
    // el usuario). Si Streamlit dispara scroll automático tardío, igual lo
    // ganamos en el primer segundo. Después soltamos el control.
    toTop();
    [50, 150, 350, 700, 1000].forEach(function(d) { setTimeout(toTop, d); });
})();
</script>
""", height=0)
st.session_state["_last_rendered_step"] = step

# ══════════════════════════════════════════════════════════════════════════════
# INTRO
# ══════════════════════════════════════════════════════════════════════════════
if step == "intro":
    st.markdown("""<div class="hero-card">
<div class="hero-icon">🤝</div>
<h1 class="hero-title">Su capital puede trabajar para usted.<br>Sin letra chica. Sin tecnicismos.</h1>
<p class="hero-subtitle">
Si alguna vez sintió que invertir es solo para quienes ya saben,<br>
o que tuvo una mala experiencia previa — <strong>esta herramienta es para usted.</strong>
</p>
<div class="hero-features">
<div class="hero-feature-pill"><span class="hero-feature-icon">✅</span>Sin conocimientos previos</div>
<div class="hero-feature-pill"><span class="hero-feature-icon">🛡️</span>Sin venderle nada</div>
<div class="hero-feature-pill"><span class="hero-feature-icon">🇦🇷</span>Pensado para Argentina</div>
<div class="hero-feature-pill"><span class="hero-feature-icon">⏱️</span>5 minutos y obtiene su cartera sugerida</div>
<div class="hero-feature-pill"><span class="hero-feature-icon">💬</span>Explicamos cada decisión</div>
<div class="hero-feature-pill"><span class="hero-feature-icon">🔒</span>Educativo, no asesoramiento</div>
</div>
</div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("""<div class="audience-note">
<strong>¿Qué hace esta herramienta?</strong> Analizamos su situación en 5 minutos y le mostramos
cómo podría estar invertido su capital — qué instrumentos, en qué proporción y por qué cada uno.
Usted decide si desea avanzar con un asesor real. Aquí solo comprende sus opciones.
</div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("¿Cuánto perdí por no invertir?", key="cost_btn", use_container_width=True):
        st.session_state.step = "costo_no_invertir"
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Iniciar Evaluación", key="start_btn", use_container_width=True):
        st.session_state.step = "profiling"
        st.rerun()

    st.markdown("""<p class="disclaimer">
⚠️ Esta herramienta es de carácter educativo y no constituye asesoramiento financiero regulado por la CNV.
Consulte siempre con un asesor habilitado antes de tomar decisiones de inversión.
</p>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# COSTO DE NO INVERTIR
# ══════════════════════════════════════════════════════════════════════════════
elif step == "costo_no_invertir":
    render_cost_of_not_investing()

elif step == "cost_results":
    render_cost_results()

# ══════════════════════════════════════════════════════════════════════════════
# CUESTIONARIO
# ══════════════════════════════════════════════════════════════════════════════
elif step == "profiling":
    profile_data = render_profiler()

    if profile_data:
        st.session_state.profile = profile_data
        with st.spinner("Construyendo su cartera personalizada..."):
            portfolio  = build_portfolio(profile_data)
            simulation = simulate_portfolio(
                portfolio,
                years=profile_data["horizon"],
                initial_capital=profile_data["capital"],
            )
            st.session_state.portfolio  = portfolio
            st.session_state.simulation = simulation

        st.session_state.step             = "results"
        st.session_state.show_celebration = True
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# RESULTADOS
# ══════════════════════════════════════════════════════════════════════════════
elif step == "results":
    # No usamos un anchor extra — Streamlit envuelve el div en un element-container
    # con padding default que genera un hueco visible. El JS de scroll-on-step-change
    # ahora apunta directo a window.parent (top: 0), que es suficiente.

    profile    = st.session_state.profile
    portfolio  = st.session_state.portfolio
    simulation = st.session_state.simulation

    # ── Procesar input pendiente ANTES que cualquier otro widget ─────────────
    # El procesamiento se hace acá (no dentro del módulo Lucas) para evitar
    # que los widgets de arriba se dupliquen durante el rerun.
    # Mostramos un OVERLAY FIJO en el viewport para que el usuario vea
    # 'Lucas está pensando' sin importar dónde esté scrolleando.
    if st.session_state.get("_lucas_pending_input"):
        _pending = st.session_state.pop("_lucas_pending_input")
        _hist_for_call = list(st.session_state.chat_history)
        # Overlay fijo en el viewport — visible aunque el usuario esté en
        # cualquier parte de la página
        st.markdown("""
<div class="lucas-thinking-overlay">
  <div class="lucas-thinking-box">
    <div class="lucas-thinking-spinner"></div>
    <div class="lucas-thinking-text">
      <strong>Lucas está pensando tu respuesta...</strong>
      <small>Esto suele tardar unos segundos</small>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)
        _answer = chat_with_advisor(_pending, _hist_for_call,
                                    st.session_state.profile,
                                    st.session_state.portfolio)
        st.session_state.chat_history.append({"role": "user",      "content": _pending})
        st.session_state.chat_history.append({"role": "assistant", "content": _answer})
        st.session_state["_lucas_scroll_pending"] = True
        st.rerun()

    # ── Resolución de moneda de display ──────────────────────────────────────
    try:
        from modules.market_data import get_mep_rate as _get_mep
        _MEP_RATE = _get_mep()
    except Exception:
        _MEP_RATE = 1200                                   # fallback estático
    _currency_in   = profile.get("currency", "USD")       # moneda con que el usuario ingresó
    _capital_usd   = profile["capital"]                    # siempre en USD internamente
    _capital_orig  = profile.get("capital_original", _capital_usd)
    # Tasa efectiva usada al ingresar: capital_orig / capital_usd
    _fx_rate       = _capital_orig / _capital_usd if _currency_in == "ARS" else 1.0

    # Toggle (solo si el usuario ingresó en ARS)
    if _currency_in == "ARS":
        if "_display_currency" not in st.session_state:
            st.session_state._display_currency = "ARS"
        _tog_col, _ = st.columns([3, 5])
        with _tog_col:
            st.markdown('<div class="currency-toggle-wrap"><span class="currency-toggle-label">Ver cifras en:</span></div>', unsafe_allow_html=True)
            _disp_sel = st.radio(
                "Ver cifras en:", ["ARS (Pesos)", "USD (Dólares)"],
                horizontal=True, key="currency_toggle", label_visibility="collapsed",
            )
        st.session_state._display_currency = "ARS" if "ARS" in _disp_sel else "USD"

    _disp_curr = st.session_state.get("_display_currency", _currency_in)

    if _disp_curr == "ARS" and _currency_in == "ARS":
        _disp_factor  = _fx_rate
        _disp_capital = _capital_orig
        _disp_prefix  = "$"
        _disp_suffix  = " ARS"
    else:
        _disp_factor  = 1.0
        _disp_capital = _capital_usd
        _disp_prefix  = "USD "
        _disp_suffix  = ""

    # FAB removido: con st.chat_input sticky al fondo, el chat de Lucas
    # está SIEMPRE visible al final del viewport. El FAB era redundante
    # y colisionaba con el chat_input en mobile.

    # ── Aviso de scores actualizados en esta sesión ───────────────────────────
    if st.session_state.scores_refreshed and not st.session_state.get("refresh_banner_dismissed"):
        col_b1, col_b2 = st.columns([5, 1])
        with col_b1:
            st.info("Los datos de mercado fueron actualizados. Podés generar una nueva evaluación para reflejar los últimos fundamentals.")
        with col_b2:
            if st.button("Recalcular", key="recalc_btn", use_container_width=True):
                st.session_state.refresh_banner_dismissed = True
                keys_to_clear = ["portfolio", "simulation", "chat_history", "show_celebration"]
                for k in keys_to_clear:
                    st.session_state[k] = None if k != "chat_history" else []
                st.session_state.step = "profiling"
                st.rerun()

    # ── Pantalla de celebración (primera vez) ─────────────────────────────────
    if st.session_state.get("show_celebration"):
        st.session_state.show_celebration = False
        components.html(_CELEBRATION_HTML, height=0)

    risk_colors = {
        "conservador": "#22c55e",
        "estable":     "#60a5fa",
        "moderado":    "#f59e0b",
        "agresivo":    "#ef4444",
    }
    risk_emojis = {"conservador": "🟢", "estable": "🔵", "moderado": "🟡", "agresivo": "🔴"}
    risk_labels = {
        "conservador": "Inversor Conservador",
        "estable":     "Inversor Balanceado",
        "moderado":    "Inversor Moderado",
        "agresivo":    "Inversor Agresivo",
    }
    risk_explanations = {
        "conservador": "Usted prioriza la preservación del capital por encima del crecimiento. Su cartera apunta a proteger el patrimonio con bajo riesgo.",
        "estable":     "Usted desea un rendimiento superior al plazo fijo sin exponerse a caídas significativas. Su cartera combina dólares, bonos sólidos y algo de renta variable global.",
        "moderado":    "Usted busca un equilibrio entre crecimiento y protección patrimonial. Su cartera combina instrumentos seguros con activos de mayor rendimiento.",
        "agresivo":    "Usted está dispuesto a asumir mayor riesgo para maximizar el crecimiento a largo plazo. Su cartera apunta al mayor rendimiento posible.",
    }

    rc  = risk_colors.get(profile["risk_profile"], "#60a5fa")
    re  = risk_emojis.get(profile["risk_profile"], "🔵")
    rl  = risk_labels.get(profile["risk_profile"], profile["risk_profile"].upper())
    rex = risk_explanations.get(profile["risk_profile"], "")

    _disc_by_risk = {
        "conservador": "orientada a preservación de capital con bajo riesgo.",
        "estable":     "con exposición moderada a bonos y renta variable global.",
        "moderado":    "equilibrada entre seguridad y crecimiento; puede fluctuar en el corto plazo.",
        "agresivo":    "de alto crecimiento; puede sufrir caídas significativas en el corto plazo.",
    }
    _disc_text = _disc_by_risk.get(profile["risk_profile"], "")

    # ── Mensaje personalizado para usuario novato/lastimado ───────────────────
    # Detecta el patrón en las respuestas del cuestionario y muestra una nota
    # de validación + reassurance al inicio del resultado.
    _exp_answer  = profile.get("experience", "")
    _loss_answer = profile.get("loss_tolerance", "")
    _mot_answer  = profile.get("objective", "")

    _is_novice = "Prácticamente nada" in _exp_answer or "Solo conozco el plazo fijo" in _exp_answer
    _was_burned = "Los saco de inmediato" in _loss_answer or "Saco la mitad" in _loss_answer
    _wants_protection = "La inflación me come" in _mot_answer

    _personal_msg = None
    if _was_burned and _is_novice:
        _personal_msg = {
            "icon": "🤝",
            "title": "Sabemos que ya intentaste y no salió como esperabas.",
            "body": (
                "Esta cartera está diseñada para que entiendas cada decisión, "
                "no para que confíes a ciegas. Va a ser conservadora porque "
                "tu prioridad ahora es no volver a sentir esa frustración. "
                "Cada activo tiene una explicación en lenguaje simple — "
                "tomate el tiempo de leerlas."
            ),
        }
    elif _was_burned:
        _personal_msg = {
            "icon": "🛡️",
            "title": "Notamos que las caídas te incomodan, y eso está bien.",
            "body": (
                "La cartera prioriza estabilidad sobre rendimiento máximo. "
                "Vas a ver el bloque <strong>'¿Qué pasó en crisis reales?'</strong> "
                "más abajo — todos los mercados se recuperaron. "
                "El objetivo es que vos también puedas mantener la calma cuando pase."
            ),
        }
    elif _is_novice and _wants_protection:
        _personal_msg = {
            "icon": "🌱",
            "title": "Es tu primer paso — y es la decisión correcta.",
            "body": (
                "No hace falta que entiendas todos los términos hoy. "
                "Cada palabra técnica tiene un <strong>tooltip</strong> "
                "(pasale el dedo por encima o tocala). "
                "Y abajo a la derecha tenés a Lucas, el asesor IA, "
                "para preguntarle cualquier duda en lenguaje normal."
            ),
        }
    elif _is_novice:
        _personal_msg = {
            "icon": "🌱",
            "title": "Es tu primera cartera — vamos a ir paso a paso.",
            "body": (
                "Cada activo de tu cartera tiene una explicación en lenguaje simple. "
                "Los términos técnicos tienen tooltips (pasá el dedo o tocá). "
                "Y si querés profundizar más, abrí el glosario desde el header."
            ),
        }

    if _personal_msg:
        st.markdown(f"""<div class="personal-msg">
  <div class="pm-icon">{_personal_msg['icon']}</div>
  <div class="pm-body">
    <strong>{_personal_msg['title']}</strong>
    <p>{_personal_msg['body']}</p>
  </div>
</div>""", unsafe_allow_html=True)

    # ── Panel de resumen rápido ───────────────────────────────────────────────
    st.markdown(f"""<div class="summary-panel">
<div class="summary-top">
<div class="profile-pill" style="background:{rc}22;border:1.5px solid {rc};color:{rc};">
{re} {rl}
</div>
<h2 class="summary-title">Cartera Sugerida</h2>
<div class="explain-outer"><p class="summary-explain">{rex}</p></div>
<div class="legal-disclaimer">
  ⚠️ <strong>Aviso legal</strong> · Cartera {_disc_text}
  Capital: {_disp_prefix}{_disp_capital:,.0f}{_disp_suffix} · Horizonte: {profile['horizon']} años · Perfil: {rl}.
  Esta herramienta tiene fines educativos y no reemplaza el asesoramiento de un profesional regulado por la {tip("CNV")}.
</div>
</div>
<div class="summary-grid summary-main-grid">
<div class="summary-item">
<div class="si-label">Capital a invertir</div>
<div class="si-value">{_disp_prefix}{_disp_capital:,.0f}{_disp_suffix}</div>
</div>
<div class="summary-item">
<div class="si-label">Horizonte</div>
<div class="si-value">{profile['horizon']} años</div>
</div>
<div class="summary-item">
<div class="si-label">Retorno estimado/año</div>
<div class="si-value" style="color:#22c55e;">{portfolio['expected_cagr']*100:.1f}%</div>
<div class="si-sub">Rendimiento histórico esperado (base USD)</div>
</div>
</div>
<details class="summary-detail">
<summary class="summary-detail-btn">Ver detalle completo</summary>
<div class="summary-grid summary-detail-grid">
<div class="summary-item">
<div class="si-label">Activos en la cartera</div>
<div class="si-value">{len(portfolio['positions'])}</div>
</div>
<div class="summary-item">
<div class="si-label">En pesos ARS</div>
<div class="si-value" style="color:#a3e635;">{portfolio['pesos_pct']:.0f}%</div>
</div>
<div class="summary-item">
<div class="si-label">En dólares USD</div>
<div class="si-value" style="color:#38bdf8;">{portfolio['usd_pct']:.0f}%</div>
</div>
<div class="summary-item">
<div class="si-label">Diversificación</div>
<div class="si-value">{portfolio['diversification'].upper()}</div>
</div>
<div class="summary-item">
<div class="si-label">{tip("volatilidad", "Volatilidad")} estimada</div>
<div class="si-value" style="color:#f59e0b;">{portfolio['expected_volatility']*100:.1f}%</div>
</div>
</div>
</details>
<div class="summary-desc">{portfolio['summary']}</div>
</div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Métricas de simulación ────────────────────────────────────────────────
    sim_data       = simulation["scenarios"]["base"]
    total_end_usd  = sim_data[-1]
    total_gain_usd = total_end_usd - _capital_usd
    cagr           = portfolio["expected_cagr"]
    vol            = portfolio["expected_volatility"]

    total_end_disp  = total_end_usd  * _disp_factor
    total_gain_disp = total_gain_usd * _disp_factor

    gain_color = "#22c55e" if total_gain_disp >= 0 else "#ef4444"
    sign       = "+" if total_gain_disp >= 0 else ""
    cagr_sub   = "Rendimiento histórico esperado (base USD)"

    _horizon = profile['horizon']
    _results_timeline = "6 a 18 meses" if _horizon >= 3 else "3 a 6 meses"
    st.markdown(f"""<div class="metrics-grid">
<div class="metric-card">
  <div class="metric-label">Retorno anual estimado</div>
  <div class="metric-value" style="color:#22c55e;">{cagr*100:.1f}%</div>
  <div class="metric-sub">{cagr_sub}</div>
</div>
<div class="metric-card">
  <div class="metric-label">¿Cuánto puede bajar?</div>
  <div class="metric-value" style="color:#f59e0b;">−{vol*100:.0f}%</div>
  <div class="metric-sub">Caída máxima probable en un mal año</div>
</div>
<div class="metric-card">
  <div class="metric-label">Capital proyectado en {_horizon}a</div>
  <div class="metric-value" style="color:#60a5fa;">{_disp_prefix}{total_end_disp:,.0f}{_disp_suffix}</div>
  <div class="metric-sub">Escenario base</div>
</div>
<div class="metric-card">
  <div class="metric-label">Ganancia estimada</div>
  <div class="metric-value" style="color:{gain_color};">{sign}{_disp_prefix}{abs(total_gain_disp):,.0f}{_disp_suffix}</div>
  <div class="metric-sub">Sobre el capital inicial</div>
</div>
</div>
<div class="metric-card results-timeline-card">
  <div class="metric-label">🕐 ¿Cuándo ver resultados?</div>
  <div class="metric-sub results-timeline-text">Con un horizonte de <strong>{_horizon} años</strong>, los primeros resultados visibles suelen notarse entre <strong>{_results_timeline}</strong>. Las inversiones requieren paciencia — el tiempo es el principal aliado del inversor.</div>
</div>""", unsafe_allow_html=True)

    if _currency_in == "ARS":
        st.markdown(
            f'<p class="fx-rate-note">Tipo de cambio MEP: ${_MEP_RATE:,.0f} ARS/USD · '
            f'<span style="font-size:0.8em;opacity:0.7;">actualizado en tiempo real · '
            f'tasa usada al ingresar: ${_fx_rate:,.0f}</span></p>',
            unsafe_allow_html=True,
        )

    # ── Métricas cuantitativas — solo modo avanzado ───────────────────────────
    if st.session_state.get("_modo_avanzado"):
        _beta   = portfolio.get("beta_portfolio", 0)
        _sharpe = portfolio.get("sharpe_ratio", 0)
        _hhi    = portfolio.get("hhi", 0)
        _hhi_lb = portfolio.get("hhi_label", "")
        _avgsco = portfolio.get("avg_score")

        _beta_color   = "#22c55e" if _beta < 1.0 else ("#f59e0b" if _beta < 1.3 else "#ef4444")
        _sharpe_color = "#22c55e" if _sharpe >= 0.5 else ("#f59e0b" if _sharpe >= 0 else "#ef4444")
        _hhi_color    = "#22c55e" if _hhi < 0.15 else ("#f59e0b" if _hhi < 0.25 else "#ef4444")

        with st.expander("📐 Métricas cuantitativas del portafolio", expanded=True):
            st.markdown(f"""<div class="metrics-grid">
<div class="metric-card">
  <div class="metric-label">{tip("Beta")} del portafolio</div>
  <div class="metric-value" style="color:{_beta_color};">{_beta:.2f}</div>
  <div class="metric-sub">Sensibilidad al mercado (1.0 = neutral)</div>
</div>
<div class="metric-card">
  <div class="metric-label">{tip("Sharpe", "Sharpe Ratio")} estimado</div>
  <div class="metric-value" style="color:{_sharpe_color};">{_sharpe:.2f}</div>
  <div class="metric-sub">Retorno ajustado por riesgo (rf = 4.5%)</div>
</div>
<div class="metric-card">
  <div class="metric-label">Índice {tip("HHI")} (concentración)</div>
  <div class="metric-value" style="color:{_hhi_color};">{_hhi:.3f}</div>
  <div class="metric-sub">{_hhi_lb} — 0 = perfecto, 1 = todo en un activo</div>
</div>
{f'<div class="metric-card"><div class="metric-label">Score promedio ponderado</div><div class="metric-value" style="color:#a78bfa;">{_avgsco}/100</div><div class="metric-sub">Calidad fundamental de los activos scorables</div></div>' if _avgsco else ""}
</div>""", unsafe_allow_html=True)
            st.markdown(
                f'<p style="font-size:0.78rem;color:#64748b;margin-top:0.6rem;">'
                f'{tip("Beta")}: ponderado por betas Finviz. '
                f'{tip("Sharpe")}: (CAGR − 4.5%) / σ. '
                f'{tip("HHI")}: Herfindahl-Hirschman. '
                f'Pesos equity optimizados con {tip("Markowitz")} (scipy).'
                f'</p>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Cálculo de exposición geográfica ──────────────────────────────────────
    # mep excluido: el resultado es USD — riesgo argentino mínimo
    # on_corp incluidos: riesgo corporativo argentino aunque paguen en USD
    _ARG_ASSET_IDS = {
        "lecap", "cer_tx26", "cer_tx28", "cer_dicp",
        "money_market", "plazo_fijo", "fci_t0", "cash_pesos",
        "fci_renta_pesos",
        "al30", "gd30", "al35", "gd35", "gd38",
        "on_corp", "on_ypf", "on_tecpetrol", "on_tgs", "on_macro",
        "on_meli", "on_telecom", "on_genneia", "on_vista", "on_pampa",
        "on_tgs2", "on_arcor", "on_telecom2", "on_irsa", "on_cresud",
        "dual_bond", "dollar_linked",
        "gd29", "gd41",
        "galicia", "ypf", "bbar", "pampa", "tgs", "cepu", "bma", "supv",
        "alua", "txar", "teco2", "vist", "loma", "irsa", "cres",
        "edn", "come", "valo", "harg", "txar", "mirg", "moli", "cvh", "metr",
    }
    _arg_exposure  = sum(p["weight"] for p in portfolio["positions"] if p["id"] in _ARG_ASSET_IDS)
    _intl_exposure = max(0.0, 1.0 - _arg_exposure)

    # ── Distribución + Evolución ──────────────────────────────────────────────
    col_pie, col_evo = st.columns([1, 1.6])

    with col_pie:
        st.markdown('<div class="section-title">📊 Distribución de la Cartera</div>', unsafe_allow_html=True)
        render_pie_chart(portfolio)
        _n_pos = len(portfolio["positions"])
        _profile_labels = {
            "conservador": "conservador (máx. 5)",
            "estable": "balanceado (máx. 7)",
            "moderado": "moderado (máx. 8)",
            "agresivo": "agresivo (máx. 12)",
        }
        _plabel = _profile_labels.get(profile.get("risk_profile", ""), profile.get("risk_profile", ""))
        st.markdown(
            f'<p style="font-size:0.78rem;color:#94a3b8;margin:0 0 0.5rem;line-height:1.55;">'
            f'Su cartera está compuesta por <strong>{_n_pos} instrumentos</strong>, '
            f'número óptimo para su perfil {_plabel} según principios de '
            f'diversificación eficiente ({tip("Evans & Archer", "Evans & Archer, 1968")}).'
            f'</p>',
            unsafe_allow_html=True,
        )

        # ── Nota positiva de diversificación geográfica ─────────────────────
        _extra_msg = ""
        if _arg_exposure > 0.70:
            _extra_msg = (
                "<br><span style='opacity:0.8;'>Considere consultar con un asesor "
                "para evaluar si desea ampliar su diversificación internacional.</span>"
            )
        st.markdown(
            f"""<div class="geo-diversification-note">
  <span class="geo-icon">🌍</span>
  <div class="geo-body">
    <p>Su cartera incluye activos en Argentina y en mercados globales.
    Esta diversificación geográfica reduce su dependencia de un solo país o economía.{_extra_msg}</p>
    <p class="geo-breakdown">
      Exposición local: <strong>{_arg_exposure*100:.0f}%</strong> ·
      Internacional: <strong>{_intl_exposure*100:.0f}%</strong>
    </p>
  </div>
</div>""",
            unsafe_allow_html=True,
        )

    with col_evo:
        st.markdown('<div class="section-title">📈 Proyección de Crecimiento</div>', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-headline">¿Cuánto podría valer su dinero con el tiempo?</h3>', unsafe_allow_html=True)
        # Pasar capital_original según la moneda seleccionada en el toggle
        _bar_cap_orig = _disp_capital if _disp_curr != _currency_in else profile.get("capital_original", _capital_usd)
        render_bar_simulation(portfolio, _capital_usd,
                              currency=_disp_curr,
                              capital_original=_bar_cap_orig)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Tabla de activos + razón por activo ──────────────────────────────────
    st.markdown('<div class="section-title">📋 Composición de su cartera</div>', unsafe_allow_html=True)
    render_allocation_table(portfolio, _disp_capital, currency_label=_disp_curr)

    # ── Análisis fundamental por activo (solo modo avanzado) ─────────────────
    _scored = [p for p in portfolio["positions"] if p.get("score") and p.get("bloques")]
    if _scored and st.session_state.get("_modo_avanzado"):
        with st.expander(f"🔬 Análisis fundamental detallado ({len(_scored)} activos con score Finviz)", expanded=False):
            st.caption("Score calculado sobre 5 bloques: Valuación (25) + Calidad (25) + Solvencia (20) + Crecimiento (20) + Cualitativo (10) = 100 pts")
            for pos in sorted(_scored, key=lambda x: x.get("score", 0), reverse=True):
                bloques = pos["bloques"]
                ratios  = pos.get("ratios", {})
                sc      = pos["score"]
                rating_color = {"STRONG BUY": "#22c55e", "BUY": "#4fa3ff", "HOLD": "#f59e0b",
                                "UNDERWEIGHT": "#f97316", "AVOID": "#ef4444"}.get(
                    "STRONG BUY" if sc >= 85 else ("BUY" if sc >= 70 else ("HOLD" if sc >= 55 else ("UNDERWEIGHT" if sc >= 40 else "AVOID"))), "#94a3b8")
                rating_label = "STRONG BUY" if sc >= 85 else ("BUY" if sc >= 70 else ("HOLD" if sc >= 55 else ("UNDERWEIGHT" if sc >= 40 else "AVOID")))

                col_name, col_score, col_bars = st.columns([2, 1, 3])
                with col_name:
                    st.markdown(f"**{pos['name']}**  \n`{pos.get('ticker','')}`  \n_{pos.get('sector_framework', pos.get('sub',''))}_")
                with col_score:
                    st.markdown(f"<div style='font-size:1.8rem;font-weight:800;color:{rating_color};'>{sc}</div><div style='font-size:0.75rem;color:{rating_color};'>{rating_label}</div>", unsafe_allow_html=True)
                with col_bars:
                    b = bloques
                    st.markdown(f"""
<div style='font-size:0.8rem;line-height:1.8;'>
<span style='opacity:0.6;'>Valuación</span> <b>{b.get('valuacion',0)}/25</b> &nbsp;
<span style='opacity:0.6;'>Calidad</span> <b>{b.get('calidad',0)}/25</b> &nbsp;
<span style='opacity:0.6;'>Solvencia</span> <b>{b.get('solvencia',0)}/20</b> &nbsp;
<span style='opacity:0.6;'>Crecimiento</span> <b>{b.get('crecimiento',0)}/20</b> &nbsp;
<span style='opacity:0.6;'>Cualitativo</span> <b>{b.get('cualitativo',0)}/10</b>
</div>""", unsafe_allow_html=True)
                    # Ratios clave en una línea
                    r_items = []
                    if ratios.get("forward_pe"):    r_items.append(f"P/E fwd: {ratios['forward_pe']:.1f}×")
                    if ratios.get("roe"):           r_items.append(f"ROE: {ratios['roe']:.1f}%")
                    if ratios.get("margen_neto"):   r_items.append(f"Margen: {ratios['margen_neto']:.1f}%")
                    if ratios.get("eps_cagr_5y"):   r_items.append(f"EPS CAGR 5y: {ratios['eps_cagr_5y']:.1f}%")
                    if ratios.get("deuda_equity"):  r_items.append(f"D/E: {ratios['deuda_equity']:.2f}×")
                    if r_items:
                        st.caption(" · ".join(r_items))
                st.divider()

    # ── Advertencias de solapamiento ──────────────────────────────────────────
    overlaps = portfolio.get("overlaps", [])
    if overlaps:
        st.markdown("<br>", unsafe_allow_html=True)
        for ov in overlaps:
            etf = ov["etf"].upper()
            conflicts = ", ".join(c.upper() for c in ov["conflicts"])
            reason = ov["reason"]
            st.markdown(f"""<div class="alert-card alert-medium">
<span class="alert-icon">⚠️</span>
<div><strong>Solapamiento detectado: {etf} + {conflicts}</strong><br>
<span>{reason}</span></div>
</div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Simulaciones ─────────────────────────────────────────────────────────
    with st.expander("📊 Simulaciones: ¿qué pasa con su dinero?", expanded=False):
        _sim_tab1, _sim_tab2 = st.tabs(["📉 Sin invertir", "💰 Aporte mensual"])

        with _sim_tab1:
            _cagr      = portfolio["expected_cagr"]
            _infl_anual = 0.025  # 2.5% inflación global anual en USD

            # Proyección a 5 años
            _con_5y  = _capital_usd * (1 + _cagr) ** 5 * _disp_factor
            _sin_5y  = _capital_usd * (1 - _infl_anual) ** 5 * _disp_factor
            _dif_5y  = _con_5y - _sin_5y
            _dif_sign = "+" if _dif_5y >= 0 else ""

            # 2 cards
            st.markdown(f"""<div class="metrics-grid" style="grid-template-columns:1fr 1fr;gap:16px;">
<div class="metric-card" style="border-left:3px solid #22c55e;">
  <div class="metric-label">CON ESTA CARTERA EN 5 AÑOS</div>
  <div class="metric-value" style="color:#22c55e;">{_disp_prefix}{_con_5y:,.0f}{_disp_suffix}</div>
  <div class="metric-sub">Estimación basada en retorno histórico</div>
</div>
<div class="metric-card" style="border-left:3px solid #ef4444;">
  <div class="metric-label">SIN INVERTIR EN 5 AÑOS</div>
  <div class="metric-value" style="color:#ef4444;">{_disp_prefix}{_sin_5y:,.0f}{_disp_suffix}</div>
  <div class="metric-sub">Perdiendo poder adquisitivo cada año</div>
</div>
</div>""", unsafe_allow_html=True)

            # Línea de diferencia
            st.markdown(f"""<div style="text-align:center;padding:14px 18px;background:rgba(34,197,94,0.07);
border-radius:10px;margin:4px 0 20px 0;border:1px solid rgba(34,197,94,0.15);">
  <span style="font-size:0.95rem;color:#e2e8f0;">La diferencia estimada:
  <strong style="color:#22c55e;font-size:1.05rem;">&nbsp;{_dif_sign}{_disp_prefix}{_dif_5y:,.0f}{_disp_suffix}</strong>
  a su favor si invierte vs si no hace nada.</span>
</div>""", unsafe_allow_html=True)

            # Gráfico de barras: 1, 3, 5 años — dos barras por punto
            try:
                import plotly.graph_objects as _go
                _yr_labels = ["1 año", "3 años", "5 años"]
                _yr_nums   = [1, 3, 5]
                _vals_con  = [_capital_usd * (1 + _cagr) ** y * _disp_factor for y in _yr_nums]
                _vals_sin  = [_capital_usd * (1 - _infl_anual) ** y * _disp_factor for y in _yr_nums]
                _fig_sim   = _go.Figure()
                _fig_sim.add_trace(_go.Bar(
                    name="Con esta cartera", x=_yr_labels, y=_vals_con,
                    marker_color="#22c55e", opacity=0.9,
                    text=[f"{_disp_prefix}{v:,.0f}" for v in _vals_con],
                    textposition="outside", textfont=dict(size=11, color="#22c55e"),
                    hovertemplate=f"{_disp_prefix}%{{y:,.0f}}{_disp_suffix}<extra>Con cartera</extra>",
                ))
                _fig_sim.add_trace(_go.Bar(
                    name="Sin invertir", x=_yr_labels, y=_vals_sin,
                    marker_color="#ef4444", opacity=0.7,
                    text=[f"{_disp_prefix}{v:,.0f}" for v in _vals_sin],
                    textposition="outside", textfont=dict(size=11, color="#ef4444"),
                    hovertemplate=f"{_disp_prefix}%{{y:,.0f}}{_disp_suffix}<extra>Sin invertir</extra>",
                ))
                _y_max_sim = max(_vals_con) * 1.18
                _fig_sim.update_layout(
                    paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
                    font=dict(color="#94a3b8", size=12),
                    barmode="group", bargap=0.28, bargroupgap=0.06,
                    xaxis=dict(showgrid=False, tickfont=dict(size=14, color="#e2e8f0")),
                    yaxis=dict(title=_disp_curr, gridcolor="#1e293b", zerolinecolor="#1e293b",
                               tickformat=",.0f", range=[0, _y_max_sim]),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                                bgcolor="rgba(0,0,0,0)"),
                    margin=dict(l=0, r=0, t=40, b=0),
                )
                st.plotly_chart(_fig_sim, use_container_width=True, config={"displayModeBar": False, "responsive": True})
            except Exception:
                pass

            st.caption("Proyección estimada basada en datos históricos. No garantiza rendimientos futuros.")

        with _sim_tab2:
            st.caption("No hace falta tener mucho para empezar. Si además de su inversión inicial aparta una pequeña cantidad cada mes, el resultado a largo plazo cambia enormemente. Pruebe con distintos montos y vea la diferencia.")

            _aporte_key = "aporte_mensual_usd"
            _col_aporte, _col_slider = st.columns([1, 2])
            with _col_aporte:
                if _currency_in == "ARS":
                    _aporte_ars = st.number_input(
                        "¿Cuánto podría apartar por mes? (en pesos)", min_value=0, max_value=50_000_000,
                        value=st.session_state.get(_aporte_key + "_ars", 50_000),
                        step=50_000, key=_aporte_key + "_ars",
                    )
                    if _aporte_ars > 0:
                        _fmt_ars = f"${_aporte_ars:,.0f}".replace(",", ".")
                        st.caption(f"→ {_fmt_ars} ARS")
                    _aporte_usd_val = _aporte_ars / _MEP_RATE
                else:
                    _aporte_usd_val = st.number_input(
                        "¿Cuánto podría apartar por mes? (en USD)", min_value=0, max_value=500_000,
                        value=st.session_state.get(_aporte_key, 100),
                        step=100, key=_aporte_key,
                    )

            _proy     = proyectar_con_aportes(_capital_usd, _aporte_usd_val, profile["horizon"], portfolio["expected_cagr"])
            _proy_sin = _proy["final_sin"]      * _disp_factor
            _proy_con = _proy["final_con"]      * _disp_factor
            _proy_ext = _proy["ganancia_extra"] * _disp_factor
            _aporte_disp = _aporte_usd_val * _disp_factor

            with _col_slider:
                if _aporte_usd_val > 0:
                    st.markdown(f"""<div style="padding:18px 20px;background:rgba(34,197,94,0.08);border-radius:12px;border:1px solid rgba(34,197,94,0.2);">
<div style="font-size:0.85rem;color:#94a3b8;margin-bottom:6px;">Ahorrando {_disp_prefix}{_aporte_disp:,.0f}{_disp_suffix} por mes durante {profile['horizon']} años:</div>
<div style="font-size:1.8rem;font-weight:800;color:#22c55e;margin-bottom:10px;">{_disp_prefix}{_proy_con:,.0f}{_disp_suffix}</div>
<div style="font-size:0.84rem;color:#94a3b8;margin-bottom:4px;">En cambio, sin aportes mensuales tendría: <strong style="color:#e2e8f0;">{_disp_prefix}{_proy_sin:,.0f}{_disp_suffix}</strong></div>
<div style="font-size:0.84rem;color:#22c55e;font-weight:600;">La diferencia: +{_disp_prefix}{_proy_ext:,.0f}{_disp_suffix} solo por apartar {_disp_prefix}{_aporte_disp:,.0f}{_disp_suffix} por mes</div>
</div>""", unsafe_allow_html=True)
                else:
                    st.info("Ingrese un monto mensual para ver el impacto")

            if _aporte_usd_val > 0:
                try:
                    import plotly.graph_objects as _go2
                    _ap_años = _proy["años"]
                    _ap_con  = [v * _disp_factor for v in _proy["con_aporte"]]
                    _ap_sin  = [v * _disp_factor for v in _proy["sin_aporte"]]
                    _fig_ap  = _go2.Figure()
                    _fig_ap.add_trace(_go2.Scatter(x=_ap_años, y=_ap_con,
                        name="Invirtiendo + ahorrando cada mes",
                        line=dict(color="#22c55e", width=3), mode="lines",
                        fill="tonexty", fillcolor="rgba(34,197,94,0.08)",
                        hovertemplate=f"{_disp_prefix}%{{y:,.0f}}{_disp_suffix}<extra>Con aportes</extra>",
                    ))
                    _fig_ap.add_trace(_go2.Scatter(x=_ap_años, y=_ap_sin,
                        name="Solo con lo que invirtió hoy",
                        line=dict(color="#60a5fa", width=2, dash="dot"), mode="lines",
                        hovertemplate=f"{_disp_prefix}%{{y:,.0f}}{_disp_suffix}<extra>Sin aportes</extra>",
                    ))
                    _fig_ap.update_layout(
                        paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
                        font=dict(color="#94a3b8", size=12),
                        xaxis=dict(title="Años", tickmode="linear", dtick=1,
                                   gridcolor="#1e293b", zerolinecolor="#1e293b"),
                        yaxis=dict(title="", range=[min(_ap_sin)*0.97, max(_ap_con)*1.03],
                                   gridcolor="#1e293b", zerolinecolor="#1e293b", tickformat=",.0f"),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                                    bgcolor="rgba(0,0,0,0)"),
                        margin=dict(l=0, r=0, t=40, b=0), hovermode="x unified",
                    )
                    st.markdown(
                        f'<p style="font-size:0.73rem;color:#64748b;margin:0 0 4px 0;">'
                        f'Valores en {_disp_curr}</p>',
                        unsafe_allow_html=True,
                    )
                    st.plotly_chart(_fig_ap, use_container_width=True, config={"displayModeBar": False, "responsive": True})
                except Exception:
                    pass

            st.caption("Este cálculo asume que los aportes mensuales se invierten al mismo retorno estimado que su cartera. Es una proyección, no una garantía.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # MÓDULO UNIFICADO: HABLÁ CON LUCAS
    # El procesamiento del input pendiente se hace AL TOPE de la pantalla de
    # results (no acá) para que el spinner no quede en el medio y los widgets
    # de arriba no se dupliquen durante el rerun.
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown('<div class="lucas-card">', unsafe_allow_html=True)

    # Header con avatar + título
    st.markdown("""<div class="lucas-header">
  <div class="lucas-avatar">💬</div>
  <div class="lucas-title-wrap">
    <h3 class="lucas-title">Hablá con Lucas</h3>
    <p class="lucas-subtitle">Tu asesor financiero IA</p>
  </div>
</div>""", unsafe_allow_html=True)

    chat_history = st.session_state.chat_history

    # Si el chat está vacío, mostrar bienvenida personalizada
    if not chat_history:
        _profile_label_display = {
            "conservador": "conservadora",
            "estable":     "balanceada",
            "moderado":    "moderada",
            "agresivo":    "agresiva",
        }.get(profile.get("risk_profile", ""), profile.get("risk_profile", ""))
        _horizonte = profile.get("horizon", 5)
        _h_unit = "año" if _horizonte == 1 else "años"
        _capital_str = f"{_disp_prefix}{_disp_capital:,.0f}{_disp_suffix}"
        st.markdown(f"""<div class="lucas-welcome">
  ¡Hola! Vi que armamos para vos una cartera <strong>{_profile_label_display}</strong>
  de <strong>{_capital_str}</strong> con horizonte a <strong>{_horizonte} {_h_unit}</strong>.
  Puedo ayudarte a entender por qué te sugerimos estos activos, qué tener en cuenta,
  o cualquier duda sobre cómo empezar a invertir.
</div>""", unsafe_allow_html=True)

    # ── Chips de preguntas pre-armadas — ARRIBA (antes de los mensajes) ─────
    # Layout chat-real: chips fijos arriba, mensajes crecen hacia abajo, último
    # mensaje queda pegado al input.
    _suggested_input = None
    _chips_label = "Estas son las preguntas más comunes:" if not chat_history else "¿Querés explorar otra cosa?"
    st.markdown(f'<p class="lucas-chips-label">{_chips_label}</p>', unsafe_allow_html=True)
    st.markdown('<div class="lucas-chips-block">', unsafe_allow_html=True)
    _chips = [
        "¿Por qué me sugeriste estos activos?",
        "¿Qué cosas debo tener en cuenta?",
        "¿Cuándo debería revisar mi cartera?",
        "Dame consejos concretos para mi caso",
        "¿Qué puede salir mal?",
        "¿Qué hago si necesito el dinero antes?",
        "¿Cómo abro cuenta en un broker?",
        "¿Cuánto pago de impuestos?",
    ]
    for _row_start in range(0, len(_chips), 3):
        _row = _chips[_row_start:_row_start + 3]
        _cols = st.columns(len(_row))
        for i, q in enumerate(_row):
            with _cols[i]:
                if st.button(q, key=f"lucas_chip_{_row_start + i}", use_container_width=True):
                    _suggested_input = q
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Render del historial — DESPUÉS de los chips, ANTES del input ────────
    # Los mensajes crecen hacia abajo. La última respuesta de Lucas queda
    # pegada justo encima del input, como cualquier app de chat real.
    if chat_history:
        import html as _html
        for i, msg in enumerate(chat_history):
            is_last  = (i == len(chat_history) - 1)
            is_user  = msg["role"] == "user"
            align    = "chat-user" if is_user else "chat-advisor"
            label    = "Usted" if is_user else "Lucas · Asesor IA"
            safe_content = _html.escape(msg["content"]).replace("\n", "<br>")
            id_attr = ' id="last-message-anchor"' if is_last else ''
            st.markdown(
                f'<div class="chat-bubble {align}"{id_attr}>'
                f'<div class="chat-label">{label}</div>'
                f'<div class="chat-text">{safe_content}</div></div>',
                unsafe_allow_html=True,
            )

    # ── Input INLINE — JUSTO debajo del último mensaje ───────────────────────
    st.markdown('<p class="lucas-input-label">o escribí tu propia pregunta:</p>', unsafe_allow_html=True)
    with st.form("lucas_form_inline", clear_on_submit=True):
        col_inp, col_btn = st.columns([5, 1])
        with col_inp:
            user_input = st.text_input(
                "Tu pregunta a Lucas",
                placeholder="Ej: ¿Conviene comprar dólares ahora? ¿Qué es la TIR?",
                label_visibility="collapsed",
            )
        with col_btn:
            send = st.form_submit_button("Enviar", use_container_width=True, type="primary")

    # Resolver input desde chip o form, guardarlo como pendiente y rerun.
    # El procesamiento real (con spinner) ocurre al PRINCIPIO del módulo en el
    # próximo render — así el form no se ve duplicado durante el "Lucas está pensando".
    _final_input = _suggested_input or (user_input.strip() if send and user_input.strip() else None)
    if _final_input:
        st.session_state["_lucas_pending_input"] = _final_input
        st.rerun()

    # Footer mini: disclaimer + link 'empezar de nuevo'
    st.markdown("""<p class="lucas-footer-note">
  Lucas es un asistente IA con fines educativos.
  No reemplaza el asesoramiento de un profesional matriculado por la CNV.
</p>""", unsafe_allow_html=True)

    if chat_history:
        st.markdown('<div class="lucas-restart">', unsafe_allow_html=True)
        if st.button("¿Empezar de nuevo?", key="lucas_restart"):
            st.session_state.chat_history = []
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # cierra .lucas-card

    # ── Auto-scroll a la última respuesta tras un nuevo mensaje ──────────────
    if st.session_state.pop("_lucas_scroll_pending", False):
        components.html("""
<script>
(function() {
    function scrollToLast() {
        try {
            const doc = window.parent.document;
            const anchor = doc.getElementById('last-message-anchor');
            if (anchor) {
                anchor.scrollIntoView({
                    behavior: 'smooth',
                    block: 'center',
                    inline: 'nearest'
                });
            }
        } catch(e) { /* noop */ }
    }
    setTimeout(scrollToLast, 300);
    setTimeout(scrollToLast, 700);
})();
</script>
""", height=0)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── ¿Y ahora qué? ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">❓ Próximos Pasos</div>', unsafe_allow_html=True)
    st.markdown("""<div class="action-guide">
<div class="action-step">
  <div class="action-step-number">1</div>
  <div class="action-step-body">
    <div class="action-step-title">Abra una cuenta en un broker habilitado por la CNV</div>
    <div class="action-step-copy">El proceso es gratuito y demora aproximadamente 10 minutos.</div>
    <details class="action-step-help"><summary>¿Cómo hacerlo?</summary>
      <div>Elija un broker regulado por la CNV, complete sus datos personales y verifique su identidad con DNI y selfie.</div>
    </details>
    <details class="action-step-help"><summary>¿Cuánto necesito para empezar?</summary>
      <div>No existe un mínimo formal. En la práctica:<br>
      • Desde $10.000 ARS ya puede invertir en un Fondo Money Market<br>
      • Desde $50.000 ARS puede armar una cartera básica con 2 o 3 instrumentos<br>
      • Con $200.000 ARS o más puede replicar la cartera sugerida completa<br>
      Lo importante es empezar, aunque sea con poco.</div>
    </details>
    <details class="action-step-help"><summary>¿Qué pasa si necesito el dinero antes de tiempo?</summary>
      <div style="line-height:1.7;">
        La liquidez depende del instrumento:<br><br>
        <strong style="color:#38bdf8;">💧 Retiro en el día:</strong> Fondo Money Market (24 hs) · Dólar MEP (48 hs)<br>
        <strong style="color:#f59e0b;">📅 1–5 días hábiles:</strong> LECAPs, bonos soberanos, ONs corporativas — venta en mercado secundario<br>
        <strong style="color:#10d98a;">📈 Conviene esperar:</strong> CEDEARs y ETFs se pueden vender cualquier día, pero si el mercado está bajo puede implicar una pérdida<br><br>
        <strong style="color:#a78bfa;">Recomendación:</strong> antes de invertir, asegúrese de tener un fondo de emergencia equivalente a 3–6 meses de gastos. Ese dinero nunca debe invertirse.
      </div>
    </details>
  </div>
</div>
<div class="action-step">
  <div class="action-step-number">2</div>
  <div class="action-step-body">
    <div class="action-step-title">Deposite el capital que desea invertir</div>
    <div class="action-step-copy">Transfiera desde su cuenta bancaria o billetera digital.</div>
    <details class="action-step-help"><summary>¿Cómo hacerlo?</summary>
      <div>Acceda a la opción de depósito o transferencia en la app y siga los pasos para enviar pesos o dólares.</div>
    </details>
  </div>
</div>
<div class="action-step">
  <div class="action-step-number">3</div>
  <div class="action-step-body">
    <div class="action-step-title">Adquiera los instrumentos de su cartera</div>
    <div class="action-step-copy">Respete la ponderación sugerida para cada instrumento.</div>
    <details class="action-step-help"><summary>¿Cómo hacerlo?</summary>
      <div>Seleccione cada instrumento, ingrese la cantidad y confirme la operación. Si tiene dudas, comience por el activo más conservador.</div>
    </details>
  </div>
</div>
<div class="action-step">
  <div class="action-step-number">4</div>
  <div class="action-step-body">
    <div class="action-step-title">Revise el rendimiento de su cartera mensualmente</div>
    <div class="action-step-copy">No es necesario monitorear la cartera a diario.</div>
    <details class="action-step-help"><summary>¿Cómo hacerlo?</summary>
      <div>Ingrese a su cuenta cada 30 días, verifique el rendimiento y ajuste solo si cambiaron sus objetivos o su situación financiera.</div>
    </details>
  </div>
</div>
</div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Disclaimer legal de cierre ────────────────────────────────────────────
    st.markdown(f"""<div class="portfolio-disclaimer">
  <div class="pd-icon">ℹ️</div>
  <div class="pd-body">
    <strong>Esta cartera es una sugerencia educativa, no asesoramiento financiero.</strong>
    <p>Está construida con datos históricos y modelos académicos ({tip("Markowitz")},
    {tip("Evans & Archer")}) aplicados a su perfil. No considera su situación impositiva,
    patrimonio total ni objetivos personales puntuales. Antes de operar, consulte con un
    asesor financiero matriculado por la <strong>{tip("CNV")} (Comisión Nacional de Valores)</strong>
    para validar que esta estrategia se ajuste a su realidad.</p>
    <p class="pd-fine">TuPortafolioIA no recibe comisiones por las recomendaciones · No opera por
    cuenta de los usuarios · Fines exclusivamente educativos.</p>
  </div>
</div>""", unsafe_allow_html=True)

    # ── Glosario CTA ──────────────────────────────────────────────────────────
    st.markdown("""<div class="glosario-cta">
<div class="glosario-cta-title">📚 ¿Hay algún término que no conoce?</div>
<p class="glosario-cta-sub">Consulte el Glosario Financiero con definiciones claras y ejemplos prácticos.</p>
</div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_eval, col_glos, col_meto = st.columns([1, 1, 1])
    with col_eval:
        if st.button("🔄 Nueva Evaluación", key="restart", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    with col_glos:
        if st.button("📚 Ver Glosario", key="glosario_from_results", use_container_width=True):
            st.session_state._prev_step = "results"
            st.session_state.step = "glosario"
            st.rerun()
    with col_meto:
        if st.button("ℹ️ Cómo funciona", key="how_from_results", use_container_width=True):
            st.session_state._prev_step = "results"
            st.session_state.step = "como_funciona"
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# GLOSARIO
# ══════════════════════════════════════════════════════════════════════════════
elif step == "glosario":
    render_glossary()

# ══════════════════════════════════════════════════════════════════════════════
# METODOLOGÍA ACADÉMICA (modo avanzado)
# ══════════════════════════════════════════════════════════════════════════════
elif step == "metodologia":
    render_methodology()

# ══════════════════════════════════════════════════════════════════════════════
# CÓMO FUNCIONA (para el usuario general)
# ══════════════════════════════════════════════════════════════════════════════
elif step == "como_funciona":
    render_how_it_works()

render_footer()
