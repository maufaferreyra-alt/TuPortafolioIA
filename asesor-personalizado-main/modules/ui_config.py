"""
Configuración visual y CSS personalizado para FinanzasIA
Aesthetic: Luxury Dark Finance — inspired by Bloomberg terminals and premium trading platforms
"""

import streamlit as st


def apply_custom_css():
    # ── Meta tags para iOS Safari (theme-color del notch + viewport) ─────
    # Sin esto, iOS pinta de blanco la zona del notch y la barra inferior
    # del browser, aunque el body sea oscuro.
    st.markdown("""
<meta name="theme-color" content="#0f1423" media="(prefers-color-scheme: dark)">
<meta name="theme-color" content="#0f1423">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
""", unsafe_allow_html=True)

    # ── Forzar fondo dark en TODAS las capas de Streamlit ─────────────────
    # iOS Safari muestra blanco en zonas que Streamlit no controla por default
    # (header, toolbar, decoration, safe areas).
    st.markdown("""
<style>
html, body, #root, .stApp,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > section,
[data-testid="stMain"],
.main {
    background: #0f1423 !important;
    background-color: #0f1423 !important;
}
[data-testid="stHeader"],
header[data-testid="stHeader"],
.stApp > header,
[data-testid="stToolbar"],
[data-testid="stDecoration"] {
    background: #0f1423 !important;
    background-color: #0f1423 !important;
}
[data-testid="stHeader"]::before,
[data-testid="stHeader"]::after {
    background: transparent !important;
    display: none !important;
}
/* Altura mínima full viewport para que no aparezca blanco abajo */
/* Escala tipográfica global +15%: el CSS es rem-based, así que subir el
   root font-size escala todas las fuentes y el espaciado proporcionalmente.
   Mejora la legibilidad al proyectar en pantallas compartidas / jurado. */
html {
    font-size: 18.4px;
}
html, body, #root, .stApp {
    min-height: 100vh;
    min-height: 100dvh;
}
/* Safe areas para iPhone con notch */
@supports (padding: max(0px)) {
    .stApp {
        padding-top: env(safe-area-inset-top);
        padding-left: env(safe-area-inset-left);
        padding-right: env(safe-area-inset-right);
    }
}
</style>
""", unsafe_allow_html=True)

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&family=Space+Grotesk:wght@300;400;500;600;700&display=swap');

    /* ── Reset & Base ─────────────────────────────────────────────── */
    :root {
        --bg-0:       #050810;
        --bg-1:       #0b0f1a;
        --bg-2:       #111827;
        --bg-3:       #1a2235;
        --bg-card:    #0f1623;
        --border:     rgba(99,120,180,0.18);
        --border-glow:rgba(99,182,255,0.35);
        --gold:       #f0b429;
        --gold-dim:   #c99a1e;
        --green:      #10d98a;
        --green-dim:  #0bb074;
        --red:        #ff4d6a;
        --blue:       #4fa3ff;
        --blue-dim:   #2d7dcc;
        --text-1:     #eef2ff;
        --text-2:     #94a3b8;
        --text-3:     #64748b;
        --accent:     #4fa3ff;
        --font-display: 'Syne', sans-serif;
        --font-body:    'DM Sans', sans-serif;
        --font-numbers: 'Space Grotesk', sans-serif;
        --radius-sm:  8px;
        --radius-md:  14px;
        --radius-lg:  20px;
        --shadow-card: 0 4px 32px rgba(0,0,0,0.5), 0 1px 0 rgba(255,255,255,0.04) inset;
    }

    html, body, [class*="css"] {
        font-family: var(--font-body) !important;
        color: var(--text-1) !important;
        background-color: var(--bg-0) !important;
    }

    /* ── Hide Streamlit chrome ────────────────────────────────────── */
    #MainMenu, footer, header { visibility: hidden; }
    .stDeployButton { display: none; }
    [data-testid="stToolbar"],
    [data-testid="stHeader"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"] { display: none !important; }
    .block-container {
        padding: 0 2rem 4rem !important;
        max-width: 1280px !important;
    }
    
    /* ── Responsive Container ─────────────────────────────────────── */
    @media (max-width: 1024px) {
        .block-container {
            padding: 0 1.5rem 3rem !important;
            max-width: 100% !important;
        }
    }
    
    @media (max-width: 640px) {
        .block-container {
            padding: 0 1rem 2rem !important;
        }
    }

    /* ── Scrollbar ────────────────────────────────────────────────── */
    ::-webkit-scrollbar { width: 6px; background: var(--bg-1); }
    ::-webkit-scrollbar-thumb { background: var(--bg-3); border-radius: 99px; }

    /* ── Esconder iframes de utilidad (scroll JS) que generan hueco ─ */
    /* components.html(height=0) inserta un iframe envuelto en un contenedor
       con padding/margin default. Lo colapsamos para que no genere espacio. */
    .stIFrame:has(iframe[height="0"]),
    [data-testid="stIFrame"]:has(iframe[height="0"]),
    iframe[height="0"] {
        height: 0 !important;
        min-height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        display: block;
    }

    /* ── Header ───────────────────────────────────────────────────── */
    .app-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1.2rem 0 1rem;
        border-bottom: 1px solid var(--border);
        margin-bottom: 1.5rem;
        flex-wrap: wrap;
        gap: 1rem;
    }

    @media (max-width: 640px) {
        .app-header {
            padding: 0.8rem 0 0.6rem;
            margin-bottom: 1rem;
            justify-content: center;
            text-align: center;
        }
    }
    
    .app-logo {
        font-family: var(--font-display);
        font-size: 1.5rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        color: var(--text-1);
    }
    
    @media (max-width: 640px) {
        .app-logo {
            font-size: 1.2rem;
        }
    }
    
    .app-logo span { color: var(--gold); }
    .app-badge {
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--text-3);
        background: var(--bg-3);
        border: 1px solid var(--border);
        padding: 0.3rem 0.8rem;
        border-radius: 99px;
    }
    
    @media (max-width: 640px) {
        .app-badge {
            font-size: 0.65rem;
            padding: 0.25rem 0.6rem;
        }
    }

    /* ── Hero Card ────────────────────────────────────────────────── */
    .hero-card {
        background: linear-gradient(135deg, var(--bg-card) 0%, #0d1729 100%);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 3.5rem 3rem;
        text-align: center;
        box-shadow: var(--shadow-card), 0 0 80px rgba(79,163,255,0.05);
        position: relative;
        overflow: hidden;
        margin: 1rem 0 2rem;
    }
    
    @media (max-width: 768px) {
        .hero-card {
            padding: 2.5rem 2rem;
            margin: 0.5rem 0 1.5rem;
        }
    }
    
    @media (max-width: 640px) {
        .hero-card {
            padding: 1.8rem 1.5rem;
            margin: 0.5rem 0 1rem;
        }
    }
    .hero-card::before {
        content: '';
        position: absolute;
        top: -60px; right: -60px;
        width: 240px; height: 240px;
        background: radial-gradient(circle, rgba(240,180,41,0.08) 0%, transparent 70%);
        border-radius: 50%;
        pointer-events: none;
    }
    .hero-icon {
        font-size: 3.5rem;
        margin-bottom: 1rem;
        filter: drop-shadow(0 0 20px rgba(240,180,41,0.4));
    }
    .hero-features {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.9rem;
        margin-top: 2rem;
    }
    @media (max-width: 768px) {
        .hero-features { grid-template-columns: repeat(2, 1fr); gap: 0.7rem; }
    }
    @media (max-width: 480px) {
        .hero-features { grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-top: 1.2rem; }
    }
    .hero-feature-pill {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 1rem 1.1rem;
        border-radius: var(--radius-md);
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.07);
        color: var(--text-2);
        font-weight: 600;
        transition: transform 0.2s ease, border-color 0.2s ease, color 0.2s ease;
    }
    .hero-feature-pill:hover {
        transform: translateY(-1px);
        border-color: rgba(79,163,255,0.3);
        color: var(--text-1);
    }
    @media (max-width: 768px) {
        .hero-feature-pill { padding: 0.8rem 0.9rem; font-size: 0.88rem; gap: 0.55rem; }
    }
    @media (max-width: 480px) {
        .hero-feature-pill { padding: 0.65rem 0.7rem; font-size: 0.78rem; gap: 0.4rem; }
    }
    .hero-feature-icon {
        font-size: 1.2rem;
    }
    @media (max-width: 480px) {
        .hero-feature-icon { font-size: 1rem; }
    }
    
    @media (max-width: 640px) {
        .hero-icon {
            font-size: 2.5rem;
            margin-bottom: 0.8rem;
        }
    }
    
    .hero-title {
        font-family: var(--font-display);
        font-size: 2.1rem;
        font-weight: 800;
        line-height: 1.18;
        letter-spacing: -0.03em;
        color: var(--text-1);
        margin-bottom: 1rem;
    }
    
    @media (max-width: 768px) {
        .hero-title {
            font-size: 1.6rem;
        }
    }
    
    @media (max-width: 640px) {
        .hero-title {
            font-size: 1.3rem;
            margin-bottom: 0.8rem;
        }
    }
    
    .hero-subtitle {
        font-size: 1.05rem;
        font-weight: 300;
        color: var(--text-2);
        line-height: 1.7;
        margin-bottom: 2rem;
    }
    
    @media (max-width: 768px) {
        .hero-subtitle {
            font-size: 0.95rem;
            margin-bottom: 1.5rem;
        }
    }
    
    @media (max-width: 640px) {
        .hero-subtitle {
            font-size: 0.85rem;
            margin-bottom: 1rem;
            line-height: 1.5;
        }
    }
    
    .hero-human-copy {
        font-size: 1rem;
        font-weight: 400;
        color: var(--text-2);
        margin-top: 1.2rem;
        opacity: 0.85;
        font-style: italic;
    }

    @media (max-width: 640px) {
        .hero-human-copy {
            font-size: 0.9rem;
        }
    }

    /* ── Buttons ──────────────────────────────────────────────────── */
    .stButton > button {
        font-family: var(--font-display) !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
        letter-spacing: 0.02em !important;
        border-radius: var(--radius-md) !important;
        border: 1px solid rgba(79,163,255,0.4) !important;
        background: linear-gradient(135deg, #1a3a6a 0%, #0f2247 100%) !important;
        color: var(--blue) !important;
        padding: 0.7rem 1.5rem !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 12px rgba(79,163,255,0.15) !important;
        width: 100% !important;
    }
    
    @media (max-width: 640px) {
        .stButton > button {
            font-size: 0.8rem !important;
            padding: 0.6rem 1.2rem !important;
        }
    }
    
    .stButton > button:hover {
        border-color: var(--blue) !important;
        box-shadow: 0 4px 20px rgba(79,163,255,0.3) !important;
        transform: translateY(-1px) !important;
    }
    [data-testid="baseButton-primary"] > button,
    button[kind="primary"] {
        background: linear-gradient(135deg, var(--gold) 0%, var(--gold-dim) 100%) !important;
        color: #050810 !important;
        border-color: var(--gold) !important;
        box-shadow: 0 4px 20px rgba(240,180,41,0.3) !important;
    }

    /* ── Metric Cards ─────────────────────────────────────────────── */
    .metric-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        padding: 1.3rem 1.5rem;
        box-shadow: var(--shadow-card);
        transition: border-color 0.2s;
        height: 100%;
        text-align: center;
    }
    
    @media (max-width: 1024px) {
        .metric-card {
            padding: 1rem 1.2rem;
        }
    }
    
    @media (max-width: 640px) {
        .metric-card {
            padding: 0.8rem 1rem;
        }
    }
    
    .metric-card:hover { border-color: var(--border-glow); }
    .metric-label {
        font-size: 0.78rem;
        font-weight: 500;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: var(--text-3);
        margin-bottom: 0.6rem;
    }
    
    @media (max-width: 640px) {
        .metric-label {
            font-size: 0.65rem;
            margin-bottom: 0.4rem;
        }
    }
    
    .metric-value {
        font-family: var(--font-numbers);
        font-size: 2rem;
        font-weight: 600;
        letter-spacing: -0.02em;
        line-height: 1;
        font-variant-numeric: tabular-nums;
    }
    
    @media (max-width: 768px) {
        .metric-value {
            font-size: 1.5rem;
        }
    }
    
    @media (max-width: 640px) {
        .metric-value {
            font-size: 1.2rem;
        }
    }

    /* ── Section Title ────────────────────────────────────────────── */
    .section-title {
        font-family: var(--font-display);
        font-size: 1.05rem;
        font-weight: 700;
        letter-spacing: 0.02em;
        color: var(--text-1);
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid var(--border);
    }
    
    @media (max-width: 768px) {
        .section-title {
            font-size: 0.95rem;
            margin-bottom: 0.8rem;
        }
    }
    
    @media (max-width: 640px) {
        .section-title {
            font-size: 0.85rem;
            margin-bottom: 0.6rem;
        }
    }

    .chart-headline {
        font-family: var(--font-display);
        font-size: 1.05rem;
        font-weight: 600;
        color: var(--green);
        margin: 0 0 0.75rem 0;
        line-height: 1.4;
        text-align: center;
    }
    @media (max-width: 768px) {
        .chart-headline { font-size: 0.95rem; }
    }
    .chart-currency-note {
        font-size: 0.72rem;
        color: var(--text-3);
        text-align: center;
        margin: -0.25rem 0 0.75rem 0;
        font-style: italic;
    }

    /* ── Results Header ───────────────────────────────────────────── */
    .results-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    .profile-badge {
        display: inline-block;
        border: 2px solid;
        border-radius: 99px;
        padding: 0.4rem 1.4rem;
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 1rem;
    }
    .results-title {
        font-family: var(--font-display);
        font-size: 1.8rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        margin-bottom: 0.3rem;
    }
    @media (max-width: 768px) { .results-title { font-size: 1.4rem; } }
    @media (max-width: 480px) { .results-title { font-size: 1.15rem; } }
    .results-sub { color: var(--text-2); font-size: 0.9rem; }

    /* ── AI Response ──────────────────────────────────────────────── */
    .ai-response {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-left: 3px solid var(--blue);
        border-radius: var(--radius-md);
        padding: 1.5rem 1.75rem;
        line-height: 1.8;
        color: var(--text-2);
        font-size: 1rem;
    }
    .ai-response p { margin: 0 0 0.9rem 0; }
    .ai-section { margin-bottom: 1.6rem; }
    .ai-section-title {
        font-size: 0.95rem;
        font-weight: 700;
        color: var(--text-1);
        margin: 0 0 1rem 0;
        padding-bottom: 0.45rem;
        border-bottom: 1px solid var(--border);
        letter-spacing: 0.01em;
    }
    .asset-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid var(--border);
        border-left: 3px solid var(--blue);
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.85rem;
    }
    .asset-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.6rem;
    }
    .asset-name {
        font-weight: 700;
        font-size: 0.97rem;
        color: var(--text-1);
    }
    .asset-weight {
        background: var(--blue);
        color: #fff;
        font-size: 0.78rem;
        font-weight: 700;
        padding: 2px 10px;
        border-radius: 20px;
        letter-spacing: 0.03em;
    }
    .asset-row {
        font-size: 0.94rem;
        margin-bottom: 0.4rem;
        color: var(--text-2);
    }
    .asset-row strong { color: var(--text-1); margin-right: 4px; }
    .asset-row-risk { color: rgba(248,113,113,0.85) !important; }
    .asset-row-risk strong { color: #f87171 !important; }
    .ai-intro {
        background: rgba(96,165,250,0.07);
        border: 1px solid rgba(96,165,250,0.2);
        border-radius: 8px;
        padding: 0.9rem 1.1rem;
        margin-bottom: 1.4rem;
        font-size: 0.91rem;
        color: var(--text-2);
        line-height: 1.7;
    }
    .ai-tip-list { list-style: none; padding: 0; margin: 0; }
    .ai-tip-list li {
        padding: 0.55rem 0;
        border-bottom: 1px solid var(--border);
        font-size: 0.9rem;
        color: var(--text-2);
        display: flex;
        gap: 0.6rem;
        align-items: flex-start;
    }
    .ai-tip-list li:last-child { border-bottom: none; }
    .ai-tip-list li span.tip-icon { font-size: 1rem; flex-shrink: 0; padding-top: 1px; }
    .rebalance-block {
        background: rgba(255,255,255,0.03);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 0.9rem 1.1rem;
        margin-bottom: 0.85rem;
    }
    .rebalance-block strong { color: var(--text-1); display: block; margin-bottom: 0.3rem; font-size: 0.9rem; }

    /* ── Chat ─────────────────────────────────────────────────────────── */
    .chat-bubble {
        max-width: 82%;
        margin-bottom: 0.75rem;
        padding: 0.75rem 1rem;
        border-radius: 12px;
        font-size: 0.9rem;
        line-height: 1.65;
    }
    @media (max-width: 640px) {
        .chat-bubble { max-width: 96%; font-size: 0.85rem; padding: 0.65rem 0.85rem; }
    }
    .chat-label {
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        margin-bottom: 0.3rem;
        opacity: 0.6;
        text-transform: uppercase;
    }
    .chat-text { color: var(--text-1); white-space: pre-wrap; font-size: 0.97rem; line-height: 1.7; }
    .chat-user {
        background: rgba(96,165,250,0.1);
        border: 1px solid rgba(96,165,250,0.25);
        margin-left: auto;
        text-align: right;
    }
    .chat-advisor {
        background: rgba(255,255,255,0.04);
        border: 1px solid var(--border);
        margin-right: auto;
    }
    /* ── AI Empty State ───────────────────────────────────────────── */
    @keyframes aiIconPulse {
        0%, 100% { transform: scale(1);    filter: drop-shadow(0 0 10px rgba(79,163,255,0.4)); }
        50%       { transform: scale(1.1);  filter: drop-shadow(0 0 22px rgba(79,163,255,0.75)); }
    }
    @keyframes aiBtnGlow {
        0%, 100% { box-shadow: 0 2px 12px rgba(79,163,255,0.15) !important; }
        50%       { box-shadow: 0 2px 28px rgba(79,163,255,0.55), 0 0 48px rgba(79,163,255,0.2) !important; }
    }
    .ai-empty-state {
        background: linear-gradient(135deg, var(--bg-card) 0%, #0a1628 100%);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 2.5rem 2rem 2rem;
        text-align: center;
        margin-bottom: 1.2rem;
    }
    .ai-empty-icon {
        font-size: 3rem;
        display: inline-block;
        margin-bottom: 1rem;
        animation: aiIconPulse 2.5s ease-in-out infinite;
    }
    .ai-empty-title {
        font-family: var(--font-display);
        font-size: 1.05rem;
        font-weight: 700;
        color: var(--text-1);
        margin-bottom: 1.2rem;
    }
    .ai-empty-bullets {
        display: inline-flex;
        flex-direction: column;
        gap: 0.5rem;
        text-align: left;
        margin: 0 auto;
    }
    .ai-bullet {
        font-size: 0.88rem;
        color: var(--text-2);
        padding: 0.35rem 0.8rem;
        background: rgba(79,163,255,0.06);
        border-left: 2px solid var(--blue);
        border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
    }
    /* Glow on the CTA button that follows the marker div */
    div[data-testid="stMarkdownContainer"]:has(.ai-cta-marker) + div[data-testid="stHorizontalBlock"] button,
    div[data-testid="stMarkdownContainer"]:has(.ai-cta-marker) ~ div[data-testid="stHorizontalBlock"] button {
        animation: aiBtnGlow 2s ease-in-out infinite !important;
        border-color: var(--blue) !important;
    }

    /* ── Alert Cards ──────────────────────────────────────────────── */
    .alert-card {
        display: flex;
        align-items: flex-start;
        gap: 1rem;
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        padding: 1rem 1.2rem;
        margin-bottom: 0.8rem;
        font-size: 0.88rem;
    }
    .alert-high   { border-left: 3px solid var(--red); }
    .alert-medium { border-left: 3px solid var(--gold); }
    .alert-low    { border-left: 3px solid var(--green); }
    .alert-icon   { font-size: 1.2rem; margin-top: 0.1rem; flex-shrink: 0; }

    /* ── Form Elements ────────────────────────────────────────────── */
    .stSlider > div > div { background: var(--bg-3) !important; }
    .stSlider [data-baseweb="slider"] [data-testid="stThumbValue"] {
        background: var(--blue) !important;
    }
    .stRadio > label { font-size: 1rem !important; color: var(--text-2) !important; }
    div[data-testid="stRadio"] div[role="radiogroup"] label,
    div[data-testid="stRadio"] div[role="radiogroup"] label p {
        color: #d0d5e0 !important;
        font-size: 1rem !important;
    }
    @media (max-width: 640px) {
        div[data-testid="stRadio"] div[role="radiogroup"] label,
        div[data-testid="stRadio"] div[role="radiogroup"] label p {
            font-size: 1rem !important;
        }
    }
    .stSelectbox > div > div {
        background: var(--bg-2) !important;
        border-color: var(--border) !important;
        border-radius: var(--radius-sm) !important;
        color: var(--text-1) !important;
    }
    .stNumberInput > div > div > input {
        background: var(--bg-2) !important;
        border-color: var(--border) !important;
        color: var(--text-1) !important;
    }

    /* ── Progress Step ────────────────────────────────────────────── */
    .step-progress {
        display: flex;
        justify-content: center;
        gap: 0.5rem;
        margin-bottom: 2rem;
    }
    .step-dot {
        width: 8px; height: 8px;
        border-radius: 50%;
        background: var(--bg-3);
        border: 1px solid var(--border);
        transition: all 0.3s;
    }
    .step-dot.active {
        background: var(--gold);
        border-color: var(--gold);
        width: 24px; border-radius: 4px;
    }
    .step-dot.done { background: var(--green); border-color: var(--green); }

    /* ── Native table (column-based) ─────────────────────────────── */
    .tbl-header {
        font-family: var(--font-display);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.09em;
        text-transform: uppercase;
        color: var(--text-3);
        padding: 0.5rem 0.3rem 0.6rem;
    }
    .tbl-divider {
        border-top: 1px solid var(--border);
        margin: 0 0 0.15rem;
    }
    .tbl-cell {
        font-size: 0.93rem;
        color: var(--text-2);
        padding: 0.65rem 0.3rem;
        border-bottom: 1px solid rgba(99,120,180,0.08);
        min-height: 56px;
    }
    .tbl-text { color: var(--text-2); font-size: 0.9rem; }
    .asset-name { color: #eef2ff; font-weight: 600; font-size: 0.95rem; }
    .asset-sub  { color: var(--text-3); font-size: 0.8rem; }
    .asset-dot {
        display: inline-block;
        width: 10px; height: 10px;
        border-radius: 50%;
        margin-right: 8px;
        vertical-align: middle;
    }
    .pct-bar-bg {
        background: var(--bg-3);
        border-radius: 99px;
        height: 6px;
        width: 100%;
        overflow: hidden;
    }
    .pct-bar-fill {
        height: 100%;
        border-radius: 99px;
        transition: width 0.8s ease;
    }
    .tag {
        display: inline-block;
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.06em;
        padding: 0.2rem 0.6rem;
        border-radius: 4px;
        text-transform: uppercase;
    }

    /* ── Asset Simple View ────────────────────────────────────────── */
    .asset-simple-card {
        display: flex;
        align-items: center;
        gap: 1rem;
        background: var(--bg-3);
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        padding: 1rem 1.2rem;
        margin-bottom: 0.6rem;
        transition: border-color 0.2s;
    }
    .asset-simple-card:hover { border-color: rgba(79,163,255,0.3); }
    .asc-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        flex-shrink: 0;
    }
    .asc-content { flex: 1; min-width: 0; }
    .asc-name {
        font-weight: 600;
        color: var(--text-1);
        font-size: 0.9rem;
        margin-bottom: 0.2rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .asc-desc {
        font-size: 0.78rem;
        color: var(--text-2);
        line-height: 1.4;
    }
    .asc-pct {
        font-family: var(--font-numbers);
        font-size: 1.3rem;
        font-weight: 700;
        color: var(--text-1);
        text-align: right;
        flex-shrink: 0;
        line-height: 1.1;
    }
    .asc-pct-sub {
        display: block;
        font-size: 0.6rem;
        font-weight: 400;
        color: var(--text-3);
        font-family: var(--font-body);
    }

    .category-card {
        display: flex;
        justify-content: space-between;
        gap: 1rem;
        flex-wrap: wrap;
        background: var(--bg-3);
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        padding: 1rem 1.2rem;
        margin-bottom: 0.75rem;
        transition: border-color 0.2s ease;
    }
    .category-card:hover { border-color: rgba(79,163,255,0.3); }
    .category-card-left { min-width: 0; }
    .category-label {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.25rem 0.65rem;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin-bottom: 0.6rem;
    }
    .category-title {
        font-size: 1rem;
        font-weight: 700;
        color: var(--text-1);
        margin-bottom: 0.35rem;
    }
    .category-desc {
        color: var(--text-2);
        font-size: 0.88rem;
        line-height: 1.6;
    }
    .category-card-right {
        display: flex;
        align-items: flex-end;
        justify-content: flex-end;
        min-width: 110px;
    }
    .category-pct {
        font-family: var(--font-numbers);
        font-size: 1.8rem;
        color: var(--text-1);
        font-weight: 800;
        line-height: 1;
    }
    .category-pct-sub {
        font-size: 0.74rem;
        color: var(--text-3);
        margin-top: 0.15rem;
    }
    .detail-note,
    .detail-footer {
        color: var(--text-2);
        font-size: 0.9rem;
        margin-bottom: 1rem;
    }
    .asset-detail-card {
        background: rgba(79,163,255,0.05);
        border: 1px solid rgba(79,163,255,0.1);
        border-radius: var(--radius-md);
        padding: 1rem 1rem 0.9rem;
        margin-bottom: 0.85rem;
    }
    .adc-top {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 1rem;
        flex-wrap: wrap;
        margin-bottom: 0.55rem;
    }
    .adc-title-wrap { min-width: 0; flex: 1; }
    .adc-title {
        font-weight: 700;
        color: var(--text-1);
        font-size: 0.95rem;
        margin-bottom: 0.2rem;
    }
    .adc-meta {
        color: var(--text-3);
        font-size: 0.8rem;
        line-height: 1.5;
    }
    .adc-pct {
        font-family: var(--font-numbers);
        font-size: 1.2rem;
        font-weight: 800;
        color: var(--text-1);
        text-align: right;
        flex-shrink: 0;
    }
    .adc-desc {
        color: var(--text-2);
        font-size: 0.88rem;
        line-height: 1.6;
        margin-bottom: 0.7rem;
    }
    .adc-footer {
        color: var(--text-3);
        font-size: 0.85rem;
        font-weight: 600;
    }
    @media (max-width: 640px) {
        .asc-name { font-size: 0.82rem; }
        .asc-desc { font-size: 0.72rem; }
        .asc-pct  { font-size: 1.1rem; }
    }

    /* ── st.chat_input — sticky bottom (Lucas) ─────────────────────── */
    /* Streamlit lo posiciona fijo al fondo del viewport. Aseguramos
       safe-area-inset-bottom para iPhone con notch + dark theme. */
    [data-testid="stChatInput"] {
        background: #0f1423 !important;
        border-top: 1px solid rgba(148,163,184,0.12) !important;
        padding-bottom: env(safe-area-inset-bottom) !important;
    }
    [data-testid="stChatInput"] textarea,
    [data-testid="stChatInputTextArea"] {
        background: rgba(255,255,255,0.04) !important;
        color: var(--text-1) !important;
        border-color: rgba(148,163,184,0.2) !important;
    }
    [data-testid="stChatInput"] textarea:focus,
    [data-testid="stChatInputTextArea"]:focus {
        border-color: rgba(79,163,255,0.5) !important;
        box-shadow: 0 0 0 1px rgba(79,163,255,0.2) !important;
    }
    /* Padding extra al body para que el chat_input no tape contenido */
    .block-container {
        padding-bottom: 6rem !important;
    }
    @media (max-width: 640px) {
        .block-container {
            padding-bottom: 7rem !important;
        }
        [data-testid="stChatInput"] textarea,
        [data-testid="stChatInputTextArea"] {
            font-size: 0.88rem !important;
        }
    }

    /* ── Remove Confirm Banner ────────────────────────────────────── */
    .remove-confirm {
        background: rgba(239,68,68,0.08);
        border: 1px solid rgba(239,68,68,0.3);
        border-radius: var(--radius-sm);
        padding: 0.75rem 1rem;
        font-size: 0.88rem;
        color: var(--text-2);
        margin-bottom: 0.75rem;
        line-height: 1.5;
    }
    .remove-confirm strong { color: var(--text-1); }

    /* ── Tabs ─────────────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        background: var(--bg-1) !important;
        border-radius: var(--radius-sm) !important;
        padding: 4px !important;
        gap: 4px !important;
        border: 1px solid var(--border) !important;
    }
    
    @media (max-width: 640px) {
        .stTabs [data-baseweb="tab-list"] {
            padding: 2px !important;
            gap: 2px !important;
            overflow-x: auto !important;
            flex-wrap: nowrap !important;
            -webkit-overflow-scrolling: touch;
        }
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: var(--text-3) !important;
        border-radius: 6px !important;
        font-family: var(--font-body) !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
    }
    
    @media (max-width: 640px) {
        .stTabs [data-baseweb="tab"] {
            font-size: 0.7rem !important;
            padding: 0.3rem 0.5rem !important;
        }
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--bg-3) !important;
        color: var(--text-1) !important;
    }
    .stTabs [data-baseweb="tab-highlight"] { display: none !important; }

    /* ── Expander ─────────────────────────────────────────────────── */
    /* Streamlit 1.57+ pinta su propio border/background en MÚLTIPLES
       wrappers anidados: [data-testid="stExpander"] + div intermedio +
       <details>. Los neutralizamos todos para que el ÚNICO recuadro
       visible sea el <summary>. Sin este reset, se ven 2-3 cuadros
       superpuestos. La regla excluye explícitamente .streamlit-expanderContent
       para que su styling propio (background, border) sobreviva cuando
       el expander se abre. */
    [data-testid="stExpander"],
    [data-testid="stExpander"] > div:not(.streamlit-expanderContent),
    [data-testid="stExpander"] > details {
        background: transparent !important;
        border: none !important;
        border-radius: 0 !important;
        box-shadow: none !important;
        padding: 0 !important;
    }
    .streamlit-expanderHeader,
    [data-testid="stExpander"] > details > summary {
        background: var(--bg-2) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        font-size: 0.85rem !important;
        color: var(--text-2) !important;
        outline: none !important;
        box-shadow: none !important;
    }
    [data-testid="stExpander"] > details[open],
    [data-testid="stExpander"] > details[open] > summary {
        border-color: var(--border) !important;
        outline: none !important;
        box-shadow: none !important;
    }
    [data-testid="stExpander"] > details > summary:focus,
    [data-testid="stExpander"] > details > summary:active {
        outline: none !important;
        box-shadow: none !important;
        border-color: var(--border) !important;
    }
    .streamlit-expanderContent {
        background: var(--bg-1) !important;
        border: 1px solid var(--border) !important;
        border-top: none !important;
    }

    /* ── Expanders grandes — aplica a todos los de la página principal ── */
    [data-testid="stExpander"] > details > summary {
        padding: 20px 24px !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        color: var(--text-1) !important;
        min-height: 68px !important;
        display: flex !important;
        align-items: center !important;
    }
    [data-testid="stExpander"] > details > summary > span,
    [data-testid="stExpander"] > details > summary p {
        font-size: 1rem !important;
        font-weight: 600 !important;
    }
    [data-testid="stExpander"] > details > summary:hover {
        background: rgba(255,255,255,0.03) !important;
    }
    /* Borde izquierdo por color usando el marcador en el DOM padre */
    [data-testid="stVerticalBlock"]:has(.big-expander-orange) > div > [data-testid="stExpander"] > details {
        border-left: 3px solid #f59e0b !important;
    }
    [data-testid="stVerticalBlock"]:has(.big-expander-green) > div > [data-testid="stExpander"] > details {
        border-left: 3px solid #22c55e !important;
    }
    [data-testid="stVerticalBlock"]:has(.big-expander-blue) > div > [data-testid="stExpander"] > details {
        border-left: 3px solid #38bdf8 !important;
    }
    [data-testid="stVerticalBlock"]:has(.big-expander-red) > div > [data-testid="stExpander"] > details {
        border-left: 3px solid #ef4444 !important;
    }

    /* ── Footer ───────────────────────────────────────────────────── */
    .app-footer {
        margin-top: 4rem;
        padding: 1.5rem 0;
        border-top: 1px solid var(--border);
        text-align: center;
        font-size: 0.78rem;
        color: var(--text-3);
    }
    .disclaimer {
        font-size: 0.75rem;
        color: var(--text-3);
        margin-top: 1.5rem;
        padding: 0.8rem;
        background: rgba(240,180,41,0.05);
        border: 1px solid rgba(240,180,41,0.15);
        border-radius: var(--radius-sm);
    }

    /* ── Audience note (intro) ────────────────────────────────── */
    .audience-note {
        background: rgba(79,163,255,0.07);
        border: 1px solid rgba(79,163,255,0.2);
        border-radius: var(--radius-md);
        padding: 1rem 1.4rem;
        font-size: 0.9rem;
        color: var(--text-2);
        text-align: center;
    }

    /* ── Profiler card ────────────────────────────────────────── */
    .profiler-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 2.2rem 2rem 1.5rem;
        box-shadow: var(--shadow-card);
        margin-bottom: 1.5rem;
    }
    
    @media (max-width: 768px) {
        .profiler-card {
            padding: 1.5rem 1.5rem 1.2rem;
            margin-bottom: 1rem;
        }
    }
    
    @media (max-width: 640px) {
        .profiler-card {
            padding: 1.2rem 1rem 1rem;
            margin-bottom: 0.8rem;
        }
    }
    
    .q-emoji { 
        font-size: 2.2rem;
        margin-bottom: 0.6rem;
    }
    
    @media (max-width: 640px) {
        .q-emoji {
            font-size: 1.8rem;
            margin-bottom: 0.5rem;
        }
    }
    
    .q-title {
        font-family: var(--font-display);
        font-size: 1.25rem;
        font-weight: 700;
        margin-bottom: 0.4rem;
        color: var(--text-1);
    }
    
    @media (max-width: 768px) {
        .q-title {
            font-size: 1.1rem;
        }
    }
    
    @media (max-width: 640px) {
        .q-title {
            font-size: 0.95rem;
        }
    }
    
    .profiler-card p.hint {
        font-size: 0.84rem;
        color: var(--text-3);
        margin-bottom: 0;
    }

    @media (max-width: 640px) {
        .profiler-card p.hint {
            font-size: 0.75rem;
        }
    }

    .progress-wrap {
        margin-bottom: 1.2rem;
    }
    .progress-label {
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--text-2);
        margin-bottom: 0.4rem;
        opacity: 0.7;
    }
    .progress-track {
        width: 100%;
        height: 6px;
        background: var(--bg-3);
        border-radius: 99px;
        overflow: hidden;
    }
    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, var(--blue-dim), var(--blue));
        border-radius: 99px;
        transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
    }

    /* ── Explanation flex wrapper (centrado confiable) ───────── */
    .explain-outer {
        display: flex;
        justify-content: center;
        width: 100%;
        margin-top: 0.75rem;
    }
    .reveal-explanation, .summary-explain {
        max-width: 560px;
        width: 100%;
        text-align: left;
        margin: 0;
        padding: 0.8rem 1rem 0.8rem 1.1rem;
        border-left: 3px solid rgba(255,255,255,0.12);
        background: rgba(255,255,255,0.025);
        border-radius: 0 8px 8px 0;
        line-height: 1.75;
    }
    @media (max-width: 640px) {
        .reveal-explanation, .summary-explain {
            padding: 0.65rem 0.8rem 0.65rem 0.9rem;
        }
    }

    /* ── Profile Reveal ───────────────────────────────────────── */
    .reveal-card {
        background: linear-gradient(135deg, var(--bg-card) 0%, #0a1628 100%);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 2.5rem 2.2rem 2rem;
        text-align: center;
        box-shadow: var(--shadow-card);
        margin-bottom: 1.5rem;
    }
    @media (max-width: 768px) { .reveal-card { padding: 1.8rem 1.5rem 1.5rem; } }
    @media (max-width: 480px) { .reveal-card { padding: 1.2rem 1rem; margin-bottom: 1rem; } }
    .reveal-badge {
        display: inline-block;
        font-family: var(--font-display);
        font-size: 1.4rem;
        font-weight: 800;
        border: 2px solid;
        border-radius: 99px;
        padding: 0.5rem 1.6rem;
        margin-bottom: 1rem;
        letter-spacing: -0.01em;
    }
    @media (max-width: 480px) { .reveal-badge { font-size: 1.1rem; padding: 0.4rem 1.1rem; } }
    .reveal-tagline {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--text-1);
        margin-bottom: 0.8rem;
        text-align: center;
    }
    @media (max-width: 480px) { .reveal-tagline { font-size: 0.95rem; } }
    .reveal-explanation {
        font-size: 0.93rem;
        color: var(--text-2);
        line-height: 1.75;
    }
    @media (max-width: 480px) { .reveal-explanation { font-size: 0.82rem; line-height: 1.6; } }
    .reveal-columns {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1rem;
        margin-bottom: 1.5rem;
    }
    @media (max-width: 768px) {
        .reveal-columns {
            grid-template-columns: 1fr;
        }
    }
    .reveal-section {
        background: rgba(255,255,255,0.03);
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        padding: 1.2rem 1.4rem;
        text-align: left;
    }
    .reveal-section-title {
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: var(--text-3);
        margin-bottom: 0.85rem;
    }
    .reveal-item {
        font-size: 0.88rem;
        color: var(--text-2);
        padding: 0.4rem 0;
        border-bottom: 1px solid rgba(99,120,180,0.1);
        line-height: 1.5;
    }
    .reveal-item:last-child { border-bottom: none; }

    /* ── Summary panel ────────────────────────────────────────── */
    .summary-panel {
        background: linear-gradient(135deg, var(--bg-card) 0%, #0d1e35 100%);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 2rem 2.2rem;
        box-shadow: var(--shadow-card);
        margin-bottom: 1.5rem;
    }
    .summary-top { text-align: center; margin-bottom: 1.8rem; }
    .profile-pill {
        display: inline-block;
        border-radius: 99px;
        padding: 0.35rem 1.2rem;
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 0.9rem;
    }
    .summary-title {
        font-family: var(--font-display);
        font-size: 1.6rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        margin-bottom: 0.5rem;
        color: var(--text-1);
    }
    @media (max-width: 768px) { .summary-title { font-size: 1.25rem; } }
    @media (max-width: 480px) { .summary-title { font-size: 1.05rem; } }
    .summary-explain {
        color: var(--text-2);
        font-size: 1.05rem;
        line-height: 1.7;
    }
    
    @media (max-width: 768px) {
        .summary-explain {
            font-size: 0.88rem;
        }
    }
    
    @media (max-width: 640px) {
        .summary-explain {
            font-size: 0.8rem;
        }
    }
    
    .summary-grid {
        display: grid;
        gap: 1rem;
        margin-bottom: 1rem;
    }
    .summary-main-grid {
        grid-template-columns: repeat(3, 1fr);
    }
    .summary-detail-grid {
        grid-template-columns: repeat(3, 1fr);
        margin-top: 0.75rem;
    }

    @media (max-width: 768px) {
        /* Mantener Capital/Horizonte/Retorno en una sola fila horizontal compacta */
        .summary-main-grid {
            grid-template-columns: repeat(3, 1fr);
            gap: 0.4rem;
        }
        .summary-main-grid .summary-item {
            padding: 0.5rem 0.4rem;
        }
        .summary-main-grid .si-label {
            font-size: 0.55rem;
            text-transform: none;
            letter-spacing: 0;
            margin-bottom: 0.2rem;
        }
        .summary-main-grid .si-value {
            font-size: 0.95rem;
        }
        .summary-main-grid .si-sub { display: none; }

        .summary-detail-grid {
            grid-template-columns: repeat(2, 1fr);
            gap: 0.5rem;
        }
    }

    @media (max-width: 480px) {
        .summary-detail-grid {
            grid-template-columns: 1fr;
            gap: 0.4rem;
        }
    }

    .summary-detail {
        margin-bottom: 1rem;
    }
    .summary-detail-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.4rem;
        list-style: none;
        cursor: pointer;
        font-size: 0.78rem;
        font-weight: 600;
        color: var(--blue);
        padding: 0.5rem 1rem;
        border: 1px solid rgba(79,163,255,0.25);
        border-radius: var(--radius-sm);
        background: rgba(79,163,255,0.05);
        transition: background 0.2s, border-color 0.2s;
        user-select: none;
        width: 100%;
        box-sizing: border-box;
    }
    .summary-detail-btn::-webkit-details-marker { display: none; }
    .summary-detail-btn::marker { display: none; }
    .summary-detail-btn::after {
        content: "↓";
        display: inline-block;
        transition: transform 0.3s ease;
    }
    .summary-detail[open] .summary-detail-btn::after {
        transform: rotate(180deg);
    }
    .summary-detail-btn:hover {
        background: rgba(79,163,255,0.1);
        border-color: rgba(79,163,255,0.45);
    }

    @keyframes detailSlideDown {
        from { opacity: 0; transform: translateY(-6px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    .summary-detail[open] .summary-detail-grid {
        animation: detailSlideDown 0.25s ease-out;
    }
    
    .summary-item {
        background: var(--bg-3);
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        padding: 1rem;
        text-align: center;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
    
    @media (max-width: 640px) {
        .summary-item {
            padding: 0.8rem;
        }
    }
    
    .si-label {
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.07em;
        color: var(--text-3);
        margin-bottom: 0.4rem;
    }
    
    @media (max-width: 640px) {
        .si-label {
            font-size: 0.65rem;
        }
    }
    
    .si-value {
        font-family: var(--font-numbers);
        font-size: 1.3rem;
        font-weight: 600;
        letter-spacing: -0.02em;
        font-variant-numeric: tabular-nums;
        color: var(--text-1);
    }
    .si-sub {
        font-size: 0.65rem;
        color: var(--text-3);
        margin-top: 0.25rem;
        line-height: 1.3;
    }
    .summary-desc {
        background: rgba(79,163,255,0.06);
        border: 1px solid rgba(79,163,255,0.15);
        border-left: 3px solid var(--blue);
        border-radius: var(--radius-md);
        padding: 1rem 1.4rem;
        font-size: 1rem;
        color: var(--text-2);
        line-height: 1.75;
        text-align: center;
    }

    .results-timeline-card {
        margin-top: 0.75rem;
        border-left: 3px solid #a78bfa !important;
        background: rgba(167,139,250,0.06) !important;
    }
    .results-timeline-text {
        font-size: 0.9rem !important;
        color: var(--text-2) !important;
        line-height: 1.65 !important;
        padding-top: 0.25rem;
    }

    .worst-case-context {
        margin-top: 0.6rem;
        font-size: 0.8rem;
        color: var(--text-3);
        line-height: 1.55;
        padding: 0.5rem 0.75rem;
        background: rgba(249,115,22,0.06);
        border-radius: 6px;
        border-left: 2px solid #f97316;
    }

    .market-context-bar {
        background: rgba(16, 217, 138, 0.06);
        border: 1px solid rgba(16, 217, 138, 0.18);
        border-radius: var(--radius-md);
        padding: 0.55rem 1.2rem;
        font-size: 0.82rem;
        color: var(--text-3);
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .market-context-bar strong { color: var(--text-2); }

    .action-guide {
        display: grid;
        gap: 1rem;
        margin-top: 1rem;
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 1.5rem 1.6rem;
    }
    .action-step {
        display: grid;
        grid-template-columns: auto 1fr;
        gap: 1rem;
        align-items: start;
        padding: 1rem 0;
        border-bottom: 1px solid rgba(255,255,255,0.06);
    }
    .action-step:last-child { border-bottom: none; }
    .action-step-number {
        width: 2.7rem;
        height: 2.7rem;
        min-width: 2.7rem;
        border-radius: 50%;
        display: grid;
        place-items: center;
        font-weight: 700;
        color: var(--bg-0);
        background: var(--gold);
        font-size: 1rem;
    }
    .action-step-body {
        display: grid;
        gap: 0.3rem;
    }
    .action-step-title {
        font-family: var(--font-display);
        font-size: 1rem;
        font-weight: 700;
        color: var(--text-1);
    }
    .action-step-copy {
        color: var(--text-2);
        font-size: 0.95rem;
        line-height: 1.6;
    }
    .action-step-help {
        margin-top: 0.55rem;
        border: 1px solid rgba(79,163,255,0.15);
        border-radius: var(--radius-sm);
        background: rgba(79,163,255,0.04);
        padding: 0.75rem 1rem;
    }
    .action-step-help summary {
        cursor: pointer;
        font-weight: 600;
        color: var(--blue);
        list-style: none;
    }
    .action-step-help summary::-webkit-details-marker { display: none; }
    .action-step-help div {
        margin-top: 0.7rem;
        color: var(--text-2);
        font-size: 0.9rem;
        line-height: 1.6;
    }

    /* ── Metric card sub ──────────────────────────────────────── */
    .metric-sub {
        font-size: 0.72rem;
        color: var(--text-3);
        margin-top: 0.3rem;
    }

    /* ── Remove asset button (✕) ─────────────────────────────── */
    button:has(> div > p:only-child) {
        padding: 0.25rem 0.55rem !important;
        font-size: 0.8rem !important;
        border-radius: 6px !important;
        border-color: rgba(239,68,68,0.3) !important;
        color: #f87171 !important;
        background: rgba(239,68,68,0.08) !important;
        box-shadow: none !important;
    }

    /* ── Radio options styled ─────────────────────────────────── */
    .stRadio [data-baseweb="radio"] {
        background: var(--bg-2) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        padding: 0.7rem 1rem !important;
        margin-bottom: 0.4rem !important;
        transition: border-color 0.2s !important;
    }
    .stRadio [data-baseweb="radio"]:hover {
        border-color: var(--blue) !important;
    }

    /* ── Cuestionario MOBILE compacto: que entre todo en 1 pantalla ─ */
    @media (max-width: 640px) {
        /* Card del cuestionario muy compacta */
        .profiler-card {
            padding: 0.85rem 0.9rem 0.7rem !important;
            margin-bottom: 0.5rem !important;
        }
        .q-emoji {
            font-size: 1.5rem !important;
            margin-bottom: 0.3rem !important;
        }
        .q-title {
            font-size: 0.95rem !important;
            line-height: 1.3 !important;
            margin-bottom: 0.25rem !important;
        }
        .profiler-card p.hint {
            font-size: 0.72rem !important;
            line-height: 1.4 !important;
        }
        /* Progress más chico */
        .progress-wrap { margin-bottom: 0.5rem !important; }
        .progress-label {
            font-size: 0.6rem !important;
            margin-bottom: 0.2rem !important;
        }
        .progress-track { height: 4px !important; }
        /* Radio options compactos para que entren todas */
        .stRadio [data-baseweb="radio"] {
            padding: 0.5rem 0.7rem !important;
            margin-bottom: 0.3rem !important;
            font-size: 0.82rem !important;
        }
        /* Texto dentro del radio más chico */
        div[data-testid="stRadio"] div[role="radiogroup"] label,
        div[data-testid="stRadio"] div[role="radiogroup"] label p {
            font-size: 0.82rem !important;
            line-height: 1.35 !important;
        }
        /* Botones de navegación compactos al pie */
        .stRadio + div .stButton > button,
        .stButton[data-key^="next_"] > button,
        .stButton[data-key^="back_"] > button {
            padding: 0.5rem 0.8rem !important;
            font-size: 0.78rem !important;
        }
        /* Reducir gap general entre elementos */
        [data-testid="stVerticalBlock"] { gap: 0.4rem !important; }
        /* Padding del contenedor principal */
        .block-container {
            padding-top: 0.5rem !important;
            padding-bottom: 0.5rem !important;
        }
    }

    /* ── Responsive Columns: stack on tablet & mobile ────────────── */
    @media (max-width: 768px) {
        [data-testid="stHorizontalBlock"] {
            flex-direction: column !important;
            gap: 0.75rem !important;
        }
        [data-testid="stHorizontalBlock"] > [data-testid="column"] {
            width: 100% !important;
            min-width: 100% !important;
            flex: unset !important;
        }
    }

    /* ── Metrics grid (4 KPIs responsive) ─────────────────────────── */
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin-bottom: 1rem;
    }
    @media (max-width: 1024px) {
        .metrics-grid { grid-template-columns: repeat(2, 1fr); gap: 0.75rem; }
    }
    @media (max-width: 768px) {
        /* En mobile mantener 2x2 (no colapsar a 1 columna) */
        .metrics-grid { grid-template-columns: 1fr 1fr; gap: 0.5rem; }
        .metrics-grid .metric-card { padding: 0.7rem 0.6rem; }
    }

    /* ── Make Streamlit containers responsive ───────────────────── */
    @media (max-width: 640px) {
        [data-testid="stMetricContainer"] {
            margin-bottom: 0.5rem !important;
        }
    }

    /* ── Mobile form elements ──────────────────────────────────────– */
    @media (max-width: 640px) {
        input, textarea, select, [data-baseweb="select"] {
            font-size: 16px !important; /* evita zoom automático en iOS */
        }
        .stSlider > div {
            padding: 0.5rem 0 !important;
        }
    }

    /* ── Ensure text doesn't overflow ──────────────────────────────– */
    @media (max-width: 640px) {
        p, span, div {
            word-break: break-word !important;
        }
    }

    /* ── Header nav button ───────────────────────────────────────── */
    .header-nav-spacer { padding-top: 1.1rem; }

    /* ── Currency toggle ─────────────────────────────────────────── */
    .currency-toggle-wrap {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        margin-bottom: 1rem;
        flex-wrap: wrap;
    }
    .currency-toggle-label {
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: var(--text-3);
    }
    .fx-rate-note {
        text-align: center;
        font-size: 0.72rem;
        color: var(--text-3);
        margin-top: 0.5rem;
        font-style: italic;
    }

    /* ── Theme Toggle ────────────────────────────────────────────── */
    .theme-toggle-row {
        margin-top: 0.25rem;
        display: flex;
        align-items: center;
        gap: 0.4rem;
        justify-content: flex-end;
    }
    .theme-toggle-label {
        font-size: 0.72rem;
        color: var(--text-3);
        font-family: var(--font-body);
        letter-spacing: 0.02em;
        user-select: none;
    }
    [data-testid="stToggle"] {
        display: flex !important;
        flex-direction: row !important;
        justify-content: center !important;
        align-items: center !important;
        gap: 6px !important;
    }
    /* Modo oscuro (default): luna brillante, sol tenue */
    [data-testid="stToggle"]::before {
        content: "🌙";
        font-size: 0.85rem;
        line-height: 1;
        flex-shrink: 0;
        opacity: 1;
        filter: grayscale(0.2);
        transition: opacity 0.25s ease, filter 0.25s ease;
    }
    [data-testid="stToggle"]::after {
        content: "☀️";
        font-size: 0.85rem;
        line-height: 1;
        flex-shrink: 0;
        opacity: 0.35;
        filter: grayscale(0.7);
        transition: opacity 0.25s ease, filter 0.25s ease;
    }
    /* Track: fondo oscuro cuando OFF (modo oscuro) */
    [data-testid="stToggle"] [data-baseweb="checkbox"] > div:first-child {
        width: 48px !important;
        height: 26px !important;
        border-radius: 99px !important;
        background-color: #1a2235 !important;
        border: 1.5px solid rgba(99,120,180,0.35) !important;
        transition: background-color 0.25s ease !important;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.4) !important;
    }
    /* Track: azul cuando ON (modo claro) */
    [data-testid="stToggle"] [data-baseweb="checkbox"]:has(input:checked) > div:first-child {
        background-color: #4fa3ff !important;
        border-color: #3b82f6 !important;
        box-shadow: 0 0 10px rgba(79,163,255,0.35) !important;
    }
    /* Thumb (bolita blanca) */
    [data-testid="stToggle"] [data-baseweb="checkbox"] > div:first-child > div {
        width: 20px !important;
        height: 20px !important;
        border-radius: 50% !important;
        background-color: #eef2ff !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.45) !important;
    }

    /* ── Glosario ─────────────────────────────────────────────────── */
    .glosario-header {
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        padding: 2.5rem 1rem 1.5rem;
    }
    .glosario-icon { font-size: 3rem; margin-bottom: 0.8rem; }
    .glosario-title {
        font-family: var(--font-display);
        font-size: clamp(1.8rem, 4vw, 2.6rem);
        font-weight: 800;
        letter-spacing: -0.03em;
        color: var(--text-1);
        margin: 0 0 0.8rem;
    }
    .glosario-sub {
        font-size: 1rem;
        color: var(--text-2);
        line-height: 1.7;
        max-width: 600px;
        margin: 0 auto;
        text-align: center;
    }

    .glosario-cat-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        border-left: 3px solid var(--border);
        padding: 0.6rem 0.8rem 0.6rem 1rem;
        margin-bottom: 0.75rem;
        background: rgba(255,255,255,0.02);
        border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
    }
    .glosario-cat-icon { font-size: 1.2rem; }
    .glosario-cat-title {
        font-family: var(--font-display);
        font-size: 1.05rem;
        font-weight: 700;
        color: var(--text-1);
        flex: 1;
    }
    .glosario-cat-count {
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--text-3);
        background: var(--bg-3);
        padding: 0.2rem 0.6rem;
        border-radius: 99px;
    }

    .risk-badge {
        display: inline-block;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        padding: 0.25rem 0.7rem;
        border-radius: 99px;
    }

    .glosario-definition {
        background: var(--bg-2);
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        padding: 1rem 1.2rem;
        margin-bottom: 0.8rem;
    }
    .glosario-def-label {
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: var(--text-3);
        margin-bottom: 0.5rem;
    }
    .glosario-def-text {
        font-size: 0.93rem;
        color: var(--text-2);
        line-height: 1.7;
        margin: 0;
    }

    .glosario-example {
        background: rgba(79,163,255,0.06);
        border: 1px solid rgba(79,163,255,0.18);
        border-radius: var(--radius-md);
        padding: 1rem 1.2rem;
    }
    .glosario-example-label {
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: #4fa3ff;
        margin-bottom: 0.5rem;
    }
    .glosario-example-text {
        font-size: 0.9rem;
        color: var(--text-2);
        line-height: 1.7;
        margin: 0;
    }

    .glosario-empty {
        text-align: center;
        padding: 3rem 2rem;
        color: var(--text-2);
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
    }

    .glosario-cta {
        background: linear-gradient(135deg, rgba(79,163,255,0.08) 0%, rgba(16,217,138,0.05) 100%);
        border: 1px solid rgba(79,163,255,0.2);
        border-radius: var(--radius-lg);
        padding: 1.5rem 2rem;
        text-align: center;
        margin-top: 1rem;
    }
    .glosario-cta-title {
        font-family: var(--font-display);
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--text-1);
        margin-bottom: 0.4rem;
    }
    .glosario-cta-sub {
        font-size: 0.88rem;
        color: var(--text-2);
        margin: 0;
    }

    /* ── Category L1 cards (Nivel 1 de instrumentos) ─────────────── */
    /* ── Expandable category cards (details/summary) ──────────────── */
    .cat-exp {
        margin-bottom: 0.45rem;
    }
    .cat-exp > summary {
        list-style: none;
        cursor: pointer;
        display: block;
        outline: none;
    }
    .cat-exp > summary::-webkit-details-marker,
    .cat-exp > summary::marker { display: none; content: ''; }
    /* Card inside summary */
    .cat-exp > summary .cat-l1-card {
        margin-bottom: 0;
        transition: border-bottom-left-radius 0.15s, border-bottom-right-radius 0.15s, background 0.15s;
    }
    .cat-exp[open] > summary .cat-l1-card {
        border-bottom-left-radius: 0;
        border-bottom-right-radius: 0;
        border-bottom: 1px solid rgba(99,120,180,0.12);
        background: rgba(255,255,255,0.04);
    }
    .cat-exp[open] > summary .cat-exp-chevron { transform: rotate(90deg); }
    /* Expanded body */
    .cat-exp-body {
        background: rgba(255,255,255,0.018);
        border: 1px solid var(--border);
        border-top: none;
        border-left: 4px solid;
        border-bottom-left-radius: var(--radius-md);
        border-bottom-right-radius: var(--radius-md);
        padding: 0.8rem 0.85rem 0.55rem;
    }

    .cat-l1-card {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-left: 4px solid var(--blue);
        border-radius: var(--radius-md);
        padding: 1.1rem 1.4rem;
        margin-bottom: 0;
        transition: border-color 0.2s, background 0.2s;
    }
    .cat-l1-card:hover { background: rgba(255,255,255,0.03); }
    .cat-l1-body  { flex: 1; min-width: 0; }
    .cat-l1-name  {
        font-family: var(--font-display);
        font-weight: 700;
        font-size: 0.97rem;
        color: var(--text-1);
        margin-bottom: 0.3rem;
        letter-spacing: 0.01em;
    }
    .cat-l1-desc {
        font-size: 0.83rem;
        color: var(--text-2);
        line-height: 1.55;
    }
    .cat-l1-right {
        text-align: right;
        margin-left: 1.5rem;
        flex-shrink: 0;
    }
    .cat-l1-pct {
        font-family: var(--font-numbers);
        font-size: 2rem;
        font-weight: 700;
        line-height: 1;
        letter-spacing: -0.03em;
    }
    .cat-l1-pct-sub {
        font-size: 0.62rem;
        color: var(--text-3);
        margin-top: 0.25rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    /* Chevron indicator */
    .cat-exp-chevron {
        font-size: 1.3rem;
        font-weight: 300;
        color: var(--text-3);
        margin-left: 0.85rem;
        transition: transform 0.2s ease;
        flex-shrink: 0;
        line-height: 1;
        user-select: none;
    }
    @media (max-width: 640px) {
        .cat-l1-card  { padding: 0.85rem 1rem; }
        .cat-l1-pct   { font-size: 1.5rem; }
        .cat-l1-name  { font-size: 0.88rem; }
        .cat-l1-desc  { font-size: 0.76rem; }
        .cat-exp-chevron { margin-left: 0.5rem; font-size: 1.1rem; }
    }
    /* Ticker badge inline */
    .adc-ticker-badge {
        display: inline-block;
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        color: var(--blue);
        background: rgba(79,163,255,0.1);
        border: 1px solid rgba(79,163,255,0.22);
        padding: 1px 7px;
        border-radius: 4px;
        margin-left: 7px;
        vertical-align: middle;
        flex-shrink: 0;
    }
    /* Platform row */
    .adc-plat {
        font-size: 0.77rem !important;
        color: var(--text-3) !important;
        margin-top: 0.2rem;
    }
    /* New chip types */
    .adc-chip-ret { background: rgba(16,217,138,0.10); color: #34d399; border: 1px solid rgba(16,217,138,0.22); }
    .adc-chip-vol { background: rgba(245,158,11,0.10); color: #fbbf24; border: 1px solid rgba(245,158,11,0.22); }
    .adc-chip-liq { background: rgba(96,165,250,0.10); color: #93c5fd; border: 1px solid rgba(96,165,250,0.22); }

    /* ── Asset detail cards (Nivel 2) ────────────────────────────── */
    .asset-detail-card {
        background: rgba(255,255,255,0.025);
        border: 1px solid var(--border);
        border-left: 3px solid var(--blue);
        border-radius: var(--radius-sm);
        padding: 0.9rem 1rem;
        margin-bottom: 0.6rem;
        transition: border-color 0.2s;
    }
    .asset-detail-card:last-child { margin-bottom: 0; }
    .asset-detail-card:hover { border-color: rgba(99,120,180,0.3); }
    .adc-top {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 0.75rem;
        margin-bottom: 0.5rem;
    }
    .adc-title-wrap { flex: 1; min-width: 0; }
    .adc-title {
        font-weight: 600;
        font-size: 0.9rem;
        color: var(--text-1);
        margin-bottom: 0.2rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .adc-meta {
        font-size: 0.71rem;
        color: var(--text-3);
        letter-spacing: 0.02em;
    }
    .adc-right { text-align: right; flex-shrink: 0; }
    .adc-pct {
        font-family: var(--font-numbers);
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--text-1);
        line-height: 1;
    }
    .adc-amt {
        font-family: var(--font-numbers);
        font-size: 0.76rem;
        color: var(--text-3);
        margin-top: 0.2rem;
    }
    .adc-desc {
        font-size: 0.82rem;
        color: var(--text-2);
        line-height: 1.6;
    }
    .adc-chips {
        display: flex;
        flex-wrap: wrap;
        gap: 0.35rem;
        margin-top: 0.55rem;
    }
    .adc-chip {
        display: inline-block;
        padding: 0.18rem 0.55rem;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.01em;
    }
    .adc-chip-tir   { background: rgba(34,197,94,0.12);  color: #4ade80; border: 1px solid rgba(34,197,94,0.25); }
    .adc-chip-dur   { background: rgba(96,165,250,0.10); color: #93c5fd; border: 1px solid rgba(96,165,250,0.22); }
    .adc-chip-score { background: rgba(167,139,250,0.10);color: #c4b5fd; border: 1px solid rgba(167,139,250,0.22); }
    @media (max-width: 640px) {
        .adc-title { font-size: 0.83rem; }
        .adc-desc  { font-size: 0.76rem; }
        .adc-pct   { font-size: 0.97rem; }
    }

    /* ── Legal disclaimer (Feature 4) ────────────────────────────── */
    .legal-disclaimer {
        background: rgba(240,180,41,0.06);
        border: 1px solid rgba(240,180,41,0.2);
        border-radius: var(--radius-sm);
        padding: 0.65rem 1rem;
        font-size: 0.75rem;
        color: var(--text-3);
        margin-top: 0.9rem;
        line-height: 1.55;
        text-align: center;
    }
    .legal-disclaimer strong { color: rgba(240,180,41,0.75); }

    /* ── Macro allocation breakdown (Feature 6) ──────────────────── */
    .macro-cat-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.45rem 0.85rem;
        border-left: 3px solid var(--blue);
        background: rgba(255,255,255,0.03);
        border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
        margin: 0.75rem 0 0.25rem;
    }
    .macro-cat-name {
        font-weight: 700;
        font-size: 0.86rem;
        color: var(--text-1);
    }
    .macro-cat-pct {
        font-family: var(--font-numbers);
        font-size: 0.88rem;
        font-weight: 600;
        color: var(--text-1);
    }
    .macro-asset-row {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.28rem 0.85rem 0.28rem 1.5rem;
        font-size: 0.81rem;
        color: var(--text-2);
        border-bottom: 1px solid rgba(99,120,180,0.06);
    }
    .macro-asset-row:last-child { border-bottom: none; }
    .macro-asset-dot {
        width: 7px; height: 7px;
        border-radius: 50%;
        flex-shrink: 0;
        display: inline-block;
    }
    .macro-asset-name { flex: 1; min-width: 0; }
    .macro-asset-ticker {
        font-size: 0.72rem;
        font-weight: 600;
        color: var(--text-3);
        background: rgba(255,255,255,0.05);
        padding: 1px 5px;
        border-radius: 3px;
        flex-shrink: 0;
        letter-spacing: 0.03em;
    }
    .macro-asset-pct {
        color: var(--text-3);
        font-size: 0.78rem;
        flex-shrink: 0;
        min-width: 36px;
        text-align: right;
    }

    /* ── Buy guide ticker badge (Feature 5) ──────────────────────── */
    .buy-ticker {
        display: inline-block;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        color: var(--blue);
        background: rgba(79,163,255,0.1);
        border: 1px solid rgba(79,163,255,0.2);
        padding: 2px 7px;
        border-radius: 4px;
    }
    </style>
    """, unsafe_allow_html=True)

    if st.session_state.get("theme") == "light":
        st.markdown(_LIGHT_THEME_CSS, unsafe_allow_html=True)


_LIGHT_THEME_CSS = """<style>
/* ── Tema claro: variables ───────────────────────────────────────────── */
:root {
    --bg-0:        #f8fafc;
    --bg-1:        #f1f5f9;
    --bg-2:        #e2e8f0;
    --bg-3:        #cbd5e1;
    --bg-card:     #ffffff;
    --border:      rgba(100,116,139,0.2);
    --border-glow: rgba(37,99,235,0.4);
    --gold:        #d97706;
    --gold-dim:    #b45309;
    --green:       #059669;
    --green-dim:   #047857;
    --red:         #dc2626;
    --blue:        #2563eb;
    --blue-dim:    #1d4ed8;
    --text-1:      #0f172a;
    --text-2:      #334155;
    --text-3:      #64748b;
    --accent:      #2563eb;
    --shadow-card: 0 2px 12px rgba(0,0,0,0.07);
}

/* ── Fondos ──────────────────────────────────────────────────────────── */
html, body, [class*="css"],
[data-testid="stAppViewContainer"],
[data-testid="stApp"],
[data-testid="stMain"],
.main { background-color: #f8fafc !important; }

/* ── Texto global: Streamlit sobreescribe h1-h6 con sus propios estilos ─ */
h1, h2, h3, h4, h5, h6,
h1 *, h2 *, h3 *, h4 *, h5 *, h6 * { color: #0f172a !important; }
p, li, span:not(.app-logo span) { color: #334155 !important; }
a { color: #2563eb !important; }

/* ── Clases custom de la app ─────────────────────────────────────────── */
.hero-title, .q-title, .summary-title, .results-title,
.reveal-tagline, .reveal-badge, .section-title,
.glosario-title, .glosario-cat-title,
.action-step-title, .ai-empty-title,
.ai-section-title, .rebalance-block strong,
.app-logo      { color: #0f172a !important; }

.hero-subtitle, .hero-human-copy,
.reveal-explanation, .reveal-item,
.summary-explain, .summary-desc,
.results-sub,
.ai-response, .ai-response *,
.ai-bullet, .ai-tip-list li,
.action-step-copy, .action-step-help div,
.chat-text,
.glosario-sub, .glosario-def-text, .glosario-example-text,
.glosario-cta-sub,
.asset-row, .asset-sub, .asc-desc,
.tbl-text       { color: #334155 !important; }

.progress-label, .metric-label, .metric-sub,
.si-label, .si-sub,
.reveal-section-title, .chart-headline,
.tbl-header, .glosario-cat-count,
.chat-label, .app-badge,
.profiler-card p.hint, p.hint,
.disclaimer, .app-footer,
.glosario-def-label, .glosario-example-label,
.chart-currency-note, .fx-rate-note,
.asc-pct-sub    { color: #64748b !important; }

/* ── Gradientes hardcodeados → versión clara ─────────────────────────── */
.hero-card {
    background: linear-gradient(135deg, #ffffff 0%, #eff6ff 100%) !important;
    box-shadow: 0 4px 24px rgba(0,0,0,0.06) !important;
}
.hero-card::before {
    background: radial-gradient(circle, rgba(37,99,235,0.05) 0%, transparent 70%) !important;
}
.reveal-card   { background: linear-gradient(135deg, #ffffff 0%, #eff6ff 100%) !important; }
.summary-panel { background: linear-gradient(135deg, #ffffff 0%, #eff6ff 100%) !important; }
.ai-empty-state{ background: linear-gradient(135deg, #ffffff 0%, #eff6ff 100%) !important; }
.action-guide  { background: #ffffff !important; }
.profiler-card { background: #ffffff !important; }
.ai-response   { background: #ffffff !important; border-left-color: #2563eb !important; }
.alert-card    { background: #ffffff !important; }
.metric-card   { background: #ffffff !important; }
.summary-item  { background: #f1f5f9 !important; }
.reveal-section{ background: rgba(0,0,0,0.02) !important; border-color: rgba(100,116,139,0.2) !important; }
.reveal-item   { border-bottom-color: rgba(100,116,139,0.12) !important; }

.glosario-cta {
    background: linear-gradient(135deg, rgba(37,99,235,0.06) 0%, rgba(5,150,105,0.04) 100%) !important;
    border-color: rgba(37,99,235,0.18) !important;
}
.glosario-definition { background: #f1f5f9 !important; border-color: rgba(100,116,139,0.2) !important; }
.glosario-example    { background: rgba(37,99,235,0.04) !important; border-color: rgba(37,99,235,0.15) !important; }

/* App header / badge */
.app-header { border-bottom-color: rgba(100,116,139,0.2) !important; }
.app-badge  { background: #f1f5f9 !important; border-color: rgba(100,116,139,0.2) !important; }
.app-footer { border-top-color: rgba(100,116,139,0.2) !important; }

/* Progress bar track */
.progress-track { background: #e2e8f0 !important; }

/* Inputs nativos */
.stSelectbox > div > div { color: #0f172a !important; }
div[data-testid="stRadio"] div[role="radiogroup"] label,
div[data-testid="stRadio"] div[role="radiogroup"] label p { color: #334155 !important; }
.stRadio [data-baseweb="radio"] { background: #f1f5f9 !important; border-color: rgba(100,116,139,0.25) !important; }

/* Chat */
.chat-user   { background: rgba(37,99,235,0.07) !important; border-color: rgba(37,99,235,0.18) !important; }
.chat-advisor{ background: rgba(0,0,0,0.03) !important; border-color: rgba(100,116,139,0.18) !important; }

/* Botones */
.stButton > button {
    background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%) !important;
    color: #1d4ed8 !important;
    border-color: rgba(37,99,235,0.35) !important;
    box-shadow: 0 2px 8px rgba(37,99,235,0.12) !important;
}
.stButton > button:hover {
    border-color: #2563eb !important;
    box-shadow: 0 4px 16px rgba(37,99,235,0.25) !important;
}


/* Tabs */
.stTabs [data-baseweb="tab-list"] { background: #f1f5f9 !important; border-color: rgba(100,116,139,0.2) !important; }
.stTabs [data-baseweb="tab"]      { color: #64748b !important; }
.stTabs [aria-selected="true"]    { background: #ffffff !important; color: #0f172a !important; }

/* Captions y textos pequeños de Streamlit */
.stCaption, [data-testid="stCaptionContainer"] p { color: #64748b !important; }
[data-testid="stMarkdownContainer"] p { color: #334155 !important; }

/* Scrollbar */
::-webkit-scrollbar       { background: #f1f5f9; }
::-webkit-scrollbar-thumb { background: #cbd5e1; }

/* Toggle en modo claro */
[data-testid="stToggle"] [data-baseweb="checkbox"] > div:first-child {
    background-color: #cbd5e1 !important;
    border-color: #94a3b8 !important;
}
[data-testid="stToggle"] input:checked ~ div > div:first-child {
    background-color: #2563eb !important;
}
/* Modo claro: invertir brillos — sol brillante, luna tenue */
[data-testid="stToggle"]::before {
    opacity: 0.35 !important;
    filter: grayscale(0.7) !important;
}
[data-testid="stToggle"]::after {
    opacity: 1 !important;
    filter: grayscale(0.2) !important;
}

/* Category L1 cards en modo claro */
.cat-l1-card  { background: #ffffff !important; }
.cat-l1-name  { color: #0f172a !important; }
.cat-l1-desc  { color: #475569 !important; }
.cat-l1-pct-sub { color: #64748b !important; }
.cat-l1-card:hover { background: #f8fafc !important; }

/* Category expandable en modo claro */
.cat-exp-body { background: #f1f5f9 !important; border-color: rgba(100,116,139,0.2) !important; }
details.cat-exp[open] > summary .cat-l1-card { background: #f1f5f9 !important; border-bottom-color: rgba(100,116,139,0.15) !important; }

/* Asset detail cards en modo claro */
.asset-detail-card { background: #f8fafc !important; }
.adc-title { color: #0f172a !important; }
.adc-meta  { color: #64748b !important; }
.adc-pct   { color: #0f172a !important; }
.adc-amt   { color: #64748b !important; }
.adc-desc  { color: #334155 !important; }
.adc-ticker-badge { background: rgba(37,99,235,0.07) !important; color: #2563eb !important; border-color: rgba(37,99,235,0.18) !important; }
.adc-plat  { color: #94a3b8 !important; }
.adc-chip-ret   { background: rgba(5,150,105,0.08)  !important; color: #047857 !important; border-color: rgba(5,150,105,0.18) !important; }
.adc-chip-vol   { background: rgba(217,119,6,0.08)  !important; color: #b45309 !important; border-color: rgba(217,119,6,0.18) !important; }
.adc-chip-liq   { background: rgba(37,99,235,0.07)  !important; color: #1d4ed8 !important; border-color: rgba(37,99,235,0.16) !important; }
.adc-chip-tir   { background: rgba(22,163,74,0.08)  !important; color: #15803d !important; border-color: rgba(22,163,74,0.2) !important; }
.adc-chip-dur   { background: rgba(59,130,246,0.08) !important; color: #1d4ed8 !important; border-color: rgba(59,130,246,0.2) !important; }
.adc-chip-score { background: rgba(124,58,237,0.08) !important; color: #6d28d9 !important; border-color: rgba(124,58,237,0.2) !important; }

/* Legal disclaimer en modo claro */
.legal-disclaimer {
    background: rgba(217,119,6,0.05) !important;
    border-color: rgba(217,119,6,0.2) !important;
    color: #64748b !important;
}
.legal-disclaimer strong { color: #b45309 !important; }

/* Macro breakdown en modo claro */
.macro-cat-header { background: rgba(0,0,0,0.02) !important; }
.macro-cat-name, .macro-cat-pct { color: #0f172a !important; }
.macro-asset-name { color: #334155 !important; }
.macro-asset-ticker {
    color: #475569 !important;
    background: rgba(0,0,0,0.04) !important;
}
.macro-asset-pct { color: #64748b !important; }
.macro-asset-row { border-bottom-color: rgba(100,116,139,0.1) !important; }

/* Buy ticker badge en modo claro */
.buy-ticker {
    color: #1d4ed8 !important;
    background: rgba(37,99,235,0.08) !important;
    border-color: rgba(37,99,235,0.2) !important;
}

/* ── Mensaje personalizado para novato / lastimado ────────────── */
.personal-msg {
    display: flex;
    gap: 14px;
    align-items: flex-start;
    background: linear-gradient(135deg, rgba(34,197,94,0.07), rgba(79,163,255,0.05));
    border: 1px solid rgba(34,197,94,0.22);
    border-left: 3px solid #22c55e;
    border-radius: 10px;
    padding: 16px 20px;
    margin: 0 0 1.2rem;
}
.personal-msg .pm-icon {
    font-size: 1.7rem;
    flex-shrink: 0;
    line-height: 1.3;
}
.personal-msg .pm-body { flex: 1; min-width: 0; }
.personal-msg strong {
    display: block;
    color: #cbd5e1;
    font-size: 0.97rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    line-height: 1.4;
}
.personal-msg p {
    font-size: 0.86rem;
    color: #94a3b8;
    margin: 0;
    line-height: 1.65;
}
.personal-msg p strong {
    display: inline;
    color: #cbd5e1;
    font-weight: 600;
    font-size: inherit;
    margin: 0;
}
@media (max-width: 640px) {
    .personal-msg { padding: 14px 16px; gap: 10px; }
    .personal-msg .pm-icon { font-size: 1.4rem; }
    .personal-msg strong { font-size: 0.88rem; }
    .personal-msg p { font-size: 0.78rem; }
}

/* ── Header sticky + logo clickeable + Nuevo test ────────────── */
/* Aplica position:sticky al primer bloque horizontal (header) */
section.main > div[data-testid="block-container"] > div[data-testid="stVerticalBlock"]
  > div[data-testid="stHorizontalBlock"]:first-of-type {
    position: sticky;
    top: 0;
    z-index: 999;
    background: rgba(5, 8, 16, 0.92);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-bottom: 1px solid rgba(148, 163, 184, 0.1);
    padding: 0.6rem 0 !important;
    margin: 0 -1rem 1rem !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
}


/* Modal de confirmación inline (no usamos st.dialog para portabilidad) */
.reset-confirm-overlay {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(5, 8, 16, 0.85);
    backdrop-filter: blur(6px);
    -webkit-backdrop-filter: blur(6px);
    z-index: 99999;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1rem;
    animation: fadeIn 0.2s ease;
}
.reset-confirm-modal {
    background: var(--bg-2);
    border: 1px solid var(--border-glow);
    border-radius: 14px;
    padding: 24px 28px;
    max-width: 420px;
    width: 100%;
    box-shadow: 0 20px 60px rgba(0,0,0,0.5);
}
.reset-confirm-modal h3 {
    font-family: var(--font-display);
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--text-1);
    margin: 0 0 10px;
}
.reset-confirm-modal p {
    font-size: 0.88rem;
    color: var(--text-2);
    line-height: 1.6;
    margin: 0 0 18px;
}
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

/* ── Hablá con Lucas: módulo unificado ──────────────────────── */
.lucas-card {
    background: linear-gradient(180deg, rgba(79,163,255,0.04), rgba(79,163,255,0.01));
    border: 1px solid rgba(79,163,255,0.18);
    border-radius: 14px;
    padding: 20px 22px 16px;
    margin: 0 0 1.2rem;
}
.lucas-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 4px;
}
.lucas-avatar {
    width: 44px;
    height: 44px;
    border-radius: 50%;
    background: linear-gradient(135deg, #4fa3ff, #2563eb);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.25rem;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: -0.02em;
    flex-shrink: 0;
    box-shadow: 0 4px 14px rgba(79,163,255,0.35);
}
/* Avatar mini para los mensajes del asistente en el chat */
.chat-avatar-mini {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 1.15rem;
    height: 1.15rem;
    border-radius: 50%;
    background: linear-gradient(135deg, #4fa3ff, #2563eb);
    color: #ffffff;
    font-weight: 700;
    font-size: 0.7rem;
    letter-spacing: -0.02em;
    margin-right: 0.35rem;
    vertical-align: middle;
}
.lucas-title-wrap { flex: 1; min-width: 0; }
.lucas-title {
    font-family: var(--font-display);
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--text-1);
    margin: 0;
    letter-spacing: -0.01em;
}
.lucas-subtitle {
    font-size: 0.78rem;
    color: var(--text-3);
    margin: 2px 0 0;
}
.lucas-welcome {
    background: rgba(79,163,255,0.06);
    border-left: 3px solid rgba(79,163,255,0.5);
    border-radius: 8px;
    padding: 12px 14px;
    margin: 14px 0 6px;
    font-size: 0.88rem;
    color: var(--text-2);
    line-height: 1.6;
}
.lucas-welcome strong { color: var(--text-1); font-weight: 600; }
.lucas-chips-label {
    font-size: 0.78rem;
    color: var(--text-3);
    margin: 14px 0 8px;
    font-weight: 500;
}
.lucas-input-label {
    font-size: 0.78rem;
    color: var(--text-3);
    margin: 16px 0 6px;
    font-weight: 500;
}
/* Los chips usan .stButton dentro de .lucas-chips-block — los reestilamos */
.lucas-chips-block .stButton > button {
    background: rgba(79,163,255,0.08) !important;
    border: 1px solid rgba(79,163,255,0.22) !important;
    color: #93c5fd !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    padding: 0.6rem 0.9rem !important;
    text-align: left !important;
    box-shadow: none !important;
    height: auto !important;
    min-height: 44px;
    line-height: 1.35 !important;
    white-space: normal !important;
    letter-spacing: 0 !important;
}
.lucas-chips-block .stButton > button:hover {
    background: rgba(79,163,255,0.15) !important;
    border-color: rgba(79,163,255,0.4) !important;
    transform: none !important;
    box-shadow: 0 2px 8px rgba(79,163,255,0.15) !important;
}
.lucas-divider {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 18px 0 10px;
    color: var(--text-3);
    font-size: 0.74rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
.lucas-divider::before,
.lucas-divider::after {
    content: "";
    flex: 1;
    height: 1px;
    background: rgba(148,163,184,0.18);
}
.lucas-footer-note {
    font-size: 0.72rem;
    color: var(--text-3);
    text-align: center;
    margin: 14px 0 0;
    font-style: italic;
    line-height: 1.55;
}
.lucas-restart {
    text-align: center;
    margin: 8px 0 0;
}
.lucas-restart .stButton > button {
    background: transparent !important;
    border: none !important;
    color: var(--text-3) !important;
    font-size: 0.74rem !important;
    text-decoration: underline !important;
    padding: 4px 0 !important;
    width: auto !important;
    box-shadow: none !important;
    min-height: 0 !important;
    opacity: 0.55 !important;
    font-weight: 400 !important;
    letter-spacing: 0 !important;
    transition: opacity 0.15s ease, color 0.15s ease !important;
}
.lucas-restart .stButton > button:hover {
    color: #ef4444 !important;
    background: transparent !important;
    transform: none !important;
    opacity: 1 !important;
}
@media (max-width: 640px) {
    .lucas-card { padding: 14px 14px 10px; }
    .lucas-avatar { width: 36px; height: 36px; font-size: 1.15rem; }
    .lucas-title { font-size: 1rem; }
    .lucas-subtitle { font-size: 0.72rem; }
    .lucas-welcome { font-size: 0.8rem; padding: 10px 12px; }
    .lucas-chips-label { font-size: 0.7rem; margin: 10px 0 6px; }
    .lucas-input-label { font-size: 0.7rem; margin: 12px 0 4px; }
    .lucas-footer-note { font-size: 0.66rem; line-height: 1.5; margin: 10px 0 4px; }
    .lucas-chips-block .stButton > button {
        font-size: 0.74rem !important;
        padding: 0.6rem 0.7rem !important;
        min-height: 44px;  /* iOS HIG touch target */
        line-height: 1.2 !important;
    }
    /* Form input + Enviar: cuando Streamlit empila las columnas en mobile,
       darles ancho completo y altura coherente */
    form[data-testid="stForm"] [data-testid="stTextInput"] input {
        font-size: 16px !important;  /* evita zoom auto en iOS Safari */
        padding: 0.6rem 0.8rem !important;
        min-height: 44px;
    }
    form[data-testid="stForm"] button[kind="primary"],
    form[data-testid="stForm"] button[kind="primaryFormSubmit"] {
        min-height: 44px;
        font-size: 0.85rem !important;
    }
    /* Chat bubbles más compactos en mobile */
    .chat-bubble {
        padding: 0.6rem 0.85rem !important;
        margin-bottom: 0.5rem !important;
        max-width: 100% !important;
        font-size: 0.85rem !important;
    }
    .chat-text { font-size: 0.85rem !important; line-height: 1.55 !important; }
    .chat-label { font-size: 0.6rem !important; margin-bottom: 0.2rem !important; }
}

/* ── Overlay 'Lucas está pensando' (fijo en viewport, visible en cualquier scroll) */
.lucas-thinking-overlay {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(5, 8, 16, 0.55);
    backdrop-filter: blur(4px);
    -webkit-backdrop-filter: blur(4px);
    z-index: 99998;
    display: flex;
    align-items: center;
    justify-content: center;
    pointer-events: none;
    animation: lucasFadeIn 0.2s ease;
}
.lucas-thinking-box {
    background: linear-gradient(135deg, #1a3a6a 0%, #0f2247 100%);
    border: 1px solid rgba(79,163,255,0.35);
    border-radius: 14px;
    padding: 18px 22px;
    display: flex;
    align-items: center;
    gap: 14px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.5);
    max-width: 90vw;
}
.lucas-thinking-spinner {
    width: 28px;
    height: 28px;
    border: 3px solid rgba(79,163,255,0.25);
    border-top-color: #4fa3ff;
    border-radius: 50%;
    animation: lucasSpin 0.8s linear infinite;
    flex-shrink: 0;
}
.lucas-thinking-text { display: flex; flex-direction: column; gap: 2px; }
.lucas-thinking-text strong {
    color: #eef2ff;
    font-family: 'Syne', sans-serif;
    font-size: 0.95rem;
    font-weight: 700;
}
.lucas-thinking-text small {
    color: #94a3b8;
    font-size: 0.78rem;
}
@keyframes lucasSpin { to { transform: rotate(360deg); } }
@keyframes lucasFadeIn { from { opacity: 0; } to { opacity: 1; } }
@media (max-width: 480px) {
    .lucas-thinking-box { padding: 14px 16px; gap: 10px; }
    .lucas-thinking-spinner { width: 22px; height: 22px; border-width: 2.5px; }
    .lucas-thinking-text strong { font-size: 0.85rem; }
    .lucas-thinking-text small { font-size: 0.72rem; }
}

/* iOS Safari específico: prevenir bounce-scroll que oculta el header */
@supports (-webkit-touch-callout: none) {
    body { overscroll-behavior-y: none; }
    .lucas-card { -webkit-overflow-scrolling: touch; }
}

/* ── Chips Lucas: forzar 2 columnas en mobile (más legible que 3 apretadas) */
@media (max-width: 640px) {
    .lucas-chips-block [data-testid="stHorizontalBlock"] {
        flex-wrap: wrap !important;
        gap: 0.4rem !important;
    }
    .lucas-chips-block [data-testid="column"],
    .lucas-chips-block [data-testid="stColumn"] {
        flex: 0 0 calc(50% - 0.2rem) !important;
        min-width: calc(50% - 0.2rem) !important;
        max-width: calc(50% - 0.2rem) !important;
    }
}

/* ── Form Lucas en mobile: input full-width arriba, botón abajo ─────────── */
@media (max-width: 480px) {
    form[data-testid="stForm"] [data-testid="stHorizontalBlock"] {
        flex-wrap: wrap !important;
        gap: 0.4rem !important;
    }
    form[data-testid="stForm"] [data-testid="column"],
    form[data-testid="stForm"] [data-testid="stColumn"] {
        flex: 0 0 100% !important;
        min-width: 100% !important;
        max-width: 100% !important;
    }
}

/* ── Chat form: ocultar helper "Press Enter" + borde verde ──── */
/* Streamlit muestra "Press Enter to submit form" debajo del input.
   Cubrimos múltiples selectores porque cambia entre versiones. */
[data-testid="InputInstructions"],
[data-testid="stFormInputInstruction"],
[data-testid="stTextInputInstruction"],
[data-testid="stFormSubmitButton"] + small,
.stForm small,
form[data-testid="stForm"] small,
form[data-testid="stForm"] [data-testid="InputInstructions"],
form[data-testid="stForm"] div[class*="instruction"] {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}

/* Borde verde sutil del text_input — reemplaza el rojo/naranja default */
form[data-testid="stForm"] .stTextInput input,
form[data-testid="stForm"] [data-baseweb="input"],
form[data-testid="stForm"] [data-baseweb="base-input"],
.stTextInput input,
.stTextInput [data-baseweb="input"] {
    border-color: rgba(34,197,94,0.4) !important;
    box-shadow: none !important;
    outline: none !important;
}
form[data-testid="stForm"] .stTextInput input:focus,
form[data-testid="stForm"] [data-baseweb="input"]:focus-within,
.stTextInput input:focus,
.stTextInput [data-baseweb="input"]:focus-within {
    border-color: #22c55e !important;
    box-shadow: 0 0 0 1px rgba(34,197,94,0.25) !important;
    outline: none !important;
}

/* ── Header: toggle de tema alineado verticalmente con los botones ─ */
.header-theme-wrap {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    min-height: 40px;
    padding-top: 4px;
}
.header-theme-wrap [data-testid="stToggle"] {
    margin: 0 !important;
}

/* ── Mobile: header compacto (Glosario + Cómo funciona + Toggle) ── */
@media (max-width: 640px) {
    /* Hace los botones del header MUY compactos para que entren los 3 + toggle */
    button[kind="secondary"][data-testid="stBaseButton-secondary"][aria-label*="Glosario"],
    button[kind="secondary"][data-testid="stBaseButton-secondary"][aria-label*="Cómo"],
    .stButton button[data-testid="stBaseButton-secondary"]:has-text("Glosario"),
    .stButton button[data-testid="stBaseButton-secondary"]:has-text("Cómo funciona") {
        font-size: 0 !important;
    }
    /* Fallback genérico: todos los botones del header son chicos en mobile */
    [data-testid="stHorizontalBlock"]:first-of-type .stButton > button {
        font-size: 0.65rem !important;
        padding: 0.35rem 0.4rem !important;
        letter-spacing: 0 !important;
    }
    .header-theme-wrap { min-height: 32px; padding-top: 0; }
    .app-logo { font-size: 1.1rem !important; }
    .app-badge { font-size: 0.6rem !important; }
}

/* ── Risk scenarios cards (clase para poder media-query en mobile) ─ */
.risk-scenario-card {
    background: rgba(255,255,255,0.03);
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 12px;
}
.risk-scenario-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 8px;
    flex-wrap: wrap;
}
.risk-scenario-icon { font-size: 1.1rem; }
.risk-scenario-title {
    font-weight: 700;
    color: #e2e8f0;
    font-size: 0.95rem;
}
.risk-scenario-sev-badge {
    font-size: 0.67rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    padding: 2px 8px;
    border-radius: 999px;
}
.risk-scenario-body {
    font-size: 0.84rem;
    color: #94a3b8;
    line-height: 1.65;
    margin: 0 0 8px 0;
}
.risk-scenario-tip {
    font-size: 0.8rem;
    color: #64748b;
    margin: 0;
}
.risk-scenario-tip strong { color: #94a3b8; }
@media (max-width: 640px) {
    .risk-scenario-card {
        padding: 10px 12px;
        margin-bottom: 8px;
    }
    .risk-scenario-icon { font-size: 0.95rem; }
    .risk-scenario-title { font-size: 0.82rem; }
    .risk-scenario-sev-badge { font-size: 0.58rem; padding: 1px 6px; }
    .risk-scenario-body { font-size: 0.74rem; line-height: 1.55; }
    .risk-scenario-tip { font-size: 0.7rem; }
}

/* ── Tooltips inline del glosario ─────────────────────────────── */
.term-tip {
    border-bottom: 1px dotted rgba(79,163,255,0.55);
    cursor: help;
    position: relative;
    color: inherit;
    transition: color 0.15s ease;
    outline: none;
}
.term-tip:hover,
.term-tip:focus {
    color: #4fa3ff;
}
.term-tip:hover::after,
.term-tip:focus::after {
    content: attr(data-tip);
    position: absolute;
    bottom: calc(100% + 6px);
    left: 50%;
    transform: translateX(-50%);
    background: #0f172a;
    color: #cbd5e1;
    padding: 8px 12px;
    border-radius: 6px;
    border: 1px solid rgba(79,163,255,0.25);
    font-size: 0.78rem;
    line-height: 1.5;
    width: max-content;
    max-width: 280px;
    white-space: normal;
    z-index: 9999;
    box-shadow: 0 6px 20px rgba(0,0,0,0.5);
    font-weight: 400;
    text-transform: none;
    letter-spacing: normal;
    pointer-events: none;
}
.term-tip:hover::before,
.term-tip:focus::before {
    content: "";
    position: absolute;
    bottom: calc(100% + 1px);
    left: 50%;
    transform: translateX(-50%);
    border: 5px solid transparent;
    border-top-color: rgba(79,163,255,0.25);
    z-index: 9999;
    pointer-events: none;
}
/* Mobile: tooltip ocupa más ancho relativo y se centra */
@media (max-width: 640px) {
    .term-tip:hover::after,
    .term-tip:focus::after {
        max-width: calc(100vw - 2rem);
        font-size: 0.74rem;
    }
}
/* Light theme: invertir colores */

/* ── Portfolio disclaimer (cierre legal) ──────────────────────── */
.portfolio-disclaimer {
    display: flex;
    gap: 14px;
    align-items: flex-start;
    background: rgba(79,163,255,0.04);
    border: 1px solid rgba(79,163,255,0.15);
    border-left: 3px solid #4fa3ff;
    border-radius: 10px;
    padding: 16px 20px;
    margin: 1.5rem 0 1rem;
}
.portfolio-disclaimer .pd-icon {
    font-size: 1.3rem;
    flex-shrink: 0;
    line-height: 1.4;
}
.portfolio-disclaimer .pd-body { flex: 1; min-width: 0; }
.portfolio-disclaimer strong {
    color: #cbd5e1;
    font-size: 0.93rem;
    display: block;
    margin-bottom: 0.5rem;
}
.portfolio-disclaimer p {
    font-size: 0.83rem;
    color: #94a3b8;
    margin: 0 0 0.7rem;
    line-height: 1.6;
}
.portfolio-disclaimer p:last-child { margin-bottom: 0; }
.portfolio-disclaimer .pd-fine {
    font-size: 0.72rem;
    color: #64748b;
    font-style: italic;
}
@media (max-width: 640px) {
    .portfolio-disclaimer {
        padding: 14px 16px;
        gap: 10px;
    }
    .portfolio-disclaimer .pd-icon { font-size: 1.1rem; }
    .portfolio-disclaimer strong { font-size: 0.85rem; }
    .portfolio-disclaimer p { font-size: 0.78rem; }
    .portfolio-disclaimer .pd-fine { font-size: 0.68rem; }
}

/* ── Geographic diversification note (positive tone) ──────────── */
.geo-diversification-note {
    display: flex;
    gap: 10px;
    align-items: flex-start;
    background: rgba(148,163,184,0.05);
    border-radius: 8px;
    padding: 10px 12px;
    margin: 0.5rem 0 0.75rem;
}
.geo-diversification-note .geo-icon {
    font-size: 1rem;
    flex-shrink: 0;
    line-height: 1.4;
}
.geo-diversification-note .geo-body { flex: 1; min-width: 0; }
.geo-diversification-note p {
    font-size: 0.78rem;
    color: #94a3b8;
    margin: 0;
    line-height: 1.55;
}
.geo-diversification-note .geo-breakdown {
    margin-top: 4px;
    font-size: 0.72rem;
    opacity: 0.75;
}
.geo-diversification-note .geo-breakdown strong { color: #cbd5e1; font-weight: 600; }
@media (max-width: 640px) {
    .geo-diversification-note p { font-size: 0.74rem; }
    .geo-diversification-note .geo-breakdown { font-size: 0.68rem; }
}

/* ── #7 Ticker badges más sutiles en mobile ──────────────────── */
@media (max-width: 768px) {
    .adc-ticker-badge,
    .ticker-badge {
        font-size: 0.65rem !important;
        opacity: 0.65;
        padding: 0.15rem 0.4rem !important;
    }
}

/* ── #8 Profile badge compacto en mobile ──────────────────────── */
@media (max-width: 768px) {
    .profile-badge {
        padding: 0.4rem 0.9rem !important;
        font-size: 0.72rem !important;
        letter-spacing: 0.06em !important;
        margin-bottom: 0.6rem !important;
    }
}

/* ── #10 Tipografía global mobile ─────────────────────────────── */
@media (max-width: 768px) {
    h1, .stMarkdown h1 { font-size: 1.5rem !important; line-height: 1.2; }
    h2, .stMarkdown h2 { font-size: 1.1rem !important; line-height: 1.3; }
    h3, .stMarkdown h3 { font-size: 0.95rem !important; line-height: 1.35; }
    .stMarkdown p, .stMarkdown li { font-size: 0.9rem !important; line-height: 1.45; }
    .block-container {
        padding-left: 0.75rem !important;
        padding-right: 0.75rem !important;
    }
}

/* ── Mobile spacing & section-title reduction (#6) ────────────── */
@media (max-width: 768px) {
    .section-title {
        font-size: 0.9rem;
        margin-bottom: 0.6rem;
        padding-bottom: 0.35rem;
    }
    .stMarkdown { margin-bottom: 0.6rem; }
    /* Reducir gap entre secciones */
    .block-container {
        padding-top: 0.6rem !important;
    }
    [data-testid="stVerticalBlock"] { gap: 0.6rem !important; }
}

/* ── Cat-l1-card: ocultar descripción en mobile (#5) ──────────── */
@media (max-width: 640px) {
    .cat-l1-desc { display: none; }
    .cat-l1-name { margin-bottom: 0; }
    .cat-l1-pct-sub { display: none; }
    .cat-l1-card {
        padding: 0.7rem 0.85rem;
    }
    .cat-l1-pct { font-size: 1.35rem; }
}

/* ── Donut legend below chart in mobile (#3) ──────────────────── */
@media (max-width: 768px) {
    .stPlotlyChart .legendtext { font-size: 11px !important; }
}

/* ── Simulador panel: fixes mobile focalizados ─────────────────── */
@media (max-width: 640px) {
    /* h4 (títulos de sub-paneles del simulador) — alinear con h3 */
    .stMarkdown h4 { font-size: 1rem !important; line-height: 1.3; margin: 0.4rem 0 0.6rem; }

    /* Override del inline gap:16px en .metrics-grid del simulador */
    .metrics-grid[style*="1fr 1fr"] { gap: 8px !important; }

    /* st.columns([1,2]) del aporte mensual: apilar en lugar de 33/67 */
    [data-testid="stHorizontalBlock"]:has([data-testid="stNumberInput"]) {
        flex-direction: column !important;
        gap: 0.6rem !important;
    }
    [data-testid="stHorizontalBlock"]:has([data-testid="stNumberInput"]) > [data-testid="stColumn"] {
        width: 100% !important; flex: 1 1 100% !important; min-width: 0 !important;
    }

    /* Expander summary: aliviar padding/min-height para títulos largos */
    [data-testid="stExpander"] > details > summary {
        padding: 14px 16px !important;
        min-height: 56px !important;
        font-size: 0.92rem !important;
        line-height: 1.3 !important;
    }
    [data-testid="stExpander"] > details > summary > span,
    [data-testid="stExpander"] > details > summary p { font-size: 0.92rem !important; }

    /* Plotly: ajustar textfont outside y evitar overflow horizontal */
    .stPlotlyChart { overflow-x: hidden !important; }
    .stPlotlyChart .bartext, .stPlotlyChart text.bartext { font-size: 9px !important; }
}
</style>"""


def _trigger_reset_confirm(target_step: str = "intro"):
    """Setea flag para mostrar modal de confirmación de reset."""
    st.session_state["_reset_confirm_target"] = target_step


def _do_reset(target_step: str):
    """Resetea el state del usuario y navega al destino."""
    keys_to_clear = [
        "portfolio", "simulation", "chat_history", "show_celebration",
        "answers", "profile",
    ]
    for k in keys_to_clear:
        if k == "chat_history":
            st.session_state[k] = []
        elif k == "answers":
            st.session_state[k] = {}
        else:
            st.session_state[k] = None
    st.session_state.step = target_step
    st.session_state.pop("_reset_confirm_target", None)


def _render_reset_confirm_modal():
    """Modal inline de confirmación antes de perder el portfolio actual."""
    target = st.session_state.get("_reset_confirm_target")
    if not target:
        return
    st.markdown("""<div class="reset-confirm-overlay">
  <div class="reset-confirm-modal">
    <h3>¿Empezar de nuevo?</h3>
    <p>Vas a perder el portafolio actual y el cuestionario que completaste.
    ¿Querés continuar?</p>
  </div>
</div>""", unsafe_allow_html=True)
    # Botones reales debajo (Streamlit no puede inyectar botones dentro del overlay HTML)
    _, _c1, _c2, _ = st.columns([2, 2, 2, 2])
    with _c1:
        if st.button("Cancelar", key="reset_cancel", use_container_width=True):
            st.session_state.pop("_reset_confirm_target", None)
            st.rerun()
    with _c2:
        if st.button("Sí, empezar de nuevo", key="reset_confirm",
                     type="primary", use_container_width=True):
            _do_reset(target)
            st.rerun()


def render_header():
    theme = st.session_state.get("theme", "dark")
    has_portfolio = bool(st.session_state.get("portfolio"))

    # Mostrar modal si fue solicitado
    if st.session_state.get("_reset_confirm_target"):
        _render_reset_confirm_modal()

    # Layout: [Logo + badge | Nuevo test (si hay portfolio) | Glosario | Cómo funciona | Toggle]
    # Glosario queda centrado entre Nuevo test (izquierda) y Cómo funciona (derecha)
    if has_portfolio:
        col_logo, col_nuevo, col_glos, col_meto, col_theme = st.columns(
            [3, 1.4, 1.4, 1.4, 0.7]
        )
    else:
        col_logo, col_glos, col_meto, col_theme = st.columns([4, 1.5, 1.5, 0.7])

    with col_logo:
        # Logo HTML clásico — "TuPortafolio" + "IA" en gold
        st.markdown("""
        <div class="app-header">
            <div class="app-logo">TuPortafolio<span>IA</span></div>
        </div>
        """, unsafe_allow_html=True)

    if has_portfolio:
        with col_nuevo:
            st.markdown('<div class="header-nav-spacer"></div>', unsafe_allow_html=True)
            if st.button("🔄 Nuevo test", key="header_nuevo_test",
                         use_container_width=True):
                _trigger_reset_confirm("profiling")
                st.rerun()

    # Pantallas secundarias: si el usuario navega entre ellas (ej. Glosario →
    # Cómo funciona), NO sobreescribimos _prev_step para que el botón "Volver"
    # siempre regrese a la pantalla "main" original (results, intro, etc.).
    _SECONDARY_SCREENS = {"glosario", "metodologia", "como_funciona"}
    _current_step = st.session_state.get("step", "intro")

    with col_glos:
        st.markdown('<div class="header-nav-spacer"></div>', unsafe_allow_html=True)
        if st.button("📚 Glosario", key="header_glosario", use_container_width=True):
            if _current_step not in _SECONDARY_SCREENS:
                st.session_state._prev_step = _current_step
            st.session_state.step = "glosario"
            st.rerun()
    with col_meto:
        st.markdown('<div class="header-nav-spacer"></div>', unsafe_allow_html=True)
        if st.button("ℹ️ Cómo funciona", key="header_metodologia", use_container_width=True):
            if _current_step not in _SECONDARY_SCREENS:
                st.session_state._prev_step = _current_step
            st.session_state.step = "como_funciona"
            st.rerun()
    with col_theme:
        st.markdown('<div class="header-nav-spacer"></div>', unsafe_allow_html=True)
        st.markdown('<div class="header-theme-wrap">', unsafe_allow_html=True)
        _is_light = st.toggle(
            "Modo claro",
            value=(theme == "light"),
            key="theme_toggle_widget",
            label_visibility="collapsed",
        )
        st.markdown('</div>', unsafe_allow_html=True)
        if _is_light != (theme == "light"):
            st.session_state.theme = "light" if _is_light else "dark"
            st.rerun()


def render_footer():
    st.markdown("""
    <div class="app-footer">
        TuPortafolioIA · Herramienta educativa de planificación financiera · No constituye asesoramiento regulado por la CNV · Argentina
    </div>
    """, unsafe_allow_html=True)
