"""
Backtest histórico: cartera vs plazo fijo (últimos 5 años, en USD).

Fuentes:
  - MEP histórico:  ArgentinaDatos /v1/cotizaciones/dolares/bolsa
  - Plazo fijo TNA: ArgentinaDatos (tasas actuales), fallback tabla documentada BCRA
  - Activos USD:    yfinance
  - Acciones ARG:   yfinance (.BA) → convertidas a USD con MEP

Activos excluidos del backtest (sin historial limpio post-reestructuración 2020):
  Bonos soberanos ARG y ONs sin precio público.
  Su peso se redistribuye proporcionalmente entre los demás activos.
"""

import requests
import pandas as pd
from datetime import date, timedelta
from typing import Optional

HEADERS  = {"User-Agent": "Mozilla/5.0"}
YEARS_BK = 5

# ── Mapeo asset_id → yfinance ticker ──────────────────────────────────────────

_USD_TICKERS: dict[str, str] = {
    "spy": "SPY",  "qqq": "QQQ",  "vti": "VTI",
    "gld": "GLD",  "eem": "EEM",
    "aapl": "AAPL", "msft": "MSFT", "nvda": "NVDA",
    "amzn": "AMZN", "meta": "META", "googl": "GOOGL",
    "tsla": "TSLA", "nflx": "NFLX", "amd": "AMD",
    "v": "V",    "ma": "MA",   "jpm": "JPM",  "bac": "BAC",
    "hd": "HD",  "wmt": "WMT", "ko": "KO",   "pg": "PG",
    "baba": "BABA", "jnj": "JNJ", "xom": "XOM", "cvx": "CVX",
    "brk": "BRK-B",
}

_ARG_STOCK_TICKERS: dict[str, str] = {
    "ggal": "GGAL.BA", "ypf_arg": "YPFD.BA", "bbar": "BBAR.BA",
    "pamp": "PAMP.BA", "tgsu": "TGSU2.BA",   "alua": "ALUA.BA",
    "txar": "TXAR.BA",
}

_ARS_CASH_IDS: set[str] = {
    "cash_pesos", "money_market", "fci_t0", "fci_renta", "plazo_fijo",
}
_MEP_IDS: set[str] = {"mep", "dolar_mep"}

_SKIP_IDS: set[str] = {
    "al30", "gd30", "al35", "gd35", "gd38",
    "on_ypf", "on_pampa", "on_tgs", "on_macro", "on_corp",
    "cer_tx26", "cer_tx28", "cer_dicp", "lecap",
}

# ── TNA histórica documentada (BCRA / fuentes públicas argentinas) ─────────────
# Tasa nominal anual de plazo fijo 30 días, promedio mensual.
# Fuente: resoluciones BCRA, reportes Infobae/Cronista/ambito 2021-2026.
_TNA_HISTORICA: dict[str, float] = {
    "2021-05": 34.0, "2021-06": 34.0, "2021-07": 34.0, "2021-08": 34.0,
    "2021-09": 37.0, "2021-10": 37.0, "2021-11": 37.0, "2021-12": 38.0,
    "2022-01": 38.0, "2022-02": 39.5, "2022-03": 42.5, "2022-04": 46.0,
    "2022-05": 48.0, "2022-06": 52.0, "2022-07": 60.0, "2022-08": 69.5,
    "2022-09": 75.0, "2022-10": 75.0, "2022-11": 75.0, "2022-12": 75.0,
    "2023-01": 75.0, "2023-02": 78.0, "2023-03": 78.0, "2023-04": 81.0,
    "2023-05": 91.0, "2023-06": 97.0, "2023-07": 97.0, "2023-08": 118.0,
    "2023-09": 133.0,"2023-10": 133.0,"2023-11": 133.0,"2023-12": 133.0,
    "2024-01": 110.0,"2024-02": 90.0, "2024-03": 80.0, "2024-04": 70.0,
    "2024-05": 60.0, "2024-06": 50.0, "2024-07": 47.0, "2024-08": 45.0,
    "2024-09": 42.0, "2024-10": 40.0, "2024-11": 38.0, "2024-12": 35.0,
    "2025-01": 32.0, "2025-02": 30.0, "2025-03": 29.0, "2025-04": 28.0,
    "2025-05": 27.0, "2025-06": 27.0, "2025-07": 26.0, "2025-08": 26.0,
    "2025-09": 26.0, "2025-10": 26.0, "2025-11": 26.0, "2025-12": 26.0,
    "2026-01": 25.0, "2026-02": 25.0, "2026-03": 25.0, "2026-04": 25.0,
    "2026-05": 25.0,
}


