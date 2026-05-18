"""
El Costo de No Invertir — pantalla de impacto emocional pre-cuestionario.
"""

import streamlit as st
import urllib.request
import json as _json

# ============================================================
# DATOS HARDCODED — Última actualización: mayo 2026
# ============================================================
# IMPORTANTE: Revisar y actualizar TRIMESTRALMENTE.
# Próxima revisión sugerida: agosto 2026.
#
# Fuentes verificadas:
#   - Inflación: INDEC IPC oficial
#       · 2024 anual: 117.8%
#       · 2025 anual: 31.5%
#       · 2026 ene-abr: 11.2% (Libertad y Progreso + Criteria)
#   - Plazo fijo: BCRA TNA histórica capitalizada mensualmente
#   - MEP histórico: ArgentinaDatos + dolarhistorico.com
#       · Mayo 2024 (día 2): $1.064,56
#       · Mayo 2025: $1.191,72
#       · Hoy 12-may-2026: $1.428,66 (Cronista)
#   - S&P 500: SPDR SPY total return — 11% anual promedio histórico
#       (los últimos 10 años fueron 13-14% por outliers tech, usamos
#       cifra conservadora de largo plazo)
# ============================================================

# Inflación acumulada por período (factor: 1.10 = +110%)
INFLATION_ACUM = {
    2:  1.10,    # mayo 2024 → mayo 2026: ~110% acumulado
    5:  25.00,   # mayo 2021 → mayo 2026: ~2.500% acumulado
    10: 143.00,  # mayo 2016 → mayo 2026: ~14.300% acumulado
}

# Plazo fijo capitalizado mensualmente (factor acumulado)
_PF_ACUM = {
    2:  1.15,    # ~115% en 2 años (TNAs reales positivas bajo Milei)
    5:  9.50,    # ~950% en 5 años
    10: 127.00,  # ~12.700% en 10 años (apenas pierde vs inflación)
}

# Dólar MEP al inicio de cada período (ARS/USD)
_MEP_HIST = {
    2:  1_065.0,  # mayo 2024 — verificado: $1.064,56 (2-may-24)
    5:  160.0,    # mayo 2021 — promedio mensual
    10: 14.0,     # mayo 2016 — post-salida del cepo macrista
}
_MEP_FALLBACK = 1_400.0   # actualizado al rango actual (~$1.428 mayo 2026)

# Tasas anuales en USD de alternativas de inversión
_SPY_RATE = 0.11   # CEDEAR S&P 500 — promedio histórico conservador 30+ años
_ON_RATE  = 0.08   # ONs corporativas — secundario, usado para comparativas

STORAGE_LABELS = {
    "caja_ahorro":     "Caja de ahorro bancaria",
    "efectivo_casa":   "Efectivo en casa",
    "plazo_fijo":      "Plazo fijo tradicional",
    "dolares_billete": "Dólares billete guardados",
}

PERIOD_LABELS = {2: "2 años", 5: "5 años", 10: "10 años"}


# ── API en tiempo real ────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def _get_mep() -> tuple[float, bool]:
    """Dólar MEP actual — mismo origen que profiler.py."""
    try:
        req = urllib.request.Request(
            "https://dolarapi.com/v1/dolares/bolsa",
            headers={"User-Agent": "Mozilla/5.0"},
        )
        with urllib.request.urlopen(req, timeout=4) as resp:
            d = _json.loads(resp.read())
            rate = float(d.get("venta") or d.get("compra") or 0)
            if rate > 0:
                return rate, True
    except Exception:
        pass
    return _MEP_FALLBACK, False


# ── Cálculos ──────────────────────────────────────────────────────────────────

