"""
Filtros de fundamentals para selección de activos.
Aplica tres capas en orden: peers → calidad → score.
Al primer fallo retorna inmediatamente con la razón específica.
"""

import statistics
from dataclasses import dataclass, field
from typing import Optional

from memory_manager import get_parametros, guardar_mediana_sector


# ─── Umbrales por sector ──────────────────────────────────────────────────────

_ROE_MIN = {
    "tecnologia": 16, "bancos": 10, "energia": 8, "utilities": 7,
    "consumo_defensivo": 12, "consumo_discrecional": 9, "salud": 12,
    "industriales": 10, "materiales": 8, "telecom": 7,
    "transporte": 6, "default": 8,
}

_MARGEN_NETO_MIN = {
    "tecnologia": 10, "bancos": 12, "energia": 5, "utilities": 5,
    "consumo_defensivo": 6, "consumo_discrecional": 4, "salud": 10,
    "industriales": 4, "materiales": 4, "telecom": 4,
    "transporte": 2, "default": 4,
}

_DEUDA_EQ_MAX = {
    "tecnologia": 2.0, "bancos": 999, "energia": 2.0, "utilities": 4.0,
    "consumo_defensivo": 2.0, "consumo_discrecional": 3.0, "salud": 3.0,
    "industriales": 2.5, "materiales": 2.0, "telecom": 3.5,
    "transporte": 4.0, "default": 2.0,
}


# ─── Dataclass resultado ──────────────────────────────────────────────────────

@dataclass
class FiltroResultado:
    ticker:                  str
    paso_fallo:              Optional[str]    # "peers" | "calidad" | "score" | None si pasó
    razon:                   str
    pe:                      Optional[float]
    ev_ebitda:               Optional[float]
    mediana_pe_sector:       Optional[float]
    mediana_ev_sector:       Optional[float]
    descuento_pe_pct:        Optional[float]
    descuento_ev_pct:        Optional[float]
    roe:                     Optional[float]
    margen_neto:             Optional[float]
    deuda_equity:            Optional[float]
    score:                   Optional[int]    = None


# ─── Medianas ─────────────────────────────────────────────────────────────────

def calcular_medianas(lista_ratios: list) -> tuple:
    """
    Calcula medianas de P/E y EV/EBITDA del universo de peers.
    Ignora None, negativos y ceros. Requiere mínimo 3 valores válidos.
    Retorna (mediana_pe, mediana_ev) o (None, None) si hay menos de 3.
    """
    pes = [r["pe"] for r in lista_ratios
           if r.get("pe") is not None and r["pe"] > 0]
    evs = [r["ev_ebitda"] for r in lista_ratios
           if r.get("ev_ebitda") is not None and r["ev_ebitda"] > 0]

    med_pe = statistics.median(pes) if len(pes) >= 3 else None
    med_ev = statistics.median(evs) if len(evs) >= 3 else None

    return med_pe, med_ev


# ─── Filtro 1: peers ──────────────────────────────────────────────────────────

def filtro_peers(
    ratios: dict,
    mediana_pe: Optional[float],
    mediana_ev: Optional[float],
) -> FiltroResultado:
    """
    Compara P/E y EV/EBITDA del activo contra la mediana de su sector.
    Para bancos usa P/B en lugar de EV/EBITDA.
    PASA si al menos una comparación verificable resulta favorable.
    """
    ticker  = ratios["ticker"]
    sector  = ratios["sector_framework"]
    pe      = ratios.get("pe")
    roe     = ratios.get("roe")
    margen  = ratios.get("margen_neto")
    deuda   = ratios.get("deuda_equity")

    # Bancos: P/B sustituye a EV/EBITDA
    ev = ratios.get("pb") if sector == "bancos" else ratios.get("ev_ebitda")

    # Descuentos (positivo = más barato que la mediana)
    desc_pe = (
        round((mediana_pe - pe) / mediana_pe * 100, 1)
        if (pe is not None and mediana_pe and mediana_pe != 0) else None
    )
    desc_ev = (
        round((mediana_ev - ev) / mediana_ev * 100, 1)
        if (ev is not None and mediana_ev and mediana_ev != 0) else None
    )

    kwargs = dict(
        ticker=ticker, pe=pe, ev_ebitda=ev,
        mediana_pe_sector=mediana_pe, mediana_ev_sector=mediana_ev,
        descuento_pe_pct=desc_pe, descuento_ev_pct=desc_ev,
        roe=roe, margen_neto=margen, deuda_equity=deuda,
    )

    # Sin medianas suficientes → pasar sin comparar
    if mediana_pe is None and mediana_ev is None:
        return FiltroResultado(**kwargs,
            paso_fallo=None, razon="Sin peers suficientes para comparar")

    # Construir lista de checks verificables
    checks = []
    if pe is not None and mediana_pe is not None:
        checks.append(("pe",  pe  < mediana_pe,  pe,  mediana_pe))
    if ev is not None and mediana_ev is not None:
        checks.append(("ev", ev < mediana_ev, ev, mediana_ev))

    if not checks:
        return FiltroResultado(**kwargs,
            paso_fallo=None, razon="Sin datos de valuación para comparar con peers")

    # Al menos una pasa → OK
    if any(ok for _, ok, *_ in checks):
        return FiltroResultado(**kwargs, paso_fallo=None, razon="OK peers")

    # Todas fallan → excluir
    partes = []
    for name, _, val, med in checks:
        label = "P/E" if name == "pe" else "EV/EBITDA"
        partes.append(f"{label} {val:.1f} vs mediana {med:.1f}")
    return FiltroResultado(**kwargs,
        paso_fallo="peers", razon=" | ".join(partes))


