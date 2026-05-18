"""
Módulo de visualizaciones
"""

import re
import math
import plotly.graph_objects as go
import streamlit as st


PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans, sans-serif", color="#94a3b8"),
    margin=dict(l=0, r=0, t=10, b=0),
)

# Display label por perfil de riesgo (la clave interna sigue siendo "estable")
_RISK_DISPLAY = {
    "conservador": "Conservador",
    "estable":     "Balanceado",
    "moderado":    "Moderado",
    "agresivo":    "Agresivo",
}

_CATEGORY_ORDER = [
    "Liquidez",
    "Cobertura cambiaria",
    "Renta fija",
    "Fondos globales",
    "Renta variable",
]

_CATEGORY_META = {
    "Liquidez": {
        "icon":        "💵",
        "description": "Capital disponible en todo momento. Rescatable sin espera ni penalidades.",
        "color":       "#60a5fa",
    },
    "Cobertura cambiaria": {
        "icon":        "🛡️",
        "description": "Dólares legales comprados por la bolsa. Protege sus ahorros de la devaluación del peso.",
        "color":       "#f59e0b",
    },
    "Renta fija": {
        "icon":        "📄",
        "description": "Préstamos a empresas o al Estado que le devuelven su dinero con intereses en dólares. Más predecible que las acciones.",
        "color":       "#22c55e",
    },
    "Fondos globales": {
        "icon":        "🌍",
        "description": "Las 500 empresas más grandes del mundo en una sola compra — Apple, Google, Amazon, todas juntas. Es \"comprar el paquete\" en vez de elegir empresa por empresa.",
        "color":       "#4fa3ff",
    },
    "Renta variable": {
        "icon":        "📈",
        "description": "Empresas específicas que el modelo eligió por su potencial — pueden rendir más que el promedio, pero también bajar más. Acá vas con casos puntuales, no con el paquete entero.",
        "color":       "#a78bfa",
    },
}

_CATEGORY_ASSET_IDS = {
    "Liquidez": {"cash_pesos", "money_market", "plazo_fijo", "fci_t0"},
    "Cobertura cambiaria": {"mep"},
    "Renta fija": {"lecap", "cer_tx26", "cer_tx28", "cer_dicp", "fci_renta_pesos",
                   "al30", "gd30", "on_ypf", "on_corp", "on_pampa", "on_tecpetrol",
                   "al35", "gd35", "gd38", "on_tgs", "on_macro",
                   "fci_usd_rf", "fci_usd_ahorro", "fci_latam",
                   "on_meli", "on_telecom", "on_genneia", "on_vista", "on_pampa",
                   "on_tgs2", "on_arcor", "on_telecom2", "on_irsa", "on_cresud",
                   "dual_bond", "dollar_linked",
                   "gd29", "gd41"},
    "Fondos globales": {"spy", "qqq", "vti"},
    "Renta variable": {"aapl", "msft", "nvda", "meli", "ypf", "galicia"},
}

# ── Macro-categorías para el gráfico de 2 capas ────────────────────────────────
_MACRO_MAP = {
    "Pesos ARS":    ("Liquidez ARS",            "#a3e635"),
    "Dólar MEP":    ("Cobertura Cambiaria",      "#38bdf8"),
    "Bonos USD":    ("Renta Fija USD",           "#4fa3ff"),
    "CEDEARs":      ("Renta Variable Intl.",     "#a78bfa"),
    "ETFs":         ("Fondos Globales (ETFs)",   "#10d98a"),
    "Acciones ARG": ("Acciones Argentinas",      "#f59e0b"),
}

# ── Guía de compra: plataforma + cómo buscarlo ────────────────────────────────
_BROKERS_FONDOS   = "IOL, Cocos, PPI, Balanz, Bullmarket"
_BROKERS_BONOS    = "IOL, Cocos, PPI, Balanz, Bullmarket"
_BROKERS_MEP      = "IOL, Cocos, PPI, Balanz, Bullmarket"
_BROKERS_CEDEARS  = "IOL, Cocos, PPI, Balanz, Bullmarket"
_BROKERS_ACCIONES = "IOL, Cocos, PPI, Balanz, Bullmarket"

