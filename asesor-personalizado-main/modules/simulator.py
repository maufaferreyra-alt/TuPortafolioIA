"""
Módulo de simulación de cartera
Implementa simulación de trayectoria con escenarios: optimista, base y pesimista.
También incluye Monte Carlo simplificado.
"""

import numpy as np
from typing import Dict, Any


def comparar_vs_alternativas(
    capital_usd: float,
    years: int,
    portfolio_cagr: float,
) -> Dict[str, Any]:
    """
    Compara el portafolio contra plazo fijo y dólares en el colchón.
    Todos los valores en USD (poder adquisitivo real).

    Supuestos:
      - Plazo fijo ARS: tasa nominal alta pero inflación mayor → real ≈ 1% anual en USD
      - Dólares en el colchón: 0% nominal, pierden contra inflación global (~2.5%/año)
      - Inflación global: 2.5% anual (reduce poder adquisitivo del colchón)
    """
    t = np.arange(0, years + 1)

    portfolio_vals = capital_usd * (1 + portfolio_cagr) ** t
    pf_vals        = capital_usd * (1 + 0.01) ** t          # plazo fijo ~1% real en USD
    colchon_vals   = capital_usd * (1 - 0.025) ** t         # dólares pierden vs inflación global

    return {
        "years":     t.tolist(),
        "portfolio": portfolio_vals.tolist(),
        "pf":        pf_vals.tolist(),
        "colchon":   colchon_vals.tolist(),
        "diferencia_vs_pf":      round(portfolio_vals[-1] - pf_vals[-1], 0),
        "diferencia_vs_colchon": round(portfolio_vals[-1] - colchon_vals[-1], 0),
        "portfolio_final":       round(portfolio_vals[-1], 0),
        "pf_final":              round(pf_vals[-1], 0),
        "colchon_final":         round(colchon_vals[-1], 0),
    }


def proyectar_con_aportes(
    capital_usd: float,
    aporte_mensual_usd: float,
    years: int,
    cagr: float,
) -> Dict[str, Any]:
    """
    Proyecta el capital final con aportes mensuales.
    FV = PV*(1+r)^n + PMT * ((1+r)^n - 1) / r   (r mensual)
    """
    r_mensual = (1 + cagr) ** (1 / 12) - 1
    n_meses   = years * 12

    meses      = np.arange(0, n_meses + 1)
    sin_aporte = capital_usd * (1 + r_mensual) ** meses

    # Con aportes: capital inicial + valor futuro de anualidad
    if r_mensual > 0:
        fv_aportes = aporte_mensual_usd * ((1 + r_mensual) ** meses - 1) / r_mensual
    else:
        fv_aportes = aporte_mensual_usd * meses

    con_aporte   = sin_aporte + fv_aportes
    total_aportado = capital_usd + aporte_mensual_usd * n_meses

    # Reducir a puntos anuales para el gráfico
    años_idx = list(range(0, years + 1))
    sin_anual = [float(sin_aporte[m * 12]) for m in años_idx]
    con_anual = [float(con_aporte[m * 12]) for m in años_idx]

    return {
        "años":           años_idx,
        "sin_aporte":     sin_anual,
        "con_aporte":     con_anual,
        "final_sin":      round(float(sin_aporte[-1]), 0),
        "final_con":      round(float(con_aporte[-1]), 0),
        "total_aportado": round(total_aportado, 0),
        "ganancia_extra": round(float(con_aporte[-1]) - total_aportado, 0),
    }


def simulate_portfolio(
    portfolio: dict,
    years: int = 5,
    initial_capital: float = 10_000,
    custom_cagr: float | None = None,
    custom_vol: float | None = None,
    n_simulations: int = 200,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Simula la evolución del portafolio a lo largo del tiempo.

    Retorna:
        - scenarios: dict con arrays de valores para 'base', 'optimista', 'pesimista'
        - monte_carlo: percentiles de las simulaciones MC
        - years_axis: eje temporal
        - summary: estadísticas clave
    """
    rng = np.random.default_rng(seed)

    cagr = custom_cagr if custom_cagr is not None else portfolio["expected_cagr"]
    vol  = custom_vol  if custom_vol  is not None else portfolio["expected_volatility"]

    # Convertir horizonte a puntos mensuales
    months = years * 12
    t = np.linspace(0, years, months + 1)
    dt = 1 / 12  # paso mensual

    # ── Escenarios deterministas — interés compuesto anual (1+r)^t ───────────
    base = initial_capital * (1 + cagr) ** t

    optimistic_cagr = cagr + vol * 0.5
    optimista = initial_capital * (1 + optimistic_cagr) ** t

    pessimistic_cagr = max(cagr - vol * 0.7, -0.30)
    pesimista = initial_capital * (1 + pessimistic_cagr) ** t

    # ── Monte Carlo ────────────────────────────────────────────────────────────
    mu  = cagr - 0.5 * vol ** 2
    sig = vol

    paths = np.zeros((n_simulations, months + 1))
    paths[:, 0] = initial_capital

    for s in range(n_simulations):
        z = rng.standard_normal(months)
        log_returns = mu * dt + sig * np.sqrt(dt) * z
        paths[s, 1:] = initial_capital * np.exp(np.cumsum(log_returns))

    p10 = np.percentile(paths, 10, axis=0)
    p25 = np.percentile(paths, 25, axis=0)
    p50 = np.percentile(paths, 50, axis=0)
    p75 = np.percentile(paths, 75, axis=0)
    p90 = np.percentile(paths, 90, axis=0)

    # ── Métricas resumen ───────────────────────────────────────────────────────
    prob_positive = float(np.mean(paths[:, -1] > initial_capital))
    prob_double   = float(np.mean(paths[:, -1] > initial_capital * 2))
    prob_loss_20  = float(np.mean(paths[:, -1] < initial_capital * 0.80))
    median_final  = float(np.median(paths[:, -1]))
    mean_final    = float(np.mean(paths[:, -1]))
    worst_final   = float(np.percentile(paths[:, -1], 5))
    best_final    = float(np.percentile(paths[:, -1], 95))

    return {
        "scenarios": {
            "base":      base.tolist(),
            "optimista": optimista.tolist(),
            "pesimista": pesimista.tolist(),
        },
        "monte_carlo": {
            "p10": p10.tolist(),
            "p25": p25.tolist(),
            "p50": p50.tolist(),
            "p75": p75.tolist(),
            "p90": p90.tolist(),
        },
        "years_axis": t.tolist(),
        "summary": {
            "prob_positive": prob_positive,
            "prob_double":   prob_double,
            "prob_loss_20":  prob_loss_20,
            "median_final":  median_final,
            "mean_final":    mean_final,
            "worst_final":   worst_final,
            "best_final":    best_final,
            "cagr_used":     cagr,
            "vol_used":      vol,
        },
        "n_simulations": n_simulations,
        "years":         years,
        "initial_capital": initial_capital,
    }
