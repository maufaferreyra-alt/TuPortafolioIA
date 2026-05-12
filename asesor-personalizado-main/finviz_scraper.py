"""
Scraper de datos fundamentales desde Finviz.
Fuente primaria para el motor de scoring de CEDEARs y acciones.
"""

import time
import re


# ─── Mapeo sector Finviz → sector framework interno ───────────────────────────

_SECTOR_MAP = {
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


# ─── parse_float ──────────────────────────────────────────────────────────────

def parse_float(v) -> float | None:
    """
    Convierte strings de Finviz a float limpio.

    Ejemplos:
        "23.5"   → 23.5
        "12.3%"  → 12.3
        "1.2B"   → 1_200_000_000.0
        "500M"   → 500_000_000.0
        "3.4K"   → 3_400.0
        "1.1T"   → 1_100_000_000_000.0
        "-"      → None
        "N/A"    → None
        None     → None
    """
    if v is None:
        return None
    s = str(v).strip()
    if s in ("-", "N/A", "", "nan"):
        return None

    # Quitar % y espacios
    s = s.replace("%", "").replace(",", "").strip()

    # Sufijos de magnitud
    suffixes = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000, "T": 1_000_000_000_000}
    if s and s[-1].upper() in suffixes:
        mult = suffixes[s[-1].upper()]
        s    = s[:-1]
        try:
            return float(s) * mult
        except ValueError:
            return None

    try:
        return float(s)
    except ValueError:
        return None


# ─── Obtención de datos ───────────────────────────────────────────────────────

def get_ticker_data(ticker: str) -> dict | None:
    """
    Obtiene los fundamentals del ticker desde Finviz usando finvizfinance.
    Retorna el dict raw o None si falla.
    Incluye delay de 1.5s para no saturar el servidor.
    """
    try:
        from finvizfinance.quote import finvizfinance
        stock = finvizfinance(ticker)
        data  = stock.ticker_fundament()
        time.sleep(1.5)
        return data
    except Exception as e:
        print(f"  ⚠ Error obteniendo {ticker}: {e}")
        return None


def get_tickers_sector(sector_finviz: str) -> list:
    """
    Retorna lista de tickers del sector dado usando el screener de Finviz.
    Filtra: Country=USA, Mid Cap a Large Cap.
    """
    try:
        from finvizfinance.screener.overview import Overview
        screener = Overview()
        screener.set_filter(filters_dict={
            "Sector":      sector_finviz,
            "Country":     "USA",
            "Market Cap.": "+Small (over $300mln)",
        })
        df = screener.screener_view()
        if df is None or df.empty:
            return []
        return df["Ticker"].tolist()
    except Exception as e:
        print(f"  ⚠ Error screener sector '{sector_finviz}': {e}")
        return []


# ─── Mapeo de ratios ──────────────────────────────────────────────────────────

def mapear_ratios(raw: dict, ticker: str) -> dict:
    """
    Extrae y parsea los campos relevantes del dict raw de Finviz.
    Retorna dict estructurado con ticker y sector_framework incluidos.
    """
    def f(key: str):
        return parse_float(raw.get(key))

    sector_finviz    = raw.get("Sector") or ""
    sector_framework = _SECTOR_MAP.get(sector_finviz, "default")

    return {
        # Identificación
        "ticker":            ticker,
        "sector_finviz":     sector_finviz,
        "sector_framework":  sector_framework,

        # Valuación
        "pe":                f("P/E"),
        "forward_pe":        f("Forward P/E"),
        "peg":               f("PEG"),
        "pb":                f("P/B"),
        "ps":                f("P/S"),
        "ev_ebitda":         f("EV/EBITDA"),
        "price_fcf":         f("Price/FCF"),
        "dividend_yield":    f("Dividend %"),

        # Calidad
        "roe":               f("ROE"),
        "roi":               f("ROI"),
        "roa":               f("ROA"),
        "margen_bruto":      f("Gross Margin"),
        "margen_operativo":  f("Oper. Margin"),
        "margen_neto":       f("Profit Margin"),

        # Solvencia
        "deuda_equity":      f("Debt/Eq"),
        "current_ratio":     f("Current Ratio"),
        "quick_ratio":       f("Quick Ratio"),

        # Crecimiento
        "eps_cagr_5y":       f("EPS next 5Y"),
        "ventas_cagr_5y":    f("Sales past 5Y"),
        "eps_qoq":           f("EPS Q/Q"),
        "ventas_qoq":        f("Sales Q/Q"),

        # Contexto
        "market_cap":        f("Market Cap"),
        "precio":            f("Price"),
        "beta":              f("Beta"),

        # Cualitativo (Bloque 5) — datos de analistas en Finviz
        "recomendacion":     f("Recom."),          # 1.0=Strong Buy … 5.0=Sell
        "target_price":      f("Target Price"),     # precio objetivo consenso analistas
        "short_float":       f("Short Float"),      # % del float vendido en corto
    }


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    print(f"Obteniendo datos de {ticker}...")
    raw = get_ticker_data(ticker)
    if raw:
        ratios = mapear_ratios(raw, ticker)
        for k, v in ratios.items():
            print(f"  {k:<22} {v}")
        non_null = len([v for v in ratios.values() if v is not None])
        print(f"\n✅ finviz_scraper OK — {non_null} campos con datos")
    else:
        print("❌ No se pudieron obtener datos")