# ─── Filtro 2: calidad ────────────────────────────────────────────────────────

def filtro_calidad(ratios: dict) -> FiltroResultado:
    """
    Verifica ROE, margen neto y deuda/equity contra umbrales del sector.
    Si el dato es None, se omite esa verificación.
    Si los tres son None, pasa con nota.
    """
    ticker  = ratios["ticker"]
    sector  = ratios["sector_framework"]
    roe     = ratios.get("roe")
    margen  = ratios.get("margen_neto")
    deuda   = ratios.get("deuda_equity")

    kwargs = dict(
        ticker=ticker, pe=ratios.get("pe"),
        ev_ebitda=ratios.get("ev_ebitda"),
        mediana_pe_sector=None, mediana_ev_sector=None,
        descuento_pe_pct=None, descuento_ev_pct=None,
        roe=roe, margen_neto=margen, deuda_equity=deuda,
    )

    if roe is None and margen is None and deuda is None:
        return FiltroResultado(**kwargs,
            paso_fallo=None, razon="Sin datos de calidad disponibles")

    roe_min   = _ROE_MIN.get(sector,       _ROE_MIN["default"])
    mar_min   = _MARGEN_NETO_MIN.get(sector, _MARGEN_NETO_MIN["default"])
    deu_max   = _DEUDA_EQ_MAX.get(sector,  _DEUDA_EQ_MAX["default"])

    if roe is not None and roe < roe_min:
        return FiltroResultado(**kwargs,
            paso_fallo="calidad",
            razon=f"ROE {roe:.1f}% insuficiente (mínimo {roe_min}% para {sector})")

    if margen is not None and margen < mar_min:
        return FiltroResultado(**kwargs,
            paso_fallo="calidad",
            razon=f"Margen neto {margen:.1f}% insuficiente (mínimo {mar_min}% para {sector})")

    if deuda is not None and deuda > deu_max:
        return FiltroResultado(**kwargs,
            paso_fallo="calidad",
            razon=f"Deuda/Equity {deuda:.2f} excede máximo {deu_max} para {sector}")

    return FiltroResultado(**kwargs, paso_fallo=None, razon="OK calidad")


# ─── Filtro 3: score ──────────────────────────────────────────────────────────

def filtro_score(score: int, ticker: str = "") -> FiltroResultado:
    """Verifica que el score Finviz supere el mínimo del perfil de aprendizaje."""
    params    = get_parametros()
    score_min = params["score_minimo"]

    kwargs = dict(
        ticker=ticker, pe=None, ev_ebitda=None,
        mediana_pe_sector=None, mediana_ev_sector=None,
        descuento_pe_pct=None, descuento_ev_pct=None,
        roe=None, margen_neto=None, deuda_equity=None,
        score=score,
    )

    if score < score_min:
        return FiltroResultado(**kwargs,
            paso_fallo="score",
            razon=f"Score {score}/100 menor al mínimo {score_min}")

    return FiltroResultado(**kwargs, paso_fallo=None, razon="OK score")


# ─── Pipeline completo ────────────────────────────────────────────────────────

def aplicar_filtros(
    ratios: dict,
    score: int,
    mediana_pe: Optional[float],
    mediana_ev: Optional[float],
) -> FiltroResultado:
    """
    Aplica los tres filtros en orden: peers → calidad → score.
    Al primer fallo retorna ese FiltroResultado inmediatamente.
    Si los tres pasan, retorna FiltroResultado con paso_fallo=None y razon="OK".
    """
    ticker = ratios["ticker"]

    # 1 — Peers
    res = filtro_peers(ratios, mediana_pe, mediana_ev)
    if res.paso_fallo is not None:
        return res

    # 2 — Calidad
    res = filtro_calidad(ratios)
    if res.paso_fallo is not None:
        return res

    # 3 — Score
    res = filtro_score(score, ticker=ticker)
    if res.paso_fallo is not None:
        return res

    # Todo OK
    roe   = ratios.get("roe")
    margen = ratios.get("margen_neto")
    deuda  = ratios.get("deuda_equity")
    pe     = ratios.get("pe")
    ev     = ratios.get("pb") if ratios["sector_framework"] == "bancos" else ratios.get("ev_ebitda")
    desc_pe = (
        round((mediana_pe - pe) / mediana_pe * 100, 1)
        if (pe is not None and mediana_pe and mediana_pe != 0) else None
    )
    desc_ev = (
        round((mediana_ev - ev) / mediana_ev * 100, 1)
        if (ev is not None and mediana_ev and mediana_ev != 0) else None
    )

    return FiltroResultado(
        ticker=ticker, paso_fallo=None, razon="OK",
        pe=pe, ev_ebitda=ev,
        mediana_pe_sector=mediana_pe, mediana_ev_sector=mediana_ev,
        descuento_pe_pct=desc_pe, descuento_ev_pct=desc_ev,
        roe=roe, margen_neto=margen, deuda_equity=deuda,
        score=score,
    )