_PLATFORMS = {
    "cash_pesos":      ("Naranja X, Ualá, Mercado Pago",  "App → sección 'Cuenta'"),
    "money_market":    (f"Mercado Pago, Ualá, {_BROKERS_FONDOS}", "Fondos → Money Market"),
    "plazo_fijo":      ("Tu banco (Galicia, Santander…)", "App del banco → Inversiones"),
    "fci_t0":          (_BROKERS_FONDOS,                  "Fondos → Renta Fija T+0"),
    "lecap":           (_BROKERS_BONOS,                   "Renta Fija → S31M26 / S30J26"),
    "cer_tx26":        (_BROKERS_BONOS,                   "Renta Fija → TX26"),
    "cer_tx28":        (_BROKERS_BONOS,                   "Renta Fija → TX28"),
    "cer_dicp":        (_BROKERS_BONOS,                   "Renta Fija → DICP"),
    "fci_renta_pesos": (_BROKERS_FONDOS,                  "Fondos → Renta Fija"),
    "mep":             (_BROKERS_MEP,                     "Dólar MEP → operación AL30 48hs"),
    "al30":            (_BROKERS_BONOS,                   "Renta Fija → AL30"),
    "gd30":            (_BROKERS_BONOS,                   "Renta Fija → GD30"),
    "on_ypf":          (_BROKERS_BONOS,                   "Renta Fija → YPFDS"),
    "on_corp":         (_BROKERS_BONOS,                   "Renta Fija → YPFDS / TGSU2O / TCCUD"),
    "on_tecpetrol":    (_BROKERS_BONOS,                   "Renta Fija → TCCUD"),
    "spy":             (_BROKERS_CEDEARS,                 "CEDEARs → SPY"),
    "qqq":             (_BROKERS_CEDEARS,                 "CEDEARs → QQQ"),
    "eem":             (_BROKERS_CEDEARS,                 "CEDEARs → EEM"),
    "vti":             (_BROKERS_CEDEARS,                 "CEDEARs → VTI"),
    "gld":             (_BROKERS_CEDEARS,                 "CEDEARs → GLD"),
    "aapl":            (_BROKERS_CEDEARS,                 "CEDEARs → AAPL"),
    "msft":            (_BROKERS_CEDEARS,                 "CEDEARs → MSFT"),
    "googl":           (_BROKERS_CEDEARS,                 "CEDEARs → GOOGL"),
    "amzn":            (_BROKERS_CEDEARS,                 "CEDEARs → AMZN"),
    "nvda":            (_BROKERS_CEDEARS,                 "CEDEARs → NVDA"),
    "meli":            (_BROKERS_CEDEARS,                 "CEDEARs → MELI"),
    "meta":            (_BROKERS_CEDEARS,                 "CEDEARs → META"),
    "brk":             (_BROKERS_CEDEARS,                 "CEDEARs → BRKB"),
    "jpm":             (_BROKERS_CEDEARS,                 "CEDEARs → JPM"),
    "ko":              (_BROKERS_CEDEARS,                 "CEDEARs → KO"),
    "wmt":             (_BROKERS_CEDEARS,                 "CEDEARs → WMT"),
    "jnj":             (_BROKERS_CEDEARS,                 "CEDEARs → JNJ"),
    "pfe":             (_BROKERS_CEDEARS,                 "CEDEARs → PFE"),
    "xom":             (_BROKERS_CEDEARS,                 "CEDEARs → XOM"),
    "tsla":            (_BROKERS_CEDEARS,                 "CEDEARs → TSLA"),
    "bac":             (_BROKERS_CEDEARS,                 "CEDEARs → BAC"),
    "dis":             (_BROKERS_CEDEARS,                 "CEDEARs → DIS"),
    "ypf":             (_BROKERS_ACCIONES,                "Acciones → YPFD"),
    "galicia":         (_BROKERS_ACCIONES,                "Acciones → GGAL"),
    "teco2":           (_BROKERS_ACCIONES,                "Acciones → TECO2"),
    "pampa":           (_BROKERS_ACCIONES,                "Acciones → PAMP"),
    "vist":            (_BROKERS_ACCIONES,                "Acciones → VIST"),
    "bbar":            (_BROKERS_ACCIONES,                "Acciones → BBAR"),
    "loma":            (_BROKERS_ACCIONES,                "Acciones → LOMA"),
    # ARG nuevas
    "alua":  (_BROKERS_CEDEARS, "Acciones → ALUA"),
    "edn":   (_BROKERS_CEDEARS, "Acciones → EDN"),
    "come":  (_BROKERS_CEDEARS, "Acciones → COME"),
    "valo":  (_BROKERS_CEDEARS, "Acciones → VALO"),
    "harg":  (_BROKERS_CEDEARS, "Acciones → HARG"),
    "txar":  (_BROKERS_CEDEARS, "Acciones → TXAR"),
    "mirg":  (_BROKERS_CEDEARS, "Acciones → MIRG"),
    "moli":  (_BROKERS_CEDEARS, "Acciones → MOLI"),
    "cvh":   (_BROKERS_CEDEARS, "Acciones → CVH"),
    "metr":  (_BROKERS_CEDEARS, "Acciones → METR"),
    # CEDEARs nuevos — Bancos
    "wfc":   (_BROKERS_CEDEARS, "CEDEARs → WFC"),
    "c":     (_BROKERS_CEDEARS, "CEDEARs → C"),
    "axp":   (_BROKERS_CEDEARS, "CEDEARs → AXP"),
    "cof":   (_BROKERS_CEDEARS, "CEDEARs → COF"),
    "schw":  (_BROKERS_CEDEARS, "CEDEARs → SCHW"),
    "blk":   (_BROKERS_CEDEARS, "CEDEARs → BLK"),
    # Tech/Cloud
    "pltr":  (_BROKERS_CEDEARS, "CEDEARs → PLTR"),
    "now":   (_BROKERS_CEDEARS, "CEDEARs → NOW"),
    "crwd":  (_BROKERS_CEDEARS, "CEDEARs → CRWD"),
    "panw":  (_BROKERS_CEDEARS, "CEDEARs → PANW"),
    "ddog":  (_BROKERS_CEDEARS, "CEDEARs → DDOG"),
    "net":   (_BROKERS_CEDEARS, "CEDEARs → NET"),
    "ftnt":  (_BROKERS_CEDEARS, "CEDEARs → FTNT"),
    "coin":  (_BROKERS_CEDEARS, "CEDEARs → COIN"),
    "sq":    (_BROKERS_CEDEARS, "CEDEARs → SQ"),
    "hood":  (_BROKERS_CEDEARS, "CEDEARs → HOOD"),
    "rblx":  (_BROKERS_CEDEARS, "CEDEARs → RBLX"),
    "snow":  (_BROKERS_CEDEARS, "CEDEARs → SNOW"),
    # Pharma
    "abbv":  (_BROKERS_CEDEARS, "CEDEARs → ABBV"),
    "bmy":   (_BROKERS_CEDEARS, "CEDEARs → BMY"),
    "gild":  (_BROKERS_CEDEARS, "CEDEARs → GILD"),
    "amgn":  (_BROKERS_CEDEARS, "CEDEARs → AMGN"),
    "mrna":  (_BROKERS_CEDEARS, "CEDEARs → MRNA"),
    "regn":  (_BROKERS_CEDEARS, "CEDEARs → REGN"),
    "vrtx":  (_BROKERS_CEDEARS, "CEDEARs → VRTX"),
    # Consumo/Viajes
    "low":   (_BROKERS_CEDEARS, "CEDEARs → LOW"),
    "tjx":   (_BROKERS_CEDEARS, "CEDEARs → TJX"),
    "abnb":  (_BROKERS_CEDEARS, "CEDEARs → ABNB"),
    "bkng":  (_BROKERS_CEDEARS, "CEDEARs → BKNG"),
    "mar":   (_BROKERS_CEDEARS, "CEDEARs → MAR"),
    "hlt":   (_BROKERS_CEDEARS, "CEDEARs → HLT"),
    "ccl":   (_BROKERS_CEDEARS, "CEDEARs → CCL"),
    "rcl":   (_BROKERS_CEDEARS, "CEDEARs → RCL"),
    "dkng":  (_BROKERS_CEDEARS, "CEDEARs → DKNG"),
    "ebay":  (_BROKERS_CEDEARS, "CEDEARs → EBAY"),
    # Media/Telecom
    "spot":  (_BROKERS_CEDEARS, "CEDEARs → SPOT"),
    "t":     (_BROKERS_CEDEARS, "CEDEARs → T"),
    "vz":    (_BROKERS_CEDEARS, "CEDEARs → VZ"),
    "cmcsa": (_BROKERS_CEDEARS, "CEDEARs → CMCSA"),
    # Industrial/Defensa
    "rtx":   (_BROKERS_CEDEARS, "CEDEARs → RTX"),
    "lmt":   (_BROKERS_CEDEARS, "CEDEARs → LMT"),
    "de":    (_BROKERS_CEDEARS, "CEDEARs → DE"),
    "hon":   (_BROKERS_CEDEARS, "CEDEARs → HON"),
    "ups":   (_BROKERS_CEDEARS, "CEDEARs → UPS"),
    "fdx":   (_BROKERS_CEDEARS, "CEDEARs → FDX"),
    "ge":    (_BROKERS_CEDEARS, "CEDEARs → GE"),
    # Energía adicional
    "oxy":   (_BROKERS_CEDEARS, "CEDEARs → OXY"),
    "slb":   (_BROKERS_CEDEARS, "CEDEARs → SLB"),
    "cop":   (_BROKERS_CEDEARS, "CEDEARs → COP"),
    # Semis
    "asml":  (_BROKERS_CEDEARS, "CEDEARs → ASML"),
    "mu":    (_BROKERS_CEDEARS, "CEDEARs → MU"),
    "amat":  (_BROKERS_CEDEARS, "CEDEARs → AMAT"),
    "avgo":  (_BROKERS_CEDEARS, "CEDEARs → AVGO"),
    # Auto/EV
    "f":     (_BROKERS_CEDEARS, "CEDEARs → F"),
    "gm":    (_BROKERS_CEDEARS, "CEDEARs → GM"),
    "rivn":  (_BROKERS_CEDEARS, "CEDEARs → RIVN"),
    "nio":   (_BROKERS_CEDEARS, "CEDEARs → NIO"),
    # Utilities
    "so":    (_BROKERS_CEDEARS, "CEDEARs → SO"),
    "d":     (_BROKERS_CEDEARS, "CEDEARs → D"),
    # REITs
    "amt":   (_BROKERS_CEDEARS, "CEDEARs → AMT"),
    "pld":   (_BROKERS_CEDEARS, "CEDEARs → PLD"),
    "o":     (_BROKERS_CEDEARS, "CEDEARs → O"),
    # FCIs adicionales
    "fci_usd_rf":    (_BROKERS_FONDOS,  "Fondos → Renta Fija USD"),
    "fci_usd_ahorro":(_BROKERS_FONDOS,  "Fondos → Ahorro en Dólares"),
    "fci_latam":     (_BROKERS_FONDOS,  "Fondos → Deuda Latinoamérica"),
    "fci_acciones":  (_BROKERS_FONDOS,  "Fondos → Acciones Argentinas"),
    "fci_cedears":   (_BROKERS_FONDOS,  "Fondos → CEDEARs / Acciones Globales"),
    "fci_mixto":     (_BROKERS_FONDOS,  "Fondos → Mixto / Balanceado"),
    # ONs adicionales
    "on_meli":       (_BROKERS_BONOS,   "Renta Fija → ON MercadoLibre MLIUSD"),
    "on_telecom":    (_BROKERS_BONOS,   "Renta Fija → ON Telecom TCOMD"),
    "on_genneia":    (_BROKERS_BONOS,   "Renta Fija → ON Genneia GNCXO"),
    "on_vista":      (_BROKERS_BONOS,   "Renta Fija → ON Vista VSCOD"),
    "on_pampa":      (_BROKERS_BONOS,   "Renta Fija → ON Pampa PGN2O"),
    # Soberanos adicionales
    "gd29":          (_BROKERS_BONOS,   "Renta Fija → GD29"),
    "gd41":          (_BROKERS_BONOS,   "Renta Fija → GD41"),
    # ONs nuevas
    "on_tgs2":       (_BROKERS_BONOS,   "Renta Fija → ON TGS TGS2O"),
    "on_arcor":      (_BROKERS_BONOS,   "Renta Fija → ON Arcor RCCJO"),
    "on_telecom2":   (_BROKERS_BONOS,   "Renta Fija → ON Telecom TLCMO"),
    "on_irsa":       (_BROKERS_BONOS,   "Renta Fija → ON IRSA IRCFO"),
    "on_cresud":     (_BROKERS_BONOS,   "Renta Fija → ON Cresud CSDOO"),
    # Bonos pesos nuevos
    "dual_bond":     (_BROKERS_BONOS,   "Renta Fija → Bono Dual TDA27"),
    "dollar_linked": (_BROKERS_BONOS,   "Renta Fija → Dollar Linked TV26"),
}