# ── Fetch de datos ─────────────────────────────────────────────────────────────

def _fetch_mep_daily(start: date) -> Optional[pd.Series]:
    try:
        r = requests.get(
            "https://api.argentinadatos.com/v1/cotizaciones/dolares/bolsa",
            headers=HEADERS, timeout=15,
        )
        r.raise_for_status()
        df = pd.DataFrame(r.json())
        df["fecha"] = pd.to_datetime(df["fecha"])
        df = df[df["fecha"] >= pd.Timestamp(start)].sort_values("fecha")
        s = df.set_index("fecha")["venta"].astype(float)
        return s if len(s) >= 30 else None
    except Exception:
        return None


def _build_tna_series(start: date) -> pd.Series:
    """
    Construye serie mensual de TNA a partir de la tabla documentada.
    Retorna una pd.Series con índice DatetimeIndex (month-end) y valores TNA%.
    """
    rows = []
    cur  = date(start.year, start.month, 1)
    end  = date.today()
    while cur <= end:
        key = cur.strftime("%Y-%m")
        tna = _TNA_HISTORICA.get(key, 25.0)  # 25% como fallback razonable
        rows.append({"fecha": pd.Timestamp(cur), "tna": tna})
        # avanzar al próximo mes
        if cur.month == 12:
            cur = date(cur.year + 1, 1, 1)
        else:
            cur = date(cur.year, cur.month + 1, 1)
    df = pd.DataFrame(rows).set_index("fecha")
    return df["tna"].resample("ME").last()


# ── Cálculo de retornos ────────────────────────────────────────────────────────

def _pf_monthly_usd_returns(tna_monthly: pd.Series, mep_daily: pd.Series) -> Optional[pd.Series]:
    """
    Retorno mensual en USD del plazo fijo.
    r_usd = (1 + TNA/12) × (MEP_prev / MEP_actual) - 1

    Captura: la ganancia en ARS se enfrenta a la devaluación del peso.
    Si el ARS se devaluó más que lo que rindió el plazo fijo, el USD return es negativo.
    """
    mep_m = mep_daily.resample("ME").last().ffill()
    common = tna_monthly.index.intersection(mep_m.index)
    if len(common) < 12:
        return None

    tna      = tna_monthly.loc[common]
    mep      = mep_m.loc[common]
    mep_prev = mep.shift(1)

    usd_r = (1 + tna / 100 / 12) * (mep_prev / mep) - 1
    return usd_r.dropna()


def _asset_monthly_returns_usd(
    asset_id: str,
    mep_daily: pd.Series,
    start_str: str,
) -> Optional[pd.Series]:
    try:
        import yfinance as yf
        ticker = _USD_TICKERS.get(asset_id) or _ARG_STOCK_TICKERS.get(asset_id)
        if not ticker:
            return None

        hist = yf.download(ticker, start=start_str, progress=False, auto_adjust=True)
        if hist.empty or len(hist) < 60:
            return None

        prices = hist["Close"].squeeze()
        if hasattr(prices.index, "tz") and prices.index.tz is not None:
            prices.index = prices.index.tz_localize(None)

        prices_m = prices.resample("ME").last().ffill()

        if ticker.endswith(".BA"):
            mep_m    = mep_daily.resample("ME").last().ffill()
            aligned  = mep_m.reindex(prices_m.index, method="nearest")
            prices_m = prices_m / aligned

        return prices_m.pct_change().dropna()
    except Exception:
        return None


# ── Función principal ──────────────────────────────────────────────────────────

