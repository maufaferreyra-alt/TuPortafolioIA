"""
Motor de scoring fundamental para acciones y CEDEARs.
Evalúa 5 bloques: Valuación (25) + Calidad (25) + Solvencia (20) +
Crecimiento (20) + Cualitativo (10) = 100 pts máximo.
"""

from dataclasses import dataclass, field
from typing import Optional

from memory_manager import load_memory


# ─── Dataclass resultado ──────────────────────────────────────────────────────

@dataclass
class ScoreResult:
    ticker:              str
    sector:              str
    score_total:         int
    rating:              str
    bloque_valuacion:    int          # max 25
    bloque_calidad:      int          # max 25
    bloque_solvencia:    int          # max 20
    bloque_crecimiento:  int          # max 20
    bloque_cualitativo:  int          # max 10  (siempre 5, neutral)
    detalle:             dict  = field(default_factory=dict)
    ajustes_aplicados:   list  = field(default_factory=list)


# ─── Umbrales por sector ──────────────────────────────────────────────────────
# Formato: (excelente, bueno, neutral, malo)
# menor=mejor: excelente < bueno < neutral
# mayor=mejor: excelente > bueno > neutral

UMBRALES_FWD_PE = {          # menor=mejor
    "tecnologia":          (18, 25, 35, 999),
    "bancos":              ( 8, 11, 14, 999),
    "energia":             ( 7, 10, 14, 999),
    "utilities":           (12, 15, 18, 999),
    "consumo_defensivo":   (16, 21, 25, 999),
    "consumo_discrecional":(10, 15, 20, 999),
    "salud":               (14, 20, 26, 999),
    "industriales":        (13, 18, 22, 999),
    "materiales":          ( 9, 13, 18, 999),
    "telecom":             (11, 15, 19, 999),
    "transporte":          (10, 14, 18, 999),
    "default":             (14, 20, 25, 999),
}

UMBRALES_EV = {              # menor=mejor
    "tecnologia":          (15, 20, 25, 999),
    "bancos":              (999,999,999, 999),   # no aplica — neutral
    "energia":             ( 5,  7,  9, 999),
    "utilities":           ( 8, 10, 13, 999),
    "consumo_defensivo":   (12, 16, 20, 999),
    "consumo_discrecional":(10, 14, 18, 999),
    "salud":               (12, 16, 22, 999),
    "industriales":        (10, 13, 17, 999),
    "materiales":          ( 5,  7, 10, 999),
    "telecom":             ( 5,  7,  9, 999),
    "transporte":          ( 7, 10, 14, 999),
    "default":             (10, 14, 18, 999),
}

UMBRALES_PEG = {             # menor=mejor
    "default":             (1.0, 1.5, 2.0, 999),
}

UMBRALES_DIV = {             # mayor=mejor
    "utilities":           (5.0, 4.0, 3.0, 0),
    "consumo_defensivo":   (3.5, 2.5, 1.5, 0),
    "telecom":             (6.0, 4.0, 2.5, 0),
    "energia":             (5.0, 3.0, 2.0, 0),
    "bancos":              (5.0, 3.0, 1.5, 0),
    "tecnologia":          (2.0, 1.0, 0.5, 0),
    "default":             (4.0, 2.5, 1.0, 0),
}

UMBRALES_ROE = {             # mayor=mejor
    "tecnologia":          (25, 15,  8, 0),
    "bancos":              (18, 13,  8, 0),
    "energia":             (15, 10,  6, 0),
    "utilities":           (12,  9,  6, 0),
    "consumo_defensivo":   (20, 15, 10, 0),
    "consumo_discrecional":(18, 12,  7, 0),
    "salud":               (20, 15, 10, 0),
    "industriales":        (20, 15,  9, 0),
    "materiales":          (18, 12,  7, 0),
    "telecom":             (15, 10,  5, 0),
    "default":             (18, 13,  8, 0),
}

