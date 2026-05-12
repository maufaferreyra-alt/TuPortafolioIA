"""
Motor de scoring Finviz para el universo de CEDEARs y ADRs argentinos.

Uso offline (antes de cada release):
    python -m modules.finviz_scorer
Genera finviz_scores.json en la raíz del proyecto.
portfolio.py lo consume en build_portfolio() para ajustar pesos y filtrar.

Requiere: pip install finvizfinance requests pandas
"""

import json
import time
from datetime import datetime
from pathlib import Path

# ─── Tickers del universo ─────────────────────────────────────────────────────
SCOREABLE_TICKERS = [
    # CEDEARs — originales
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "BRK-B",
    "JPM",  "KO",   "WMT",   "JNJ",  "PFE",  "XOM",  "TSLA", "BAC", "DIS",
    "MELI",
    # CEDEARs — tecnología adicional
    "AMD",  "NFLX", "ORCL", "CRM",  "ADBE", "UBER", "GLOB",
    # CEDEARs — finanzas adicional
    "V",    "MA",   "GS",   "MS",
    # CEDEARs — salud adicional
    "UNH",  "LLY",  "MRK",
    # CEDEARs — consumo adicional
    "HD",   "COST", "MCD",  "NKE",
    # CEDEARs — energía adicional
    "CVX",
    # CEDEARs — semiconductores/tech adicional
    "INTC", "TSM", "QCOM", "SHOP", "PYPL",
    # CEDEARs — consumo defensivo adicional
    "PG", "PM", "SBUX", "TGT",
    # CEDEARs — industrial adicional
    "BA", "CAT",
    # CEDEARs — global/emergentes
    "BABA",
    # CEDEARs — utilities/energía renovable
    "NEE",
    # Bancos/Finanzas adicional
    "WFC", "C", "AXP", "COF", "SCHW", "BLK",
    # Tech/SaaS/Cloud
    "PLTR", "NOW", "CRWD", "PANW", "DDOG", "NET", "FTNT", "COIN", "SQ", "HOOD", "RBLX", "SNOW",
    # Pharma/Biotech
    "ABBV", "BMY", "GILD", "AMGN", "MRNA", "REGN", "VRTX",
    # Consumo/Viajes
    "LOW", "TJX", "ABNB", "BKNG", "MAR", "HLT", "CCL", "RCL", "DKNG", "EBAY",
    # Media/Telecom
    "SPOT", "T", "VZ", "CMCSA",
    # Industrial/Defensa
    "RTX", "LMT", "DE", "HON", "UPS", "FDX", "GE",
    # Energía adicional
    "OXY", "SLB", "COP",
    # Semiconductores adicional
    "ASML", "MU", "AMAT", "AVGO",
    # Auto/EV
    "F", "GM", "RIVN", "NIO",
    # Utilities
    "SO", "D",
    # REITs
    "AMT", "PLD", "O",
    # Acciones ARG (ADRs en NYSE/NASDAQ)
    "YPF",  "VIST", "GGAL", "LOMA", "TEO",  "PAM",  "BBAR",
    "BMA",  "SUPV", "TGS",  "CEPU", "IRS",  "CRESY", "EDN",
    # ETFs — NO van aquí; se scorean por el motor ETF estático en run_and_save()
]

# Tickers benchmark por sector — se usan SOLO para calcular medianas de sector.
# No están en ASSET_TO_FINVIZ (nunca entran al portfolio), pero enriquecen
# los sectores con pocos CEDEARs para que las señales históricas sean confiables.
BENCHMARK_TICKERS: dict[str, list[str]] = {
    # Utilities: NEE + CEPU solo dan 2 puntos → insuficiente
    "utilities": ["DUK", "SO", "EXC", "AES", "D"],
    # Materiales: LOMA solo da 1 punto → insuficiente
    "materiales": ["FCX", "NEM", "LIN", "APD", "ECL"],
    # Transporte: no tenemos ninguno en CEDEARs ARG
    "transporte": ["UPS", "FDX", "CSX", "NSC", "DAL"],
}

# Mapeo asset_id (portfolio.py) → ticker Finviz
ASSET_TO_FINVIZ = {
    # CEDEARs originales
    "aapl":    "AAPL",
    "msft":    "MSFT",
    "googl":   "GOOGL",
    "amzn":    "AMZN",
    "nvda":    "NVDA",
    "meta":    "META",
    "brk":     "BRK-B",
    "jpm":     "JPM",
    "ko":      "KO",
    "wmt":     "WMT",
    "jnj":     "JNJ",
    "pfe":     "PFE",
    "xom":     "XOM",
    "tsla":    "TSLA",
    "bac":     "BAC",
    "dis":     "DIS",
    "meli":    "MELI",
    # CEDEARs tecnología adicional
    "amd":     "AMD",
    "nflx":    "NFLX",
    "orcl":    "ORCL",
    "crm":     "CRM",
    "adbe":    "ADBE",
    "uber":    "UBER",
    "glob":    "GLOB",
    # CEDEARs finanzas adicional
    "v":       "V",
    "ma":      "MA",
    "gs":      "GS",
    "ms":      "MS",
    # CEDEARs salud adicional
    "unh":     "UNH",
    "lly":     "LLY",
    "mrk":     "MRK",
    # CEDEARs consumo adicional
    "hd":      "HD",
    "cost":    "COST",
    "mcd":     "MCD",
    "nke":     "NKE",
    # CEDEARs energía adicional
    "cvx":     "CVX",
    # CEDEARs semiconductores/tech adicional
    "intc":    "INTC",
    "tsm":     "TSM",
    "qcom":    "QCOM",
    "shop":    "SHOP",
    "pypl":    "PYPL",
    # CEDEARs consumo defensivo adicional
    "pg":      "PG",
    "pm":      "PM",
    "sbux":    "SBUX",
    "tgt":     "TGT",
    # CEDEARs industrial adicional
    "ba":      "BA",
    "cat":     "CAT",
    # CEDEARs global/emergentes
    "baba":    "BABA",
    # CEDEARs utilities/energía renovable
    "nee":     "NEE",
    # Bancos/Finanzas adicional
    "wfc":   "WFC",
    "c":     "C",
    "axp":   "AXP",
    "cof":   "COF",
    "schw":  "SCHW",
    "blk":   "BLK",
    # Tech/SaaS/Cloud
    "pltr":  "PLTR",
    "now":   "NOW",
    "crwd":  "CRWD",
    "panw":  "PANW",
    "ddog":  "DDOG",
    "net":   "NET",
    "ftnt":  "FTNT",
    "coin":  "COIN",
    "sq":    "SQ",
    "hood":  "HOOD",
    "rblx":  "RBLX",
    "snow":  "SNOW",
    # Pharma/Biotech
    "abbv":  "ABBV",
    "bmy":   "BMY",
    "gild":  "GILD",
    "amgn":  "AMGN",
    "mrna":  "MRNA",
    "regn":  "REGN",
    "vrtx":  "VRTX",
    # Consumo/Viajes
    "low":   "LOW",
    "tjx":   "TJX",
    "abnb":  "ABNB",
    "bkng":  "BKNG",
    "mar":   "MAR",
    "hlt":   "HLT",
    "ccl":   "CCL",
    "rcl":   "RCL",
    "dkng":  "DKNG",
    "ebay":  "EBAY",
    # Media/Telecom
    "spot":  "SPOT",
    "t":     "T",
    "vz":    "VZ",
    "cmcsa": "CMCSA",
    # Industrial/Defensa
    "rtx":   "RTX",
    "lmt":   "LMT",
    "de":    "DE",
    "hon":   "HON",
    "ups":   "UPS",
    "fdx":   "FDX",
    "ge":    "GE",
    # Energía adicional
    "oxy":   "OXY",
    "slb":   "SLB",
    "cop":   "COP",
    # Semiconductores adicional
    "asml":  "ASML",
    "mu":    "MU",
    "amat":  "AMAT",
    "avgo":  "AVGO",
    # Auto/EV
    "f":     "F",
    "gm":    "GM",
    "rivn":  "RIVN",
    "nio":   "NIO",
    # Utilities
    "so":    "SO",
    "d":     "D",
    # REITs
    "amt":   "AMT",
    "pld":   "PLD",
    "o":     "O",
    # Acciones ARG
    "ypf":     "YPF",
    "vist":    "VIST",
    "galicia": "GGAL",
    "loma":    "LOMA",
    "teco2":   "TEO",
    "pampa":   "PAM",
    "bbar":    "BBAR",
    "bma":     "BMA",
    "supv":    "SUPV",
    "tgs":     "TGS",
    "cepu":    "CEPU",
    "irsa":    "IRS",
    "cres":    "CRESY",
    # ARG con ADR
    "edn":   "EDN",
    # ETFs — mapeados para el motor ETF estático de run_and_save()
    "spy":     "SPY",
    "qqq":     "QQQ",
    "vti":     "VTI",
    "iau":     "IAU",
    "gld":     "GLD",
    "eem":     "EEM",
}