def _t1() -> str:
    """Color de texto primario según el tema activo."""
    return "#1e293b" if st.session_state.get("theme") == "light" else "#eef2ff"


def _t2() -> str:
    """Color de texto secundario según el tema activo."""
    return "#475569" if st.session_state.get("theme") == "light" else "#94a3b8"


def _pie_border() -> str:
    return "#f1f5f9" if st.session_state.get("theme") == "light" else "#050810"


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _remove_asset(portfolio: dict, asset_id: str) -> dict:
    """Elimina un activo y renormaliza todos los pesos."""
    positions = [dict(p) for p in portfolio["positions"] if p["id"] != asset_id]
    if not positions:
        return portfolio

    total = sum(p["weight"] for p in positions)
    for p in positions:
        p["weight"] = round(p["weight"] / total, 4)

    cat_exp, sec_exp, cur_exp = {}, {}, {}
    for p in positions:
        cat_exp[p["category"]] = cat_exp.get(p["category"], 0) + p["weight"]
        sec_exp[p["sub"]]      = sec_exp.get(p["sub"], 0)      + p["weight"]
        cur_exp[p["currency"]] = cur_exp.get(p["currency"], 0) + p["weight"]

    pesos_pct = sum(p["weight"] for p in positions if p["currency"] == "ARS") * 100

    return {
        **portfolio,
        "positions":           positions,
        "expected_cagr":       round(sum(p["weight"] * p["expected_return"] for p in positions), 4),
        "expected_volatility": round(sum(p["weight"] * p["volatility"]      for p in positions), 4),
        "category_exposure":   cat_exp,
        "sector_exposure":     sec_exp,
        "currency_exposure":   cur_exp,
        "pesos_pct":           round(pesos_pct, 1),
        "usd_pct":             round(100 - pesos_pct, 1),
    }