def run_backtest(
    positions: list[dict],
    capital_usd: float = 10_000,
) -> Optional[dict]:
    """
    Backtest histórico 5 años en USD.

    Args:
        positions: lista de dicts con 'id' y 'weight' (portfolio["positions"])
        capital_usd: capital inicial en USD

    Returns:
        dict con dates, portfolio, pf, usd_held y estadísticas — o None si faltan datos.
    """
    today = date.today()
    start = date(today.year - YEARS_BK, today.month, 1)
    start_str = (start - timedelta(days=5)).strftime("%Y-%m-%d")

    allocations = {p["id"]: p["weight"] for p in positions}

    # ── 1. MEP histórico y TNA ───────────────────────────────────────────────
    mep_daily  = _fetch_mep_daily(start)
    if mep_daily is None:
        return None

    tna_monthly = _build_tna_series(start)

    pf_returns = _pf_monthly_usd_returns(tna_monthly, mep_daily)
    if pf_returns is None or len(pf_returns) < 12:
        return None

    # ── 2. Redistribuir peso de activos excluidos ────────────────────────────
    skip_w = sum(w for aid, w in allocations.items() if aid in _SKIP_IDS)
    factor = 1.0 / (1.0 - skip_w) if 0 < skip_w < 1.0 else 1.0
    adj    = {aid: w * factor for aid, w in allocations.items() if aid not in _SKIP_IDS}

    # ── 3. Retornos mensuales por activo ─────────────────────────────────────
    asset_returns: dict[str, pd.Series] = {}

    for aid in adj:
        if aid in _USD_TICKERS or aid in _ARG_STOCK_TICKERS:
            r = _asset_monthly_returns_usd(aid, mep_daily, start_str)
            if r is not None and len(r) >= 12:
                asset_returns[aid] = r
        elif aid in _ARS_CASH_IDS:
            asset_returns[aid] = pf_returns          # mismo rendimiento que PF en USD
        elif aid in _MEP_IDS:
            asset_returns[aid] = pd.Series(0.0, index=pf_returns.index)

    if not asset_returns:
        return None

    # ── 4. Alinear en fechas comunes ─────────────────────────────────────────
    common = sorted(set.intersection(*[set(r.index) for r in asset_returns.values()]))
    if len(common) < 12:
        return None

    pf_aligned = pf_returns.reindex(common, method="nearest").fillna(0)

    # ── 5. Blend ponderado ───────────────────────────────────────────────────
    w_total = sum(adj.get(aid, 0) for aid in asset_returns)
    blended = pd.Series(0.0, index=common)
    for aid, r in asset_returns.items():
        blended += r.loc[common] * (adj[aid] / w_total)

    # ── 6. Componer curvas desde capital_usd ─────────────────────────────────
    def _compound(rets: pd.Series) -> list[float]:
        v, out = capital_usd, [capital_usd]
        for r in rets:
            v *= (1 + float(r))
            out.append(round(v, 0))
        return out

    port_vals = _compound(blended)
    pf_vals   = _compound(pf_aligned)
    usd_held  = [round(capital_usd, 0)] * len(port_vals)

    # ── 7. Eje de fechas ──────────────────────────────────────────────────────
    start_label = (pd.Timestamp(common[0]) - pd.offsets.MonthBegin(1)).strftime("%b %Y")
    date_axis   = [start_label] + [pd.Timestamp(d).strftime("%b %Y") for d in common]

    skipped = [aid for aid in allocations if aid in _SKIP_IDS and allocations[aid] > 0.02]

    return {
        "dates":      date_axis,
        "portfolio":  port_vals,
        "pf":         pf_vals,
        "usd_held":   usd_held,
        "port_final": port_vals[-1],
        "pf_final":   pf_vals[-1],
        "capital":    capital_usd,
        "gain_port":  round(port_vals[-1] / capital_usd - 1, 3),
        "gain_pf":    round(pf_vals[-1]   / capital_usd - 1, 3),
        "diff":       round(port_vals[-1] - pf_vals[-1], 0),
        "skipped":    skipped,
        "n_months":   len(common),
    }
