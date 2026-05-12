"""
Página de metodología: explica el framework académico del sistema.
Para presentación institucional (rector, docentes, inversores).
"""

import streamlit as st


def render_methodology():
    st.markdown('<div class="section-title">🎓 Metodología del Sistema</div>', unsafe_allow_html=True)
    st.caption("Fundamentos teóricos y técnicos del motor de construcción de carteras.")

    # ── Tabs principales ──────────────────────────────────────────────────────
    tabs = st.tabs([
        "📐 Framework general",
        "🔢 Scoring de activos",
        "🏗️ Construcción del portafolio",
        "📡 Señales de mercado",
        "🧠 Sistema de aprendizaje",
        "📊 Fuentes de datos",
    ])

    # ── Tab 1: Framework general ──────────────────────────────────────────────
    with tabs[0]:
        st.markdown("""
### Arquitectura del sistema

El sistema sigue un pipeline de 6 etapas que transforma las respuestas del inversor
en una cartera personalizada con fundamentos cuantitativos:
""")
        st.markdown("""
| Etapa | Componente | Descripción |
|---|---|---|
| 1 | **Perfil de riesgo** | 8 preguntas → 4 perfiles (Conservador / Estable / Moderado / Agresivo) |
| 2 | **Scoring de activos** | 75 tickers evaluados en 5 bloques fundamentales (0–100 pts) |
| 3 | **Selección por buckets** | Cada perfil tiene segmentos con candidatos rankeados por score |
| 4 | **Ajustes dinámicos** | Horizonte, fondo de emergencia, experiencia, ingresos |
| 5 | **Señales de sector** | Histórico de valuación sectorial ajusta pesos ±15% |
| 6 | **Filtros estructurales** | Liquidez mínima, overlap ETF/acciones, concentración |
""")

        st.markdown("---")
        st.markdown("""
### Teoría de base

El sistema integra conceptos de **Modern Portfolio Theory (Markowitz, 1952)**
con ajustes para el mercado argentino:

- **Diversificación**: el índice HHI (Herfindahl-Hirschman) mide la concentración de la cartera.
  HHI < 0.15 indica alta diversificación.
- **Riesgo-retorno**: el Sharpe Ratio cuantifica el exceso de retorno por unidad de riesgo
  asumida, usando el T-Bill de EE.UU. como tasa libre de riesgo (≈ 4.5% anual).
- **Beta de portfolio**: mide la sensibilidad de la cartera al mercado. Beta = 1 implica
  movimiento idéntico al mercado; < 1 implica menor volatilidad sistemática.
- **Ajuste por perfil**: los pesos no son fijos — emergen del scoring de cada activo
  candidato dentro de cada segmento (bucket), ponderados proporcionalmente a su score.
""")

    # ── Tab 2: Scoring de activos ─────────────────────────────────────────────
    with tabs[1]:
        st.markdown("""
### Framework de scoring: 5 bloques (0–100 puntos)

Cada activo equity se evalúa en 5 dimensiones con **umbrales diferenciados por sector**.
Los bonos tienen su propio framework de 5 bloques (Rendimiento / Duración / Calidad / Paridad / Liquidez).
""")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
**Bloque 1 — Valuación (25 pts)**
- Forward P/E vs umbrales sectoriales (7 pts)
- EV/EBITDA (8 pts)
- PEG ratio (5 pts)
- Dividend Yield (5 pts)

**Bloque 2 — Calidad (25 pts)**
- ROE vs umbrales por sector (10 pts)
- Margen neto (8 pts)
- ROA (7 pts)

**Bloque 3 — Solvencia (20 pts)**
- Deuda/Equity — no aplica para bancos (10 pts)
- Current ratio (5 pts)
- Quick ratio (5 pts)
""")
        with col2:
            st.markdown("""
**Bloque 4 — Crecimiento (20 pts)**
- EPS CAGR 5 años (8 pts)
- Ventas CAGR 5 años (7 pts)
- EPS trimestral Q/Q (5 pts)

**Bloque 5 — Cualitativo (10 pts)**
- Recomendación de analistas: escala 1–5 (4 pts)
  - ≤ 2.0 = Strong Buy → 4 pts
  - ≤ 2.5 = Buy → 3 pts
- Upside al precio objetivo consenso (3 pts)
  - > 15% upside → 3 pts
- Short float < 2% → señal de confianza (3 pts)

**Ajuste ARG** — descuento regulatorio adicional para acciones argentinas:
riesgo país, liquidez BYMA, exposición cambiaria.
""")

        st.markdown("---")
        st.markdown("""
### Umbrales sectoriales

Los umbrales **no son universales** — cada sector tiene sus propios parámetros.
Ejemplo: un P/E de 25× es "excelente" en tecnología pero "neutral" en energía.
""")
        st.markdown("""