# ─── Torta (misma categorización que la tabla de instrumentos) ───────────────

def render_pie_chart(portfolio: dict):
    positions = portfolio["positions"]

    # Usar la misma lógica que render_allocation_table para que ambas vistas sean consistentes
    cat_data: dict = {}
    for p in positions:
        cat   = _asset_to_user_category(p)
        color = _CATEGORY_META.get(cat, {}).get("color", "#94a3b8")
        if cat not in cat_data:
            cat_data[cat] = {"weight": 0.0, "color": color, "assets": []}
        cat_data[cat]["weight"] += p["weight"]
        cat_data[cat]["assets"].append(p)

    # Ordenar según _CATEGORY_ORDER para que sea consistente con la tabla
    sorted_macro = sorted(
        cat_data.items(),
        key=lambda x: (_CATEGORY_ORDER.index(x[0]) if x[0] in _CATEGORY_ORDER else 99),
    )

    labels = [m[0] for m in sorted_macro]
    values = [round(m[1]["weight"] * 100, 1) for m in sorted_macro]
    colors = [m[1]["color"] for m in sorted_macro]

    hovers = []
    for name, info in sorted_macro:
        lines = "<br>".join(
            f"  · {a['name'].split('(')[0].split('—')[0].strip()} ({a['weight']*100:.1f}%)"
            for a in sorted(info["assets"], key=lambda x: -x["weight"])
        )
        hovers.append(f"<b>{name}</b> — {info['weight']*100:.1f}%<br>{lines}")

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.52,
        marker=dict(colors=colors, line=dict(color=_pie_border(), width=2)),
        hovertemplate="%{customdata}<extra></extra>",
        customdata=hovers,
        textfont=dict(size=11, color=_t1()),
        textinfo="percent",
        showlegend=True,
    )])

    # Leyenda horizontal debajo del gráfico — funciona bien en mobile y desktop.
    # Plotly auto-distribuye en columnas según ancho disponible.
    _layout = {**PLOTLY_LAYOUT, "margin": dict(l=10, r=10, t=20, b=80)}
    fig.update_layout(
        **_layout,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.05,
            xanchor="center",
            x=0.5,
            font=dict(size=11, color=_t2()),
            bgcolor="rgba(0,0,0,0)",
            itemwidth=60,
        ),
        annotations=[dict(
            text=f"<b>{_RISK_DISPLAY.get(portfolio['risk_profile'], portfolio['risk_profile']).upper()}</b>",
            x=0.5, y=0.5,
            font=dict(size=13, color=_t1(), family="Syne, sans-serif"),
            showarrow=False,
        )],
        height=420,
    )

    st.plotly_chart(fig, use_container_width=True, config={"staticPlot": True})

    # Capa 2: desglose (mismas categorías que la tabla de abajo)
    with st.expander("Ver desglose detallado →"):
        for name, info in sorted_macro:
            pct   = info["weight"] * 100
            color = info["color"]
            icon  = _CATEGORY_META.get(name, {}).get("icon", "📊")
            st.markdown(
                f'<div class="macro-cat-header" style="border-left-color:{color};">'
                f'<span class="macro-cat-name">{icon}&nbsp;{name}</span>'
                f'<span class="macro-cat-pct">{pct:.0f}%</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
            for a in sorted(info["assets"], key=lambda x: -x["weight"]):
                a_pct = a["weight"] * 100
                st.markdown(
                    f'<div class="macro-asset-row">'
                    f'<span class="macro-asset-dot" style="background:{a["color"]};"></span>'
                    f'<span class="macro-asset-name">{a["name"].split("(")[0].split("—")[0].strip()}</span>'
                    f'<span class="macro-asset-ticker">{a["ticker"]}</span>'
                    f'<span class="macro-asset-pct">{a_pct:.1f}%</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )


# ─── Gráfico de evolución (3 líneas simples) ──────────────────────────────────

def render_evolution_chart(simulation: dict, initial_capital: float, years: int):
    t    = simulation["years_axis"]
    sc   = simulation["scenarios"]
    summ = simulation["summary"]

    fig = go.Figure()

    # Pésimo
    fig.add_trace(go.Scatter(
        x=t, y=sc["pesimista"],
        mode="lines",
        name="😟 Pésimo",
        line=dict(color="#ef4444", width=2.5, dash="dot"),
        hovertemplate="Año %{x:.0f}: $%{y:,.0f}<extra>Pésimo</extra>",
    ))

    # Base
    fig.add_trace(go.Scatter(
        x=t, y=sc["base"],
        mode="lines",
        name="📊 Base",
        line=dict(color="#f0b429", width=3),
        hovertemplate="Año %{x:.0f}: $%{y:,.0f}<extra>Base</extra>",
    ))

    # Excelente
    fig.add_trace(go.Scatter(
        x=t, y=sc["optimista"],
        mode="lines",
        name="🚀 Excelente",
        line=dict(color="#10d98a", width=2.5, dash="dot"),
        hovertemplate="Año %{x:.0f}: $%{y:,.0f}<extra>Excelente</extra>",
    ))

    fig.add_hline(
        y=initial_capital,
        line_dash="dot",
        line_color="rgba(100,116,139,0.4)",
        line_width=1,
        annotation_text=f"Capital inicial: ${initial_capital:,.0f}",
        annotation_font=dict(size=10, color="#64748b"),
    )

    fig.update_layout(
        **PLOTLY_LAYOUT,
        xaxis=dict(
            title="Años",
            showgrid=True,
            gridcolor="rgba(99,120,180,0.07)",
            zeroline=False,
            tickfont=dict(size=10),
        ),
        yaxis=dict(
            title="Valor USD",
            showgrid=True,
            gridcolor="rgba(99,120,180,0.07)",
            zeroline=False,
            tickformat="$,.0f",
            tickfont=dict(size=10),
        ),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.14,
            xanchor="center",
            x=0.5,
            font=dict(size=11),
            bgcolor="rgba(0,0,0,0)",
        ),
        hovermode="x unified",
        height=360,
    )

    st.plotly_chart(fig, use_container_width=True, config={"staticPlot": True})

    # Solo 2 métricas, con lenguaje simple
    col1, col2 = st.columns(2)
    with col1:
        prob_g = summ["prob_positive"] * 100
        st.markdown(f"""<div class="metric-card" style="text-align:center;">
<div class="metric-label">Chances de ganar plata</div>
<div class="metric-value" style="color:#22c55e;">{prob_g:.0f}%</div>
<div class="metric-sub">De terminar con más de lo que pusiste</div>
</div>""", unsafe_allow_html=True)
    with col2:
        prob_d = summ["prob_double"] * 100
        st.markdown(f"""<div class="metric-card" style="text-align:center;">
<div class="metric-label">Chances de duplicar</div>
<div class="metric-value" style="color:#60a5fa;">{prob_d:.0f}%</div>
<div class="metric-sub">De terminar con el doble o más</div>
</div>""", unsafe_allow_html=True)


# ─── Gráfico de barras: proyección a 1, 5 y 10 años ──────────────────────────

def render_bar_simulation(portfolio: dict, initial_capital: float,
                          currency: str = "USD", capital_original: float = None):
    # Usar el CAGR neto (descontado el haircut de costos reales). Fallback
    # defensivo al bruto si por alguna razón no está el neto.
    cagr = portfolio.get("expected_cagr_neto", portfolio["expected_cagr"])
    vol  = portfolio["expected_volatility"]

    cagr_opt  = cagr + vol * 0.5
    cagr_pess = max(cagr - vol * 0.7, -0.30)

    years  = [1, 5, 10]
    labels = ["1 año", "5 años", "10 años"]

    # factor de conversión para mostrar en la moneda del usuario
    if capital_original is None:
        capital_original = initial_capital
    display_factor = capital_original / initial_capital if initial_capital else 1.0

    def proj(c, y):    return initial_capital * (1 + c) ** y
    def proj_d(c, y):  return proj(c, y) * display_factor
    def pct(v):        return (v / initial_capital - 1) * 100

    vals_pess = [proj(cagr_pess, y) for y in years]
    vals_base = [proj(cagr,      y) for y in years]
    vals_opt  = [proj(cagr_opt,  y) for y in years]

    # valores escalados a la moneda del usuario para display
    disp_pess = [proj_d(cagr_pess, y) for y in years]
    disp_base = [proj_d(cagr,      y) for y in years]
    disp_opt  = [proj_d(cagr_opt,  y) for y in years]

    currency_label = "ARS" if currency == "ARS" else "USD"
    currency_note  = (
        "Los montos están expresados en pesos argentinos (ARS)"
        if currency == "ARS"
        else "Los montos están expresados en dólares (USD)"
    )

    def fmt_pct(v):
        p    = pct(v)
        sign = "+" if p >= 0 else ""
        return f"{sign}{p:.0f}%"

    fig = go.Figure()

    # Mostrar solo % encima de las barras (evita superposición en mobile).
    # El monto $ aparece en el hover/tap.
    # Pésimo
    fig.add_trace(go.Bar(
        name="😟 Pésimo",
        x=labels,
        y=disp_pess,
        marker_color="#ef4444",
        marker_line_width=0,
        opacity=0.85,
        text=[fmt_pct(v) for v in vals_pess],
        textposition="outside",
        textfont=dict(size=12, color="#ef4444", family="Space Grotesk, sans-serif"),
        hovertemplate=f"<b>%{{x}} — Pésimo</b><br>Capital: $%{{y:,.0f}} {currency_label}<extra></extra>",
    ))

    # Base
    fig.add_trace(go.Bar(
        name="📊 Base",
        x=labels,
        y=disp_base,
        marker_color="#f0b429",
        marker_line_width=0,
        opacity=0.9,
        text=[fmt_pct(v) for v in vals_base],
        textposition="outside",
        textfont=dict(size=12, color="#f0b429", family="Space Grotesk, sans-serif"),
        hovertemplate=f"<b>%{{x}} — Base</b><br>Capital: $%{{y:,.0f}} {currency_label}<extra></extra>",
    ))

    # Excelente
    fig.add_trace(go.Bar(
        name="🚀 Excelente",
        x=labels,
        y=disp_opt,
        marker_color="#10d98a",
        marker_line_width=0,
        opacity=0.9,
        text=[fmt_pct(v) for v in vals_opt],
        textposition="outside",
        textfont=dict(size=12, color="#10d98a", family="Space Grotesk, sans-serif"),
        hovertemplate=f"<b>%{{x}} — Excelente</b><br>Capital: $%{{y:,.0f}} {currency_label}<extra></extra>",
    ))

    # Línea de capital inicial — sin label sobre la línea (evita pisar las etiquetas
    # de % de las barras del año 1 cuando todavía no creció mucho).
    fig.add_hline(
        y=capital_original,
        line_dash="dot",
        line_color="rgba(148,163,184,0.4)",
        line_width=1.5,
    )
    # Label del capital inicial en la esquina superior izquierda del plot
    fig.add_annotation(
        xref="paper", yref="paper",
        x=0.0, y=1.0,
        text=f"— Capital inicial ${capital_original:,.0f}",
        showarrow=False,
        font=dict(size=10, color="#64748b"),
        xanchor="left",
        yanchor="bottom",
        yshift=2,
    )

    # Headroom de 15% arriba para que las etiquetas % no choquen con el borde
    _y_max = max(disp_opt) * 1.18

    _layout = {**PLOTLY_LAYOUT, "margin": dict(l=10, r=20, t=50, b=10)}
    fig.update_layout(
        **_layout,
        barmode="group",
        bargap=0.22,
        bargroupgap=0.06,
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(99,120,180,0.07)",
            zeroline=False,
            tickformat="$,.0f",
            tickfont=dict(size=10),
            title="",
            range=[0, _y_max],
        ),
        xaxis=dict(
            showgrid=False,
            tickfont=dict(size=13, family="Space Grotesk, sans-serif", color=_t1()),
        ),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.12,
            xanchor="center",
            x=0.5,
            font=dict(size=11),
            bgcolor="rgba(0,0,0,0)",
        ),
        height=420,
    )
    fig.update_traces(cliponaxis=False)

    st.plotly_chart(fig, use_container_width=True, config={"staticPlot": True})

    st.markdown(
        f'<p class="chart-currency-note">{currency_note}</p>',
        unsafe_allow_html=True,
    )

    # ── Cards de proyección eliminados ─────────────────────────────────
    # El gráfico de barras de arriba ya muestra los 3 escenarios
    # (Pésimo/Base/Excelente) × 3 períodos (1/5/10 años) visualmente.
    # Los cards repetían esa info Y mezclaban unidades ($ en card 1,
    # % en cards 2-3), generando sobrecarga cognitiva para el público
    # objetivo. Si en el futuro se quiere reintroducir un resumen
    # numérico, mantener UNA sola unidad (todo $ o todo %) y máximo
    # 1-2 cards, no 3.