UMBRALES_MARGEN = {          # mayor=mejor
    "tecnologia":          (25, 15,  8, 0),
    "bancos":              (25, 18, 10, 0),
    "energia":             (12,  8,  4, 0),
    "utilities":           (12,  8,  4, 0),
    "consumo_defensivo":   (15, 10,  6, 0),
    "consumo_discrecional":(12,  7,  3, 0),
    "salud":               (25, 18, 10, 0),
    "industriales":        (10,  7,  3, 0),
    "materiales":          (12,  7,  3, 0),
    "telecom":             (10,  7,  3, 0),
    "default":             (12,  8,  4, 0),
}

UMBRALES_ROA = {             # mayor=mejor
    "bancos":              (1.5, 1.0, 0.5, 0),
    "default":             (10,   6,   3,  0),
}

UMBRALES_DE = {              # menor=mejor
    "tecnologia":          (0.5, 1.0, 2.0, 999),
    "bancos":              (999, 999, 999, 999),  # no aplica — neutral
    "energia":             (0.5, 1.0, 2.0, 999),
    "utilities":           (1.5, 2.5, 4.0, 999),
    "consumo_defensivo":   (0.5, 1.0, 2.0, 999),
    "consumo_discrecional":(0.5, 1.5, 3.0, 999),
    "salud":               (0.5, 1.5, 3.0, 999),
    "industriales":        (0.5, 1.5, 2.5, 999),
    "materiales":          (0.3, 1.0, 2.0, 999),
    "telecom":             (1.0, 2.0, 3.5, 999),
    "default":             (0.5, 1.0, 2.0, 999),
}

UMBRALES_CR = {              # mayor=mejor
    "default":             (2.0, 1.5, 1.0, 0),
}

UMBRALES_QR = {              # mayor=mejor
    "default":             (1.5, 1.0, 0.7, 0),
}

UMBRALES_EPS_CAGR = {        # mayor=mejor
    "tecnologia":          (20, 12,  5, 0),
    "bancos":              (12,  8,  3, 0),
    "energia":             (10,  6,  2, 0),
    "consumo_defensivo":   ( 8,  5,  2, 0),
    "salud":               (12,  8,  4, 0),
    "industriales":        (12,  8,  4, 0),
    "default":             (12,  8,  3, 0),
}

UMBRALES_SALES_CAGR = {      # mayor=mejor
    "tecnologia":          (20, 12,  5, 0),
    "consumo_defensivo":   ( 6,  3,  1, 0),
    "salud":               (10,  6,  3, 0),
    "default":             (10,  6,  2, 0),
}

UMBRALES_EPS_QOQ = {         # mayor=mejor
    "default":             (15, 8, 2, -999),
}


# ─── Funciones base ───────────────────────────────────────────────────────────

def score_menor_mejor(v: Optional[float], umbral: tuple, max_pts: int) -> int:
    """Puntúa métricas donde menor valor es mejor (P/E, EV/EBITDA, Deuda/Eq)."""
    if v is None:
        return 0
    exc, bue, neu, _ = umbral
    if exc == 999:                    # métrica no aplica para este sector
        return round(max_pts * 0.5)
    if v <= exc:   return max_pts
    if v <= bue:   return round(max_pts * 0.75)
    if v <= neu:   return round(max_pts * 0.45)
    return round(max_pts * 0.10)


def score_mayor_mejor(v: Optional[float], umbral: tuple, max_pts: int) -> int:
    """Puntúa métricas donde mayor valor es mejor (ROE, márgenes, crecimiento)."""
    if v is None:
        return 0
    exc, bue, neu, _ = umbral
    if v >= exc:   return max_pts
    if v >= bue:   return round(max_pts * 0.75)
    if v >= neu:   return round(max_pts * 0.45)
    return round(max_pts * 0.10)


def get_umbral(metrica: str, sector: str, tabla: dict) -> tuple:
    """Retorna el umbral del sector si existe, sino el default."""
    return tabla.get(sector, tabla.get("default", (999, 999, 999, 999)))


def get_rating(score: int) -> str:
    if score >= 85:   return "STRONG BUY"
    elif score >= 70: return "BUY"
    elif score >= 55: return "HOLD"
    elif score >= 40: return "UNDERWEIGHT"
    else:             return "AVOID"


# ─── Motor de scoring ─────────────────────────────────────────────────────────

