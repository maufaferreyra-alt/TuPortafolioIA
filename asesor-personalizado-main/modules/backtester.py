"""
Backtester simple para carteras sugeridas.
Calcula retorno histórico ponderado de los activos equity de la cartera
y lo compara contra SPY como benchmark.
"""

from datetime import datetime, timedelta
import pandas as pd

# Mapeo asset_id → ticker yfinance para los activos que tienen datos históricos
_ASSET_TO_YF: dict = {
    # CEDEARs (cotización en USD en NYSE/NASDAQ)
    "aapl": "AAPL", "msft": "MSFT", "googl": "GOOGL", "amzn": "AMZN",
    "nvda": "NVDA", "meta": "META", "brk":   "BRK-B", "jpm":  "JPM",
    "ko":   "KO",   "wmt":  "WMT",  "jnj":   "JNJ",   "pfe":  "PFE",
    "xom":  "XOM",  "tsla": "TSLA", "bac":   "BAC",   "dis":  "DIS",
    "meli": "MELI", "amd":  "AMD",  "nflx":  "NFLX",  "orcl": "ORCL",
    "crm":  "CRM",  "adbe": "ADBE", "uber":  "UBER",  "glob": "GLOB",
    "v":    "V",    "ma":   "MA",   "gs":    "GS",    "ms":   "MS",
    "unh":  "UNH",  "lly":  "LLY",  "mrk":   "MRK",   "hd":   "HD",
    "cost": "COST", "mcd":  "MCD",  "nke":   "NKE",   "cvx":  "CVX",
    "intc": "INTC", "tsm":  "TSM",  "qcom":  "QCOM",  "shop": "SHOP",
    "pypl": "PYPL", "pg":   "PG",   "pm":    "PM",    "sbux": "SBUX",
    "tgt":  "TGT",  "ba":   "BA",   "cat":   "CAT",   "baba": "BABA",
    "nee":  "NEE",
    # Acciones ARG (ADRs en NYSE)
    "ypf":     "YPF",  "vist":    "VIST",  "galicia": "GGAL",
    "loma":    "LOMA", "teco2":   "TEO",   "pampa":   "PAM",
    "bbar":    "BBAR", "bma":     "BMA",   "supv":    "SUPV",
    "tgs":     "TGS",  "cepu":    "CEPU",  "irsa":    "IRS",
    "cres":    "CRESY",
    # ETFs
    "spy": "SPY", "qqq": "QQQ", "vti": "VTI", "iau": "IAU",
    "gld": "GLD", "eem": "EEM",
}

_EQUITY_CATEGORIES = {"CEDEARs", "Acciones ARG", "ETFs Globales", "ETFs"}
_BENCHMARK         = "SPY"