# ─── Sección 4: Mapeo sector Finviz → sector framework ────────────────────────
SECTOR_MAP = {
    "Technology":                 "tecnologia",
    "Financial":                  "bancos",
    "Financial Services":         "bancos",
    "Banks":                      "bancos",
    "Energy":                     "energia",
    "Utilities":                  "utilities",
    "Consumer Defensive":         "consumo_defensivo",
    "Consumer Staples":           "consumo_defensivo",
    "Consumer Cyclical":          "consumo_discrecional",
    "Consumer Discretionary":     "consumo_discrecional",
    "Healthcare":                 "salud",
    "Health Care":                "salud",
    "Industrials":                "industriales",
    "Basic Materials":            "materiales",
    "Materials":                  "materiales",
    "Communication Services":     "telecom",
    "Telecommunication Services": "telecom",
    "Transportation":             "transporte",
}

# Override de sector para tickers que Finviz clasifica incorrectamente.
# BRK-B es un holding diversificado (no banco puro) → usar "default".
SECTOR_OVERRIDE = {
    "BRK-B": "default",
}

# ─── Tablas de umbrales por sector ────────────────────────────────────────────
# Formato: (excelente, bueno, neutral, malo)
# NA (999) en posición 0 → métrica no aplica → 0 pts para ese sector

NA = 999

# ── VALUACIÓN: menor = mejor ──────────────────────────────────────────────────

FWD_PE = {
    "tecnologia":           (18, 25, 35, NA),
    "bancos":               ( 8, 11, 14, NA),
    "energia":              ( 7, 10, 14, NA),
    "utilities":            (12, 15, 18, NA),
    "consumo_defensivo":    (16, 21, 25, NA),
    "consumo_discrecional": (10, 15, 20, NA),
    "salud":                (14, 20, 26, NA),
    "industriales":         (13, 18, 22, NA),
    "materiales":           ( 9, 13, 18, NA),
    "telecom":              (11, 15, 19, NA),
    "transporte":           (10, 14, 18, NA),
    "agro":                 ( 9, 13, 17, NA),
    "default":              (14, 20, 25, NA),
}

EV_EBITDA = {
    "tecnologia":           (15, 20, 25, NA),
    "bancos":               (NA, NA, NA, NA),   # no aplica
    "energia":              ( 5,  7,  9, NA),
    "utilities":            ( 8, 10, 13, NA),
    "consumo_defensivo":    (12, 16, 20, NA),
    "consumo_discrecional": (10, 14, 18, NA),
    "salud":                (12, 16, 22, NA),
    "industriales":         (10, 13, 17, NA),
    "materiales":           ( 5,  7, 10, NA),
    "telecom":              ( 5,  7,  9, NA),
    "transporte":           ( 7, 10, 14, NA),
    "agro":                 ( 6,  8, 11, NA),
    "default":              (10, 14, 18, NA),
}

PEG = {
    "default": (1.0, 1.5, 2.0, NA),
}

# ── VALUACIÓN: mayor = mejor ──────────────────────────────────────────────────

DIV_YIELD = {
    "utilities":            (5.0, 4.0, 3.0, 0),
    "consumo_defensivo":    (3.5, 2.5, 1.5, 0),
    "telecom":              (6.0, 4.0, 2.5, 0),
    "energia":              (5.0, 3.0, 2.0, 0),
    "bancos":               (5.0, 3.0, 1.5, 0),
    "tecnologia":           (2.0, 1.0, 0.5, 0),
    "default":              (4.0, 2.5, 1.0, 0),
}

# ── CALIDAD: mayor = mejor ────────────────────────────────────────────────────

ROE = {
    "tecnologia":           (25, 15,  8, 0),
    "bancos":               (18, 13,  8, 0),
    "energia":              (15, 10,  6, 0),
    "utilities":            (12,  9,  6, 0),
    "consumo_defensivo":    (20, 15, 10, 0),
    "consumo_discrecional": (18, 12,  7, 0),
    "salud":                (20, 15, 10, 0),
    "industriales":         (20, 15,  9, 0),
    "materiales":           (18, 12,  7, 0),
    "telecom":              (15, 10,  5, 0),
    "default":              (18, 13,  8, 0),
}

PROFIT_MARGIN = {
    "tecnologia":           (25, 15,  8, 0),
    "bancos":               (25, 18, 10, 0),
    "energia":              (12,  8,  4, 0),
    "utilities":            (12,  8,  4, 0),
    "consumo_defensivo":    (15, 10,  6, 0),
    "consumo_discrecional": (12,  7,  3, 0),
    "salud":                (25, 18, 10, 0),
    "industriales":         (10,  7,  3, 0),
    "materiales":           (12,  7,  3, 0),
    "telecom":              (10,  7,  3, 0),
    "default":              (12,  8,  4, 0),
}