# ─── Tabla de activos con botón de eliminar ───────────────────────────────────

def _asset_to_user_category(asset: dict) -> str:
    aid = asset.get("id", "")
    if aid in _CATEGORY_ASSET_IDS["Liquidez"]:
        return "Liquidez"
    if aid in _CATEGORY_ASSET_IDS["Cobertura cambiaria"]:
        return "Cobertura cambiaria"
    if aid in _CATEGORY_ASSET_IDS["Fondos globales"]:
        return "Fondos globales"
    if aid in _CATEGORY_ASSET_IDS["Renta fija"]:
        return "Renta fija"
    if aid in _CATEGORY_ASSET_IDS["Renta variable"]:
        return "Renta variable"
    if asset.get("category") in {"CEDEARs", "Acciones ARG", "Acciones"}:
        return "Renta variable"
    if asset.get("category") in {"Bonos USD", "Dólar MEP", "Pesos ARS"}:
        return "Renta fija"
    return "Renta variable"


def _group_positions_by_user_category(positions: list) -> dict:
    groups = {cat: [] for cat in _CATEGORY_ORDER}
    for p in positions:
        category = _asset_to_user_category(p)
        groups.setdefault(category, []).append(p)
    return groups


def _liquidity_label(asset_id: str) -> str:
    if asset_id in {"cash_pesos", "money_market", "fci_t0", "mep"}:
        return "Inmediata"
    if asset_id == "plazo_fijo":
        return "Al vencimiento (30d)"
    if asset_id in {"lecap", "cer_tx26", "cer_tx28", "cer_dicp", "fci_renta_pesos",
                    "al30", "gd30", "al35", "gd35", "gd38",
                    "on_ypf", "on_corp", "on_pampa", "on_tecpetrol"}:
        return "1–5 días hábiles"
    return "1–3 días hábiles"