def backtest_portfolio(positions: list, days: int = 90) -> dict:
    """
    Calcula el retorno histórico ponderado de los activos equity de la cartera
    en los últimos N días calendario y lo compara con SPY.

    Args:
        positions: lista de dicts con keys asset_id, label, weight, category, ...
        days:      período de backtest en días calendario (default 90)

    Returns dict con:
        portfolio_return  float  — retorno total ponderado (0.10 = +10%)
        benchmark_return  float  — retorno SPY en el mismo período
        alpha             float  — diferencia (portfolio - benchmark)
        period_days       int
        start_date        str    ISO
        end_date          str    ISO
        chart_data        list[{date, portfolio, benchmark}]  — normalizado a 100
        positions_used    list[{asset_id, ticker, weight, return}]
        skipped           list[str]  — asset_ids sin datos históricos
        error             str | None
    """
    try:
        import yfinance as yf
        import pandas as pd
    except ImportError:
        return {"error": "yfinance no instalado — pip install yfinance", "portfolio_return": None}

    end_dt   = datetime.now()
    start_dt = end_dt - timedelta(days=days + 5)   # +5 buffer para fines de semana
    start_str = start_dt.strftime("%Y-%m-%d")
    end_str   = end_dt.strftime("%Y-%m-%d")

    # Filtrar posiciones equity con ticker conocido (campo "id" en positions)
    equity_positions = [
        p for p in positions
        if p.get("category") in _EQUITY_CATEGORIES
        and p.get("id") in _ASSET_TO_YF
    ]

    if not equity_positions:
        return {
            "error":            "No hay activos equity con datos históricos en la cartera",
            "portfolio_return": None,
            "benchmark_return": None,
            "alpha":            None,
            "period_days":      days,
            "chart_data":       [],
            "positions_used":   [],
            "skipped":          [],
        }

    tickers_needed = list({_ASSET_TO_YF[p["id"]] for p in equity_positions})
    if _BENCHMARK not in tickers_needed:
        tickers_needed.append(_BENCHMARK)

    # Descargar datos históricos
    try:
        raw = yf.download(
            tickers_needed, start=start_str, end=end_str,
            auto_adjust=True, progress=False,
        )
    except Exception as e:
        return {"error": f"Error al descargar datos: {e}", "portfolio_return": None}

    if raw.empty:
        return {"error": "yfinance no devolvió datos para el período", "portfolio_return": None}

    # Extraer columna Close — yfinance varía según versión y nº de tickers
    try:
        close = raw["Close"]
    except KeyError:
        close = raw

    # Serie → DataFrame (un solo ticker en versiones viejas de yfinance)
    if isinstance(close, pd.Series):
        close = close.to_frame(name=tickers_needed[0])

    # MultiIndex columns (yfinance >= 0.2 con múltiples tickers) → aplanar
    if isinstance(close.columns, pd.MultiIndex):
        close.columns = close.columns.get_level_values(-1)

    # Normalizar al primer día disponible
    first_valid = close.dropna(how="all").index[0]
    close = close.loc[first_valid:]
    close_norm = close / close.iloc[0] * 100   # índice base 100

    # Retorno total de cada ticker (último / primero - 1)
    ticker_returns: dict = {}
    skipped: list        = []
    for ticker in tickers_needed:
        col = close[ticker] if ticker in close.columns else None
        if col is None or col.dropna().empty:
            skipped.append(ticker)
            continue
        first = col.dropna().iloc[0]
        last  = col.dropna().iloc[-1]
        ticker_returns[ticker] = float(last / first) - 1.0

    # Retorno ponderado de la cartera (solo equity, re-normaliza pesos)
    total_eq_weight = sum(p["weight"] for p in equity_positions
                          if _ASSET_TO_YF[p["id"]] in ticker_returns)
    positions_used = []
    portfolio_return = 0.0

    for pos in equity_positions:
        yf_ticker = _ASSET_TO_YF[pos["id"]]
        if yf_ticker not in ticker_returns:
            skipped.append(pos["id"])
            continue
        ret          = ticker_returns[yf_ticker]
        norm_weight  = pos["weight"] / total_eq_weight if total_eq_weight > 0 else 0
        portfolio_return += norm_weight * ret
        positions_used.append({
            "asset_id": pos["id"],
            "ticker":   yf_ticker,
            "label":    pos.get("label", pos["id"]),
            "weight":   round(norm_weight, 4),
            "return":   round(ret * 100, 2),
        })

    benchmark_return = ticker_returns.get(_BENCHMARK)
    alpha = (portfolio_return - benchmark_return) if benchmark_return is not None else None

    # Serie temporal para el gráfico (portfolio ponderado vs benchmark)
    chart_data = []
    dates_idx = close_norm.index

    # Construir serie de portfolio ponderado
    port_series = None
    for pos in equity_positions:
        yf_ticker = _ASSET_TO_YF.get(pos["id"])
        if yf_ticker not in close_norm.columns:
            continue
        norm_weight = pos["weight"] / total_eq_weight if total_eq_weight > 0 else 0
        contribution = close_norm[yf_ticker] * norm_weight
        port_series = contribution if port_series is None else port_series + contribution

    bench_series = close_norm.get(_BENCHMARK)

    if port_series is not None:
        port_series = port_series / port_series.iloc[0] * 100   # re-base 100

    for dt in dates_idx:
        row = {"date": str(dt.date())}
        if port_series is not None and dt in port_series.index:
            row["portfolio"] = round(float(port_series[dt]), 2)
        if bench_series is not None and dt in bench_series.index:
            row["benchmark"] = round(float(bench_series[dt]), 2)
        if "portfolio" in row or "benchmark" in row:
            chart_data.append(row)

    return {
        "portfolio_return": round(portfolio_return * 100, 2),
        "benchmark_return": round(benchmark_return * 100, 2) if benchmark_return is not None else None,
        "alpha":            round(alpha * 100, 2) if alpha is not None else None,
        "period_days":      days,
        "start_date":       str(first_valid.date()),
        "end_date":         str(close.index[-1].date()),
        "chart_data":       chart_data,
        "positions_used":   sorted(positions_used, key=lambda x: x["weight"], reverse=True),
        "skipped":          skipped,
        "error":            None,
    }