ROA = {
    "bancos":  (1.5, 1.0, 0.5, 0),
    "default": (10,  6,   3,   0),
}

# ── SOLVENCIA ─────────────────────────────────────────────────────────────────

DEBT_EQ = {                             # menor = mejor
    "tecnologia":           (0.5, 1.0, 2.0, NA),
    "bancos":               (NA,  NA,  NA,  NA),  # D/E no aplica
    "energia":              (0.5, 1.0, 2.0, NA),
    "utilities":            (1.5, 2.5, 4.0, NA),
    "consumo_defensivo":    (0.5, 1.0, 2.0, NA),
    "consumo_discrecional": (0.5, 1.5, 3.0, NA),
    "salud":                (0.5, 1.5, 3.0, NA),
    "industriales":         (0.5, 1.5, 2.5, NA),
    "materiales":           (0.3, 1.0, 2.0, NA),
    "telecom":              (1.0, 2.0, 3.5, NA),
    "default":              (0.5, 1.0, 2.0, NA),
}

CURRENT_RATIO = {"default": (2.0, 1.5, 1.0, 0)}
QUICK_RATIO   = {"default": (1.5, 1.0, 0.7, 0)}

# ── CRECIMIENTO: mayor = mejor ────────────────────────────────────────────────

EPS_5Y = {
    "tecnologia":           (20, 12, 5, 0),
    "bancos":               (12,  8, 3, 0),
    "energia":              (10,  6, 2, 0),
    "consumo_defensivo":    ( 8,  5, 2, 0),
    "salud":                (12,  8, 4, 0),
    "industriales":         (12,  8, 4, 0),
    "default":              (12,  8, 3, 0),
}

SALES_5Y = {
    "tecnologia":           (20, 12, 5, 0),
    "consumo_defensivo":    ( 6,  3, 1, 0),
    "salud":                (10,  6, 3, 0),
    "default":              (10,  6, 2, 0),
}

# EPS Q/Q: malo=-999 → incluso momentum muy negativo da floor de 0.10 × pts
EPS_QQ = (15, 8, 2, -999)


# ─── Sección 5: funciones de scoring ─────────────────────────────────────────

def score_menor_mejor(valor, umbral: tuple, max_pts: int) -> int:
    """Para P/E, EV/EBITDA, Deuda/Equity, etc."""
    if valor is None:
        return 0
    exc, bue, neu, _ = umbral
    if exc == NA:
        return 0        # métrica no aplica a este sector
    if valor <= exc:
        return max_pts
    elif valor <= bue:
        return round(max_pts * 0.75)
    elif valor <= neu:
        return round(max_pts * 0.45)
    else:
        return round(max_pts * 0.10)


def score_mayor_mejor(valor, umbral: tuple, max_pts: int) -> int:
    """Para ROE, márgenes, crecimiento, etc."""
    if valor is None:
        return 0
    exc, bue, neu, _ = umbral
    if exc == NA:
        return 0
    if valor >= exc:
        return max_pts
    elif valor >= bue:
        return round(max_pts * 0.75)
    elif valor >= neu:
        return round(max_pts * 0.45)
    else:
        return round(max_pts * 0.10)


def _get(table: dict, sector: str) -> tuple:
    return table.get(sector, table.get("default", (NA, NA, NA, NA)))


# ─── Ratings por score final ──────────────────────────────────────────────────

def rating_label(score: int) -> str:
    if score >= 85: return "STRONG BUY"
    if score >= 70: return "BUY"
    if score >= 55: return "HOLD"
    if score >= 40: return "UNDERWEIGHT"
    return "AVOID"


# Score mínimo por perfil de riesgo para incluir el activo en cartera
MIN_SCORE_BY_RISK = {
    "conservador": 70,   # requiere BUY o mejor
    "estable":     55,   # requiere HOLD o mejor
    "moderado":    55,   # requiere HOLD o mejor
    "agresivo":    40,   # acepta UNDERWEIGHT
}


# ─── Motor de scoring por ticker ──────────────────────────────────────────────