def _asset_card_html(p: dict, capital: float, amt_prefix: str, category_items: list | None = None) -> str:
    a_pct  = p["weight"] * 100
    a_amt  = p["weight"] * capital
    razon  = (p.get("razon_en_cartera") or p.get("simple_desc") or p.get("description", ""))
    ticker = p.get("ticker", "")
    plat, how = _PLATFORMS.get(p["id"], ("IOL, PPI", f"Buscar → {ticker}"))
    short_name = p["name"].split("(")[0].split("—")[0].strip()

    # ── Liquidez como texto simple junto a las plataformas ───────────────────
    liq_text = _liquidity_label(p["id"])
    plat_line = f'🛒 {plat} · {how} · Liquidez: {liq_text}'

    # ── Nota de ponderación desigual dentro de la categoría ──────────────────
    imbalance_html = ""
    if category_items and len(category_items) >= 2:
        cat_weights = [i["weight"] for i in category_items]
        max_w = max(cat_weights)
        min_w = min(w for w in cat_weights if w > 0)
        if max_w / min_w >= 3 and abs(p["weight"] - max_w) < 0.001:
            imbalance_html = (
                '<div style="font-size:0.75rem;color:#64748b;margin-top:4px;font-style:italic;">'
                'Mayor ponderación: mejor relación retorno/riesgo para este perfil</div>'
            )

    return (
        f'<div class="asset-detail-card" style="border-left-color:{p["color"]};">'
        f'  <div class="adc-top">'
        f'    <div class="adc-title-wrap">'
        f'      <div class="adc-title">{short_name}'
        f'        <span class="adc-ticker-badge">{ticker}</span>'
        f'      </div>'
        f'    </div>'
        f'    <div class="adc-right">'
        f'      <div class="adc-pct">{a_pct:.1f}%</div>'
        f'      <div class="adc-amt">{amt_prefix}{a_amt:,.0f}</div>'
        f'    </div>'
        f'  </div>'
        f'  <div class="adc-desc">{razon}</div>'
        f'  <div class="adc-meta adc-plat">{plat_line}</div>'
        f'  {imbalance_html}'
        f'</div>'
    )


