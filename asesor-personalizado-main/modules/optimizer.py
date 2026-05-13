"""
Optimizador de Markowitz para la porción equity de la cartera.

- Conservador  → mínima varianza (minimizar riesgo)
- Estable      → máximo Sharpe con límite de volatilidad bajo
- Moderado     → máximo Sharpe
- Agresivo     → máximo Sharpe con más libertad de concentración

El optimizador actúa SOLO sobre los activos equity con datos en yfinance.
Bonos, pesos y MEP mantienen sus pesos del sistema de buckets.
"""

import math
from typing import Optional

# Tasa libre de riesgo: T-Bill 3M EE.UU. en términos anuales
_RF = 0.045

# Mapeo asset_id → ticker yfinance (misma tabla que backtester)
_YF_MAP: dict = {
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
    "ypf":  "YPF",  "vist": "VIST", "galicia": "GGAL", "loma": "LOMA",
    "teco2":"TEO",  "pampa":"PAM",  "bbar":  "BBAR",  "bma":  "BMA",
    "supv": "SUPV", "tgs":  "TGS",  "cepu":  "CEPU",  "irsa": "IRS",
    "cres": "CRESY",
    "spy":  "SPY",  "qqq":  "QQQ",  "vti":   "VTI",   "iau":  "IAU",
    "gld":  "GLD",  "eem":  "EEM",
}

# Límites de peso por activo según perfil.
# Conservador y estable: caps bajos para evitar concentración excesiva.
# Moderado: cap medio (0.25), balanceado.
# Agresivo: cap alto (0.35) para permitir concentración real, alineado con
# la promesa "máximo Sharpe con concentración" de la pantalla 'Cómo funciona'.
_BOUNDS = {
    "conservador": (0.05, 0.20),
    "estable":     (0.05, 0.22),
    "moderado":    (0.05, 0.25),
    "agresivo":    (0.05, 0.35),
}


def optimize_equity_slice(
    equity_asset_ids: list,
    risk_profile: str,
    lookback_days: int = 365,
) -> Optional[dict]:
    """
    Calcula pesos óptimos para los activos equity usando Markowitz.

    Args:
        equity_asset_ids : lista de asset_ids con ticker en yfinance
        risk_profile     : 'conservador' | 'estable' | 'moderado' | 'agresivo'
        lookback_days    : ventana histórica en días calendario

    Returns:
        {asset_id: peso_float}  o  None si falla (el caller usa pesos heurísticos)
    """
    try:
        import numpy as np
        import yfinance as yf
        from scipy.optimize import minimize
    except ImportError:
        return None

    # Filtrar los que tienen ticker yfinance
    valid = [(aid, _YF_MAP[aid]) for aid in equity_asset_ids if aid in _YF_MAP]
    if len(valid) < 2:
        return None

    asset_ids = [v[0] for v in valid]
    tickers   = [v[1] for v in valid]

    # ── Descargar precios históricos ─────────────────────────────────────────
    period = f"{lookback_days}d"
    try:
        raw = yf.download(tickers, period=period, auto_adjust=True, progress=False)
        if raw.empty:
            return None
        prices = raw["Close"] if "Close" in raw else raw
        if hasattr(prices, "columns") and len(prices.columns) == 0:
            return None
    except Exception:
        return None

    # Retornos diarios → anualizados
    rets   = prices.pct_change().dropna()
    if len(rets) < 30:
        return None

    # Alinear columnas al orden de tickers
    available = [t for t in tickers if t in rets.columns]
    if len(available) < 2:
        return None
    rets       = rets[available].dropna(axis=1, how="all")
    asset_ids  = [asset_ids[tickers.index(t)] for t in available]

    mu  = rets.mean().values * 252          # retorno anual esperado
    cov = rets.cov().values  * 252          # covarianza anual
    n   = len(available)

    w0     = np.ones(n) / n
    lo, hi = _BOUNDS.get(risk_profile, (0.05, 0.45))
    bounds = [(lo, hi)] * n
    cons   = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]

    # ── Función objetivo según perfil ────────────────────────────────────────
    if risk_profile == "conservador":
        # Mínima varianza — preservación de capital ante todo
        def objective(w):
            return float(w @ cov @ w)

    elif risk_profile == "estable":
        # Máximo Sharpe con penalización extra por varianza
        def objective(w):
            ret = float(w @ mu)
            vol = math.sqrt(max(float(w @ cov @ w), 1e-10))
            sharpe = (ret - _RF) / vol
            return -(sharpe - 0.3 * vol)   # penaliza volatilidad alta

    else:
        # Máximo Sharpe (moderado / agresivo)
        def objective(w):
            ret = float(w @ mu)
            vol = math.sqrt(max(float(w @ cov @ w), 1e-10))
            return -(ret - _RF) / vol

    result = minimize(
        objective, w0,
        method="SLSQP",
        bounds=bounds,
        constraints=cons,
        options={"maxiter": 500, "ftol": 1e-9},
    )

    if not result.success:
        return None

    weights = result.x
    # Renormalizar por si hay desvíos numéricos mínimos
    weights = weights / weights.sum()

    return {asset_ids[i]: float(weights[i]) for i in range(n)}