| Sector | Forward P/E excelente | ROE excelente | EV/EBITDA excelente |
|---|---|---|---|
| Tecnología | ≤ 18× | ≥ 25% | ≤ 15× |
| Bancos | ≤ 8× | ≥ 18% | N/A |
| Energía | ≤ 7× | ≥ 15% | ≤ 5× |
| Consumo defensivo | ≤ 16× | ≥ 20% | ≤ 12× |
| Salud | ≤ 14× | ≥ 20% | ≤ 12× |
| Utilities | ≤ 12× | ≥ 12% | ≤ 8× |
| Industriales | ≤ 13× | ≥ 20% | ≤ 10× |
""")

        st.markdown("""
### Rating final

| Score | Rating | Acción |
|---|---|---|
| 85–100 | **STRONG BUY** | Incluir con peso máximo |
| 70–84 | **BUY** | Incluir con peso estándar |
| 55–69 | **HOLD** | Incluir si el perfil lo permite |
| 40–54 | **UNDERWEIGHT** | Solo en perfiles agresivos |
| 0–39 | **AVOID** | No incluir en ningún perfil |
""")

    # ── Tab 3: Construcción del portafolio ────────────────────────────────────
    with tabs[2]:
        st.markdown("""
### Sistema de buckets por perfil

Cada perfil de riesgo tiene segmentos predefinidos con target de peso y candidatos.
El algoritmo selecciona los mejores activos **por score** dentro de cada segmento:
""")
        st.markdown("""
| Perfil | Buckets principales |
|---|---|
| **Conservador** | Liquidez ARS · Cobertura MEP · Renta fija USD · ETF global |
| **Estable** | Liquidez · MEP · Renta fija · ETF global · 1 acción ARG |
| **Moderado** | MEP · Renta fija · ETF global · Equity global · Equity ARG |
| **Agresivo** | MEP · Renta fija mínima · ETF tech · Equity global × 3 · Equity ARG × 2 |
""")

        st.markdown("---")
        st.markdown("""
### Ponderación score-driven

Dentro de cada bucket, los pesos son **proporcionales al score**:

```
weight_i = score_i / Σ score_j   (para todos j en el bucket)
```

Esto significa que un activo con score 80 recibe el doble de peso
que uno con score 40, dentro del mismo segmento. No hay pesos arbitrarios.

### Ajustes secuenciales

Sobre la asignación base se aplican ajustes en cascada:

1. **Horizonte temporal**: > 10 años → reduce liquidez, sube equity
2. **Fondo de emergencia**: si no tiene → sube liquidez 10%
3. **Experiencia**: principiante → reemplaza acciones individuales por ETFs
4. **Ingresos**: irregulares → sube liquidez, reduce volátiles 25%
5. **Señales de sector**: sobrepondera sectores baratos vs su historia
6. **Filtros**: liquidez mínima, exclusión de overlaps ETF/stocks
""")

        st.markdown("---")
        st.markdown("### Base académica del modelo")
        st.info("""
**La cantidad óptima de activos por perfil está basada en:**

- **Markowitz, H. (1952).** *Portfolio Selection.* Journal of Finance. Premio Nobel 1990.
  Demostró matemáticamente que la diversificación reduce el riesgo sin sacrificar retorno esperado,
  y que existe una frontera eficiente de carteras óptimas.

- **Evans, J. & Archer, S. (1968).** *Diversification and the Reduction of Dispersion.*
  Journal of Finance. Demostró empíricamente que con 10 activos se elimina el 90% del riesgo
  diversificable; el beneficio marginal de agregar más activos cae rápidamente.

- **Vanguard Research (2012).** Demostró que 4–7 ETFs bien diversificados replican el 95%
  de los beneficios de un portafolio de 500 activos.

> **Nota:** dado que esta cartera incluye ETFs que contienen internamente cientos de empresas,
> el número óptimo de instrumentos es menor que en portafolios de acciones individuales puras.
> Un ETF como SPY ya representa 500 empresas; añadir más posiciones individuales genera
> redundancia sin mejora estadística de diversificación.

| Perfil | Posiciones máx. | Fundamento |
|---|---|---|
| Conservador | 5 | Vanguard: 4–7 ETFs = 95% del beneficio |
| Estable | 7 | Balance entre simplicidad y cobertura sectorial |
| Moderado | 8 | Evans & Archer: beneficio marginal ≈ 0 después del activo 10 |
| Agresivo | 12 | Mayor granularidad en equity individual; riesgo idiosincrático controlado |
""")

    # ── Tab 4: Señales de mercado ─────────────────────────────────────────────
    with tabs[3]:
        st.markdown("""
### Señal de valuación sectorial

El sistema acumula medianas históricas de cada sector cada vez que corre el scorer.
Con ≥ 5 snapshots históricos, calcula una señal compuesta:

