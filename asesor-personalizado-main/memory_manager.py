"""
Gestión de memoria persistente del asesor.
Base de datos local en memory.json — aprende de operaciones pasadas,
detecta patrones y ajusta parámetros automáticamente.
"""

import json
import uuid
from datetime import date
from pathlib import Path

MEMORY_PATH = Path(__file__).parent / "memory.json"

_EMPTY_MEMORY: dict = {
    "portfolios": [],
    "performance": [],
    "aprendizaje": {
        "umbral_descuento_minimo_pct": 10.0,
        "score_minimo": 55,
        "ajustes_calidad_sector": {},
        "sectores_evitar": [],
        "sectores_sobreponderar": [],
        "patrones_detectados": [],
        "reglas_aprendidas": [],
        "historial_medianas_sector": {},
        "score_ajustes": {},
    },
    "mercado_snapshot": [],
    "instrumentos_ar": {
        "bonos": [],
        "letras": [],
        "fondos": [],
        "cedears_seguimiento": [],
    },
}


# ─── Persistencia base ────────────────────────────────────────────────────────

def load_memory() -> dict:
    """Carga memory.json. Si no existe lo crea con la estructura vacía."""
    if not MEMORY_PATH.exists():
        save_memory(_EMPTY_MEMORY)
        return _EMPTY_MEMORY.copy()
    try:
        with open(MEMORY_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        save_memory(_EMPTY_MEMORY)
        return _EMPTY_MEMORY.copy()


def save_memory(mem: dict) -> None:
    """Persiste el dict en memory.json."""
    with open(MEMORY_PATH, "w", encoding="utf-8") as f:
        json.dump(mem, f, indent=2, ensure_ascii=False)


# ─── Portfolios ───────────────────────────────────────────────────────────────

def guardar_portfolio(portfolio: dict) -> str:
    """
    Agrega el portfolio a la memoria con ID único y fecha de hoy.
    Retorna el ID generado (8 primeros chars de uuid4).
    """
    mem = load_memory()
    portfolio_id = str(uuid.uuid4())[:8]
    entry = {
        "id":     portfolio_id,
        "fecha":  str(date.today()),
        **portfolio,
    }
    mem["portfolios"].append(entry)
    save_memory(mem)
    return portfolio_id


def cerrar_posicion(portfolio_id: str, ticker: str, precio_salida: float) -> None:
    """
    Cierra una posición abierta (fecha_salida == None) de un portfolio.
    Calcula retorno, clasifica resultado y dispara detección de patrones.
    """
    mem = load_memory()

    portfolio = next(
        (p for p in mem["portfolios"] if p.get("id") == portfolio_id), None
    )
    if portfolio is None:
        raise ValueError(f"Portfolio '{portfolio_id}' no encontrado.")

    posicion = next(
        (
            pos for pos in portfolio.get("posiciones", [])
            if pos.get("ticker") == ticker and pos.get("fecha_salida") is None
        ),
        None,
    )
    if posicion is None:
        raise ValueError(f"Posición abierta para '{ticker}' no encontrada en portfolio '{portfolio_id}'.")

    precio_entrada = posicion["precio_entrada"]
    retorno_pct    = ((precio_salida / precio_entrada) - 1) * 100

    if retorno_pct > 3:
        resultado = "ganador"
    elif retorno_pct < -3:
        resultado = "perdedor"
    else:
        resultado = "neutral"

    posicion["precio_salida"]  = precio_salida
    posicion["fecha_salida"]   = str(date.today())
    posicion["retorno_pct"]    = round(retorno_pct, 2)
    posicion["resultado"]      = resultado

    _actualizar_performance(mem, posicion)
    _detectar_patrones(mem, posicion)
    save_memory(mem)


# ─── Performance ──────────────────────────────────────────────────────────────

def _actualizar_performance(mem: dict, pos: dict) -> None:
    """
    Actualiza (o crea) el registro de performance del ticker.
    Acumula: operaciones, ganadores, perdedores, retorno promedio,
    descuento vs sector promedio, mejor y peor retorno.
    """
    ticker   = pos["ticker"]
    retorno  = pos.get("retorno_pct", 0.0)
    resultado = pos.get("resultado", "neutral")
    desc     = pos.get("descuento_vs_sector_entrada", 0.0)

    registro = next((r for r in mem["performance"] if r["ticker"] == ticker), None)
    if registro is None:
        registro = {
            "ticker":                        ticker,
            "operaciones":                   0,
            "ganadores":                     0,
            "perdedores":                    0,
            "retorno_promedio_pct":          0.0,
            "descuento_vs_sector_promedio_pct": 0.0,
            "mejor_retorno":                 None,
            "peor_retorno":                  None,
        }
        mem["performance"].append(registro)

    n = registro["operaciones"]

    # Promedio acumulado de retorno
    registro["retorno_promedio_pct"] = round(
        (registro["retorno_promedio_pct"] * n + retorno) / (n + 1), 2
    )
    # Promedio acumulado de descuento
    registro["descuento_vs_sector_promedio_pct"] = round(
        (registro["descuento_vs_sector_promedio_pct"] * n + desc) / (n + 1), 2
    )

    registro["operaciones"] += 1
    if resultado == "ganador":
        registro["ganadores"] += 1
    elif resultado == "perdedor":
        registro["perdedores"] += 1

    registro["mejor_retorno"] = (
        retorno if registro["mejor_retorno"] is None
        else max(registro["mejor_retorno"], retorno)
    )
    registro["peor_retorno"] = (
        retorno if registro["peor_retorno"] is None
        else min(registro["peor_retorno"], retorno)
    )


def _detectar_patrones(mem: dict, pos: dict) -> None:
    """
    Analiza la posición cerrada y ajusta parámetros de aprendizaje:
    - Descuento insuficiente → sube umbral automáticamente.
    - Win rate bajo en sector → agrega a sectores_evitar.
    - Win rate alto en sector → agrega a sectores_sobreponderar.
    """
    aprendizaje = mem["aprendizaje"]
    retorno     = pos.get("retorno_pct", 0.0)
    desc        = pos.get("descuento_vs_sector_entrada", 0.0)
    sector      = pos.get("sector", "desconocido")

    ticker = pos["ticker"]

    # Patrón 1: compra sin suficiente descuento → pérdida
    if retorno < -5 and desc < 10:
        patron = {
            "tipo":   "descuento_insuficiente",
            "ticker": ticker,
            "fecha":  str(date.today()),
            "detalle": f"Retorno {retorno:.1f}% con descuento {desc:.1f}% vs sector",
        }
        aprendizaje["patrones_detectados"].append(patron)
        aprendizaje["umbral_descuento_minimo_pct"] = round(
            aprendizaje["umbral_descuento_minimo_pct"] + 2.0, 1
        )
        regla = (
            f"Subido umbral_descuento_minimo_pct a "
            f"{aprendizaje['umbral_descuento_minimo_pct']}% "
            f"tras pérdida en {ticker} con descuento insuficiente."
        )
        if regla not in aprendizaje["reglas_aprendidas"]:
            aprendizaje["reglas_aprendidas"].append(regla)

    # Ajuste de score por ticker (aprendizaje individual)
    score_ajustes = aprendizaje.setdefault("score_ajustes", {})
    current_adj   = score_ajustes.get(ticker, 0)
    if retorno < -5:
        delta = -5
    elif retorno > 10:
        delta = +3
    else:
        delta = 0
    if delta != 0:
        new_adj = max(-20, min(10, current_adj + delta))
        score_ajustes[ticker] = new_adj
        if new_adj != current_adj:
            aprendizaje["reglas_aprendidas"].append(
                f"Score de {ticker} ajustado a {new_adj:+d} pts "
                f"(retorno {retorno:+.1f}%, acumulado)."
            )

    # Win rate por sector (calculado desde performance)
    ops_sector = [
        r for r in mem["performance"]
        if r.get("sector", "desconocido") == sector and r["operaciones"] >= 1
    ]
    if ops_sector:
        total_ops  = sum(r["operaciones"] for r in ops_sector)
        total_win  = sum(r["ganadores"]   for r in ops_sector)
        win_rate   = (total_win / total_ops * 100) if total_ops > 0 else 0

        if total_ops >= 5 and win_rate < 40:
            if sector not in aprendizaje["sectores_evitar"]:
                aprendizaje["sectores_evitar"].append(sector)
                aprendizaje["sectores_sobreponderar"] = [
                    s for s in aprendizaje["sectores_sobreponderar"] if s != sector
                ]

        if total_ops >= 5 and win_rate > 70:
            if sector not in aprendizaje["sectores_sobreponderar"]:
                aprendizaje["sectores_sobreponderar"].append(sector)
                aprendizaje["sectores_evitar"] = [
                    s for s in aprendizaje["sectores_evitar"] if s != sector
                ]


# ─── Medianas de sector ────────────────────────────────────────────────────────

def guardar_mediana_sector(
    sector: str,
    pe: float,
    ev_ebitda: float,
    score_mediano: int = None,
    bloques: dict = None,
) -> None:
    """
    Agrega un snapshot de métricas medianas del sector con fecha de hoy.
    Guarda P/E, EV/EBITDA y opcionalmente score compuesto + bloques
    (valuacion, calidad, solvencia, crecimiento) para señales más ricas.
    """
    mem = load_memory()
    historial = mem["aprendizaje"]["historial_medianas_sector"]
    if sector not in historial:
        historial[sector] = []
    entry: dict = {
        "fecha":     str(date.today()),
        "pe":        pe,
        "ev_ebitda": ev_ebitda,
    }
    if score_mediano is not None:
        entry["score_mediano"] = score_mediano
    if bloques:
        entry["bloques"] = bloques
    historial[sector].append(entry)
    save_memory(mem)


# ─── Snapshots de mercado ─────────────────────────────────────────────────────

def guardar_snapshot_mercado(snapshot: dict) -> None:
    """Agrega snapshot de mercado con fecha de hoy a mem['mercado_snapshot']."""
    mem = load_memory()
    mem["mercado_snapshot"].append({"fecha": str(date.today()), **snapshot})
    save_memory(mem)


# ─── Instrumentos AR ──────────────────────────────────────────────────────────

def guardar_bono_ar(bono: dict) -> None:
    """Upsert de bono en mem['instrumentos_ar']['bonos'] por campo 'ticker'."""
    mem = load_memory()
    bonos  = mem["instrumentos_ar"]["bonos"]
    ticker = bono.get("ticker")
    idx    = next((i for i, b in enumerate(bonos) if b.get("ticker") == ticker), None)
    if idx is not None:
        bonos[idx] = {**bonos[idx], **bono}
    else:
        bonos.append(bono)
    save_memory(mem)


def guardar_letra(letra: dict) -> None:
    """Upsert de letra en mem['instrumentos_ar']['letras'] por campo 'ticker'."""
    mem    = load_memory()
    letras = mem["instrumentos_ar"]["letras"]
    ticker = letra.get("ticker")
    idx    = next((i for i, l in enumerate(letras) if l.get("ticker") == ticker), None)
    if idx is not None:
        letras[idx] = {**letras[idx], **letra}
    else:
        letras.append(letra)
    save_memory(mem)


def guardar_fondo(fondo: dict) -> None:
    """Upsert de fondo en mem['instrumentos_ar']['fondos'] por campo 'nombre'."""
    mem    = load_memory()
    fondos = mem["instrumentos_ar"]["fondos"]
    nombre = fondo.get("nombre")
    idx    = next((i for i, f in enumerate(fondos) if f.get("nombre") == nombre), None)
    if idx is not None:
        fondos[idx] = {**fondos[idx], **fondo}
    else:
        fondos.append(fondo)
    save_memory(mem)


def actualizar_cedear(ticker: str, ccl: float, brecha: float, volumen: float) -> None:
    """Upsert del CEDEAR en cedears_seguimiento por ticker."""
    mem     = load_memory()
    cedears = mem["instrumentos_ar"]["cedears_seguimiento"]
    idx     = next((i for i, c in enumerate(cedears) if c.get("ticker") == ticker), None)
    entry   = {
        "ticker":  ticker,
        "ccl":     ccl,
        "brecha":  brecha,
        "volumen": volumen,
        "fecha":   str(date.today()),
    }
    if idx is not None:
        cedears[idx] = entry
    else:
        cedears.append(entry)
    save_memory(mem)


# ─── Consultas ────────────────────────────────────────────────────────────────

def get_parametros() -> dict:
    """Retorna los parámetros operativos actuales del motor de aprendizaje."""
    mem = load_memory()
    ap  = mem["aprendizaje"]
    return {
        "umbral_descuento_minimo_pct": ap["umbral_descuento_minimo_pct"],
        "score_minimo":                ap["score_minimo"],
    }


def get_sector_valuation_signals(min_snapshots: int = 4) -> dict:
    """
    Señal compuesta por sector comparando situación actual vs promedio histórico.
    Requiere al menos min_snapshots entradas previas (+ 1 actual) por sector.

    Lógica:
      score_signal = (actual_score - hist_avg_score) / hist_avg_score
        Positivo → fundamentals mejoraron vs historia → sobreponderar
      pe_signal = (hist_avg_pe - actual_pe) / hist_avg_pe
        Positivo → sector más barato que historia → sobreponderar
      señal_final = 0.60 × score_signal + 0.40 × pe_signal
        Clampado a [-0.30, +0.30]

    Si no hay score_mediano usa solo pe_signal.
    Retorna {} si ningún sector tiene datos suficientes.
    """
    mem       = load_memory()
    historial = mem["aprendizaje"].get("historial_medianas_sector", {})
    signals: dict = {}

    for sector, snapshots in historial.items():
        pes    = [s["pe"]          for s in snapshots if s.get("pe", 0) > 0]
        scores = [s["score_mediano"] for s in snapshots if s.get("score_mediano")]

        min_needed = min_snapshots + 1
        if len(pes) < min_needed:
            continue

        current_pe  = pes[-1]
        hist_avg_pe = sum(pes[:-1]) / len(pes[:-1])
        pe_signal   = (hist_avg_pe - current_pe) / hist_avg_pe if hist_avg_pe else 0.0

        if len(scores) >= min_needed:
            current_score  = scores[-1]
            hist_avg_score = sum(scores[:-1]) / len(scores[:-1])
            score_signal   = (current_score - hist_avg_score) / hist_avg_score if hist_avg_score else 0.0
            raw = 0.60 * score_signal + 0.40 * pe_signal
        else:
            raw = pe_signal  # fallback cuando no hay scores históricos aún

        signals[sector] = round(max(-0.30, min(0.30, raw)), 4)

    return signals


def get_sector_signals_detail(min_snapshots: int = 4) -> dict:
    """
    Igual que get_sector_valuation_signals pero con desglose por bloque.
    Útil para mostrar al usuario por qué se ajustó cada sector.
    Retorna {sector: {señal, score_actual, score_hist, pe_actual, pe_hist, bloques: {...}}}.
    """
    mem       = load_memory()
    historial = mem["aprendizaje"].get("historial_medianas_sector", {})
    detail: dict = {}

    for sector, snapshots in historial.items():
        pes    = [s["pe"]           for s in snapshots if s.get("pe", 0) > 0]
        scores = [s["score_mediano"]for s in snapshots if s.get("score_mediano")]

        min_needed = min_snapshots + 1
        if len(pes) < min_needed:
            continue

        current_pe  = pes[-1]
        hist_avg_pe = sum(pes[:-1]) / len(pes[:-1])
        pe_signal   = (hist_avg_pe - current_pe) / hist_avg_pe if hist_avg_pe else 0.0

        score_signal = 0.0
        current_score = hist_avg_score = None
        if len(scores) >= min_needed:
            current_score  = scores[-1]
            hist_avg_score = sum(scores[:-1]) / len(scores[:-1])
            score_signal   = (current_score - hist_avg_score) / hist_avg_score if hist_avg_score else 0.0

        raw = round(max(-0.30, min(0.30, 0.60 * score_signal + 0.40 * pe_signal)), 4)

        # Señal por bloque (si hay datos)
        bloque_signals = {}
        for bloque in ("valuacion", "calidad", "solvencia", "crecimiento"):
            vals = [s["bloques"][bloque] for s in snapshots
                    if s.get("bloques", {}).get(bloque) is not None]
            if len(vals) >= min_needed:
                cur  = vals[-1]
                hist = sum(vals[:-1]) / len(vals[:-1])
                bloque_signals[bloque] = round((cur - hist) / hist, 4) if hist else 0.0

        detail[sector] = {
            "señal":          raw,
            "score_actual":   current_score,
            "score_hist_avg": round(hist_avg_score, 1) if hist_avg_score else None,
            "pe_actual":      round(current_pe, 1),
            "pe_hist_avg":    round(hist_avg_pe, 1),
            "bloques":        bloque_signals,
            "snapshots_n":    len(pes),
        }

    return detail


def get_score_adjustment(ticker: str) -> int:
    """Retorna el ajuste acumulado de score para el ticker (rango -20 a +10, default 0)."""
    mem = load_memory()
    return mem["aprendizaje"].get("score_ajustes", {}).get(ticker, 0)


def get_contexto_aprendizaje() -> str:
    """
    Retorna un string con el resumen del aprendizaje acumulado:
    reglas, sectores a evitar/sobreponderar, ajustes y últimos 3 patrones.
    """
    mem = load_memory()
    ap  = mem["aprendizaje"]

    reglas      = ap.get("reglas_aprendidas", [])
    evitar      = ap.get("sectores_evitar", [])
    sobre       = ap.get("sectores_sobreponderar", [])
    patrones    = ap.get("patrones_detectados", [])[-3:]
    umbral      = ap.get("umbral_descuento_minimo_pct", 10.0)
    score_min   = ap.get("score_minimo", 55)
    ajustes     = ap.get("ajustes_calidad_sector", {})

    if not any([reglas, evitar, sobre, patrones]):
        return "Sin aprendizaje registrado aún."

    lines = ["=== CONTEXTO DE APRENDIZAJE ==="]
    lines.append(f"Parámetros: umbral_descuento={umbral}% | score_mínimo={score_min}")

    if evitar:
        lines.append(f"Sectores a EVITAR: {', '.join(evitar)}")
    if sobre:
        lines.append(f"Sectores a SOBREPONDERAR: {', '.join(sobre)}")
    if ajustes:
        lines.append(f"Ajustes de calidad: {ajustes}")
    if reglas:
        lines.append("Reglas aprendidas:")
        for r in reglas:
            lines.append(f"  · {r}")
    if patrones:
        lines.append("Últimos patrones detectados:")
        for p in patrones:
            lines.append(f"  [{p['fecha']}] {p['tipo']} — {p.get('detalle', '')}")

    return "\n".join(lines)


def reporte_performance() -> str:
    """
    Tabla de performance por ticker.
    Columnas: TICKER | OPS | WIN% | RET.PROM | MEJOR | PEOR | DESC.SECTOR.PROM
    """
    mem  = load_memory()
    perf = mem.get("performance", [])

    if not perf:
        return "Sin operaciones registradas aún."

    header = (
        f"{'TICKER':<10} {'OPS':>4} {'WIN%':>6} {'RET.PROM':>9} "
        f"{'MEJOR':>7} {'PEOR':>7} {'DESC.SECTOR.PROM':>17}"
    )
    sep    = "─" * len(header)
    rows   = [header, sep]

    for r in sorted(perf, key=lambda x: x["operaciones"], reverse=True):
        ops      = r["operaciones"]
        win_pct  = round(r["ganadores"] / ops * 100, 1) if ops > 0 else 0.0
        ret_prom = r["retorno_promedio_pct"]
        mejor    = r["mejor_retorno"] if r["mejor_retorno"] is not None else 0.0
        peor_r   = r["peor_retorno"]  if r["peor_retorno"]  is not None else 0.0
        desc     = r["descuento_vs_sector_promedio_pct"]

        rows.append(
            f"{r['ticker']:<10} {ops:>4} {win_pct:>5.1f}% {ret_prom:>+8.1f}% "
            f"{mejor:>+6.1f}% {peor_r:>+6.1f}% {desc:>+16.1f}%"
        )

    return "\n".join(rows)


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mem = load_memory()
    print("Secciones:", list(mem.keys()))
    print("Parámetros:", get_parametros())
    print(get_contexto_aprendizaje())
    print("✅ memory_manager OK")
