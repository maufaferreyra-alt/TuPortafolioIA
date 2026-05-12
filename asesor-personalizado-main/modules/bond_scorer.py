"""
Scorer de bonos argentinos.
Fuentes de datos: rava.com (primaria) → ambito.com (backup) → static fallback.

Uso offline:
    python -m modules.bond_scorer

Genera bond_scores.json con scores 0-100 por instrumento de renta fija.
"""

import json
import time
import re
from pathlib import Path
from datetime import date, datetime

import requests

BOND_SCORES_PATH = Path(__file__).parent.parent / "bond_scores.json"
REQUEST_DELAY = 1.5

# ─── Calendario de LECAPs vigentes ────────────────────────────────────────────
# (ticker_BYMA, fecha_vencimiento, TNA_est%)
# Fuente: Secretaría de Finanzas Argentina — licitaciones primarias.
LECAP_SCHEDULE: list[tuple[str, date, float]] = [
    ("S30J26", date(2026,  6, 30), 28.0),
    ("S31L26", date(2026,  7, 31), 27.0),
    ("S29A26", date(2026,  8, 28), 27.0),
    ("S30S26", date(2026,  9, 30), 26.0),
    ("S31O26", date(2026, 10, 31), 26.0),
    ("S28N26", date(2026, 11, 27), 25.0),
    ("S31D26", date(2026, 12, 31), 25.0),
    ("S31E27", date(2027,  1, 29), 24.0),
    ("S28F27", date(2027,  2, 26), 24.0),
    ("S31M27", date(2027,  3, 31), 24.0),
]

def get_active_lecap(min_days: int = 7) -> dict | None:
    """
    Retorna la LECAP más corta con al menos `min_days` días hasta vencimiento.
    Devuelve None si no hay ninguna en el calendario (requiere actualización manual).
    """
    today = date.today()
    for ticker, expiry, tna_est in LECAP_SCHEDULE:
        days_left = (expiry - today).days
        if days_left >= min_days:
            return {
                "ticker":         ticker,
                "expiry":         expiry,
                "tna_est":        tna_est,
                "days_left":      days_left,
                "duration_years": round(days_left / 365, 3),
            }
    return None