def _calc(amount: float, storage: str, years: int, mep_now: float) -> dict:
    """Calcula los escenarios de inversión para la pantalla 'Costo de no invertir'.

    Devuelve un dict con todos los campos necesarios para renderizar las
    tres cards + el mensaje adaptativo, incluyendo el flag spy_gano_vs_pf
    que indica si la narrativa "podrías tener más con SPY" es honesta.
    """
    inf      = INFLATION_ACUM[years]
    pf_rate  = _PF_ACUM[years]
    mep_then = _MEP_HIST[years]

    if storage == "dolares_billete":
        usd_amount  = amount / mep_now
        nominal_hoy = amount
        real_hoy    = amount
        on_ars  = usd_amount * (1 + _ON_RATE)  ** years * mep_now
        spy_ars = usd_amount * (1 + _SPY_RATE) ** years * mep_now
    else:
        nominal_hoy = amount * (1 + pf_rate) if storage == "plazo_fijo" else amount
        real_hoy    = nominal_hoy / (1 + inf)
        usd_then    = amount / mep_then
        on_ars  = usd_then * (1 + _ON_RATE)  ** years * mep_now
        spy_ars = usd_then * (1 + _SPY_RATE) ** years * mep_now

    base_actual          = nominal_hoy
    ganancia_spy_vs_base = spy_ars - base_actual
    ganancia_spy_pct     = (ganancia_spy_vs_base / base_actual * 100) if base_actual > 0 else 0
    spy_gano_vs_pf       = spy_ars > nominal_hoy

    return {
        "amount":               amount,
        "nominal_hoy":          nominal_hoy,
        "real_hoy":             real_hoy,
        "perdida_vs_inflacion": amount - real_hoy,
        "on_ars":               on_ars,
        "spy_ars":              spy_ars,
        "inf_pct":              inf * 100,
        "pf_pct":               pf_rate * 100,
        "mep_now":              mep_now,
        "storage":              storage,
        "years":                years,
        "ganancia_spy_vs_base": ganancia_spy_vs_base,
        "ganancia_spy_pct":     ganancia_spy_pct,
        "spy_gano_vs_pf":       spy_gano_vs_pf,
    }


# ── Pantalla 1: Inputs ────────────────────────────────────────────────────────

