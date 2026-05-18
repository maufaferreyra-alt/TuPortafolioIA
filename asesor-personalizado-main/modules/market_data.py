"""
Datos de mercado en tiempo real.
- MEP/bolsa: dolarapi.com  (cache 30 min, fallback 1200)
- Precios equity: yfinance  (sin cache — llamar sólo cuando se necesite)
"""

import requests
import streamlit as st
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


# ═══════════════════════════════════════════════════════════════════
# CLIENTES DE APIS GRATUITAS ARGENTINAS (Bloque 6B)
# ═══════════════════════════════════════════════════════════════════
#
# Las APIs gratuitas argentinas tienen limitaciones reconocidas:
#   - data912 → ~2h de delay, rate limit ~120 req/min
#   - argentinadatos → datos T-1 (cierre del día anterior)
#   - dolarapi → refresh cada 2 min
#
# La arquitectura está diseñada con interface clean (get_precio_dia)
# para reemplazar internamente por APIs pagas (Bloomberg / Refinitiv /
# proveedor profesional) sin tocar el form ni la lógica de cartera.
# Solo cambiarían los clientes internos.

DATA912_BASE = "https://data912.com"
ARGENTINADATOS_BASE = "https://api.argentinadatos.com"
DOLARAPI_BASE = "https://dolarapi.com/v1"

_TIMEOUT_SEGS = 8


def _fetch_json(url: str, source: str):
    """Fetch defensivo con timeout corto y log silencioso de errores."""
    try:
        r = requests.get(
            url,
            timeout=_TIMEOUT_SEGS,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"[market_data:{source}] Error fetching {url}: {e}")
        return None


def _parse_ticker_price_list(data, source: str) -> dict[str, float]:
    """
    Parsea una lista de dicts con ticker + precio a un dict
    {ticker: precio}. Defensivo ante variaciones de naming.
    """
    if not isinstance(data, list):
        return {}
    result = {}
    for item in data:
        if not isinstance(item, dict):
            continue
        ticker = (
            item.get("symbol")
            or item.get("ticker")
            or item.get("code")
            or item.get("id")
        )
        precio = (
            item.get("c")
            or item.get("close")
            or item.get("price")
            or item.get("last")
            or item.get("ultimo")
        )
        if ticker and precio is not None:
            try:
                result[str(ticker).upper().strip()] = float(precio)
            except (ValueError, TypeError):
                pass
    return result


# ── Clientes data912 ─────────────────────────────────────────────────
# Verificado contra la API real: la respuesta es una lista de dicts con
# campo "symbol" (ticker) y "c" (precio de cierre). El parser genérico
# encaja sin ajustes.

@st.cache_data(ttl=3600, show_spinner=False)
def get_arg_stocks_prices() -> dict[str, float]:
    """Precios de acciones argentinas. {ticker: precio_ars}."""
    data = _fetch_json(f"{DATA912_BASE}/live/arg_stocks", "data912")
    return _parse_ticker_price_list(data, "arg_stocks")


@st.cache_data(ttl=3600, show_spinner=False)
def get_arg_cedears_prices() -> dict[str, float]:
    """Precios de CEDEARs. {ticker: precio_ars}."""
    data = _fetch_json(f"{DATA912_BASE}/live/arg_cedears", "data912")
    return _parse_ticker_price_list(data, "arg_cedears")


@st.cache_data(ttl=3600, show_spinner=False)
def get_arg_bonds_prices() -> dict[str, float]:
    """Precios de bonos soberanos argentinos. {ticker: precio_ars}."""
    data = _fetch_json(f"{DATA912_BASE}/live/arg_bonds", "data912")
    return _parse_ticker_price_list(data, "arg_bonds")


@st.cache_data(ttl=3600, show_spinner=False)
def get_arg_corp_prices() -> dict[str, float]:
    """Precios de ONs corporativas. {ticker: precio_ars}."""
    data = _fetch_json(f"{DATA912_BASE}/live/arg_corp", "data912")
    return _parse_ticker_price_list(data, "arg_corp")


@st.cache_data(ttl=3600, show_spinner=False)
def get_arg_notes_prices() -> dict[str, float]:
    """Precios de LECAPs / Letras. {ticker: precio_ars}."""
    data = _fetch_json(f"{DATA912_BASE}/live/arg_notes", "data912")
    return _parse_ticker_price_list(data, "arg_notes")