def score_ticker(ticker: str, data: dict, sector: str) -> dict:
    """
    Puntúa un activo sobre 100 pts según el framework de 5 bloques.
    Valores ausentes en Finviz → 0 pts (no se omiten ni redistribuyen).
    Devuelve también los ratios crudos para el JSON de output.
    """
    def p(key):
        return parse_float(data.get(key))

    detail = {}

    # Capturar ratios crudos para el output JSON (sección 9)
    ratios = {
        "forward_pe":    p("Forward P/E"),
        "ev_ebitda":     p("EV/EBITDA"),
        "peg":           p("PEG"),
        "roe":           p("ROE"),
        "roa":           p("ROA"),
        "margen_neto":   p("Profit Margin"),
        "deuda_equity":  p("Debt/Eq"),
        "current_ratio": p("Current Ratio"),
        "quick_ratio":   p("Quick Ratio"),
        "eps_cagr_5y":   p("EPS next 5Y"),
        "sales_cagr_5y": p("Sales past 5Y"),
        "eps_qq":        p("EPS Q/Q"),
        "dividend_yield":p("Dividend %"),
        "beta":          p("Beta"),
        # Cualitativo (Bloque 5)
        "recomendacion":  p("Recom."),
        "target_price":   p("Target Price"),
        "precio":         p("Price"),
        "short_float":    p("Short Float"),
    }

    # ── BLOQUE 1: Valuación — 25 pts ─────────────────────────────────────────
    b1_fwd_pe    = score_menor_mejor(ratios["forward_pe"],    _get(FWD_PE,    sector), 7)
    b1_ev_ebitda = score_menor_mejor(ratios["ev_ebitda"],     _get(EV_EBITDA, sector), 8)
    b1_peg       = score_menor_mejor(ratios["peg"],           _get(PEG, "default"),   5)
    b1_div_yield = score_mayor_mejor(ratios["dividend_yield"],_get(DIV_YIELD, sector), 5)
    bloque1      = b1_fwd_pe + b1_ev_ebitda + b1_peg + b1_div_yield
    detail["B1_fwd_pe"]    = b1_fwd_pe
    detail["B1_ev_ebitda"] = b1_ev_ebitda
    detail["B1_peg"]       = b1_peg
    detail["B1_div_yield"] = b1_div_yield

    # ── BLOQUE 2: Calidad — 25 pts ────────────────────────────────────────────
    b2_roe    = score_mayor_mejor(ratios["roe"],         _get(ROE,           sector), 10)
    b2_margin = score_mayor_mejor(ratios["margen_neto"], _get(PROFIT_MARGIN, sector),  8)
    b2_roa    = score_mayor_mejor(ratios["roa"],         _get(ROA,           sector),  7)
    bloque2   = b2_roe + b2_margin + b2_roa
    detail["B2_roe"]    = b2_roe
    detail["B2_margin"] = b2_margin
    detail["B2_roa"]    = b2_roa

    # ── BLOQUE 3: Solvencia — 20 pts ─────────────────────────────────────────
    b3_debt_eq = score_menor_mejor(ratios["deuda_equity"],  _get(DEBT_EQ,       sector), 10)
    b3_current = score_mayor_mejor(ratios["current_ratio"], _get(CURRENT_RATIO, "default"), 5)
    b3_quick   = score_mayor_mejor(ratios["quick_ratio"],   _get(QUICK_RATIO,   "default"), 5)
    bloque3    = b3_debt_eq + b3_current + b3_quick
    detail["B3_debt_eq"] = b3_debt_eq
    detail["B3_current"] = b3_current
    detail["B3_quick"]   = b3_quick

    # ── BLOQUE 4: Crecimiento — 20 pts ───────────────────────────────────────
    b4_eps5y   = score_mayor_mejor(ratios["eps_cagr_5y"],   _get(EPS_5Y,  sector), 8)
    b4_sales5y = score_mayor_mejor(ratios["sales_cagr_5y"], _get(SALES_5Y, sector), 7)
    b4_eps_qq  = score_mayor_mejor(ratios["eps_qq"],        EPS_QQ,                 5)
    bloque4    = b4_eps5y + b4_sales5y + b4_eps_qq
    detail["B4_eps5y"]   = b4_eps5y
    detail["B4_sales5y"] = b4_sales5y
    detail["B4_eps_qq"]  = b4_eps_qq

    # ── BLOQUE 5: Cualitativo — 10 pts ───────────────────────────────────────
    recom    = ratios["recomendacion"]
    tgt_px   = ratios["target_price"]
    px       = ratios["precio"]
    short_fl = ratios["short_float"]

    # Recomendación analistas (4 pts): escala Finviz 1=Strong Buy … 5=Sell
    if recom is not None:
        b5_recom = 4 if recom <= 2.0 else (3 if recom <= 2.5 else (1 if recom < 3.0 else 0))
    else:
        b5_recom = 2

    # Upside al precio objetivo (3 pts)
    if tgt_px is not None and px is not None and px > 0:
        upside   = (tgt_px - px) / px * 100
        b5_tgt   = 3 if upside >= 15 else (1 if upside >= 0 else 0)
    else:
        b5_tgt = 1

    # Short float bajo → bullish (3 pts)
    if short_fl is not None:
        b5_short = 3 if short_fl < 2 else (1 if short_fl < 5 else 0)
    else:
        b5_short = 2

    bloque5 = min(b5_recom + b5_tgt + b5_short, 10)
    detail["B5_recom"]       = b5_recom
    detail["B5_target"]      = b5_tgt
    detail["B5_short"]       = b5_short
    detail["B5_cualitativo"] = bloque5

    # ── SCORE FINAL ───────────────────────────────────────────────────────────
    score = bloque1 + bloque2 + bloque3 + bloque4 + bloque5

    return {
        "ticker":  ticker,
        "sector":  sector,
        "score":   score,
        "rating":  rating_label(score),
        "bloques": {
            "valuacion":   bloque1,
            "calidad":     bloque2,
            "solvencia":   bloque3,
            "crecimiento": bloque4,
            "cualitativo": bloque5,
        },
        "ratios": ratios,
        "detail": detail,
    }


# ─── Factores de ajuste de retorno/volatilidad según score ───────────────────
# Se aplican SOLO a activos scorables (CEDEARs/ADRs).
# Score 70 (BUY) = neutro (×1.0). Rango: 0 → ×0.60, 100 → ×1.40.

def return_factor(score: int) -> float:
    return 0.60 + (score / 100) * 0.80


def vol_factor(score: int) -> float:
    """Mayor calidad estructural → menor volatilidad realizada."""
    return 1.30 - (score / 100) * 0.60


# ─── Parser de valores Finviz ─────────────────────────────────────────────────