def render_cost_of_not_investing():
    st.markdown("""<div class="hero-card">
<div class="hero-icon">💸</div>
<h1 class="hero-title">¿Cuánto perdió por no invertir?</h1>
<p class="hero-subtitle">
Complete tres datos simples y le mostraremos el impacto real<br>
de guardar su dinero en opciones que no generan rendimiento.
</p>
<p class="hero-human-copy">No es su culpa — nadie nos enseña esto.</p>
</div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    mep_now, mep_live = _get_mep()
    mep_tag = f"${mep_now:,.0f}/USD · tiempo real" if mep_live else f"~${mep_now:,.0f}/USD · estimado"

    with st.form("costo_form"):
        col_a, col_b = st.columns(2)
        with col_a:
            amount = st.number_input(
                "¿Cuánto dinero tiene ahorrado? (ARS)",
                min_value=1_000,
                max_value=100_000_000,
                value=500_000,
                step=10_000,
                format="%d",
                help="Si tiene dólares en efectivo, ingrese el equivalente en ARS al cambio actual.",
            )
        with col_b:
            storage = st.selectbox(
                "¿Dónde lo tiene guardado?",
                options=list(STORAGE_LABELS.keys()),
                format_func=lambda k: STORAGE_LABELS[k],
            )

        years = st.selectbox(
            "¿Hace cuánto tiempo lo tiene guardado?",
            options=[2, 5, 10],
            format_func=lambda y: PERIOD_LABELS[y],
        )

        st.caption(f"💱 Tipo de cambio MEP de referencia: {mep_tag}")
        submitted = st.form_submit_button("Calcular lo que perdió →", use_container_width=True)

    if submitted:
        st.session_state.cost_result = _calc(amount, storage, years, mep_now)
        st.session_state.step = "cost_results"
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    _, col_skip, _ = st.columns([1, 2, 1])
    with col_skip:
        if st.button("Ir directo a mi evaluación →", key="skip_cni"):
            st.session_state.step = "profiling"
            st.rerun()


# ── Pantalla 2: Resultados ────────────────────────────────────────────────────

def render_cost_results():
    r = st.session_state.get("cost_result")
    if not r:
        st.session_state.step = "costo_no_invertir"
        st.rerun()
        return

    amount    = r["amount"]
    real_hoy  = r["real_hoy"]
    spy_ars   = r["spy_ars"]
    perdida   = r["perdida_vs_inflacion"]
    years     = r["years"]
    storage   = r["storage"]
    inf_pct   = r["inf_pct"]
    pf_pct    = r["pf_pct"]
    mep_now   = r["mep_now"]
    slabel    = STORAGE_LABELS[storage]
    plabel    = PERIOD_LABELS[years]

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown(f"""<div class="reveal-card" style="border-color:rgba(240,180,41,0.25);">
<div class="reveal-badge" style="border-color:#f0b429;color:#f0b429;font-style:normal;">
  📉 Su análisis de costo de oportunidad
</div>
<p class="reveal-tagline">
  ${amount:,.0f} ARS en <strong>{slabel}</strong> durante <strong>{plabel}</strong>
</p>
</div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 3 Cards de impacto ────────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)

    with c1:
        dolares  = amount / mep_now
        nafta    = amount / 1_200
        st.markdown(f"""<div class="metric-card">
  <div class="metric-label">Lo que tenía hace {plabel}</div>
  <div class="metric-value" style="color:var(--text-1);">${amount:,.0f}</div>
  <div class="metric-sub" style="text-align:left;line-height:1.9;margin-top:0.9rem;">
    Equivalía a:<br>
    · <strong>USD {dolares:,.0f}</strong> al tipo de cambio MEP<br>
    · <strong>{nafta:,.0f}</strong> litros de nafta
  </div>
</div>""", unsafe_allow_html=True)

    with c2:
        if storage == "dolares_billete":
            c2_val   = amount
            c2_color = "var(--blue)"
            c2_note  = "Sus dólares preservaron valor contra la inflación en ARS."
            c2_loss  = "Sin pérdida nominal, pero sin rendimiento en USD."
        else:
            c2_val    = real_hoy
            pct_loss  = (perdida / amount * 100) if amount else 0
            c2_color  = "var(--red)"
            if storage == "plazo_fijo":
                c2_note = f"Inflación: {inf_pct:.0f}% · PF acumulado: {pf_pct:.0f}%"
            else:
                c2_note = f"Inflación acumulada del período: {inf_pct:.0f}%"
            c2_loss  = f"Pérdida real: −${perdida:,.0f} (−{pct_loss:.0f}%)"

        st.markdown(f"""<div class="metric-card" style="border-color:rgba(255,77,106,0.35);">
  <div class="metric-label">Lo que vale hoy sin invertir</div>
  <div class="metric-value" style="color:{c2_color};">${c2_val:,.0f}</div>
  <div class="metric-sub" style="text-align:left;line-height:1.9;margin-top:0.9rem;">
    {c2_note}<br>
    <span style="color:var(--red);font-weight:600;">{c2_loss}</span>
  </div>
</div>""", unsafe_allow_html=True)

    # ---- Card 3: CEDEAR S&P 500 (nuevo comparador principal) ----
    with c3:
        gain_spy_vs_base = r["ganancia_spy_vs_base"]
        pct_spy          = r["ganancia_spy_pct"]
        is_positive      = gain_spy_vs_base > 0
        color_acento     = "var(--green)" if is_positive else "var(--text-2)"
        signo            = "+" if is_positive else ""
        st.markdown(f"""<div class="metric-card" style="border-color:rgba(16,217,138,0.55);box-shadow:0 0 24px rgba(16,217,138,0.15);">
  <div class="metric-label">💎 Lo que tendría con el CEDEAR del S&amp;P 500</div>
  <div class="metric-value" style="color:var(--green);">${spy_ars:,.0f}</div>
  <div class="metric-sub" style="text-align:left;line-height:1.9;margin-top:0.9rem;">
    Las 500 mayores empresas de EE.UU.<br>
    <span style="opacity:0.7;font-size:0.85rem;">(11% anual USD — promedio histórico)</span><br>
    <span style="color:{color_acento};font-weight:600;">{signo}${gain_spy_vs_base:,.0f} ARS vs su escenario actual ({signo}{pct_spy:.0f}%)</span>
  </div>
</div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ---- Mensaje adaptativo según contexto real ----
    if storage == "dolares_billete":
        ganancia_ars = spy_ars - amount
        ganancia_pct = (ganancia_ars / amount * 100) if amount > 0 else 0
        usd_equiv    = amount / mep_now
        msg = (
            f"Sus dólares le protegieron del peso — eso ya es un gran paso. "
            f"Pero en {plabel} no generaron rendimiento. "
            f"Tiene <strong>USD {usd_equiv:,.0f}</strong> equivalentes a "
            f"<strong>${amount:,.0f} ARS</strong> hoy. "
            f"Si los hubiera invertido en el CEDEAR del S&P 500, "
            f"hoy tendría <strong>${spy_ars:,.0f} ARS</strong> — un "
            f"<strong>+{ganancia_pct:.0f}%</strong> que dejó pasar."
        )
    elif storage == "plazo_fijo":
        if r["spy_gano_vs_pf"]:
            diff_inflacion = r["pf_pct"] - r["inf_pct"]
            txt_inf = (
                f"su plazo fijo perdió contra la inflación "
                f"(PF: <strong>{r['pf_pct']:.0f}%</strong> vs inflación: <strong>{r['inf_pct']:.0f}%</strong>)"
                if diff_inflacion < 0 else
                f"su plazo fijo apenas empató la inflación "
                f"(PF: <strong>{r['pf_pct']:.0f}%</strong> vs inflación: <strong>{r['inf_pct']:.0f}%</strong>)"
            )
            msg = (
                f"En {plabel}, {txt_inf}. "
                f"En ese mismo período, el CEDEAR del S&P 500 le hubiera dado "
                f"<strong>${spy_ars:,.0f}</strong> — un "
                f"<strong>+{r['ganancia_spy_pct']:.0f}%</strong> "
                f"sobre lo que tiene hoy. <strong>Esa diferencia es el costo "
                f"real de no invertir en activos productivos.</strong>"
            )
        else:
            msg = (
                f"En {plabel}, su plazo fijo se comportó bien gracias al contexto "
                f"de desinflación reciente y un dólar relativamente estable "
                f"(PF: <strong>+{r['pf_pct']:.0f}%</strong>, "
                f"inflación: <strong>{r['inf_pct']:.0f}%</strong>). "
                f"Pero este es un período atípico en la historia argentina. "
                f"<strong>A plazos más largos (5 o 10 años) el CEDEAR del S&P 500 "
                f"ha superado al plazo fijo argentino por amplio margen</strong>, "
                f"porque captura el crecimiento de las empresas más importantes "
                f"del mundo — no solo la tasa de interés local de coyuntura."
            )
    else:
        msg = (
            f"En {plabel}, la inflación acumulada fue de "
            f"<strong>{r['inf_pct']:.0f}%</strong>. "
            f"Sus <strong>${amount:,.0f} ARS</strong> guardados valen hoy el "
            f"equivalente real de <strong>${real_hoy:,.0f} ARS</strong> en "
            f"poder adquisitivo. "
            f"Y si los hubiera invertido en el CEDEAR del S&P 500, hoy tendría "
            f"<strong>${spy_ars:,.0f}</strong>. "
            f"<strong>El dinero parado pierde valor todos los días en "
            f"Argentina</strong> — y deja pasar el crecimiento que otros "
            f"activos sí capturan."
        )

    st.markdown(f"""<div class="alert-card alert-medium">
<span class="alert-icon">💡</span>
<div style="line-height:1.85;font-size:0.93rem;color:var(--text-2);">
  {msg}<br><br>
  <strong style="color:var(--text-1);">No invertir también es una decisión financiera.</strong>
  Y en Argentina, suele ser una de las más costosas — no tanto por lo que se
  pierde contra la inflación, sino por lo que se deja de ganar contra activos
  productivos a largo plazo.<br>
  <span style="color:var(--green);">La buena noticia: a partir de hoy puede cambiar esto.</span>
</div>
<div style="margin-top:0.8rem;padding-top:0.8rem;border-top:1px solid rgba(255,255,255,0.06);font-size:0.78rem;opacity:0.55;line-height:1.5;">
  Los rendimientos pasados no garantizan resultados futuros. El S&P 500 promedió
  ~11% anual nominal en USD a largo plazo, pero atravesó caídas significativas
  (-37% en 2008, -19% en 2022). Esta simulación es educativa.
</div>
</div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Gráfico comparativo ───────────────────────────────────────────────────
    st.markdown(
        f'<div class="section-title">📊 ¿Qué hubiera pasado con sus ${amount:,.0f} en {plabel}?</div>',
        unsafe_allow_html=True,
    )
    bar_sin = amount if storage == "dolares_billete" else real_hoy
    _render_chart(bar_sin, spy_ars, amount)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── CTA principal ─────────────────────────────────────────────────────────
    st.markdown("""<div class="glosario-cta">
<div class="glosario-cta-title">La buena noticia es que puede cambiar esto hoy mismo</div>
<p class="glosario-cta-sub">
  Complete su perfil de inversor en menos de 2 minutos y reciba una cartera<br>
  personalizada diseñada para hacer crecer su capital en Argentina.
</p>
</div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    _, col_cta, _ = st.columns([1, 2, 1])
    with col_cta:
        if st.button(
            "Quiero que esto no vuelva a pasar → Iniciar mi evaluación",
            key="cni_cta",
            use_container_width=True,
        ):
            if storage == "plazo_fijo":
                st.session_state.pre_experience = "Solo conozco el plazo fijo o Mercado Pago."
            elif storage == "dolares_billete":
                st.session_state.pre_experience = "Algo. Escuché de CEDEARs, fondos, dólar MEP."
            st.session_state.step = "profiling"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    col_back, col_skip = st.columns(2)
    with col_back:
        if st.button("← Recalcular con otros datos", key="cni_recalc", use_container_width=True):
            st.session_state.step = "costo_no_invertir"
            st.rerun()
    with col_skip:
        if st.button("Ir directo a mi evaluación →", key="cni_skip2", use_container_width=True):
            st.session_state.step = "profiling"
            st.rerun()

    st.markdown(
        '<p style="text-align:center;color:var(--text-3);font-size:0.75rem;margin-top:1.5rem;">'
        "Los cálculos usan datos históricos de inflación (INDEC) y tasas de mercado. "
        "Rentabilidades pasadas no garantizan resultados futuros."
        "</p>",
        unsafe_allow_html=True,
    )


# ── Gráfico de barras ─────────────────────────────────────────────────────────

def _render_chart(sin_invertir: float, spy_ars: float, original: float):
    try:
        import plotly.graph_objects as go

        labels = [
            "Sin invertir<br>(valor real hoy)",
            "CEDEAR S&P 500<br>(11% anual USD)",
        ]
        values = [sin_invertir, spy_ars]
        colors = ["#ff4d6a", "#10d98a"]

        fig = go.Figure()
        for lbl, val, col in zip(labels, values, colors):
            fig.add_trace(go.Bar(
                x=[lbl],
                y=[val],
                marker_color=col,
                marker_line_width=0,
                text=[f"${val:,.0f}"],
                textposition="outside",
                textfont=dict(color="#eef2ff", size=11, family="Space Grotesk"),
                hovertemplate=f"<b>%{{x}}</b><br>${val:,.0f} ARS<extra></extra>",
            ))

        fig.add_hline(
            y=original,
            line_dash="dot",
            line_color="rgba(240,180,41,0.55)",
            line_width=1.5,
            annotation_text=f"Capital original: ${original:,.0f}",
            annotation_font_color="rgba(240,180,41,0.75)",
            annotation_font_size=10,
            annotation_position="bottom right",
        )

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94a3b8", family="DM Sans"),
            showlegend=False,
            margin=dict(t=50, b=60, l=10, r=10),
            height=360,
            yaxis=dict(
                showgrid=True,
                gridcolor="rgba(99,120,180,0.12)",
                gridwidth=1,
                showticklabels=False,
                zeroline=False,
            ),
            xaxis=dict(
                showgrid=False,
                tickfont=dict(size=10, color="#94a3b8"),
            ),
            bargap=0.4,
        )

        st.plotly_chart(fig, use_container_width=True, config={"staticPlot": True})

    except ImportError:
        import pandas as pd
        df = pd.DataFrame({
            "Escenario": ["Sin invertir", "CEDEAR S&P 500 (11% USD)"],
            "Valor ARS": [sin_invertir, spy_ars],
        }).set_index("Escenario")
        st.bar_chart(df)