# ─── Credit spreads de ONs sobre el soberano (bps) ───────────────────────────
# Negativo = ON cotiza debajo del soberano (menor riesgo percibido que la República)
# Positivo = ON paga más que el soberano (mayor riesgo o menor liquidez)
_ON_CREDIT_SPREADS_BPS: dict[str, int] = {
    "on_tgs":      -100,   # monopolio de gasoductos regulado, cashflow predecible
    "on_pampa":     -75,   # generación/distribución eléctrica, flujo estable
    "on_corp":      -50,   # mix Pampa/Arcor/MELI — calidad investment-grade local
    "on_tecpetrol":   0,   # upstream E&P, correlación con energía
    "on_ypf":       +50,   # empresa estatal con riesgo político implícito
    "on_macro":     +100,  # banco: exposición directa al ciclo económico ARG
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/html, */*",
}

# ─── Definición de bonos ──────────────────────────────────────────────────────
# tir_est   : rendimiento estimado (% anual en la moneda del bono)
# duration_est: duración modificada estimada (años)
# paridad_est : precio como % del valor par
# quality_pts : puntaje fijo de calidad crediticia (0-25)
# vol_est_m   : volumen diario estimado en millones de ARS
# ticker_rava : símbolo en rava.com / BYMA

BOND_DEFS = {
    "al30": {
        "label":        "AL30 – Bono Global USD Ley Argentina",
        "type":         "soberano_usd",
        "ticker_rava":  "AL30",
        "ticker_ambito": "AL30",
        "tir_est":      8.5,
        "duration_est": 3.5,
        "paridad_est":  47.0,
        "quality_pts":  16,
        "vol_est_m":    4.0,
    },
    "gd30": {
        "label":        "GD30 – Bono Global USD Ley Nueva York",
        "type":         "soberano_usd",
        "ticker_rava":  "GD30",
        "ticker_ambito": "GD30",
        "tir_est":      8.5,
        "duration_est": 4.0,
        "paridad_est":  47.0,
        "quality_pts":  17,
        "vol_est_m":    6.0,
    },
    "lecap": {
        "label":        "LECAP – Letra Capitalizable del Tesoro (activa)",
        "type":         "lecap",
        "ticker_rava":  "S30J26",    # reemplazado en runtime por get_active_lecap()
        "ticker_ambito": "S30J26",
        "tir_est":      28.0,        # TNA estimada de la letra activa
        "duration_est": 0.16,        # ~60 días hasta vencimiento jun-2026
        "paridad_est":  99.5,
        "quality_pts":  18,
        "vol_est_m":    10.0,
    },
    "cer_tx26": {
        "label":        "Bono CER TX26 – Ajuste por Inflación (corto)",
        "type":         "cer",
        "ticker_rava":  "TX26",
        "ticker_ambito": "TX26",
        "tir_est":      2.0,        # TIR real baja por corto plazo
        "duration_est": 0.5,        # vence 2026, ~6 meses desde mayo 2026
        "paridad_est":  99.5,
        "quality_pts":  17,
        "vol_est_m":    1.5,
    },
    "cer_tx28": {
        "label":        "Bono CER TX28 – Ajuste por Inflación",
        "type":         "cer",
        "ticker_rava":  "TX28",
        "ticker_ambito": "TX28",
        "tir_est":      5.0,
        "duration_est": 2.2,        # vence julio 2028 (~2.2 años desde mayo 2026)
        "paridad_est":  96.0,
        "quality_pts":  17,
        "vol_est_m":    2.5,
    },
    "cer_dicp": {
        "label":        "Bono DICP – CER Largo Plazo",
        "type":         "cer",
        "ticker_rava":  "DICP",
        "ticker_ambito": "DICP",
        "tir_est":      8.0,
        "duration_est": 7.0,
        "paridad_est":  80.0,
        "quality_pts":  15,
        "vol_est_m":    8.0,
    },
    "on_ypf": {
        "label":        "ON YPF USD",
        "type":         "on_corp",
        "ticker_rava":  "YPFDS",
        "ticker_ambito": "YPFDS",
        "tir_est":      9.0,
        "duration_est": 2.5,
        "paridad_est":  98.0,
        "quality_pts":  22,
        "vol_est_m":    2.0,
    },
    "on_corp": {
        "label":        "ONs Corporativas Mix (YPF / TGS / Tecpetrol)",
        "type":         "on_corp",
        "ticker_rava":  "YPFDS",   # representativo del mix — verificar ticker vigente
        "ticker_ambito": "YPFDS",
        "tir_est":      8.5,
        "duration_est": 2.0,
        "paridad_est":  100.0,
        "quality_pts":  20,
        "vol_est_m":    2.0,
    },
    # on_pampa (PTSTO) removido — venció. Reincorporar cuando Pampa emita nueva serie activa.
    "on_tecpetrol": {
        "label":        "ON Tecpetrol USD",
        "type":         "on_corp",
        "ticker_rava":  "TCCUD",
        "ticker_ambito": "TCCUD",
        "tir_est":      8.0,
        "duration_est": 2.5,
        "paridad_est":  99.0,
        "quality_pts":  22,
        "vol_est_m":    1.0,
    },
    # ── Soberanos serie 2035-2038 ─────────────────────────────────────────────
    "al35": {
        "label":        "AL35 – Bono Global USD Ley Argentina 2035",
        "type":         "soberano_usd",
        "ticker_rava":  "AL35",
        "ticker_ambito": "AL35",
        "tir_est":      9.0,       # mayor yield por mayor duration
        "duration_est": 6.5,       # duration más larga que AL30
        "paridad_est":  42.0,
        "quality_pts":  15,        # mismo emisor que AL30, menor puntuación por mayor riesgo duration
        "vol_est_m":    3.0,
    },
    "gd35": {
        "label":        "GD35 – Bono Global USD Ley Nueva York 2035",
        "type":         "soberano_usd",
        "ticker_rava":  "GD35",
        "ticker_ambito": "GD35",
        "tir_est":      9.0,
        "duration_est": 6.5,
        "paridad_est":  42.0,
        "quality_pts":  16,        # ley NY → punto extra sobre AL35
        "vol_est_m":    4.0,
    },
    "gd38": {
        "label":        "GD38 – Bono Global USD Ley Nueva York 2038",
        "type":         "soberano_usd",
        "ticker_rava":  "GD38",
        "ticker_ambito": "GD38",
        "tir_est":      9.5,       # mayor yield por mayor plazo
        "duration_est": 8.5,
        "paridad_est":  40.0,
        "quality_pts":  16,
        "vol_est_m":    3.0,
    },
    # ── ONs adicionales ───────────────────────────────────────────────────────
    "on_tgs": {
        "label":        "ON TGS USD (TGSU2O)",
        "type":         "on_corp",
        "ticker_rava":  "TGSU2O",
        "ticker_ambito": "TGSU2O",
        "tir_est":      8.5,
        "duration_est": 2.0,
        "paridad_est":  100.0,
        "quality_pts":  22,        # infraestructura regulada, alta calidad
        "vol_est_m":    1.0,
    },
    "on_macro": {
        "label":        "ON Banco Macro USD",
        "type":         "on_corp",
        "ticker_rava":  "BMA5O",
        "ticker_ambito": "BMA5O",
        "tir_est":      9.0,
        "duration_est": 2.5,
        "paridad_est":  99.0,
        "quality_pts":  20,
        "vol_est_m":    0.8,
    },
    # ── ONs corporativas adicionales ─────────────────────────────────────────
    "on_tgs2": {
        "label":        "ON TGS USD Serie 2 (TGS2O)",
        "type":         "on_corp",
        "ticker_rava":  "TGS2O",
        "ticker_ambito": "TGS2O",
        "tir_est":      8.5,
        "duration_est": 2.0,
        "paridad_est":  100.0,
        "quality_pts":  22,
        "vol_est_m":    1.0,
    },
    "on_arcor": {
        "label":        "ON Arcor USD (RCCJO)",
        "type":         "on_corp",
        "ticker_rava":  "RCCJO",
        "ticker_ambito": "RCCJO",
        "tir_est":      8.5,
        "duration_est": 2.5,
        "paridad_est":  99.0,
        "quality_pts":  21,
        "vol_est_m":    1.5,
    },
    "on_telecom2": {
        "label":        "ON Telecom Argentina USD (TLCMO)",
        "type":         "on_corp",
        "ticker_rava":  "TLCMO",
        "ticker_ambito": "TLCMO",
        "tir_est":      9.0,
        "duration_est": 2.0,
        "paridad_est":  98.0,
        "quality_pts":  20,
        "vol_est_m":    1.5,
    },
    "on_irsa": {
        "label":        "ON IRSA USD (IRCFO)",
        "type":         "on_corp",
        "ticker_rava":  "IRCFO",
        "ticker_ambito": "IRCFO",
        "tir_est":      10.0,
        "duration_est": 2.5,
        "paridad_est":  97.0,
        "quality_pts":  18,
        "vol_est_m":    2.5,
    },
    "on_cresud": {
        "label":        "ON Cresud USD (CSDOO)",
        "type":         "on_corp",
        "ticker_rava":  "CSDOO",
        "ticker_ambito": "CSDOO",
        "tir_est":      10.0,
        "duration_est": 2.0,
        "paridad_est":  97.0,
        "quality_pts":  17,
        "vol_est_m":    3.0,
    },
    # ── Bonos en pesos — cobertura dual y dollar linked ───────────────────────
    "dual_bond": {
        "label":        "Bono Dual TDA27 (max CER / devaluación)",
        "type":         "cer",          # tratado como CER para scoring de duration/calidad
        "ticker_rava":  "TDA27",
        "ticker_ambito": "TDA27",
        "tir_est":      6.0,            # TNA estimada real
        "duration_est": 1.2,            # vence 2027
        "paridad_est":  98.0,
        "quality_pts":  19,
        "vol_est_m":    2.0,
    },
    "dollar_linked": {
        "label":        "Bono Dollar Linked TV26",
        "type":         "cer",          # scoring similar a CER
        "ticker_rava":  "TV26",
        "ticker_ambito": "TV26",
        "tir_est":      3.0,            # spread sobre devaluación esperada
        "duration_est": 0.8,            # vence 2026
        "paridad_est":  99.0,
        "quality_pts":  18,
        "vol_est_m":    2.5,
    },
    # ── FCIs USD ──────────────────────────────────────────────────────────────
    "fci_usd_rf": {
        "label":        "FCI Renta Fija USD (Compass / Balanz)",
        "type":         "fci_usd",
        "ticker_rava":  "FCI-USD",
        "ticker_ambito": "FCI-USD",
        "tir_est":      6.5,
        "duration_est": 1.5,
        "paridad_est":  100.0,
        "quality_pts":  21,
        "vol_est_m":    0.5,
    },
    "fci_usd_ahorro": {
        "label":        "FCI Ahorro USD Corto Plazo (Cohen / Quinquela)",
        "type":         "fci_usd",
        "ticker_rava":  "FCI-USDCP",
        "ticker_ambito": "FCI-USDCP",
        "tir_est":      5.5,
        "duration_est": 0.3,
        "paridad_est":  100.0,
        "quality_pts":  23,
        "vol_est_m":    0.2,
    },
    "fci_latam": {
        "label":        "FCI Deuda Latinoamérica (SBS / OnCapital)",
        "type":         "fci_usd",
        "ticker_rava":  "FCI-LATAM",
        "ticker_ambito": "FCI-LATAM",
        "tir_est":      7.5,
        "duration_est": 3.0,
        "paridad_est":  100.0,
        "quality_pts":  18,
        "vol_est_m":    1.2,
    },
    # ── ONs adicionales ───────────────────────────────────────────────────────
    "on_meli": {
        "label":        "ON MercadoLibre USD (MLIUSD)",
        "type":         "on_corp",
        "ticker_rava":  "MLIUSD",
        "ticker_ambito": "MLIUSD",
        "tir_est":      7.5,
        "duration_est": 2.5,
        "paridad_est":  99.0,
        "quality_pts":  24,
        "vol_est_m":    1.5,
    },
    "on_telecom": {
        "label":        "ON Telecom Argentina USD (TCOMD)",
        "type":         "on_corp",
        "ticker_rava":  "TCOMD",
        "ticker_ambito": "TCOMD",
        "tir_est":      9.0,
        "duration_est": 2.0,
        "paridad_est":  98.0,
        "quality_pts":  20,
        "vol_est_m":    1.5,
    },
    "on_genneia": {
        "label":        "ON Genneia USD (GNCXO)",
        "type":         "on_corp",
        "ticker_rava":  "GNCXO",
        "ticker_ambito": "GNCXO",
        "tir_est":      9.5,
        "duration_est": 2.5,
        "paridad_est":  97.0,
        "quality_pts":  19,
        "vol_est_m":    2.0,
    },
    "on_vista": {
        "label":        "ON Vista Oil & Gas USD (VSCOD)",
        "type":         "on_corp",
        "ticker_rava":  "VSCOD",
        "ticker_ambito": "VSCOD",
        "tir_est":      10.0,
        "duration_est": 2.0,
        "paridad_est":  97.0,
        "quality_pts":  18,
        "vol_est_m":    2.5,
    },
    "on_pampa": {
        "label":        "ON Pampa Energía USD (PGN2O)",
        "type":         "on_corp",
        "ticker_rava":  "PGN2O",
        "ticker_ambito": "PGN2O",
        "tir_est":      9.0,
        "duration_est": 2.5,
        "paridad_est":  99.0,
        "quality_pts":  22,
        "vol_est_m":    1.5,
    },
    # ── Soberanos adicionales ─────────────────────────────────────────────────
    "gd29": {
        "label":        "GD29 – Bono Global USD Ley Nueva York 2029",
        "type":         "soberano_usd",
        "ticker_rava":  "GD29",
        "ticker_ambito": "GD29",
        "tir_est":      9.0,
        "duration_est": 3.5,
        "paridad_est":  46.0,
        "quality_pts":  17,
        "vol_est_m":    5.0,
    },
    "gd41": {
        "label":        "GD41 – Bono Global USD Ley Nueva York 2041",
        "type":         "soberano_usd",
        "ticker_rava":  "GD41",
        "ticker_ambito": "GD41",
        "tir_est":      10.0,
        "duration_est": 10.0,
        "paridad_est":  38.0,
        "quality_pts":  15,
        "vol_est_m":    5.5,
    },
}

# ─── Fetchers ─────────────────────────────────────────────────────────────────

def _fetch_rava(ticker: str) -> dict | None:
    """
    Obtiene precio, volumen y TIR desde rava.com.
    1. Intenta la API JSON (cotizaciones.php) para precio/volumen.
    2. Si no obtiene TIR por JSON, intenta scrapear la página HTML del perfil.
    Devuelve {paridad, vol_m, tir?} o None si falla completamente.
    """
    try:
        url = f"https://www.rava.com/api/cotizaciones.php?asset={ticker}&ReduccionDatos=0"
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json()

        if isinstance(data, list) and data:
            row = data[0]
        elif isinstance(data, dict):
            row = data
        else:
            return None

        precio = (
            row.get("Ultimo") or row.get("ultimo") or
            row.get("PrecioUltimo") or row.get("precioUltimo")
        )
        volumen = (
            row.get("Volumen") or row.get("volumen") or
            row.get("VolumenNominal") or row.get("volumenNominal") or 0
        )

        if precio is None:
            return None

        precio  = float(str(precio).replace(",", "."))
        volumen = float(str(volumen).replace(",", "").replace(".", "")) if volumen else 0

        result: dict = {
            "paridad": precio,
            "vol_m":   volumen / 1_000_000,
        }

        # Intentar TIR desde el mismo dict JSON
        tir_raw = row.get("TIR") or row.get("tir") or row.get("Rendimiento") or row.get("rendimiento")
        if tir_raw is not None:
            try:
                result["tir"] = float(str(tir_raw).replace(",", ".").replace("%", ""))
            except ValueError:
                pass

        # Si no llegó TIR por JSON, intentar HTML (con delay ya incluido en el caller)
        if "tir" not in result:
            tir_html = _scrape_rava_tir(ticker)
            if tir_html is not None:
                result["tir"] = tir_html

        return result
    except Exception:
        return None


def _scrape_rava_tir(ticker: str) -> float | None:
    """
    Extrae TIR desde la página HTML del perfil del bono en Rava.
    Busca patrones como 'TIR', 'Rendimiento', 'Tasa' seguidos de un número%.
    """
    try:
        url = f"https://www.rava.com/perfil/{ticker}"
        r   = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        html = r.text

        patterns = [
            r"(?:TIR|Rendimiento\s*anual|Tasa\s*interna)[^0-9\-]{0,30}([\-]?[0-9]+[.,][0-9]+)\s*%",
            r'"tir"\s*:\s*"?([\-]?[0-9]+[.,][0-9]+)',
            r"(?:TIR|tir)\s*[:\-]\s*([\-]?[0-9]+[.,][0-9]+)",
        ]
        for pat in patterns:
            m = re.search(pat, html, re.IGNORECASE)
            if m:
                return float(m.group(1).replace(",", "."))
        return None
    except Exception:
        return None


def _fetch_ambito(ticker: str) -> dict | None:
    """
    Backup: obtiene precio desde ambito.com.
    Devuelve {paridad, vol_m} o None si falla.
    """
    try:
        url = f"https://mercados.ambito.com/bonos/informacion-general/{ticker}"
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json()

        precio_raw = (
            data.get("ultimo") or data.get("cierre") or
            data.get("apertura") or data.get("Ultimo")
        )
        volumen_raw = data.get("volumen") or data.get("Volumen") or 0

        if precio_raw is None:
            return None

        precio = float(str(precio_raw).replace(",", "."))
        volumen = float(re.sub(r"[^\d]", "", str(volumen_raw))) if volumen_raw else 0

        return {
            "paridad": precio,
            "vol_m": volumen / 1_000_000,
        }
    except Exception:
        return None


def _fetch_live(ticker: str) -> dict | None:
    live = _fetch_rava(ticker)
    if not live:
        live = _fetch_ambito(ticker)
    return live


# ─── Scoring ──────────────────────────────────────────────────────────────────
# 5 bloques: Rendimiento 35 + Duration 20 + Calidad 25 + Paridad 10 + Liquidez 10

def _score_rendimiento(tir: float, bond_type: str) -> int:
    """35 pts. Mayor rendimiento = mejor, con umbrales por tipo."""
    max_pts = 35
    if bond_type in ("soberano_usd", "on_corp"):
        exc, bue, neu = 10.0, 8.0, 6.0
    elif bond_type == "cer":
        exc, bue, neu = 8.0, 5.0, 2.0
    elif bond_type == "lecap":
        exc, bue, neu = 70.0, 55.0, 45.0
    else:
        exc, bue, neu = 9.0, 7.0, 5.0

    if tir >= exc:   return max_pts
    elif tir >= bue: return round(max_pts * 0.75)
    elif tir >= neu: return round(max_pts * 0.45)
    else:            return round(max_pts * 0.10)


def _score_duration(duration_years: float) -> int:
    """20 pts. Menor duración = menor riesgo de tasa = mejor."""
    max_pts = 20
    if duration_years <= 0.5:  return max_pts
    elif duration_years <= 1.0: return round(max_pts * 0.75)
    elif duration_years <= 2.0: return round(max_pts * 0.45)
    else:                       return round(max_pts * 0.10)


def _score_paridad(paridad: float) -> int:
    """10 pts. Bajo la par = potencial de ganancia de capital = mejor."""
    max_pts = 10
    if paridad < 70:    return max_pts
    elif paridad < 85:  return round(max_pts * 0.80)
    elif paridad < 100: return round(max_pts * 0.50)
    else:               return round(max_pts * 0.20)


def _score_liquidez(vol_m: float) -> int:
    """10 pts. Volumen diario en millones de ARS."""
    max_pts = 10
    if vol_m >= 10.0:  return max_pts
    elif vol_m >= 3.0: return round(max_pts * 0.80)
    elif vol_m >= 1.0: return round(max_pts * 0.50)
    else:              return round(max_pts * 0.20)


def _rating(score: int) -> str:
    if score >= 80:   return "STRONG BUY"
    elif score >= 65: return "BUY"
    elif score >= 50: return "HOLD"
    elif score >= 35: return "UNDERWEIGHT"
    else:             return "AVOID"


def score_bond(asset_id: str, live_data: dict | None = None) -> dict:
    """
    Calcula el score de un bono (0-100).
    TIR, duration, paridad y volumen se toman de live_data si están disponibles,
    recayendo en los estimados estáticos de BOND_DEFS.

    Para LECAPs, live_data puede incluir 'duration_years' para reflejar el vencimiento real.
    """
    defn = BOND_DEFS[asset_id]

    tir      = (live_data.get("tir") if live_data else None) or defn["tir_est"]
    # Para LECAP activa, duration_years viene del calendario real
    duration = (live_data.get("duration_years") if live_data else None) or defn["duration_est"]
    paridad  = live_data["paridad"] if live_data and "paridad" in live_data else defn["paridad_est"]
    vol_m    = live_data["vol_m"]   if live_data and "vol_m"   in live_data else defn["vol_est_m"]

    pts_rend = _score_rendimiento(tir, defn["type"])
    pts_dur  = _score_duration(duration)
    pts_qual = defn["quality_pts"]
    pts_par  = _score_paridad(paridad)
    pts_liq  = _score_liquidez(vol_m)

    total = pts_rend + pts_dur + pts_qual + pts_par + pts_liq

    return {
        "score":     total,
        "rating":    _rating(total),
        "live":      live_data is not None,
        "label":     defn["label"],
        "breakdown": {
            "rendimiento": pts_rend,
            "duration":    pts_dur,
            "calidad":     pts_qual,
            "paridad":     pts_par,
            "liquidez":    pts_liq,
        },
        "inputs": {
            "tir":      tir,
            "duration": duration,
            "paridad":  paridad,
            "vol_m":    round(vol_m, 2),
        },
    }


# ─── Contexto de mercado en tiempo real ──────────────────────────────────────

def _get_riesgo_pais_bps() -> float | None:
    """EMBI+ Argentina desde ArgentinaDatos (último registro disponible)."""
    try:
        r = requests.get(
            "https://api.argentinadatos.com/v1/finanzas/indices/riesgo-pais",
            headers=HEADERS, timeout=5,
        )
        data = r.json()
        if data and isinstance(data, list) and data[-1].get("valor"):
            return float(data[-1]["valor"])
    except Exception:
        pass
    return None


def _get_us_treasury_yields() -> dict:
    """Yields del Tesoro EE.UU. vía yfinance. Fallback a valores recientes."""
    out = {"5y": 4.0, "10y": 4.4}
    try:
        import yfinance as yf
        for ticker, key in {("^FVX", "5y"), ("^TNX", "10y")}:
            hist = yf.Ticker(ticker).history(period="5d")
            if not hist.empty:
                out[key] = round(float(hist["Close"].iloc[-1]), 2)
    except Exception:
        pass
    return out


def get_market_context() -> dict:
    """
    Contexto de mercado en tiempo real.
    Retorna {riesgo_pais_bps, us_treasury_5y, us_treasury_10y, as_of}.
    Todos los campos pueden ser None si fallan las APIs.
    """
    rp      = _get_riesgo_pais_bps()
    us_ylds = _get_us_treasury_yields()
    return {
        "riesgo_pais_bps": rp,
        "us_treasury_5y":  us_ylds.get("5y"),
        "us_treasury_10y": us_ylds.get("10y"),
        "as_of":           str(date.today()),
    }


def _implied_sovereign_tir(duration_years: float, rp_bps: float, us_yields: dict) -> float:
    """TIR implícita de bono soberano USD = Treasury + riesgo_país."""
    treasury = us_yields["10y"] if duration_years > 4 else us_yields["5y"]
    return round(treasury + rp_bps / 100, 2)


def load_scores_live(path: Path = BOND_SCORES_PATH) -> tuple[dict, dict]:
    """
    Carga scores base del JSON y aplica overlay de mercado en tiempo real:

      1. Bonos soberanos USD → TIR implícita = Treasury + riesgo_país
      2. ONs corporativas   → TIR implícita = soberano + credit_spread por emisor
      3. LECAP activa       → detecta vencimiento y usa la letra más corta vigente
         (si todas vencieron, mantiene score estático como fallback)

    Returns:
        scores  dict {asset_id: score_int}
        market  dict con riesgo_pais_bps, us_treasury_5y/10y, as_of, active_lecap
    """
    base_scores = load_scores(path)
    market      = get_market_context()

    # ── LECAP activa ──────────────────────────────────────────────────────────
    active_lc = get_active_lecap()
    market["active_lecap"] = active_lc  # expone al portfolio builder

    rp_bps = market.get("riesgo_pais_bps")
    if rp_bps is None:
        # Sin riesgo país, aún podemos re-scorear la LECAP si hay una activa
        if active_lc:
            result = score_bond("lecap", {"tir": active_lc["tna_est"]})
            updated = dict(base_scores)
            updated["lecap"] = result["score"]
            return updated, market
        return base_scores, market

    us_yields = {
        "5y":  market.get("us_treasury_5y")  or 4.0,
        "10y": market.get("us_treasury_10y") or 4.4,
    }

    updated = dict(base_scores)

    # ── 1. Soberanos USD ──────────────────────────────────────────────────────
    for asset_id, defn in BOND_DEFS.items():
        if defn.get("type") != "soberano_usd":
            continue
        dynamic_tir = _implied_sovereign_tir(defn["duration_est"], rp_bps, us_yields)
        result = score_bond(asset_id, {"tir": dynamic_tir})
        updated[asset_id] = result["score"]

    # ── 2. ONs corporativas: TIR = soberano_equiv + credit_spread ────────────
    for asset_id, defn in BOND_DEFS.items():
        if defn.get("type") != "on_corp":
            continue
        spread_bps  = _ON_CREDIT_SPREADS_BPS.get(asset_id, 0)
        # Usamos el soberano de duración equivalente como base
        base_sov    = _implied_sovereign_tir(defn["duration_est"], rp_bps, us_yields)
        dynamic_tir = round(base_sov + spread_bps / 100, 2)
        result = score_bond(asset_id, {"tir": dynamic_tir})
        updated[asset_id] = result["score"]

    # ── 3. LECAP: usar la letra vigente más corta ─────────────────────────────
    if active_lc:
        result = score_bond("lecap", {
            "tir": active_lc["tna_est"],
        })
        updated["lecap"] = result["score"]
        # Guarda también la duration real para que el portfolio builder la use
        market["active_lecap"]["score"] = result["score"]

    return updated, market


# ─── Runner offline ───────────────────────────────────────────────────────────

def run_and_save(path: Path = BOND_SCORES_PATH) -> dict:
    """
    Puntúa todos los bonos, muestra resultados en consola y guarda bond_scores.json.
    Usa la LECAP activa según el calendario de vencimientos.
    """
    print(f"\n{'─'*60}")
    print(f"BOND SCORER — {date.today()}")
    print(f"{'─'*60}\n")

    # Contexto de mercado para TIR dinámica
    market    = get_market_context()
    rp_bps    = market.get("riesgo_pais_bps")
    us_yields = {
        "5y":  market.get("us_treasury_5y")  or 4.0,
        "10y": market.get("us_treasury_10y") or 4.4,
    }

    # LECAP activa
    active_lc = get_active_lecap()
    if active_lc:
        print(f"  LECAP activa: {active_lc['ticker']} — vence {active_lc['expiry']} "
              f"({active_lc['days_left']} días) TNA≈{active_lc['tna_est']}%\n")
    else:
        print("  ⚠️  Sin LECAP activa en el calendario — actualizar LECAP_SCHEDULE\n")

    results = {}

    for asset_id, defn in BOND_DEFS.items():
        ticker = defn.get("ticker_rava")
        live   = None

        if ticker:
            print(f"  Fetching {ticker} ({defn['label']})...")
            live = _fetch_live(ticker)
            time.sleep(REQUEST_DELAY)

        # Override de TIR dinámico por tipo
        if rp_bps:
            if defn["type"] == "soberano_usd":
                dyn_tir = _implied_sovereign_tir(defn["duration_est"], rp_bps, us_yields)
                live = (live or {}) | {"tir": dyn_tir}
            elif defn["type"] == "on_corp":
                spread  = _ON_CREDIT_SPREADS_BPS.get(asset_id, 0)
                dyn_tir = round(_implied_sovereign_tir(defn["duration_est"], rp_bps, us_yields)
                                + spread / 100, 2)
                live = (live or {}) | {"tir": dyn_tir}

        # Para LECAP usar siempre la letra activa
        if asset_id == "lecap" and active_lc:
            live = (live or {}) | {
                "tir":            active_lc["tna_est"],
                "duration_years": active_lc["duration_years"],
            }

        result = score_bond(asset_id, live)
        results[asset_id] = result

        tir_src = "LIVE" if (live and "tir" in live) else "STATIC"
        px_src  = "LIVE" if result["live"] else "STATIC"
        src     = f"TIR={tir_src} paridad+vol={px_src}"
        print(
            f"  {asset_id:<15} {result['score']:>3}  {result['rating']:<12}  "
            f"TIR={result['inputs']['tir']}%  par={result['inputs']['paridad']}%  "
            f"({src})"
        )

    output = {
        "as_of":        str(date.today()),
        "generated_at": datetime.now().isoformat(),
        "bond_scores":  results,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n{'─'*60}")
    print(f"Guardado en {path}")
    print(f"{'─'*60}\n")
    return results


def load_scores(path: Path = BOND_SCORES_PATH) -> dict:
    """
    Carga bond_scores.json y devuelve {asset_id: score_int}.
    Devuelve dict vacío si el archivo no existe o está corrupto.
    """
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return {k: v["score"] for k, v in data.get("bond_scores", {}).items()}
    except Exception:
        return {}


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_and_save()