# ─── Reporte ──────────────────────────────────────────────────────────────────

def _rating(score: Optional[int]) -> str:
    if score is None:    return "-"
    if score >= 80:      return "STRONG BUY"
    elif score >= 65:    return "BUY"
    elif score >= 50:    return "HOLD"
    elif score >= 35:    return "UNDERWEIGHT"
    else:                return "AVOID"


def imprimir_reporte(candidatos: list, excluidos: list) -> None:
    """
    Imprime tabla de candidatos y lista de excluidos con sus razones.
    """
    print("\n" + "═" * 80)
    print("  CANDIDATOS")
    print("═" * 80)

    if not candidatos:
        print("  ⚠️  Sin candidatos en este sector")
    else:
        header = (
            f"  {'#':>3}  {'TICKER':<10} {'P/E':>6} {'EV/EBITDA':>10} "
            f"{'DESC.SECTOR%':>13} {'ROE':>7} {'MARGEN':>7} {'SCORE':>6}  RATING"
        )
        print(header)
        print("  " + "─" * (len(header) - 2))
        for i, c in enumerate(candidatos, 1):
            pe_s   = f"{c['pe']:.1f}"      if c.get("pe")           else "-"
            ev_s   = f"{c.get('ev_ebitda', c.get('pb')):.1f}" if (c.get("ev_ebitda") or c.get("pb")) else "-"
            roe_s  = f"{c['roe']:.1f}%"    if c.get("roe")          else "-"
            mar_s  = f"{c.get('margen_neto'):.1f}%" if c.get("margen_neto") else "-"
            sc     = c.get("score")
            sc_s   = str(sc) if sc is not None else "-"
            # Descuento vs sector: mostrar si está disponible en el dict
            desc_s = f"{c['descuento_pe_pct']:+.1f}%" if c.get("descuento_pe_pct") is not None else "-"
            print(
                f"  {i:>3}  {c['ticker']:<10} {pe_s:>6} {ev_s:>10} "
                f"{desc_s:>13} {roe_s:>7} {mar_s:>7} {sc_s:>6}  {_rating(sc)}"
            )

    print("\n" + "═" * 80)
    print("  EXCLUIDOS")
    print("═" * 80)
    if not excluidos:
        print("  (ninguno)")
    else:
        for r in excluidos:
            etapa = f"[{r.paso_fallo}]" if r.paso_fallo else "[?]"
            print(f"  {r.ticker:<10} {etapa:<10}  {r.razon}")
    print("═" * 80 + "\n")


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # 5 activos mock: 2 pasan, 3 fallan por distintas razones
    mocks = [
        {"ticker":"ACT-A","sector_framework":"tecnologia","pe":18.0,"ev_ebitda":14.0,
         "pb":3.1,"roe":22.0,"margen_neto":18.0,"deuda_equity":0.4,"eps_cagr_5y":14.0,
         "ventas_cagr_5y":11.0,"eps_qoq":8.0,"dividend_yield":0.8},
        {"ticker":"ACT-B","sector_framework":"tecnologia","pe":22.0,"ev_ebitda":17.0,
         "pb":4.2,"roe":19.0,"margen_neto":15.0,"deuda_equity":0.6,"eps_cagr_5y":10.0,
         "ventas_cagr_5y":8.0,"eps_qoq":5.0,"dividend_yield":1.1},
        {"ticker":"EXC-1","sector_framework":"tecnologia","pe":35.0,"ev_ebitda":28.0,
         "pb":8.0,"roe":25.0,"margen_neto":20.0,"deuda_equity":0.3},  # caro vs sector
        {"ticker":"EXC-2","sector_framework":"tecnologia","pe":19.0,"ev_ebitda":15.0,
         "pb":3.5,"roe":5.0,"margen_neto":3.0,"deuda_equity":0.5},    # baja calidad
        {"ticker":"EXC-3","sector_framework":"tecnologia","pe":20.0,"ev_ebitda":16.0,
         "pb":3.8,"roe":18.0,"margen_neto":14.0,"deuda_equity":0.4},  # score bajo
    ]
    # mediana del sector simulada
    med_pe, med_ev = 26.0, 21.0
    print(f"Mediana del sector: P/E={med_pe} | EV/EBITDA={med_ev}\n")

    candidatos, excluidos = [], []
    for r in mocks:
        score_simulado = 62 if r["ticker"] in ("ACT-A", "ACT-B") else 40
        res = aplicar_filtros(r, score_simulado, med_pe, med_ev)
        if res.paso_fallo is None:
            candidatos.append({**r, "score": score_simulado})
        else:
            excluidos.append(res)

    imprimir_reporte(candidatos, excluidos)
    print("✅ filtros_fundamentals OK")
