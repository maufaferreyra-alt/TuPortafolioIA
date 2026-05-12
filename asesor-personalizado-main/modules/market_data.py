"""
Datos de mercado en tiempo real.
- MEP/bolsa: dolarapi.com  (cache 30 min, fallback 1200)
- Precios equity: yfinance  (sin cache — llamar sólo cuando se necesite)
"""

import requests
from datetime import datetime

_MEP_TTL_SEC  = 1800    # 30 minutos
_MEP_FALLBACK = 1200.0

_mep_cache: dict = {"rate": None, "ts": None}


def get_mep_rate() -> float:
    """
    Tipo de cambio MEP (ARS/USD) desde dolarapi.com.
    Cachea 30 min. Fallback 1200 si la API no responde.
    """
    now = datetime.now()
    cached_rate = _mep_cache["rate"]
    cached_ts   = _mep_cache["ts"]

    if cached_rate and cached_ts:
        age = (now - cached_ts).total_seconds()
        if age < _MEP_TTL_SEC:
            return cached_rate

    try:
        r = requests.get(
            "https://dolarapi.com/v1/dolares/bolsa",
            timeout=8,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        r.raise_for_status()
        data = r.json()
        # "venta" es el precio al que se compra el dólar → spread más realista para el usuario
        rate = float(data.get("venta") or data.get("compra") or _MEP_FALLBACK)
        _mep_cache["rate"] = rate
        _mep_cache["ts"]   = now
        return rate
    except Exception:
        return cached_rate or _MEP_FALLBACK


def get_equity_prices(tickers: list) -> dict:
    """
    Precio actual (último cierre) para una lista de tickers de yfinance.
    Devuelve {TICKER: precio_float}. Tickers ausentes se omiten silenciosamente.
    """
    if not tickers:
        return {}
    try:
        import yfinance as yf
        import math

        unique = list(dict.fromkeys(tickers))   # dedup, preserva orden
        data   = yf.download(unique, period="2d", auto_adjust=True, progress=False)
        if data.empty:
            return {}

        close = data["Close"]
        last  = close.iloc[-1]

        result = {}
        for t in unique:
            val = last.get(t) if hasattr(last, "get") else None
            if val is not None and not math.isnan(float(val)):
                result[t] = float(val)
        return result
    except Exception:
        return {}