def parse_float(v):
    if v in (None, "", "-", "N/A"):
        return None
    v = str(v).replace("%", "").replace(",", "").strip()
    mults = {"K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12}
    if v and v[-1].upper() in mults:
        try:
            return float(v[:-1]) * mults[v[-1].upper()]
        except ValueError:
            return None
    try:
        return float(v)
    except ValueError:
        return None


# ─── Sección 6: Ranking institucional de métricas por sector ──────────────────
# Orden de importancia al explicar un resultado.
# No afecta el scoring: es guía de narrativa para el AI advisor.

SECTOR_METRIC_RANKING = {
    "tecnologia":           ["Revenue Growth", "PEG", "Margen EBITDA", "ROIC", "EV/Sales"],
    "bancos":               ["P/BV", "ROE vs CoE", "NPL", "NIM", "CET1"],
    "energia":              ["Break-even", "EV/EBITDA mid-cycle", "Div Yield", "Reserve Replacement", "Net Debt"],
    "utilities":            ["Div Yield vs Treasury", "EV/EBITDA", "Net Debt", "RAB Growth", "Coverage"],
    "consumo_defensivo":    ["ROIC", "Organic Growth", "EV/EBITDA", "Margen Neto", "Div Yield"],
    "consumo_discrecional": ["Same-Store Sales", "Gross Margin", "Net Debt", "ROIC", "Inventory Turnover"],
    "salud":                ["Pipeline", "Patent Cliff", "PEG", "R&D/Sales", "EV/EBITDA"],
    "industriales":         ["Book-to-Bill", "FCF Yield", "Margen EBITDA", "ROE", "EV/EBITDA"],
    "materiales":           ["Cash Cost C1", "Net Debt", "EV/EBITDA", "Reserve Life", "Div Yield"],
    "telecom":              ["ARPU+Churn", "EV/EBITDA-CapEx", "Div Yield", "Net Debt", "CapEx/Sales"],
    "transporte":           ["Load Factor", "Fuel Cost", "Net Debt", "EV/EBIT", "FCF Yield"],
    "agro":                 ["Spread commodity", "EV/EBITDA", "Net Debt", "ROIC", "Crushing Margin"],
    "default":              ["EV/EBITDA", "ROE", "Margen Neto", "Net Debt", "FCF Yield"],
}


# ─── Sección 7a: Criterios para Bonos (referencia, sin datos Finviz) ──────────

SOVEREIGN_BOND_CRITERIA = {
    # EMBI spread (bps)
    "spread_embi": {
        "IG_atractivo": 150,        # < 150 bps
        "HY_normal":    (150, 400),
        "distress":     700,        # > 700 bps
    },
    # Deuda/PBI (%)
    "deuda_pbi": {
        "thresholds": (45, 70, 100),    # exc<45 | bue<70 | neu<100 | malo≥100
    },
    # Déficit fiscal (% PBI, negativo=déficit)
    "deficit_fiscal": {
        "thresholds": (0, -2, -4),      # exc≥0 | bue≥-2 | neu≥-4 | malo<-4
    },
    # Reservas en meses de importaciones
    "reservas_meses_import": {
        "thresholds": (6, 4, 2),        # exc≥6 | bue≥4 | neu≥2 | malo<2
    },
    # Duration preference
    "duration_guidance": {
        "tasas_al_alza": "Corta (<3Y)",
        "ciclo_de_baja": "Larga (>7Y)",
    },
}

CORP_BOND_CRITERIA = {
    # Spread vs Treasury (bps)
    "spread_treasury": {
        "IG_normal":  80,    # IG < 80 bps
        "HY_normal":  250,   # HY < 250 bps
        "IG_riesgo":  250,   # IG > 250 bps → alerta
        "HY_riesgo":  700,   # HY > 700 bps → distress
    },
    # Interest Coverage (EBITDA / intereses)
    "interest_coverage": {
        "thresholds": (6, 4, 2.5),      # exc≥6 | bue≥4 | neu≥2.5 | malo<2.5
    },
    # Net Debt / EBITDA
    "net_debt_ebitda": {
        "IG_thresholds": (2, 4),        # IG exc<2 | IG riesgo>4
        "HY_thresholds": (4, 7),        # HY exc<4 | HY riesgo>7
    },
    # Rating map
    "rating": {
        "IG":      ["AAA", "AA", "A", "BBB"],
        "HY":      ["BB", "B"],
        "distress": ["CCC", "CC", "C", "D"],
    },
    # Probabilidad de default anual
    "prob_default": {
        "thresholds": (0.5, 2.0, 5.0),  # exc<0.5% | bue<2% | neu<5% | malo≥5%
    },
}


# ─── Sección 7b: ETF Scoring (datos estáticos, Finviz no los provee) ──────────
# Pesos: expense_ratio=20 | aum=20 | tracking_error=20 | sharpe=25 | max_dd=15

_ETF_W = {
    "expense_ratio":  20,   # menor = mejor (%)
    "aum":            20,   # mayor = mejor (USD billions)
    "tracking_error": 20,   # menor = mejor (%)
    "sharpe_3y":      25,   # mayor = mejor
    "max_dd":         15,   # menor = mejor (% pérdida máxima, valor positivo)
}

_ETF_THRESH = {
    "expense_ratio":  (0.10, 0.25, 0.60, NA),   # menor = mejor
    "aum":            (5.0,  1.0,  0.1,  0),     # mayor = mejor (billions)
    "tracking_error": (0.05, 0.20, 0.50, NA),    # menor = mejor
    "sharpe_3y":      (1.5,  1.0,  0.5,  0),     # mayor = mejor
    "max_dd":         (10,   20,   35,   NA),     # menor = mejor
}

# Datos estáticos de los ETFs del universo (fuente: ETF.com / iShares / Vanguard)
# Actualizar antes de cada release junto con el scorer de acciones.
ETF_STATIC_DATA = {
    "spy": {
        "name": "SPDR S&P 500 ETF",
        "expense_ratio":  0.0945,
        "aum":            500.0,
        "tracking_error": 0.01,
        "sharpe_3y":      1.20,
        "max_dd":         34.0,
    },
    "qqq": {
        "name": "Invesco QQQ (Nasdaq 100)",
        "expense_ratio":  0.20,
        "aum":            200.0,
        "tracking_error": 0.02,
        "sharpe_3y":      1.40,
        "max_dd":         35.0,
    },
    "vti": {
        "name": "Vanguard Total Market ETF",
        "expense_ratio":  0.03,
        "aum":            350.0,
        "tracking_error": 0.01,
        "sharpe_3y":      1.10,
        "max_dd":         36.0,
    },
    "eem": {
        "name": "iShares MSCI Emerging Markets",
        "expense_ratio":  0.68,
        "aum":            22.0,
        "tracking_error": 0.50,
        "sharpe_3y":      0.50,
        "max_dd":         35.0,
    },
    "gld": {
        "name": "SPDR Gold Shares",
        "expense_ratio":  0.40,
        "aum":            55.0,
        "tracking_error": 0.04,
        "sharpe_3y":      0.70,
        "max_dd":         20.0,
    },
    "iau": {
        "name": "iShares Gold Trust",
        "expense_ratio":  0.25,
        "aum":            28.0,
        "tracking_error": 0.04,
        "sharpe_3y":      0.70,
        "max_dd":         20.0,
    },
}

# CCL implícito para CEDEARs (referencia, no scoring)
# CCL_implicito = (precio_ARS / ratio_cedear) / precio_USD_origen
# Brecha aceptable: <3% | Atención: 3-6% | Anomalía: >6%
CCL_BRECHA_THRESHOLDS = (3.0, 6.0)   # (aceptable, atencion) en %


def score_etf(asset_id: str, data: dict = None) -> dict:
    """
    Puntúa un ETF usando ETF_STATIC_DATA (Finviz no provee estos campos).
    Si se pasa data externo, se usa en lugar de los datos estáticos.
    """
    d = data or ETF_STATIC_DATA.get(asset_id, {})
    if not d:
        return {"asset_id": asset_id, "score": None, "rating": "SIN DATOS", "detail": {}}

    def v(key):
        return d.get(key)

    detail = {}

    b_expense  = score_menor_mejor(v("expense_ratio"),  _ETF_THRESH["expense_ratio"],  _ETF_W["expense_ratio"])
    b_aum      = score_mayor_mejor(v("aum"),            _ETF_THRESH["aum"],             _ETF_W["aum"])
    b_tracking = score_menor_mejor(v("tracking_error"), _ETF_THRESH["tracking_error"], _ETF_W["tracking_error"])
    b_sharpe   = score_mayor_mejor(v("sharpe_3y"),      _ETF_THRESH["sharpe_3y"],      _ETF_W["sharpe_3y"])
    b_dd       = score_menor_mejor(v("max_dd"),         _ETF_THRESH["max_dd"],          _ETF_W["max_dd"])

    score = b_expense + b_aum + b_tracking + b_sharpe + b_dd
    detail.update({
        "expense_ratio_pts": b_expense,
        "aum_pts":           b_aum,
        "tracking_error_pts":b_tracking,
        "sharpe_3y_pts":     b_sharpe,
        "max_dd_pts":        b_dd,
        "nota":              "datos estáticos — Finviz no provee métricas de ETF",
    })

    return {
        "asset_id": asset_id,
        "score":    score,
        "rating":   rating_label(score),
        "detail":   detail,
    }


# ─── Sección 8: Capa especial Argentina ──────────────────────────────────────

# Descuento por riesgo regulatorio local (puntos sobre score base)
ARG_REGULATORY_DISCOUNT = {
    "utilities":   8,   # tarifas reguladas → riesgo de congelamiento
    "energia":     5,   # retenciones a exportaciones
    "bancos":      5,   # encajes / regulación BCRA
    "telecom":     3,   # tarifas con rezago inflacionario
    "materiales":  2,   # ciclo construcción dependiente del Estado
}

# Clasificación por perfil cambiario
ARG_FX_PROFILE = {
    "exportadoras": {
        "assets":  ["ypf", "vist", "pampa"],
        "nota":    "Cobertura cambiaria natural. Ingresos en USD, suben con devaluación.",
    },
    "mercado_interno": {
        "assets":  ["galicia", "bbar", "loma", "teco2"],
        "nota":    "Apuesta a normalización. Sufren en devaluaciones fuertes.",
    },
}

# Activos argentinos que aplican el descuento regulatorio
_ARG_EQUITY_IDS = {
    a for perfil in ARG_FX_PROFILE.values() for a in perfil["assets"]
}

# Escenarios de exit yield para bonos soberanos ARG
BOND_SCENARIOS = {
    "optimista":  {"exit_yield_pct": 8.0,  "prob": 0.25, "descripcion": "Acceso a mercados, convergencia IG"},
    "base":       {"exit_yield_pct": 11.0, "prob": 0.50, "descripcion": "Rollover gradual sin shocks"},
    "pesimista":  {"exit_yield_pct": 15.0, "prob": 0.20, "descripcion": "Tensión de reservas, re-pricing"},
    "default":    {"exit_yield_pct": None, "prob": 0.05, "descripcion": "Reestructuración; recovery ~45 cts"},
}

# Liquidez mínima para ticket institucional (USD/día)
ARG_CEDEAR_MIN_LIQUIDITY_USD = 500_000


def apply_argentina_adjustment(score: int, asset_id: str, sector: str) -> dict:
    """
    Aplica el descuento regulatorio argentino sobre el score estándar.
    Solo afecta acciones ARG (YPF, GGAL, BBAR, PAMP, TECO2, LOMA, VIST).
    """
    if asset_id not in _ARG_EQUITY_IDS:
        return {"score_adj": score, "descuento": 0, "razon": None}

    descuento = ARG_REGULATORY_DISCOUNT.get(sector, 0)
    score_adj = max(0, score - descuento)

    # Perfil cambiario informativo
    perfil_fx = next(
        (k for k, v in ARG_FX_PROFILE.items() if asset_id in v["assets"]),
        "sin_clasificar",
    )
    nota_fx = ARG_FX_PROFILE.get(perfil_fx, {}).get("nota", "")

    return {
        "score_adj": score_adj,
        "descuento": descuento,
        "razon":     f"Riesgo regulatorio ARG ({sector}) −{descuento}pts" if descuento else None,
        "perfil_fx": perfil_fx,
        "nota_fx":   nota_fx,
    }


def ccl_brecha(precio_ars: float, ratio_cedear: float, precio_usd: float) -> dict:
    """
    Calcula el CCL implícito de un CEDEAR y la brecha vs CCL de mercado.
    ccl_implicito = (precio_ars / ratio_cedear) / precio_usd
    """
    if ratio_cedear <= 0 or precio_usd <= 0:
        return {"ccl_implicito": None, "brecha_pct": None, "alerta": "datos insuficientes"}
    ccl_impl = (precio_ars / ratio_cedear) / precio_usd
    return {
        "ccl_implicito": round(ccl_impl, 2),
        # brecha requiere el CCL de mercado como referencia externa
        "nota": "Brecha aceptable <3% | Atención 3–6% | Anomalía >6%",
    }


def bond_expected_return(paridad: float, cupon_pct: float, duration_years: float) -> dict:
    """
    Calcula retorno esperado ponderado por escenarios para bonos soberanos ARG.
    paridad: precio actual como % del valor nominal (ej: 55 = 55 cts)
    cupon_pct: tasa del cupón anual
    duration_years: duration modificada
    """
    resultados = {}
    retorno_ponderado = 0.0
    for escenario, cfg in BOND_SCENARIOS.items():
        if cfg["exit_yield_pct"] is None:
            # Default: recovery estimado en 45 cts
            ret = (45 - paridad) / paridad
        else:
            ey = cfg["exit_yield_pct"] / 100
            # Retorno = carry + variación de precio por compresión/expansión de yield
            carry = cupon_pct / 100
            precio_exit = paridad * (1 + carry * duration_years - duration_years * (ey - cupon_pct / 100))
            ret = (precio_exit - paridad) / paridad + carry * duration_years
        resultados[escenario] = {
            "retorno_total_pct": round(ret * 100, 1),
            "prob":              cfg["prob"],
            "descripcion":       cfg["descripcion"],
        }
        retorno_ponderado += ret * cfg["prob"]

    resultados["retorno_ponderado_pct"] = round(retorno_ponderado * 100, 1)
    return resultados


# ─── Sección 9: Formatters de output obligatorio ──────────────────────────────

RATING_EMOJI = {
    "STRONG BUY":  "🟢",
    "BUY":         "🟢",
    "HOLD":        "🟡",
    "UNDERWEIGHT": "🟠",
    "AVOID":       "🔴",
}

_MISSING_FROM_FINVIZ = [
    "ROIC", "EV/Sales", "NPL", "NIM", "CET1",
    "Break-even", "Reserve Replacement", "RAB Growth",
    "Same-Store Sales", "Inventory Turnover",
    "Pipeline", "Patent Cliff", "R&D/Sales",
    "Book-to-Bill", "FCF Yield",
    "Cash Cost C1", "Reserve Life",
    "ARPU", "Churn", "CapEx/Sales",
    "Load Factor", "Fuel Cost",
    "Crushing Margin", "Spread commodity",
]


def format_json_output(result: dict, asset_id: str = None, arg_adj: dict = None) -> dict:
    """
    Formatea un resultado score_ticker en la estructura JSON de output obligatorio (sección 9C).
    """
    b = result.get("bloques", {})
    ratios = result.get("ratios", {})
    score_final = result["score"]
    if arg_adj and arg_adj.get("descuento", 0) > 0:
        score_final = arg_adj["score_adj"]

    out = {
        "ticker":              result["ticker"],
        "asset_id":            asset_id or result["ticker"].lower(),
        "sector":              result["sector"],
        "score":               score_final,
        "rating":              rating_label(score_final),
        "bloque_valuacion":    b.get("valuacion", 0),
        "bloque_calidad":      b.get("calidad", 0),
        "bloque_solvencia":    b.get("solvencia", 0),
        "bloque_crecimiento":  b.get("crecimiento", 0),
        "bloque_cualitativo":  b.get("cualitativo", 5),
        "ratios": {
            "forward_pe":    ratios.get("forward_pe"),
            "ev_ebitda":     ratios.get("ev_ebitda"),
            "peg":           ratios.get("peg"),
            "roe":           ratios.get("roe"),
            "roa":           ratios.get("roa"),
            "margen_neto":   ratios.get("margen_neto"),
            "deuda_equity":  ratios.get("deuda_equity"),
            "current_ratio": ratios.get("current_ratio"),
            "quick_ratio":   ratios.get("quick_ratio"),
            "eps_cagr_5y":   ratios.get("eps_cagr_5y"),
            "sales_cagr_5y": ratios.get("sales_cagr_5y"),
            "eps_qq":        ratios.get("eps_qq"),
            "dividend_yield":ratios.get("dividend_yield"),
        },
        "nota_cualitativo": "Bloque 5 fijado en 5/10 neutral. Ajustar manualmente.",
    }

    if arg_adj and arg_adj.get("descuento", 0) > 0:
        out["ajuste_arg"] = {
            "score_base":  result["score"],
            "descuento":   arg_adj["descuento"],
            "razon":       arg_adj["razon"],
            "perfil_fx":   arg_adj.get("perfil_fx"),
            "nota_fx":     arg_adj.get("nota_fx"),
        }

    return out


def format_console_table(results: list, sector_label: str = "") -> str:
    """
    Genera la tabla ASCII con formato obligatorio (sección 9B).
    results: lista de dicts con keys ticker, score, rating, sector, bloques.
    """
    sorted_r = sorted(results, key=lambda x: x["score"], reverse=True)

    col_w = {"#": 4, "TICKER": 9, "SCORE": 6, "RATING": 16, "SECTOR": 25,
              "VAL": 5, "CAL": 5, "SOL": 5, "CRE": 5, "CUA": 5}
    total_w = sum(col_w.values()) + len(col_w) * 3 - 1

    def sep(left="├", mid="┼", right="┤", fill="─"):
        parts = [fill * (w + 2) for w in col_w.values()]
        return left + mid.join(parts) + right

    def row(*vals):
        cells = [f" {str(v).center(w)} " for v, w in zip(vals, col_w.values())]
        return "│" + "│".join(cells) + "│"

    title = f"  RANKING — {sector_label}" if sector_label else "  RANKING"
    lines = [
        "┌" + "─" * (total_w + len(col_w) * 3 - 1) + "┐",
        "│" + title.ljust(total_w + len(col_w) * 3 - 2) + " │",
        sep("├", "┬", "┤"),
        row("#", "TICKER", "SCORE", "RATING", "SECTOR", "VAL", "CAL", "SOL", "CRE", "CUA"),
        sep(),
    ]
    for i, r in enumerate(sorted_r, 1):
        b   = r.get("bloques", {})
        emoji = RATING_EMOJI.get(r["rating"], "⚪")
        lines.append(row(
            i, r["ticker"], r["score"],
            f"{emoji} {r['rating']}", r["sector"],
            b.get("valuacion", "-"), b.get("calidad", "-"),
            b.get("solvencia", "-"), b.get("crecimiento", "-"),
            b.get("cualitativo", "-"),
        ))
    lines.append("└" + "─" * (total_w + len(col_w) * 3 - 1) + "┘")
    return "\n".join(lines)


def format_summary(results: list, sector: str = "") -> str:
    """
    Genera el bloque final obligatorio (sección 9D):
    Top 3 con justificación + riesgos del sector + métricas no disponibles en Finviz.
    """
    top3   = sorted(results, key=lambda x: x["score"], reverse=True)[:3]
    sector_risks = {
        "tecnologia":           ["Compresión de múltiplos si suben tasas", "Concentración en Mag7", "Regulación antitrust"],
        "bancos":               ["Riesgo de crédito en recesión", "Compresión de NIM en ciclo de baja de tasas", "Regulación CET1"],
        "energia":              ["Caída del precio del crudo", "Riesgo de transición energética", "Retenciones (ARG)"],
        "utilities":            ["Riesgo de tasas (duration larga)", "Congelamiento tarifario (ARG)", "CapEx intensivo"],
        "consumo_defensivo":    ["Compresión de márgenes por inflación de costos", "Pérdida de share vs marcas blancas"],
        "consumo_discrecional": ["Caída del consumo en recesión", "Presión en márgenes brutos", "Inventario excesivo"],
        "salud":                ["Vencimiento de patentes (patent cliff)", "Incertidumbre regulatoria FDA", "Pricing político"],
        "industriales":         ["Ciclo de capex corporativo", "Costos de insumos", "Cadena de suministro"],
        "materiales":           ["Precio de commodities", "China demand slowdown", "Costo de energía"],
        "telecom":              ["Saturación de mercado", "CapEx de fibra/5G", "Churn competitivo"],
        "default":              ["Riesgo macro global", "Tasas de interés", "Liquidez de mercado"],
    }

    lines = []
    lines.append("\n━━━ TOP 3 POSICIONES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    for i, r in enumerate(top3, 1):
        b     = r.get("bloques", {})
        ratios = r.get("ratios", {})
        emoji = RATING_EMOJI.get(r["rating"], "⚪")
        lines.append(f"\n#{i}  {r['ticker']}  {emoji} {r['rating']}  ({r['score']}/100)")
        # Identificar las 2 fortalezas principales basadas en bloques
        fortalezas = sorted(
            [("Valuación", b.get("valuacion", 0), 25),
             ("Calidad",   b.get("calidad", 0),   25),
             ("Solvencia", b.get("solvencia", 0), 20),
             ("Crecimiento", b.get("crecimiento", 0), 20)],
            key=lambda x: x[1] / x[2], reverse=True
        )
        pct1 = round(fortalezas[0][1] / fortalezas[0][2] * 100)
        pct2 = round(fortalezas[1][1] / fortalezas[1][2] * 100)
        lines.append(f"   Fortaleza principal: {fortalezas[0][0]} ({fortalezas[0][1]}/{fortalezas[0][2]} pts = {pct1}%)")
        lines.append(f"   Segunda fortaleza:   {fortalezas[1][0]} ({fortalezas[1][1]}/{fortalezas[1][2]} pts = {pct2}%)")

    sector_key = sector if sector in sector_risks else "default"
    risks = sector_risks[sector_key]
    lines.append("\n━━━ RIESGOS PRINCIPALES DEL SECTOR ━━━━━━━━━━━━━━━━━━━━━━━")
    for r in risks:
        lines.append(f"   ⚠ {r}")

    lines.append("\n━━━ MÉTRICAS NO DISPONIBLES EN FINVIZ ━━━━━━━━━━━━━━━━━━━━")
    relevant = [m for m in _MISSING_FROM_FINVIZ
                if any(m in SECTOR_METRIC_RANKING.get(s, []) for s in [sector, "default"])]
    for m in (relevant or _MISSING_FROM_FINVIZ[:5]):
        lines.append(f"   — {m}: requiere Bloomberg / informes trimestrales / estimaciones propias")
    lines.append("")
    return "\n".join(lines)


# ─── Runner offline ───────────────────────────────────────────────────────────

def run_and_save(output_path: str = "finviz_scores.json"):
    """
    Descarga datos de Finviz, calcula scores y guarda en JSON.
    Correr desde la raíz del proyecto: python -m modules.finviz_scorer
    """
    try:
        from finvizfinance.quote import finvizfinance
    except ImportError:
        raise SystemExit("Instalá finvizfinance: pip install finvizfinance")

    by_ticker    = {}
    by_asset_id  = {}
    raw_results  = []   # portfolio tickers — para scores y tabla de consola
    bench_results= []   # benchmark tickers — solo para medianas de sector

    all_scoreable = list(SCOREABLE_TICKERS)
    benchmark_flat = {t: sect for sect, tickers in BENCHMARK_TICKERS.items() for t in tickers}

    print(f"Scoring {len(all_scoreable)} tickers + "
          f"{len(benchmark_flat)} benchmarks de sector...\n")

    for ticker in all_scoreable:
        try:
            data      = finvizfinance(ticker).ticker_fundament()
            sector    = SECTOR_OVERRIDE.get(ticker) or SECTOR_MAP.get(data.get("Sector", ""), "default")
            result    = score_ticker(ticker, data, sector)
            asset_id_guess = next(
                (aid for aid, fv in ASSET_TO_FINVIZ.items() if fv == ticker), None
            )
            arg_adj = apply_argentina_adjustment(
                result["score"], asset_id_guess or "", sector
            )
            if arg_adj["descuento"] > 0:
                result["score"]  = arg_adj["score_adj"]
                result["rating"] = rating_label(result["score"])
                result["arg_adj"] = arg_adj

            by_ticker[ticker] = result
            raw_results.append(result)
        except Exception as exc:
            print(f"{ticker:8s}  ERROR: {exc}")
        time.sleep(1.5)

    # Benchmarks — score para medianas de sector, NO se guardan en by_asset_id
    print(f"\nDescargando benchmarks de sector...")
    for ticker, forced_sector in benchmark_flat.items():
        try:
            data   = finvizfinance(ticker).ticker_fundament()
            result = score_ticker(ticker, data, forced_sector)
            result["sector"] = forced_sector   # asegurar sector correcto
            bench_results.append(result)
            print(f"  {ticker:<8} [{forced_sector}]  score={result['score']}")
        except Exception as exc:
            print(f"  {ticker:8s}  ERROR: {exc}")
        time.sleep(1.5)

    # Mapear ticker Finviz → asset_id (acciones)
    for asset_id, fv_ticker in ASSET_TO_FINVIZ.items():
        if fv_ticker in by_ticker:
            by_asset_id[asset_id] = by_ticker[fv_ticker]

    # Puntuar ETFs con datos estáticos
    etf_scores = {}
    for etf_id in ETF_STATIC_DATA:
        result = score_etf(etf_id)
        etf_scores[etf_id] = result
        by_asset_id[etf_id] = result

    # Tabla de consola (sección 9B)
    all_results = raw_results + [
        {"ticker": eid.upper(), "score": r["score"], "rating": r["rating"],
         "sector": "ETF", "bloques": {}}
        for eid, r in etf_scores.items() if r.get("score") is not None
    ]
    print(format_console_table(all_results, "Universo completo"))
    print(format_summary(raw_results, "default"))

    # Guardar medianas compuestas por sector (portfolio + benchmarks combinados)
    _guardar_medianas_sector_batch(raw_results + bench_results)

    output = {
        "generated_at": datetime.now().isoformat(),
        "by_asset_id":  by_asset_id,
        "by_ticker":    by_ticker,
        "etf_scores":   etf_scores,
    }
    Path(output_path).write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\nGuardado en {output_path}")
    return output


def _guardar_medianas_sector_batch(raw_results: list) -> None:
    """
    Agrupa raw_results por sector, calcula medianas de P/E, EV/EBITDA,
    score compuesto y cada bloque, y llama a guardar_mediana_sector().
    Requiere ≥ 3 activos por sector para guardar.
    """
    import statistics
    from collections import defaultdict

    try:
        from memory_manager import guardar_mediana_sector
    except ImportError:
        return

    groups: dict = defaultdict(list)
    for r in raw_results:
        s = r.get("sector", "default")
        if s != "default":
            groups[s].append(r)

    for sector, results in groups.items():
        if len(results) < 3:
            continue

        pes  = [r["ratios"]["forward_pe"] for r in results
                if r.get("ratios", {}).get("forward_pe") and r["ratios"]["forward_pe"] > 0]
        evs  = [r["ratios"]["ev_ebitda"]  for r in results
                if r.get("ratios", {}).get("ev_ebitda") and r["ratios"]["ev_ebitda"] > 0]
        scrs = [r["score"] for r in results if r.get("score") is not None]

        bloques_med: dict = {}
        for bloque in ("valuacion", "calidad", "solvencia", "crecimiento"):
            vals = [r["bloques"].get(bloque, 0) for r in results if r.get("bloques")]
            if vals:
                bloques_med[bloque] = round(statistics.median(vals), 1)

        guardar_mediana_sector(
            sector,
            pe           = round(statistics.median(pes), 2) if pes else 0.0,
            ev_ebitda    = round(statistics.median(evs), 2) if evs else 0.0,
            score_mediano= round(statistics.median(scrs))   if scrs else None,
            bloques      = bloques_med or None,
        )


def load_scores(path: str = "finviz_scores.json") -> dict:
    """
    Devuelve {asset_id: score_int}. Vacío si no existe el archivo → sin efecto.
    """
    p = Path(path)
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text())
        return {
            asset_id: entry["score"]
            for asset_id, entry in data.get("by_asset_id", {}).items()
        }
    except Exception:
        return {}


def load_full_data(path: str = "finviz_scores.json") -> dict:
    """
    Devuelve {asset_id: {score, sector, bloques, ratios}} con toda la info de Finviz.
    Vacío si no existe el archivo.
    """
    p = Path(path)
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text())
        return {
            asset_id: {
                "score":   entry.get("score", 0),
                "sector":  entry.get("sector", "default"),
                "bloques": entry.get("bloques", {}),
                "ratios":  entry.get("ratios", {}),
            }
            for asset_id, entry in data.get("by_asset_id", {}).items()
            if isinstance(entry, dict)
        }
    except Exception:
        return {}


def load_asset_sectors(path: str = "finviz_scores.json") -> dict:
    """
    Devuelve {asset_id: sector_framework} leyendo el campo 'sector' del JSON.
    Vacío si no existe el archivo.
    """
    p = Path(path)
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text())
        return {
            asset_id: entry["sector"]
            for asset_id, entry in data.get("by_asset_id", {}).items()
            if isinstance(entry, dict) and entry.get("sector")
        }
    except Exception:
        return {}


if __name__ == "__main__":
    run_and_save()