```
signal = 0.60 × score_signal + 0.40 × pe_signal

score_signal = (score_actual - score_histórico_promedio) / score_histórico_promedio
pe_signal    = (pe_histórico_promedio - pe_actual) / pe_histórico_promedio
```

**Interpretación:**
- Signal > 0 → sector más atractivo que su historia → sobrepesar hasta +15%
- Signal < 0 → sector más caro que su historia → subpesar hasta -15%
- |Signal| > 0.30 → clampeado a ±0.30 (evita sobreajuste)

### Ajuste de memoria individual

Si el sistema detecta que una acción perdió > 5% desde la última evaluación:
aplica -5 puntos al score en la próxima cartera.

Si ganó > 10%: aplica +3 puntos. Clampeado a [-20, +10].

Esto evita que el sistema siga recomendando activos que demostraron mal desempeño.
""")

    # ── Tab 5: Sistema de aprendizaje ────────────────────────────────────────
    with tabs[4]:
        st.markdown("""
### Memoria del sistema

El sistema mantiene un archivo `memory.json` con tres niveles de aprendizaje:
""")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("""
**Nivel 1: Historial de carteras**
- Cada cartera generada queda registrada con fecha, composición y perfil
- Permite detectar patrones de rendimiento entre sesiones
- Base para las señales de ajuste individual
""")
        with col2:
            st.markdown("""
**Nivel 2: Medianas de sector**
- Snapshots periódicos de PE, EV/EBITDA y score por sector
- Se acumulan para construir la serie histórica
- Alimentan las señales de valuación sectorial
""")
        with col3:
            st.markdown("""
**Nivel 3: Ajustes por ticker**
- Registro de retornos observados por activo
- Ajuste dinámico de score individual
- Sesgos de mercado local detectados automáticamente
""")

        st.markdown("---")
        st.info("El sistema de aprendizaje es incremental: en las primeras semanas, las señales de sector son neutras. A medida que acumula snapshots, las señales se vuelven estadísticamente confiables.")

    # ── Tab 6: Fuentes de datos ───────────────────────────────────────────────
    with tabs[5]:
        st.markdown("""
### Fuentes de datos del sistema
""")
        st.markdown("""
| Dato | Fuente | Frecuencia | Método |
|---|---|---|---|
| Fundamentals equity (PE, ROE, márgenes, etc.) | **Finviz.com** | Semanal | Web scraping via finvizfinance |
| Precios y volumen de bonos ARG | **Rava.com** | Por corrida | API JSON + HTML fallback |
| TIR estimada de bonos | **BOND_DEFS estáticos** | Manual | Actualizable en código |
| Tipo de cambio MEP | **dolarapi.com** | Tiempo real (cache 30 min) | REST API pública |
| Precios históricos para backtesting | **Yahoo Finance** | Por consulta | yfinance |
| Recomendación de analistas | **Finviz.com** | Semanal | Campo "Recom." del screener |
| Precio objetivo consenso | **Finviz.com** | Semanal | Campo "Target Price" |
| Scores de bonos ARG | **bond_scorer.py** | Por corrida | Motor propio |
""")

        st.markdown("---")
        st.markdown("""
### Universo de activos cubierto

- **75 tickers** scrapeados de Finviz (CEDEARs + ADRs argentinos)
- **13 bonos** en `BOND_DEFS` (soberanos USD, LECAPs, ONs corporativas)
- **3 sectores con benchmarks**: utilities (5 tickers), materiales (5), transporte (5)
  → garantizan señales de sector con mínimo 5 puntos de datos
- **6 ETFs globales**: SPY, QQQ, VTI, IAU, GLD, EEM
- **Activos en pesos**: plazo fijo, money market, FCI T+0, FCI renta fija
""")

        st.markdown("""
### Limitaciones conocidas

- La TIR de bonos ARG es mayormente estática (no hay API oficial confiable con datos de TIR en tiempo real)
- La memoria es local al entorno de deployment (no persiste entre instancias de Streamlit Cloud)
- El backtesting cubre solo la porción equity (bonos y pesos sin series históricas en Yahoo Finance)
- Los scores se actualizan semanalmente, no en tiempo real
""")

        if st.button("← Volver a la cartera", key="back_from_methodology"):
            st.session_state.step = st.session_state.get("_prev_step", "results")
            st.rerun()


def render_how_it_works():
    """Explicación en lenguaje simple para el usuario no experto."""
    st.markdown("""<div style="text-align:center;padding:2rem 0 0.5rem;">
<div style="font-size:2rem;margin-bottom:0.5rem;">🧩</div>
<h2 style="font-family:'Syne',sans-serif;font-size:1.6rem;font-weight:800;margin-bottom:0.3rem;">
  Cómo construimos su cartera sugerida
