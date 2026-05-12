"""
Asset Picker — integra scraping, filtros y scoring en un pipeline completo.
Descarga fundamentals de Finviz, aplica 3 capas de filtrado y rankea candidatos.
"""

import sys
import json
import time
from pathlib import Path

from memory_manager import (
    load_memory, get_contexto_aprendizaje,
    guardar_portfolio, guardar_mediana_sector, guardar_snapshot_mercado,
)

# Asset IDs que son ETFs — excluidos del screener de CEDEARs
_ETF_IDS = {"spy", "qqq", "vti", "iau", "gld", "eem"}
from finviz_scraper import get_ticker_data, get_tickers_sector, mapear_ratios
from filtros_fundamentals import (
    aplicar_filtros, calcular_medianas, imprimir_reporte, FiltroResultado,
)
from scoring_engine import calcular_score, ScoreResult, get_rating


# ─── Mapeo local sector Finviz → framework ───────────────────────────────────

_SECTOR_FW = {
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

def _mapear_sector(sector_finviz: str) -> str:
    return _SECTOR_FW.get(sector_finviz, "default")


# ─── Íconos de rating ─────────────────────────────────────────────────────────

_RATING_ICON = {
    "STRONG BUY":  "🟢",
    "BUY":         "🟩",
    "HOLD":        "🟡",
    "UNDERWEIGHT": "🟠",
    "AVOID":       "🔴",
}


# ─── analyze_ticker ───────────────────────────────────────────────────────────

def analyze_ticker(ticker: str, sector_hint: str = "") -> dict | None:
    """
    Analiza un ticker individual: descarga datos, calcula score y muestra
    el historial de performance si existe en memory.
    """
    mem = load_memory()

    print(f"\nObteniendo datos de {ticker}...")
    raw = get_ticker_data(ticker)
    if raw is None:
        print(f"❌ No se pudieron obtener datos para {ticker}")
        return None

    ratios = mapear_ratios(raw, ticker)

    # Si sector desconocido y hay hint, aplicarlo
    if sector_hint and ratios.get("sector_finviz", "") in ("", "Unknown", None):
        ratios["sector_finviz"]    = sector_hint
        ratios["sector_framework"] = _mapear_sector(sector_hint)

    score_r = calcular_score(ratios, mem)

    # Mostrar performance histórica si existe
    hist = next((p for p in mem.get("performance", []) if p["ticker"] == ticker), None)
    if hist and hist["operaciones"] > 0:
        ops     = hist["operaciones"]
        win_pct = round(hist["ganadores"] / ops * 100, 1)
        ret_avg = hist["retorno_promedio_pct"]
        print(f"  📊 Historial: {ops} op | Win rate {win_pct}% | Ret. prom. {ret_avg:+.1f}%")

    print(f"  Score: {score_r.score_total}/100 {score_r.rating}")
    print(f"  Bloques: VAL={score_r.bloque_valuacion} CAL={score_r.bloque_calidad} "
          f"SOL={score_r.bloque_solvencia} CRE={score_r.bloque_crecimiento} "
          f"CUA={score_r.bloque_cualitativo}")

    return {
        "ticker":            ticker,
        "sector":            ratios["sector_framework"],
        "score":             score_r.score_total,
        "rating":            score_r.rating,
        "bloques": {
            "valuacion":    score_r.bloque_valuacion,
            "calidad":      score_r.bloque_calidad,
            "solvencia":    score_r.bloque_solvencia,
            "crecimiento":  score_r.bloque_crecimiento,
            "cualitativo":  score_r.bloque_cualitativo,
        },
        "ratios": {
            "pe":            ratios.get("pe"),
            "forward_pe":    ratios.get("forward_pe"),
            "ev_ebitda":     ratios.get("ev_ebitda"),
            "peg":           ratios.get("peg"),
            "roe":           ratios.get("roe"),
            "margen_neto":   ratios.get("margen_neto"),
            "deuda_equity":  ratios.get("deuda_equity"),
            "eps_cagr_5y":   ratios.get("eps_cagr_5y"),
            "dividend_yield":ratios.get("dividend_yield"),
        },
        "ajustes_aplicados": score_r.ajustes_aplicados,
    }


# ─── run_screener ─────────────────────────────────────────────────────────────

def run_screener(sectores: list, top_n: int = 10) -> dict:
    """
    Pipeline completo: descarga tickers de Finviz por sector, calcula medianas,
    aplica filtros peers → calidad → score y rankea candidatos por score.
    """
    mem    = load_memory()
    params = mem["aprendizaje"]

    # sectores_evitar puede ser lista de strings o dicts
    raw_evitar      = params.get("sectores_evitar", [])
    sectores_evitar = [s["sector"] if isinstance(s, dict) else s for s in raw_evitar]

    todos_candidatos:      list = []
    todos_excluidos:       list = []
    sectores_sin_cands:    list = []
    medianas_usadas:       dict = {}

    for sector in sectores:
        sector_fw = _mapear_sector(sector)

        if sector_fw in sectores_evitar or sector in sectores_evitar:
            print(f"⛔ {sector} marcado para evitar — saltando")
            continue

        print(f"\n{'─'*60}")
        print(f"Analizando sector: {sector}")
        print(f"{'─'*60}")

        tickers = get_tickers_sector(sector)
        if not tickers:
            print(f"  ⚠ Sin tickers para {sector}")
            sectores_sin_cands.append(sector)
            continue

        print(f"  {len(tickers)} tickers encontrados")

        # Descargar fundamentals de todos los tickers del sector
        todos_ratios = []
        for i, ticker in enumerate(tickers):
            print(f"  [{i+1:>3}/{len(tickers)}] {ticker:<8}", end=" ", flush=True)
            raw = get_ticker_data(ticker)
            if raw is None:
                print("sin datos")
                continue
            r = mapear_ratios(raw, ticker)
            todos_ratios.append(r)
            pe_s  = f"P/E:{r['pe']:.1f}"        if r.get("pe")        else "P/E:-"
            ev_s  = f"EV:{r['ev_ebitda']:.1f}"  if r.get("ev_ebitda") else "EV:-"
            print(f"{pe_s}  {ev_s}")

        if len(todos_ratios) < 3:
            print(f"  ⚠ Menos de 3 tickers con datos en {sector} — saltando")
            sectores_sin_cands.append(sector)
            continue

        # Medianas de valuación del sector
        med_pe, med_ev = calcular_medianas(todos_ratios)
        medianas_usadas[sector] = {"pe": med_pe, "ev_ebitda": med_ev}

        pe_s = f"{med_pe:.1f}" if med_pe else "N/A"
        ev_s = f"{med_ev:.1f}" if med_ev else "N/A"
        print(f"\n  Mediana sector: P/E={pe_s} | EV/EBITDA={ev_s}")

        # Filtros + scoring por ticker
        candidatos_sector = []
        scored_results    = []   # acumula scores para mediana compuesta
        for ratios in todos_ratios:
            score_r   = calcular_score(ratios, mem)
            resultado = aplicar_filtros(ratios, score_r.score_total, med_pe, med_ev)
            scored_results.append(score_r)

            if resultado.paso_fallo is None:
                candidatos_sector.append({
                    "ticker":            ratios["ticker"],
                    "sector":            ratios["sector_framework"],
                    "score":             score_r.score_total,
                    "rating":            score_r.rating,
                    "bloque_valuacion":  score_r.bloque_valuacion,
                    "bloque_calidad":    score_r.bloque_calidad,
                    "bloque_solvencia":  score_r.bloque_solvencia,
                    "bloque_crecimiento":score_r.bloque_crecimiento,
                    "bloque_cualitativo":score_r.bloque_cualitativo,
                    "pe":                ratios.get("pe"),
                    "ev_ebitda":         ratios.get("ev_ebitda"),
                    "mediana_pe_sector": med_pe,
                    "mediana_ev_sector": med_ev,
                    "descuento_pe_pct":  resultado.descuento_pe_pct,
                    "descuento_ev_pct":  resultado.descuento_ev_pct,
                    "roe":               ratios.get("roe"),
                    "margen_neto":       ratios.get("margen_neto"),
                    "deuda_equity":      ratios.get("deuda_equity"),
                    "eps_cagr_5y":       ratios.get("eps_cagr_5y"),
                    "dividend_yield":    ratios.get("dividend_yield"),
                })
            else:
                todos_excluidos.append(resultado)

        # Guardar mediana compuesta del sector (PE + score + bloques)
        if med_pe is not None and scored_results:
            import statistics as _stats
            scrs = [r.score_total for r in scored_results]
            bloques_med = {
                "valuacion":   round(_stats.median(r.bloque_valuacion   for r in scored_results), 1),
                "calidad":     round(_stats.median(r.bloque_calidad     for r in scored_results), 1),
                "solvencia":   round(_stats.median(r.bloque_solvencia   for r in scored_results), 1),
                "crecimiento": round(_stats.median(r.bloque_crecimiento for r in scored_results), 1),
            }
            guardar_mediana_sector(
                sector_fw,
                pe           = med_pe or 0.0,
                ev_ebitda    = med_ev or 0.0,
                score_mediano= round(_stats.median(scrs)),
                bloques      = bloques_med,
            )

        if not candidatos_sector:
            sectores_sin_cands.append(sector)
        else:
            candidatos_sector.sort(key=lambda x: x["score"], reverse=True)
            todos_candidatos.extend(candidatos_sector[:top_n])
            print(f"  ✅ {len(candidatos_sector)} candidatos en {sector} "
                  f"(mostrando top {min(top_n, len(candidatos_sector))})")

    # Ranking global por score
    todos_candidatos.sort(key=lambda x: x["score"], reverse=True)

    # Snapshot del análisis
    guardar_snapshot_mercado({
        "tipo":                   "screener",
        "sectores_analizados":    sectores,
        "candidatos_encontrados": len(todos_candidatos),
        "excluidos":              len(todos_excluidos),
        "parametros": {
            "descuento_min": params.get("umbral_descuento_minimo_pct"),
            "score_min":     params.get("score_minimo"),
        },
    })

    return {
        "candidatos":              todos_candidatos,
        "excluidos":               todos_excluidos,
        "sectores_sin_candidatos": sectores_sin_cands,
        "medianas_usadas":         medianas_usadas,
        "parametros_usados": {
            "umbral_descuento_pct": params.get("umbral_descuento_minimo_pct"),
            "score_minimo":         params.get("score_minimo"),
        },
    }


# ─── imprimir_resultado_completo ─────────────────────────────────────────────

def imprimir_resultado_completo(resultado: dict) -> None:
    candidatos = resultado.get("candidatos", [])
    excluidos  = resultado.get("excluidos",  [])
    sin_cands  = resultado.get("sectores_sin_candidatos", [])
    params     = resultado.get("parametros_usados", {})

    print("\n" + "═" * 80)
    print("  SECCIÓN 1 — CONTEXTO DE APRENDIZAJE")
    print("═" * 80)
    print(get_contexto_aprendizaje())

    print("\n" + "═" * 80)
    print("  SECCIÓN 2 — CANDIDATOS")
    print("═" * 80)

    if not candidatos:
        print("  ⚠️  Sin candidatos — ningún activo pasó los 3 filtros")
    else:
        header = (
            f"  {'#':>3}  {'':2}{'TICKER':<8} {'SCORE':>5} {'RATING':<12} "
            f"{'P/E':>6} {'EV/EBITDA':>9} {'DESC.%':>7} "
            f"{'ROE':>7} {'MARGEN':>7}  SECTOR"
        )
        print(header)
        print("  " + "─" * (len(header) - 2))
        for i, c in enumerate(candidatos, 1):
            icon    = _RATING_ICON.get(c["rating"], " ")
            pe_s    = f"{c['pe']:.1f}"        if c.get("pe")           else "-"
            ev_s    = f"{c['ev_ebitda']:.1f}" if c.get("ev_ebitda")    else "-"
            roe_s   = f"{c['roe']:.1f}%"      if c.get("roe")          else "-"
            mar_s   = f"{c['margen_neto']:.1f}%" if c.get("margen_neto") else "-"
            desc_pe = c.get("descuento_pe_pct")
            desc_s  = f"{desc_pe:+.1f}%" if desc_pe is not None else "-"
            print(
                f"  {i:>3}  {icon} {c['ticker']:<8} {c['score']:>5} {c['rating']:<12} "
                f"{pe_s:>6} {ev_s:>9} {desc_s:>7} "
                f"{roe_s:>7} {mar_s:>7}  {c['sector']}"
            )

    print("\n" + "═" * 80)
    print("  SECCIÓN 3 — EXCLUIDOS")
    print("═" * 80)
    if not excluidos:
        print("  (ninguno)")
    else:
        for r in excluidos:
            etapa = f"[{r.paso_fallo}]" if r.paso_fallo else "[?]"
            print(f"  {r.ticker:<10} {etapa:<10}  {r.razon}")

    print("\n" + "═" * 80)
    print("  SECCIÓN 4 — SECTORES SIN CANDIDATOS")
    print("═" * 80)
    if not sin_cands:
        print("  Todos los sectores analizados aportaron candidatos.")
    else:
        for s in sin_cands:
            print(f"  ⚠️  {s} — ningún activo superó los 3 filtros en este sector")

    if candidatos:
        print("\n" + "═" * 80)
        print("  SECCIÓN 5 — TOP 3 PICKS")
        print("═" * 80)
        for i, c in enumerate(candidatos[:3], 1):
            icon = _RATING_ICON.get(c["rating"], "")
            print(f"\n  #{i}  {icon} {c['ticker']}  —  Score {c['score']}/100  ({c['rating']})")

            # Línea 1: fortaleza principal
            bloques = {
                "Valuación":   c["bloque_valuacion"],
                "Calidad":     c["bloque_calidad"],
                "Solvencia":   c["bloque_solvencia"],
                "Crecimiento": c["bloque_crecimiento"],
            }
            top2 = sorted(bloques.items(), key=lambda x: x[1], reverse=True)[:2]
            print(f"       Fortaleza principal: {top2[0][0]} ({top2[0][1]} pts)")
            print(f"       Segunda fortaleza:   {top2[1][0]} ({top2[1][1]} pts)")

            # Línea de contexto: descuento y ROE
            parts = []
            if c.get("descuento_pe_pct") is not None:
                parts.append(f"P/E con {c['descuento_pe_pct']:+.1f}% vs sector")
            if c.get("roe"):
                parts.append(f"ROE {c['roe']:.1f}%")
            if c.get("eps_cagr_5y"):
                parts.append(f"EPS CAGR {c['eps_cagr_5y']:.1f}%")
            if parts:
                print(f"       {' | '.join(parts)}")

    print("\n" + "═" * 80)
    print("  SECCIÓN 6 — PARÁMETROS USADOS")
    print("═" * 80)
    desc_min  = params.get("umbral_descuento_pct", "N/A")
    score_min = params.get("score_minimo", "N/A")
    print(f"  Descuento mínimo exigido vs sector : {desc_min}%")
    print(f"  Score mínimo                       : {score_min}/100")
    print("  Nota: el sistema ajusta estos parámetros automáticamente al cerrar posiciones.")

    print("\n" + "═" * 80)
    print("  SECCIÓN 7 — AVISO LEGAL")
    print("═" * 80)
    print("  Bloque cualitativo fijado en 5/10 (neutral) — Finviz no provee datos cualitativos.")
    print("  No constituye asesoramiento financiero.")
    print("═" * 80 + "\n")


# ─── guardar_resultado_json ───────────────────────────────────────────────────

def guardar_resultado_json(resultado: dict, filename: str = "asset_picks.json") -> None:
    """Guarda únicamente los candidatos en un JSON limpio."""
    candidatos = resultado.get("candidatos", [])
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(candidatos, f, indent=2, ensure_ascii=False)
    # Verificar que es parseable
    with open(filename, encoding="utf-8") as f:
        json.loads(f.read())
    print(f"✅ {len(candidatos)} candidatos guardados en {filename}")


# ─── run_cedear_screener ─────────────────────────────────────────────────────

def run_cedear_screener(top_n: int = 10) -> dict:
    """
    Pipeline completo solo sobre el universo de CEDEARs disponibles en BYMA.
    Itera ASSET_TO_FINVIZ (excluye ETFs), agrupa por sector, calcula medianas,
    aplica filtros peers → calidad → score y rankea por score.
    """
    from modules.finviz_scorer import ASSET_TO_FINVIZ

    mem    = load_memory()
    params = mem["aprendizaje"]
    raw_evitar      = params.get("sectores_evitar", [])
    sectores_evitar = [s["sector"] if isinstance(s, dict) else s for s in raw_evitar]

    # Solo CEDEARs (excluir ETFs)
    cedear_items = {
        asset_id: ticker
        for asset_id, ticker in ASSET_TO_FINVIZ.items()
        if asset_id not in _ETF_IDS
    }

    print(f"\nDescargando fundamentals de {len(cedear_items)} CEDEARs/acciones ARG...")
    ratios_por_sector: dict = {}

    for asset_id, finviz_ticker in cedear_items.items():
        print(f"  {finviz_ticker:<8}", end=" ", flush=True)
        raw = get_ticker_data(finviz_ticker)
        if raw is None:
            print("sin datos")
            continue
        r = mapear_ratios(raw, finviz_ticker)
        r["asset_id"] = asset_id
        sector = r["sector_framework"]
        ratios_por_sector.setdefault(sector, []).append(r)
        pe_s = f"P/E:{r['pe']:.1f}"       if r.get("pe")        else "P/E:-"
        ev_s = f"EV:{r['ev_ebitda']:.1f}" if r.get("ev_ebitda") else "EV:-"
        print(f"{pe_s}  {ev_s}")

    todos_candidatos:   list = []
    todos_excluidos:    list = []
    sectores_sin_cands: list = []
    medianas_usadas:    dict = {}

    for sector_fw, ratios_list in ratios_por_sector.items():
        if sector_fw in sectores_evitar:
            print(f"⛔ {sector_fw} marcado para evitar — saltando")
            continue

        print(f"\n{'─'*60}")
        print(f"Sector: {sector_fw}  ({len(ratios_list)} CEDEARs)")
        print(f"{'─'*60}")

        if len(ratios_list) < 3:
            print(f"  ⚠ Menos de 3 tickers — saltando")
            sectores_sin_cands.append(sector_fw)
            continue

        med_pe, med_ev = calcular_medianas(ratios_list)
        medianas_usadas[sector_fw] = {"pe": med_pe, "ev_ebitda": med_ev}
        pe_s = f"{med_pe:.1f}" if med_pe else "N/A"
        ev_s = f"{med_ev:.1f}" if med_ev else "N/A"
        print(f"  Mediana sector: P/E={pe_s} | EV/EBITDA={ev_s}")

        candidatos_sector = []
        scored_results    = []
        for ratios in ratios_list:
            score_r   = calcular_score(ratios, mem)
            resultado = aplicar_filtros(ratios, score_r.score_total, med_pe, med_ev)
            scored_results.append(score_r)

            if resultado.paso_fallo is None:
                candidatos_sector.append({
                    "ticker":             ratios["ticker"],
                    "asset_id":           ratios.get("asset_id", ""),
                    "sector":             ratios["sector_framework"],
                    "score":              score_r.score_total,
                    "rating":             score_r.rating,
                    "bloque_valuacion":   score_r.bloque_valuacion,
                    "bloque_calidad":     score_r.bloque_calidad,
                    "bloque_solvencia":   score_r.bloque_solvencia,
                    "bloque_crecimiento": score_r.bloque_crecimiento,
                    "bloque_cualitativo": score_r.bloque_cualitativo,
                    "pe":                 ratios.get("pe"),
                    "ev_ebitda":          ratios.get("ev_ebitda"),
                    "mediana_pe_sector":  med_pe,
                    "mediana_ev_sector":  med_ev,
                    "descuento_pe_pct":   resultado.descuento_pe_pct,
                    "descuento_ev_pct":   resultado.descuento_ev_pct,
                    "roe":                ratios.get("roe"),
                    "margen_neto":        ratios.get("margen_neto"),
                    "deuda_equity":       ratios.get("deuda_equity"),
                    "eps_cagr_5y":        ratios.get("eps_cagr_5y"),
                    "dividend_yield":     ratios.get("dividend_yield"),
                })
            else:
                todos_excluidos.append(resultado)

        # Guardar mediana compuesta del sector (PE + score + bloques)
        if med_pe is not None and scored_results:
            import statistics as _stats
            scrs = [r.score_total for r in scored_results]
            bloques_med = {
                "valuacion":   round(_stats.median(r.bloque_valuacion   for r in scored_results), 1),
                "calidad":     round(_stats.median(r.bloque_calidad     for r in scored_results), 1),
                "solvencia":   round(_stats.median(r.bloque_solvencia   for r in scored_results), 1),
                "crecimiento": round(_stats.median(r.bloque_crecimiento for r in scored_results), 1),
            }
            guardar_mediana_sector(
                sector_fw,
                pe           = med_pe or 0.0,
                ev_ebitda    = med_ev or 0.0,
                score_mediano= round(_stats.median(scrs)),
                bloques      = bloques_med,
            )

        if not candidatos_sector:
            sectores_sin_cands.append(sector_fw)
        else:
            candidatos_sector.sort(key=lambda x: x["score"], reverse=True)
            todos_candidatos.extend(candidatos_sector[:top_n])
            print(f"  ✅ {len(candidatos_sector)} candidatos (mostrando top {min(top_n, len(candidatos_sector))})")

    todos_candidatos.sort(key=lambda x: x["score"], reverse=True)

    guardar_snapshot_mercado({
        "tipo":                   "cedear_screener",
        "cedears_analizados":     len(cedear_items),
        "candidatos_encontrados": len(todos_candidatos),
        "excluidos":              len(todos_excluidos),
        "parametros": {
            "descuento_min": params.get("umbral_descuento_minimo_pct"),
            "score_min":     params.get("score_minimo"),
        },
    })

    return {
        "candidatos":              todos_candidatos,
        "excluidos":               todos_excluidos,
        "sectores_sin_candidatos": sectores_sin_cands,
        "medianas_usadas":         medianas_usadas,
        "parametros_usados": {
            "umbral_descuento_pct": params.get("umbral_descuento_minimo_pct"),
            "score_minimo":         params.get("score_minimo"),
        },
    }


# ─── update_cedear_scores ─────────────────────────────────────────────────────

def update_cedear_scores(scores_path: str = "finviz_scores.json") -> None:
    """
    Re-scorea todos los CEDEARs usando scoring_engine y sobreescribe finviz_scores.json.
    Preserva los scores de ETFs sin tocarlos.
    """
    from modules.finviz_scorer import ASSET_TO_FINVIZ

    scores_file = Path(scores_path)
    mem = load_memory()

    existing: dict = {}
    if scores_file.exists():
        with open(scores_file, encoding="utf-8") as f:
            existing = json.load(f)

    etf_scores  = existing.get("etf_scores", {})
    by_asset_id = {}
    by_ticker   = {}

    # Preservar scores de ETFs del JSON existente
    for asset_id in _ETF_IDS:
        prev = existing.get("by_asset_id", {}).get(asset_id)
        if prev:
            by_asset_id[asset_id] = prev
            finviz_ticker = ASSET_TO_FINVIZ.get(asset_id, asset_id.upper())
            by_ticker[finviz_ticker] = prev

    cedear_items = {
        asset_id: ticker
        for asset_id, ticker in ASSET_TO_FINVIZ.items()
        if asset_id not in _ETF_IDS
    }

    print(f"\nActualizando {len(cedear_items)} scores con scoring_engine...")
    for asset_id, finviz_ticker in cedear_items.items():
        print(f"  {finviz_ticker:<8}", end=" ", flush=True)
        raw = get_ticker_data(finviz_ticker)
        if raw is None:
            print("sin datos")
            continue

        r       = mapear_ratios(raw, finviz_ticker)
        score_r = calcular_score(r, mem)

        entry = {
            "score":  score_r.score_total,
            "rating": score_r.rating,
            "sector": score_r.sector,
            "bloques": {
                "valuacion":   score_r.bloque_valuacion,
                "calidad":     score_r.bloque_calidad,
                "solvencia":   score_r.bloque_solvencia,
                "crecimiento": score_r.bloque_crecimiento,
                "cualitativo": score_r.bloque_cualitativo,
            },
        }
        by_asset_id[asset_id]    = entry
        by_ticker[finviz_ticker] = entry
        adj_list = score_r.ajustes_aplicados
        adj_s    = f" {adj_list[0]}" if adj_list else ""
        print(f"score={score_r.score_total} {score_r.rating}{adj_s}")

    output = {
        "by_asset_id": by_asset_id,
        "by_ticker":   by_ticker,
        "etf_scores":  etf_scores,
    }
    with open(scores_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n✅ {len(by_asset_id)} scores escritos en {scores_path}")


# ─── Entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    args = sys.argv[1:]

    if not args:
        print("Uso:")
        print("  python asset_picker.py SECTOR1 SECTOR2 ... [top_n]  — screener US por sector")
        print("  python asset_picker.py cedears [top_n]              — screener solo CEDEARs BYMA")
        print("  python asset_picker.py update_scores                — actualiza finviz_scores.json")
        sys.exit(0)

    if args[0] == "update_scores":
        update_cedear_scores()
        sys.exit(0)

    if args[0] == "cedears":
        top_n = int(args[1]) if len(args) > 1 else 10
        resultado = run_cedear_screener(top_n)
        imprimir_resultado_completo(resultado)
        guardar_resultado_json(resultado, "cedear_picks.json")
        sys.exit(0)

    # Screener US por sector (comportamiento original)
    try:
        top_n    = int(args[-1])
        sectores = args[:-1]
    except ValueError:
        top_n    = 10
        sectores = args

    if not sectores:
        sectores = ["Technology"]

    resultado = run_screener(sectores, top_n)
    imprimir_resultado_completo(resultado)
    guardar_resultado_json(resultado)