# ── Cliente argentinadatos (FCIs) ────────────────────────────────────
# Verificado contra la API real: el endpoint /v1/finanzas/fci NO existe
# (404). Los FCIs se consultan por categoría — /fci/mercadoDinero/ultimo
# y /fci/rentaFija/ultimo — y cada item es {"fondo": <nombre>, "vcp":
# <valor cuotaparte>, ...}. No hay ticker: se indexan por NOMBRE de
# fondo. Por eso este cliente no usa el parser genérico.

@st.cache_data(ttl=3600, show_spinner=False)
def get_arg_fcis_prices() -> dict[str, float]:
    """
    Precios de FCIs (valor cuotaparte). {nombre_fondo_upper: vcp_ars}.

    NOTA: el form FCI del Bloque 6A no usa cuotapartes (el usuario carga
    el monto directo), así que get_precio_dia con tipo="fci" rara vez se
    ejerce. Se mantiene por completitud de la interface.
    """
    result: dict[str, float] = {}
    for categoria in ["mercadoDinero", "rentaFija"]:
        data = _fetch_json(
            f"{ARGENTINADATOS_BASE}/v1/finanzas/fci/{categoria}/ultimo",
            "argentinadatos",
        )
        if not isinstance(data, list):
            continue
        for item in data:
            if not isinstance(item, dict):
                continue
            fondo = item.get("fondo")
            vcp = item.get("vcp")
            if fondo and vcp is not None:
                try:
                    result[str(fondo).upper().strip()] = float(vcp)
                except (ValueError, TypeError):
                    pass
    return result


# ── Cliente dolarapi ─────────────────────────────────────────────────
# Verificado contra la API real: dolarapi NO expone /dolares/mep ni
# /dolares/ccl. MEP corresponde a la casa "bolsa" y CCL a la casa
# "contadoconliqui". oficial y blue sí coinciden con su nombre.

@st.cache_data(ttl=120, show_spinner=False)
def get_dolar_rates() -> dict[str, float] | None:
    """
    Devuelve dict con {tipo: precio_venta} para MEP, CCL, oficial, blue.

    Returns None si TODAS las consultas fallaron (no hay banner).
    Returns dict parcial si alguna salió (banner muestra lo que hay).
    """
    # nombre lógico → casa real en dolarapi
    casas = {
        "mep":     "bolsa",
        "ccl":     "contadoconliqui",
        "oficial": "oficial",
        "blue":    "blue",
    }
    result = {}
    for nombre, casa in casas.items():
        data = _fetch_json(f"{DOLARAPI_BASE}/dolares/{casa}", "dolarapi")
        if data and isinstance(data, dict):
            venta = data.get("venta") or data.get("compra")
            if venta is not None:
                try:
                    result[nombre] = float(venta)
                except (ValueError, TypeError):
                    pass
    return result if result else None


# ── Router público ───────────────────────────────────────────────────

def get_precio_dia(ticker: str, tipo: str) -> float | None:
    """
    INTERFACE PÚBLICA del módulo de precios en vivo.

    Devuelve el precio del día del activo en ARS, o None si no hay
    cobertura (la API no tiene el ticker, falló, o el tipo no aplica).
    El llamador debe degradar a entrada manual cuando recibe None.

    Esta función es el ÚNICO punto de contacto entre el form de carga y
    los proveedores de datos. Para migrar a API paga, solo cambiar las
    implementaciones internas (get_arg_*_prices, get_arg_fcis_prices).
    """
    ticker = (ticker or "").upper().strip()
    if not ticker:
        return None

    dispatch = {
        "accion_arg": get_arg_stocks_prices,
        "cedear":     get_arg_cedears_prices,
        "etf":        get_arg_cedears_prices,  # ETFs cotizan como CEDEARs
        "bono":       get_arg_bonds_prices,
        "on":         get_arg_corp_prices,
        "letra":      get_arg_notes_prices,
        "fci":        get_arg_fcis_prices,
    }

    fetcher = dispatch.get(tipo)
    if fetcher is None:
        return None

    try:
        precios = fetcher()
        return precios.get(ticker)
    except Exception as e:
        print(f"[market_data] Error en get_precio_dia({ticker}, {tipo}): {e}")
        return None