</h2>
<p style="color:#94a3b8;font-size:0.93rem;max-width:520px;margin:0 auto;">
  La transparencia es parte del asesoramiento responsable.
</p>
</div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    _cards = [
        {
            "icon": "🎯",
            "title": "Qué hace esta herramienta",
            "body": (
                "TuPortafolioIA analiza sus respuestas y las compara con un modelo de asignación de activos "
                "construido sobre datos históricos del mercado argentino e internacional. "
                "El resultado es una <strong>cartera teórica de referencia</strong>, no una orden de compra. "
                "Es un punto de partida para conversar con un asesor real — no un reemplazo."
            ),
        },
        {
            "icon": "📋",
            "title": "Cómo se eligen los activos",
            "body": (
                "El universo de activos fue seleccionado considerando:<br>"
                "<strong>1.</strong> Liquidez real en BYMA superior a USD 100.000 diarios<br>"
                "<strong>2.</strong> Historial de pagos y solvencia del emisor (acciones, bonos y ONs)<br>"
                "<strong>3.</strong> Accesibilidad para inversores individuales desde plataformas como IOL o Balanz<br>"
                "Los retornos esperados son promedios históricos de los últimos 5 años, no proyecciones."
            ),
        },
        {
            "icon": "📐",
            "title": "Cómo se calculan retornos y riesgo",
            "body": (
                "<strong>Retorno esperado:</strong> promedio histórico anualizado por activo.<br>"
                "<strong>Volatilidad:</strong> desviación estándar anualizada del precio.<br>"
                "<strong>TIR de bonos y ONs:</strong> calculada por fórmula "
                "(Tasa libre de riesgo USA + Riesgo país Argentina + Spread del emisor).<br>"
                "No utilizamos precios de mercado en tiempo real para renta fija — "
                "los TIR son estimaciones actualizadas semanalmente."
            ),
        },
        {
            "icon": "❌",
            "title": "Qué NO hace esta herramienta",
            "items": [
                ("No tiene memoria entre sesiones", "Cada vez que abre la app, empieza de cero."),
                ("No detecta cambios corporativos en tiempo real", "Si una empresa cambia de CEO o reporta resultados, no lo sabremos hasta la próxima actualización."),
                ("No conoce su situación patrimonial completa", "Solo ve lo que usted declara en el cuestionario."),
                ("No tiene precios de bonos y ONs en tiempo real", "Los rendimientos se estiman con fórmulas, no con datos de mercado en vivo."),
                ("No reemplaza a un asesor regulado por la CNV", "Somos una herramienta educativa. Para decisiones reales, consulte un profesional."),
                ("El universo de activos no se actualiza automáticamente", "La selección de activos se revisa manualmente cada cierto tiempo."),
            ],
        },
        {
            "icon": "📅",
            "title": "Cuándo fue la última revisión",
            "body": (
                "<strong>Universo de activos:</strong> Abril 2025<br>"
                "<strong>Retornos y volatilidades:</strong> Mayo 2025<br>"
                "<strong>Modelo de scoring (Finviz):</strong> se actualiza automáticamente cada 7 días<br>"
                "<strong>Scores de bonos:</strong> se actualizan con el riesgo país en cada sesión"
            ),
        },
    ]

    for card in _cards:
        with st.expander(f"{card['icon']}  {card['title']}", expanded=False):
            if "items" in card:
                for item_title, item_desc in card["items"]:
                    st.markdown(
                        f'<div style="display:flex;gap:10px;margin-bottom:10px;">'
                        f'<span style="color:#ef4444;font-size:1rem;flex-shrink:0;">❌</span>'
                        f'<div><strong style="color:#e2e8f0;">{item_title}</strong>'
                        f'<br><span style="font-size:0.82rem;color:#94a3b8;">{item_desc}</span></div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.markdown(
                    f'<p style="font-size:0.9rem;color:#cbd5e1;line-height:1.75;">{card["body"]}</p>',
                    unsafe_allow_html=True,
                )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""<div class="alert-card alert-medium">
<span class="alert-icon">⚠️</span>
<div style="font-size:0.88rem;color:#94a3b8;line-height:1.7;">
  Esta herramienta tiene <strong style="color:#e2e8f0;">fines educativos</strong> y no constituye
  asesoramiento financiero regulado por la CNV.
  Antes de invertir su dinero, consulte siempre con un asesor habilitado.
</div>
</div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    _, col_cta, _ = st.columns([1, 2, 1])
    with col_cta:
        if st.button("Entendido → Iniciar mi evaluación", key="how_cta", use_container_width=True):
            st.session_state.step = "profiling"
            st.rerun()

    if st.button("← Volver", key="back_from_how", use_container_width=False):
        st.session_state.step = st.session_state.get("_prev_step", "intro")
        st.rerun()