def calcular_score(ratios: dict, memory: dict) -> ScoreResult:
    """
    Calcula el score fundamental del activo en 5 bloques (0-100).
    Aplica ajustes de aprendizaje del sector si existen en memory.
    """
    sector     = ratios.get("sector_framework", "default")
    ticker     = ratios.get("ticker", "?")
    aprendizaje = memory.get("aprendizaje", {})
    ajustes    = aprendizaje.get("ajustes_calidad_sector", {}).get(sector, {})
    detalle:   dict = {}
    aplicados: list = []

    # ── Extraer ratios ────────────────────────────────────────────────────────
    fwd_pe    = ratios.get("forward_pe")
    pe        = ratios.get("pe")
    peg       = ratios.get("peg")
    ev        = ratios.get("ev_ebitda")
    div       = ratios.get("dividend_yield")
    roe       = ratios.get("roe")
    roa       = ratios.get("roa")
    margen    = ratios.get("margen_neto")
    de        = ratios.get("deuda_equity")
    cr        = ratios.get("current_ratio")
    qr        = ratios.get("quick_ratio")
    eps_cagr  = ratios.get("eps_cagr_5y")
    sales_cagr= ratios.get("ventas_cagr_5y")
    eps_qoq   = ratios.get("eps_qoq")


    # Usar forward_pe si disponible, sino pe
    fwd_pe_use = fwd_pe if fwd_pe is not None else pe

    # Aplicar ajustes de aprendizaje
    if "forward_pe" in ajustes and fwd_pe_use is not None:
        fwd_pe_use += ajustes["forward_pe"]
        aplicados.append(f"forward_pe ajustado en {ajustes['forward_pe']:+.1f} para {sector}")

    # ── Bloque 1: Valuación (max 25) ─────────────────────────────────────────
    fwd_pe_pts = score_menor_mejor(fwd_pe_use, get_umbral("fwd_pe", sector, UMBRALES_FWD_PE), 7)
    ev_pts     = score_menor_mejor(ev,         get_umbral("ev",     sector, UMBRALES_EV),     8)
    peg_pts    = score_menor_mejor(peg,        get_umbral("peg",    sector, UMBRALES_PEG),    5)
    div_pts    = score_mayor_mejor(div,        get_umbral("div",    sector, UMBRALES_DIV),    5)
    b1 = min(fwd_pe_pts + ev_pts + peg_pts + div_pts, 25)

    detalle["B1_fwd_pe"]  = fwd_pe_pts
    detalle["B1_ev"]      = ev_pts
    detalle["B1_peg"]     = peg_pts
    detalle["B1_div"]     = div_pts
    detalle["B1_total"]   = b1

    # ── Bloque 2: Calidad (max 25) ────────────────────────────────────────────
    roe_pts    = score_mayor_mejor(roe,    get_umbral("roe",    sector, UMBRALES_ROE),    10)
    margen_pts = score_mayor_mejor(margen, get_umbral("margen", sector, UMBRALES_MARGEN),  8)
    roa_pts    = score_mayor_mejor(roa,    get_umbral("roa",    sector, UMBRALES_ROA),     7)
    b2 = min(roe_pts + margen_pts + roa_pts, 25)

    detalle["B2_roe"]     = roe_pts
    detalle["B2_margen"]  = margen_pts
    detalle["B2_roa"]     = roa_pts
    detalle["B2_total"]   = b2

    # ── Bloque 3: Solvencia (max 20) ─────────────────────────────────────────
    de_pts  = score_menor_mejor(de, get_umbral("de", sector, UMBRALES_DE), 10)
    cr_pts  = score_mayor_mejor(cr, get_umbral("cr", sector, UMBRALES_CR),  5)
    qr_pts  = score_mayor_mejor(qr, get_umbral("qr", sector, UMBRALES_QR),  5)
    b3 = min(de_pts + cr_pts + qr_pts, 20)

    detalle["B3_de"]      = de_pts
    detalle["B3_cr"]      = cr_pts
    detalle["B3_qr"]      = qr_pts
    detalle["B3_total"]   = b3

    # ── Bloque 4: Crecimiento (max 20) ───────────────────────────────────────
    eps_pts   = score_mayor_mejor(eps_cagr,   get_umbral("eps",   sector, UMBRALES_EPS_CAGR),   8)
    sales_pts = score_mayor_mejor(sales_cagr, get_umbral("sales", sector, UMBRALES_SALES_CAGR), 7)
    qoq_pts   = score_mayor_mejor(eps_qoq,   UMBRALES_EPS_QOQ["default"],                       5)
    b4 = min(eps_pts + sales_pts + qoq_pts, 20)

    detalle["B4_eps_cagr"]   = eps_pts
    detalle["B4_sales_cagr"] = sales_pts
    detalle["B4_eps_qoq"]    = qoq_pts
    detalle["B4_total"]      = b4

    # ── Bloque 5: Cualitativo (max 10) ───────────────────────────────────────
    recom       = ratios.get("recomendacion")
    target_px   = ratios.get("target_price")
    precio_act  = ratios.get("precio")
    short_float = ratios.get("short_float")

    # Recomendación de analistas (4 pts): escala Finviz 1=Strong Buy … 5=Sell
    if recom is not None:
        b5_recom = 4 if recom <= 2.0 else (3 if recom <= 2.5 else (1 if recom < 3.0 else 0))
    else:
        b5_recom = 2   # neutral cuando no hay datos

    # Upside al precio objetivo (3 pts)
    if target_px is not None and precio_act is not None and precio_act > 0:
        upside = (target_px - precio_act) / precio_act * 100
        b5_target = 3 if upside >= 15 else (1 if upside >= 0 else 0)
    else:
        b5_target = 1   # neutral sin datos

    # Short float bajo → señal positiva (3 pts)
    if short_float is not None:
        b5_short = 3 if short_float < 2 else (1 if short_float < 5 else 0)
    else:
        b5_short = 2   # neutral sin datos

    b5 = min(b5_recom + b5_target + b5_short, 10)
    detalle["B5_recom"]      = b5_recom
    detalle["B5_target"]     = b5_target
    detalle["B5_short"]      = b5_short
    detalle["B5_cualitativo"] = b5

    # ── Total ─────────────────────────────────────────────────────────────────
    total = b1 + b2 + b3 + b4 + b5

    # Ajuste individual por historial del ticker
    ticker_adj = aprendizaje.get("score_ajustes", {}).get(ticker, 0)
    if ticker_adj != 0:
        total = max(0, min(100, total + ticker_adj))
        aplicados.append(f"{ticker}: ajuste histórico {ticker_adj:+d} pts → total {total}")

    return ScoreResult(
        ticker             = ticker,
        sector             = sector,
        score_total        = total,
        rating             = get_rating(total),
        bloque_valuacion   = b1,
        bloque_calidad     = b2,
        bloque_solvencia   = b3,
        bloque_crecimiento = b4,
        bloque_cualitativo = b5,
        detalle            = detalle,
        ajustes_aplicados  = aplicados,
    )


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from memory_manager import load_memory
    mem = load_memory()
    ratios_mock = {
        "ticker": "TEST", "sector_framework": "tecnologia",
        "forward_pe": 22.1, "pe": 28.5, "peg": 1.4, "ev_ebitda": 18.3,
        "dividend_yield": 0.8, "roe": 38.5, "roa": 12.1, "margen_neto": 25.3,
        "deuda_equity": 0.35, "current_ratio": 1.8, "quick_ratio": 1.5,
        "eps_cagr_5y": 14.2, "ventas_cagr_5y": 10.1, "eps_qoq": 9.5,
    }
    r = calcular_score(ratios_mock, mem)
    print(f"Ticker  : {r.ticker}")
    print(f"Score   : {r.score_total}/100")
    print(f"Rating  : {r.rating}")
    print(f"Bloques : VAL={r.bloque_valuacion} CAL={r.bloque_calidad} "
          f"SOL={r.bloque_solvencia} CRE={r.bloque_crecimiento} CUA={r.bloque_cualitativo}")
    print("\nDetalle:")
    for k, v in r.detalle.items():
        print(f"  {k:<20} {v}")
    print("✅ scoring_engine OK")