def render_allocation_table(portfolio: dict, capital: float, currency_label: str = "USD"):
    """Cards de categoría expandibles — al clic muestran activos con detalle completo."""
    positions  = portfolio["positions"]
    groups     = _group_positions_by_user_category(positions)
    amt_prefix = "$" if currency_label == "ARS" else "USD "

    html_parts = []
    for category in _CATEGORY_ORDER:
        items = groups.get(category, [])
        if not items:
            continue

        pct   = sum(p["weight"] for p in items) * 100
        meta  = _CATEGORY_META[category]
        icon  = meta["icon"]
        color = meta["color"]

        assets_html = "".join(_asset_card_html(p, capital, amt_prefix, items) for p in items)

        html_parts.append(
            f'<details class="cat-exp">'
            f'<summary class="cat-exp-summary">'
            f'  <div class="cat-l1-card" style="border-left-color:{color};">'
            f'    <div class="cat-l1-body">'
            f'      <div class="cat-l1-name">{icon}&nbsp; {category}</div>'
            f'      <div class="cat-l1-desc">{meta["description"]}</div>'
            f'    </div>'
            f'    <div class="cat-l1-right">'
            f'      <div class="cat-l1-pct" style="color:{color};">{pct:.0f}%</div>'
            f'      <div class="cat-l1-pct-sub">de tu plata</div>'
            f'    </div>'
            f'    <span class="cat-exp-chevron">›</span>'
            f'  </div>'
            f'</summary>'
            f'<div class="cat-exp-body" style="border-left-color:{color};">'
            f'  {assets_html}'
            f'</div>'
            f'</details>'
        )

    st.markdown("\n".join(html_parts), unsafe_allow_html=True)
    st.markdown(
        '<p style="font-size:0.72rem;color:#64748b;margin-top:0.6rem;text-align:center;">'
        'IOL = InvertirOnline · Cocos = Cocos Capital · PPI = Portfolio Personal · '
        'Balanz = Balanz Capital · Bullmarket Brokers. '
        'Verificá disponibilidad en cada plataforma antes de operar.'
        '</p>',
        unsafe_allow_html=True,
    )
