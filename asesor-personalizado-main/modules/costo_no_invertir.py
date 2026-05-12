"""
El Costo de No Invertir — pantalla de impacto emocional pre-cuestionario.
"""

import streamlit as st
import urllib.request
import json as _json

# ── Datos históricos hardcodeados ─────────────────────────────────────────────

INFLATION_ACUM = {
    1: 1.17,    # 2024: 117%
    2: 3.75,    # acumulada 2023-2024: 375%
    5: 18.47,   # acumulada 2020-2024: 1847%
}

# Plazo fijo: tasa nominal acumulada compuesta por período
_PF_ACUM = {
    1: 0.70,
    2: (1 + 1.33) * (1 + 0.70) - 1,                                      # ≈ 296%
    5: (1 + 0.36) * (1 + 0.37) * (1 + 0.75) * (1 + 1.33) * (1 + 0.70) - 1,  # ≈ 1192%
}

# Dólar MEP aproximado al inicio de cada período (ARS/USD)
_MEP_HIST = {1: 1_000.0, 2: 830.0, 5: 160.0}
_MEP_FALLBACK = 1_200.0

# Rendimiento anual en USD de alternativas conservadoras y moderadas
_ON_RATE  = 0.08   # ONs corporativas (Pampa, MercadoLibre, etc.)
_SPY_RATE = 0.11   # S&P 500 via CEDEAR (promedio histórico)

STORAGE_LABELS = {
    "caja_ahorro":     "Caja de ahorro bancaria",
    "efectivo_casa":   "Efectivo en casa",
    "plazo_fijo":      "Plazo fijo tradicional",
    "dolares_billete": "Dólares billete guardados",
}

PERIOD_LABELS = {1: "1 año", 2: "2 años", 5: "5 años"}


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
    inf      = INFLATION_ACUM[years]
    pf_rate  = _PF_ACUM[years]
    mep_then = _MEP_HIST[years]

    if storage == "dolares_billete":
        usd_amount  = amount / mep_now
        nominal_hoy = amount          # mismo USD al cambio actual
        real_hoy    = amount          # dólar preservó vs ARS
        perdida     = 0.0
        on_ars  = usd_amount * (1 + _ON_RATE)  ** years * mep_now
        spy_ars = usd_amount * (1 + _SPY_RATE) ** years * mep_now
    else:
        nominal_hoy = amount * (1 + pf_rate) if storage == "plazo_fijo" else amount
        real_hoy    = nominal_hoy / (1 + inf)
        perdida     = amount - real_hoy
        usd_then    = amount / mep_then                          # cuántos USD al cambio histórico
        on_ars  = usd_then * (1 + _ON_RATE)  ** years * mep_now
        spy_ars = usd_then * (1 + _SPY_RATE) ** years * mep_now

    return {
        "amount":       amount,
        "nominal_hoy":  nominal_hoy,
        "real_hoy":     real_hoy,
        "perdida":      perdida,
        "on_ars":       on_ars,
        "spy_ars":      spy_ars,
        "inf_pct":      inf * 100,
        "pf_pct":       pf_rate * 100,
        "mep_now":      mep_now,
        "storage":      storage,
        "years":        years,
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
            options=[1, 2, 5],
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
    on_ars    = r["on_ars"]
    spy_ars   = r["spy_ars"]
    perdida   = r["perdida"]
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

    with c3:
        gain   = on_ars - amount
        pct_on = (gain / amount * 100) if amount else 0
        st.markdown(f"""<div class="metric-card" style="border-color:rgba(16,217,138,0.35);">
  <div class="metric-label">Lo que tendría si hubiera invertido</div>
  <div class="metric-value" style="color:var(--green);">${on_ars:,.0f}</div>
  <div class="metric-sub" style="text-align:left;line-height:1.9;margin-top:0.9rem;">
    Con ONs corporativas (8% anual USD)<br>
    <span style="color:var(--green);font-weight:600;">+${gain:,.0f} ARS (+{pct_on:.0f}%)</span>
  </div>
</div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Mensaje emocional ─────────────────────────────────────────────────────
    if storage == "dolares_billete":
        usd_now = amount / mep_now
        usd_on  = on_ars / mep_now
        msg = (
            f"Sus dólares le protegieron de la devaluación del peso — eso ya es un gran paso. "
            f"Sin embargo, en {plabel} no generaron ningún rendimiento en dólares. "
            f"Si los hubiera invertido en obligaciones negociables de empresas como Pampa Energía o MercadoLibre, "
            f"hoy tendría <strong>USD {usd_on:,.0f}</strong> en lugar de <strong>USD {usd_now:,.0f}</strong>."
        )
    elif storage == "plazo_fijo":
        msg = (
            f"En {plabel} la inflación fue de <strong>{inf_pct:.0f}%</strong> "
            f"y su plazo fijo rindió el <strong>{pf_pct:.0f}%</strong> acumulado. "
            "En Argentina el plazo fijo <em>siempre</em> perdió contra la inflación. "
            "Existe una alternativa más inteligente con riesgo similar y mayor rendimiento."
        )
    else:
        msg = (
            f"En {plabel} la inflación acumulada fue de <strong>{inf_pct:.0f}%</strong>. "
            f"Sus <strong>${amount:,.0f} ARS</strong> guardados valen hoy el equivalente real de "
            f"<strong>${real_hoy:,.0f} ARS</strong> en poder adquisitivo. "
            "El dinero parado pierde valor todos los días en Argentina."
        )

    st.markdown(f"""<div class="alert-card alert-medium">
<span class="alert-icon">💡</span>
<div style="line-height:1.85;font-size:0.93rem;color:var(--text-2);">
  {msg}<br><br>
  <strong style="color:var(--text-1);">No invertir también es una decisión financiera.</strong>
  Y en Argentina, suele ser la más costosa.<br>
  <span style="color:var(--green);">La buena noticia es que a partir de hoy puede cambiar esto.</span>
</div>
</div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Gráfico comparativo ───────────────────────────────────────────────────
    st.markdown(
        f'<div class="section-title">📊 ¿Qué hubiera pasado con sus ${amount:,.0f} en {plabel}?</div>',
        unsafe_allow_html=True,
    )
    bar_sin = amount if storage == "dolares_billete" else real_hoy
    _render_chart(bar_sin, on_ars, spy_ars, amount)

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

def _render_chart(sin_invertir: float, on_ars: float, spy_ars: float, original: float):
    try:
        import plotly.graph_objects as go

        labels = [
            "Sin invertir<br>(valor real hoy)",
            "ONs corporativas<br>(8% anual USD)",
            "S&P 500 via CEDEAR<br>(11% anual USD)",
        ]
        values = [sin_invertir, on_ars, spy_ars]
        colors = ["#ff4d6a", "#10d98a", "#4fa3ff"]

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

        fig.add_annotation(
            x="S&P 500 via CEDEAR<br>(11% anual USD)",
            y=min(values) * 0.02,
            text="Referencia histórica: rendimiento promedio<br>del índice global más conocido (2019–2024)",
            showarrow=False,
            font=dict(size=8, color="#64748b"),
            align="center",
            xanchor="center",
            yanchor="bottom",
            yref="y",
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

        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    except ImportError:
        import pandas as pd
        df = pd.DataFrame({
            "Escenario": ["Sin invertir", "ONs (8% USD)", "SPY (11% USD)"],
            "Valor ARS": [sin_invertir, on_ars, spy_ars],
        }).set_index("Escenario")
        st.bar_chart(df)
