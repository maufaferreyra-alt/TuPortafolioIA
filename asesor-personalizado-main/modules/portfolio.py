"""
Motor de construcción de carteras
Genera asignaciones diversificadas según perfil de riesgo,
con activos del mercado argentino e internacional.
"""

from typing import List, Dict, Any
from modules.finviz_scorer import (
    load_scores as load_equity_scores,
    load_asset_sectors,
    load_full_data as load_equity_full,
    return_factor, vol_factor, MIN_SCORE_BY_RISK,
    apply_argentina_adjustment,
)
from modules.bond_scorer import (
    load_scores as load_bond_scores,
    load_scores_live as _load_bond_live,
    get_active_lecap,
    BOND_DEFS,
    _implied_sovereign_tir,
    _ON_CREDIT_SPREADS_BPS,
)


# ─── Universo de activos ───────────────────────────────────────────────────────
ASSET_UNIVERSE: List[Dict[str, Any]] = [

    # ══ PESOS ARGENTINOS — baja volatilidad ════════════════════════════════════

    {
        "id": "cash_pesos",
        "name": "Cuenta Remunerada (Naranja X / Ualá)",
        "category": "Pesos ARS",
        "sub": "Liquidez",
        "ticker": "ARS",
        "color": "#94a3b8",
        "expected_return": 0.03,
        "volatility": 0.01,
        "risk_level": "mínimo",
        "description": "Capital disponible en todo momento en cuentas como Naranja X o Ualá que pagan interés diario automático. El dinero rinde solo mientras está depositado. Rescatable sin penalidades ni plazos mínimos.",
        "currency": "ARS",
        "market": "Banco",
        "simple_desc": "Dinero en Naranja X o Ualá rindiendo interés diario, retiro inmediato",
    },
    {
        "id": "money_market",
        "name": "Fondo Money Market (Consultatio / Balanz)",
        "category": "Pesos ARS",
        "sub": "Fondos CLP",
        "ticker": "FCI-MM",
        "color": "#a3e635",
        "expected_return": 0.05,
        "volatility": 0.01,
        "risk_level": "mínimo",
        "description": "Fondos como Consultatio Money Market (disponible en IOL) o Balanz Money Market. Invierten en plazos fijos bancarios y letras de cortísimo plazo. Retiro el mismo día, rinden más que un plazo fijo tradicional. También accesible desde Mercado Pago o Ualá como 'cuenta de inversión'.",
        "currency": "ARS",
        "market": "FCI",
        "simple_desc": "Consultatio o Balanz Money Market: retiro el mismo día, más que un plazo fijo",
    },
    {
        "id": "plazo_fijo",
        "name": "Plazo Fijo 30 días (Banco Galicia / Santander)",
        "category": "Pesos ARS",
        "sub": "Ahorro bancario",
        "ticker": "PF",
        "color": "#84cc16",
        "expected_return": 0.06,
        "volatility": 0.02,
        "risk_level": "mínimo",
        "description": "Plazo fijo a 30 días en bancos como Galicia, Santander o BBVA. Tasa fija garantizada, sin riesgo de precio. Cubierto por el Fondo de Garantía de Depósitos hasta $20 millones. El capital no puede retirarse antes del vencimiento.",
        "currency": "ARS",
        "market": "Banco",
        "simple_desc": "Plazo fijo 30 días en Galicia o Santander, garantizado por el banco",
    },
    {
        "id": "fci_t0",
        "name": "Fondo Renta Fija T+0 (Balanz / PPI)",
        "category": "Pesos ARS",
        "sub": "Fondos CLP",
        "ticker": "FCI-T0",
        "color": "#65a30d",
        "expected_return": 0.07,
        "volatility": 0.02,
        "risk_level": "muy bajo",
        "description": "Fondos como Balanz Renta Fija o el fondo T+0 de PPI. Invierten en letras y bonos de corto plazo en pesos. Retiro el mismo día hábil. Un escalón más de rendimiento que el money market puro, con riesgo casi igual.",
        "currency": "ARS",
        "market": "FCI",
        "simple_desc": "Balanz o PPI Renta Fija: retiro el mismo día, mejor rendimiento que money market",
    },
    {
        "id": "lecap",
        "name": "LECAP del Tesoro (ticker vigente)",
        "category": "Pesos ARS",
        "sub": "Deuda Pública ARS",
        "ticker": "LECAP",
        "color": "#4ade80",
        "expected_return": 0.08,
        "volatility": 0.04,
        "risk_level": "bajo",
        "description": "Letra Capitalizable del Tesoro argentino a tasa fija. Se adquiere en IOL, PPI o Balanz. Riesgo: contraparte soberana argentina.",
        "currency": "ARS",
        "market": "BYMA",
        "simple_desc": "Letra del Tesoro a tasa fija — ticker y vencimiento actualizados automáticamente",
    },
    {
        "id": "cer_tx26",
        "name": "Bono CER TX26 (ajusta por inflación)",
        "category": "Bonos CER",
        "sub": "Soberano ARG / Inflación",
        "ticker": "TX26",
        "color": "#06b6d4",
        "expected_return": 0.06,
        "volatility": 0.08,
        "risk_level": "bajo",
        "description": "TX26 (vence 2026): bono del Tesoro ajustado por inflación (CER). Si la inflación sube, su valor también sube. Ideal para proteger pesos en horizonte corto. ¿Qué es un bono CER? Imaginá que prestás plata al gobierno argentino hoy. En vez de devolverte la misma cantidad de pesos, te devuelve esa cantidad más lo que subió la inflación. Es una forma de que tus pesos no pierdan valor.",
        "currency": "ARS",
        "market": "BYMA",
        "liquidity": "alta",
        "max_weight_by_profile": {"conservador": 0.20, "estable": 0.20, "moderado": 0.15, "agresivo": 0.08},
        "fecha_inclusion": "2026-05-03",
        "fecha_revision": "2026-08-01",
        "fuente_retorno": "TIR BYMA / Rava Bursátil",
        "activo": True,
        "nota_analista": "Buena opción para proteger pesos contra inflación en horizonte corto",
        "simple_desc": "TX26: bono que sube con la inflación, vence 2026, comprá en IOL o PPI",
    },
    {
        "id": "cer_tx28",
        "name": "Bono CER TX28 (ajusta por inflación)",
        "category": "Bonos CER",
        "sub": "Soberano ARG / Inflación",
        "ticker": "TX28",
        "color": "#06b6d4",
        "expected_return": 0.07,
        "volatility": 0.09,
        "risk_level": "bajo-medio",
        "description": "TX28 (vence julio 2028): bono del Tesoro ajustado por inflación (CER) con algo más de rendimiento que TX26. Horizonte ideal 3-5 años. ¿Qué es un bono CER? Imaginá que prestás plata al gobierno argentino hoy. En vez de devolverte la misma cantidad de pesos, te devuelve esa cantidad más lo que subió la inflación. Es una forma de que tus pesos no pierdan valor.",
        "currency": "ARS",
        "market": "BYMA",
        "liquidity": "alta",
        "max_weight_by_profile": {"conservador": 0.20, "estable": 0.20, "moderado": 0.15, "agresivo": 0.08},
        "fecha_inclusion": "2026-05-03",
        "fecha_revision": "2026-08-01",
        "fuente_retorno": "TIR BYMA / Rava Bursátil",
        "activo": True,
        "nota_analista": "Complemento ideal para TX26 en carteras con horizonte 3-5 años",
        "simple_desc": "TX28: bono que sube con la inflación, vence julio 2028, comprá en IOL o PPI",
    },
    {
        "id": "cer_dicp",
        "name": "Bono DICP (CER largo plazo)",
        "category": "Bonos CER",
        "sub": "Soberano ARG / Inflación",
        "ticker": "DICP",
        "color": "#06b6d4",
        "expected_return": 0.08,
        "volatility": 0.12,
        "risk_level": "medio",
        "description": "DICP: bono del Tesoro ajustado por inflación (CER) de largo plazo. Mayor rendimiento pero más sensible a cambios de tasas. ¿Qué es un bono CER? Imaginá que prestás plata al gobierno argentino hoy. En vez de devolverte la misma cantidad de pesos, te devuelve esa cantidad más lo que subió la inflación. Es una forma de que tus pesos no pierdan valor.",
        "currency": "ARS",
        "market": "BYMA",
        "liquidity": "media",
        "max_weight_by_profile": {"conservador": 0.20, "estable": 0.20, "moderado": 0.15, "agresivo": 0.08},
        "fecha_inclusion": "2026-05-03",
        "fecha_revision": "2026-08-01",
        "fuente_retorno": "TIR BYMA / Rava Bursátil",
        "activo": True,
        "nota_analista": "Solo para horizonte mayor a 5 años. Alta duración, más volátil ante cambios de política monetaria",
        "simple_desc": "DICP: bono largo que sube con la inflación, mayor rendimiento y más riesgo de precio",
    },
    {
        "id": "fci_renta_pesos",
        "name": "Fondo Renta Fija Pesos (Consultatio / SBS)",
        "category": "Pesos ARS",
        "sub": "Fondos CLP",
        "ticker": "FCI-RF",
        "color": "#16a34a",
        "expected_return": 0.09,
        "volatility": 0.05,
        "risk_level": "bajo",
        "description": "Fondos como Consultatio Renta Fija o SBS Renta Pesos. Invierten en una mezcla de LECAPs, bonos CER y otros instrumentos en pesos. Un gestor profesional decide la combinación exacta. Ideal para quien no quiere elegir bonos individuales.",
        "currency": "ARS",
        "market": "FCI",
        "simple_desc": "Consultatio o SBS Renta Fija: mezcla de bonos en pesos, manejada por expertos",
    },
    {
        "id": "fci_usd_rf",
        "name": "Fondo Renta Fija USD (Compass / Balanz)",
        "category": "Fondos USD", "sub": "Renta Fija USD",
        "ticker": "FCI-USD", "color": "#0ea5e9",
        "expected_return": 0.065, "volatility": 0.05, "risk_level": "bajo",
        "description": "Fondos como Compass Renta Fija o Balanz Capital Ahorro en USD. Invierten en obligaciones negociables y bonos corporativos en dólares. Rescate en 24-48hs hábiles. Ideal para dolarizar sin seleccionar bonos individuales.",
        "currency": "USD", "market": "FCI",
        "simple_desc": "Fondo en USD que invierte en ONs corporativas — rescate en 24-48hs",
    },
    {
        "id": "fci_usd_ahorro",
        "name": "Fondo Ahorro USD Corto Plazo (Cohen / Quinquela)",
        "category": "Fondos USD", "sub": "Liquidez USD",
        "ticker": "FCI-USDCP", "color": "#38bdf8",
        "expected_return": 0.055, "volatility": 0.03, "risk_level": "muy bajo",
        "description": "Fondos como Cohen Ahorro en Dólares o Quinquela Ahorro. Invierten en letras del Tesoro de EE.UU. y activos de muy corto plazo en USD. Rescate T+0 o T+1. Alternativa al colchón de dólares con rendimiento.",
        "currency": "USD", "market": "FCI",
        "simple_desc": "Fondo en USD de muy corto plazo — alternativa al colchón, rescate inmediato",
    },
    {
        "id": "fci_latam",
        "name": "Fondo Deuda Latinoamérica (SBS / OnCapital)",
        "category": "Fondos USD", "sub": "Deuda Emergente",
        "ticker": "FCI-LATAM", "color": "#6366f1",
        "expected_return": 0.075, "volatility": 0.09, "risk_level": "medio",
        "description": "Fondos como SBS Deuda Latinoamérica u OnCapital Renta Fija. Diversifican en bonos corporativos y soberanos de Brasil, México, Chile, Colombia y Argentina. Mayor diversificación geográfica que invertir solo en Argentina.",
        "currency": "USD", "market": "FCI",
        "simple_desc": "Fondo en USD diversificado en deuda de Brasil, México, Chile y Argentina",
    },
    {
        "id": "fci_acciones",
        "name": "Fondo Acciones Argentinas (Alpha / Criteria)",
        "category": "Fondos ARS", "sub": "Equity ARG",
        "ticker": "FCI-ACC", "color": "#f97316",
        "expected_return": 0.18, "volatility": 0.35, "risk_level": "alto",
        "description": "Fondos como Alpha Acciones o Criteria Acciones Argentinas. Invierten en acciones del panel Merval. Un gestor profesional selecciona las mejores acciones locales. Alto potencial de retorno a largo plazo, alta volatilidad de corto.",
        "currency": "ARS", "market": "FCI",
        "simple_desc": "Fondo de acciones argentinas manejado por un gestor profesional",
    },
    {
        "id": "fci_cedears",
        "name": "Fondo CEDEARs (Galicia / Balanz)",
        "category": "Fondos ARS", "sub": "Equity Global",
        "ticker": "FCI-CED", "color": "#a78bfa",
        "expected_return": 0.14, "volatility": 0.22, "risk_level": "medio-alto",
        "description": "Fondos como Galicia Acciones Globales o Balanz Performance. Invierten en CEDEARs de empresas líderes de EE.UU. y el mundo. Permiten exposición al mercado global en pesos, con cobertura cambiaria natural.",
        "currency": "ARS", "market": "FCI",
        "simple_desc": "Fondo de CEDEARs: acciones globales en pesos, cobertura cambiaria incluida",
    },
    {
        "id": "fci_mixto",
        "name": "Fondo Mixto (Consultatio / SBS)",
        "category": "Fondos ARS", "sub": "Mixto",
        "ticker": "FCI-MIX", "color": "#8b5cf6",
        "expected_return": 0.11, "volatility": 0.13, "risk_level": "medio",
        "description": "Fondos como Consultatio Balanceado o SBS Estrategia. Combinan renta fija (LECAPs, bonos CER) con acciones y CEDEARs. Un gestor decide la mezcla según el contexto de mercado. Ideal para quien quiere diversificación sin seleccionar activos.",
        "currency": "ARS", "market": "FCI",
        "simple_desc": "Fondo mixto: bonos + acciones en pesos, gestión activa profesional",
    },

    # ══ DÓLAR MEP Y COBERTURA ══════════════════════════════════════════════════

    {
        "id": "mep",
        "name": "Dólar MEP (vía AL30 en IOL o PPI)",
        "category": "Dólar MEP",
        "sub": "Reserva de valor",
        "ticker": "USD-MEP",
        "color": "#38bdf8",
        "expected_return": 0.00,
        "volatility": 0.08,
        "risk_level": "muy bajo",
        "description": "Dólares legales comprados a través de la bolsa sin límite mensual. El proceso: se adquiere el bono AL30 en pesos y se vende en dólares — la diferencia resultante es el tipo de cambio MEP. IOL y PPI lo ejecutan de forma automática en 1 clic. Los dólares quedan acreditados en la cuenta del broker.",
        "currency": "USD",
        "market": "BYMA",
        "simple_desc": "Dólares legales por la bolsa, 1 click en IOL o PPI, sin límite mensual",
    },

    # ══ BONOS SOBERANOS USD ════════════════════════════════════════════════════

    {
        "id": "al30",
        "name": "Bono AL30 — soberano USD ley argentina",
        "category": "Bonos USD",
        "sub": "Soberano ARG",
        "ticker": "AL30",
        "color": "#0ea5e9",
        "expected_return": 0.10,
        "volatility": 0.18,
        "risk_level": "medio",
        "description": "El bono soberano argentino en dólares más líquido. Vence en 2030 y paga cupones semestrales en USD. Ley argentina. Compralo en IOL, PPI o Balanz. Riesgo real: si Argentina entra en default como en 2001, puede no pagarse. Por eso es solo una parte de la cartera.",
        "currency": "USD",
        "market": "BYMA",
        "simple_desc": "AL30: bono del gobierno argentino en USD, cupones semestrales, comprá en IOL",
    },
    {
        "id": "gd30",
        "name": "Bono GD30 — soberano USD ley Nueva York",
        "category": "Bonos USD",
        "sub": "Soberano ARG",
        "ticker": "GD30",
        "color": "#0284c7",
        "expected_return": 0.10,
        "volatility": 0.17,
        "risk_level": "medio",
        "description": "Similar al AL30 pero bajo ley de Nueva York. Ante un incumplimiento de Argentina, el inversor puede recurrir a la justicia estadounidense — mayor protección legal. Es el bono soberano más demandado por fondos internacionales. Cotiza con una prima respecto al AL30 por esa razón.",
        "currency": "USD",
        "market": "BYMA",
        "simple_desc": "GD30: igual que AL30 pero con protección legal en NY, preferido por fondos",
    },

    # ══ OBLIGACIONES NEGOCIABLES ════════════════════════════════════════════════

    {
        "id": "on_ypf",
        "name": "ON YPF 2026 (YPFDS) — deuda YPF en USD",
        "category": "Bonos USD",
        "sub": "Corporativo",
        "ticker": "YPFDS",
        "color": "#0369a1",
        "expected_return": 0.09,
        "volatility": 0.10,
        "risk_level": "bajo-medio",
        "description": "La obligación negociable YPFDS: YPF toma dólares prestados y devuelve el capital más intereses. Menor riesgo que la acción de YPF porque en caso de quiebra los bonistas cobran antes que los accionistas. Se opera en IOL o PPI con el ticker YPFDS.",
        "currency": "USD",
        "market": "BYMA",
        "simple_desc": "YPFDS: YPF paga intereses en dólares, menor riesgo que la acción",
    },
    {
        "id": "on_corp",
        "name": "ONs Corporativas (YPF / TGS / Tecpetrol)",
        "category": "Bonos USD",
        "sub": "Corporativo",
        "ticker": "ON-MIX",
        "color": "#075985",
        "expected_return": 0.08,
        "volatility": 0.08,
        "risk_level": "bajo-medio",
        "description": "Mezcla de obligaciones negociables de empresas privadas argentinas: YPF (YPFDS), TGS (TGSU2O), Tecpetrol (TCCUD). Todas pagan en dólares. Son consideradas más seguras que los bonos soberanos porque empresas privadas tienen mejor historial de pago que el Estado.",
        "currency": "USD",
        "market": "BYMA",
        "simple_desc": "ONs de YPF, TGS o Tecpetrol: empresas privadas que pagan en USD",
    },
    {
        "id": "on_tecpetrol",
        "name": "ON Tecpetrol (TCCUD)",
        "category": "Bonos USD",
        "sub": "Corporativo",
        "ticker": "TCCUD",
        "color": "#0c4a6e",
        "expected_return": 0.09,
        "volatility": 0.09,
        "risk_level": "bajo-medio",
        "description": "Obligación negociable de Tecpetrol (grupo Techint) en dólares. Empresa de petróleo y gas con sólidos fundamentos. Buena opción para renta en USD.",
        "currency": "USD",
        "market": "BYMA",
        "simple_desc": "Deuda de Tecpetrol en dólares, respaldo del grupo Techint",
    },
    {
        "id": "al35",
        "name": "Bono AL35 — soberano USD ley Argentina",
        "category": "Bonos USD", "sub": "Soberano",
        "ticker": "AL35", "color": "#1d4ed8",
        "expected_return": 0.085, "volatility": 0.13, "risk_level": "medio",
        "description": "Bono soberano argentino en dólares con vencimiento 2035, ley argentina. Mayor duración que AL30, implica más sensibilidad a tasas pero mayor rendimiento potencial.",
        "currency": "USD", "market": "BYMA",
        "simple_desc": "Bono soberano USD Argentina 2035 (ley local)",
    },
    {
        "id": "gd35",
        "name": "Bono GD35 — soberano USD ley Nueva York",
        "category": "Bonos USD", "sub": "Soberano",
        "ticker": "GD35", "color": "#1d4ed8",
        "expected_return": 0.085, "volatility": 0.13, "risk_level": "medio",
        "description": "Versión ley Nueva York del bono soberano al 2035. Mejor protección legal para el inversor, prima menor frente al AL35.",
        "currency": "USD", "market": "BYMA",
        "simple_desc": "Bono soberano USD Argentina 2035 (ley NY, mayor protección)",
    },
    {
        "id": "gd38",
        "name": "Bono GD38 — soberano USD ley Nueva York",
        "category": "Bonos USD", "sub": "Soberano",
        "ticker": "GD38", "color": "#1e3a8a",
        "expected_return": 0.09, "volatility": 0.14, "risk_level": "medio-alto",
        "description": "Bono soberano argentino en USD con vencimiento 2038, ley Nueva York. Mayor duration implica más potencial de suba si mejora el riesgo país.",
        "currency": "USD", "market": "BYMA",
        "simple_desc": "Bono soberano USD Argentina 2038, mayor duración",
    },
    {
        "id": "gd29",
        "name": "Bono GD29 — soberano USD ley Nueva York",
        "category": "Bonos USD", "sub": "Soberano",
        "ticker": "GD29", "color": "#1d4ed8",
        "expected_return": 0.09, "volatility": 0.14, "risk_level": "medio",
        "description": "Bono soberano argentino en dólares con vencimiento 2029, ley de Nueva York. Plazo intermedio entre GD30 y GD35. Mayor protección legal que los bonos ley argentina. Cotiza con alta liquidez en BYMA.",
        "currency": "USD", "market": "BYMA",
        "simple_desc": "Bono soberano USD Argentina 2029 (ley NY, vencimiento cercano)",
    },
    {
        "id": "gd41",
        "name": "Bono GD41 — soberano USD ley Nueva York",
        "category": "Bonos USD", "sub": "Soberano",
        "ticker": "GD41", "color": "#1e3a8a",
        "expected_return": 0.095, "volatility": 0.16, "risk_level": "medio-alto",
        "description": "Bono soberano argentino en dólares con vencimiento 2041, ley de Nueva York. El de mayor duration de la serie Global: máxima sensibilidad a cambios en el riesgo país. Para quien apuesta al largo plazo argentino.",
        "currency": "USD", "market": "BYMA",
        "simple_desc": "Bono soberano USD Argentina 2041 — apuesta al largo plazo argentino",
    },
    {
        "id": "on_tgs",
        "name": "ON TGS USD (TGSU2O)",
        "category": "Bonos USD", "sub": "Corporativo",
        "ticker": "TGSU2O", "color": "#0369a1",
        "expected_return": 0.085, "volatility": 0.08, "risk_level": "bajo-medio",
        "description": "Obligación negociable de Transportadora Gas del Sur en dólares. Infraestructura crítica con flujos en USD regulados.",
        "currency": "USD", "market": "BYMA",
        "simple_desc": "Deuda de TGS en USD, infraestructura gasífera regulada",
    },
    {
        "id": "on_macro",
        "name": "ON Banco Macro USD",
        "category": "Bonos USD", "sub": "Corporativo",
        "ticker": "BMA5O", "color": "#f59e0b",
        "expected_return": 0.09, "volatility": 0.09, "risk_level": "bajo-medio",
        "description": "Obligación negociable de Banco Macro en dólares. Banco sólido con fuerte capitalización. Rinde más que los soberanos con riesgo corporativo diversificado.",
        "currency": "USD", "market": "BYMA",
        "simple_desc": "Deuda corporativa de Banco Macro en USD",
    },
    {
        "id": "on_meli",
        "name": "ON MercadoLibre USD (MLIUSD)",
        "category": "Bonos USD", "sub": "Corporativo",
        "ticker": "MLIUSD", "color": "#fbbf24",
        "expected_return": 0.075, "volatility": 0.07, "risk_level": "bajo-medio",
        "description": "Obligación negociable de MercadoLibre en dólares. La empresa líder de e-commerce y fintech de Latinoamérica. Menor riesgo soberano: MercadoLibre tiene ingresos en múltiples países y calificación investment grade regional.",
        "currency": "USD", "market": "BYMA",
        "simple_desc": "Deuda de MercadoLibre en USD — tech latam con ingresos en toda la región",
    },
    {
        "id": "on_telecom",
        "name": "ON Telecom Argentina USD (TCOMD)",
        "category": "Bonos USD", "sub": "Corporativo",
        "ticker": "TCOMD", "color": "#0891b2",
        "expected_return": 0.09, "volatility": 0.09, "risk_level": "bajo-medio",
        "description": "Obligación negociable de Telecom Argentina en dólares. Principal operadora de telecomunicaciones del país, con flujos en pesos y USD. Infraestructura crítica con barreras de entrada altas.",
        "currency": "USD", "market": "BYMA",
        "simple_desc": "Deuda de Telecom Argentina en USD, principal telco del país",
    },
    {
        "id": "on_genneia",
        "name": "ON Genneia USD (GNCXO)",
        "category": "Bonos USD", "sub": "Corporativo",
        "ticker": "GNCXO", "color": "#10b981",
        "expected_return": 0.095, "volatility": 0.10, "risk_level": "medio",
        "description": "Obligación negociable de Genneia en dólares. Líder en energía renovable en Argentina (eólica y solar). Sus ingresos están en USD por contratos de largo plazo con CAMMESA. Beneficiada por la transición energética global.",
        "currency": "USD", "market": "BYMA",
        "simple_desc": "Deuda de Genneia en USD — energía renovable con contratos en dólares",
    },
    {
        "id": "on_vista",
        "name": "ON Vista Oil & Gas USD (VSCOD)",
        "category": "Bonos USD", "sub": "Corporativo",
        "ticker": "VSCOD", "color": "#059669",
        "expected_return": 0.10, "volatility": 0.11, "risk_level": "medio",
        "description": "Obligación negociable de Vista Oil & Gas en dólares. Empresa de exploración y producción de petróleo en Vaca Muerta. Flujos 100% en USD. Alto crecimiento de producción. Riesgo: precio del crudo y riesgo país.",
        "currency": "USD", "market": "BYMA",
        "simple_desc": "Deuda de Vista Oil & Gas en USD — productor de Vaca Muerta",
    },
    {
        "id": "on_pampa",
        "name": "ON Pampa Energía USD (PGN2O)",
        "category": "Bonos USD", "sub": "Corporativo",
        "ticker": "PGN2O", "color": "#f59e0b",
        "expected_return": 0.09, "volatility": 0.09, "risk_level": "bajo-medio",
        "description": "Obligación negociable de Pampa Energía en dólares. Holding eléctrico más grande de Argentina: generación, transporte y distribución. Contratos regulados en USD. Alta cobertura de intereses.",
        "currency": "USD", "market": "BYMA",
        "simple_desc": "Deuda de Pampa Energía en USD, holding eléctrico con contratos regulados",
    },

    # ══ ONs CORPORATIVAS ADICIONALES ══════════════════════════════════════════

    {
        "id": "on_tgs2",
        "name": "ON TGS USD Serie 2 (TGS2O)",
        "category": "Bonos USD", "sub": "Corporativo",
        "ticker": "TGS2O", "color": "#0369a1",
        "expected_return": 0.085, "volatility": 0.08, "risk_level": "bajo-medio",
        "description": "Obligación negociable de Transportadora Gas del Sur en dólares, serie TGS2O. La mayor transportadora de gas del país, con ingresos regulados en USD. Infraestructura crítica con contratos de largo plazo.",
        "currency": "USD", "market": "BYMA",
        "simple_desc": "Deuda de la mayor transportadora de gas del país — paga intereses en dólares",
        "activo": True, "nota_analista": "Infraestructura regulada, bajo riesgo operativo",
        "fuente_retorno": "Estimación propia / BYMA",
    },
    {
        "id": "on_arcor",
        "name": "ON Arcor USD (RCCJO)",
        "category": "Bonos USD", "sub": "Corporativo",
        "ticker": "RCCJO", "color": "#f97316",
        "expected_return": 0.085, "volatility": 0.09, "risk_level": "bajo-medio",
        "description": "Obligación negociable de Arcor S.A.I.C. en dólares. La empresa de alimentos más grande de Argentina, con presencia en 120 países y exportaciones que generan divisas propias. Menor dependencia del tipo de cambio local.",
        "currency": "USD", "market": "BYMA",
        "simple_desc": "Deuda de Arcor en USD — exportadora de alimentos con ingresos en dólares",
        "activo": True, "nota_analista": "Exportadora diversificada, bajo riesgo soberano relativo",
        "fuente_retorno": "Estimación propia / BYMA",
    },
    {
        "id": "on_telecom2",
        "name": "ON Telecom Argentina USD (TLCMO)",
        "category": "Bonos USD", "sub": "Corporativo",
        "ticker": "TLCMO", "color": "#0891b2",
        "expected_return": 0.09, "volatility": 0.09, "risk_level": "bajo-medio",
        "description": "Obligación negociable de Telecom Argentina, serie TLCMO. Principal operadora de telecomunicaciones del país. Infraestructura crítica con barreras de entrada muy altas y flujos en USD.",
        "currency": "USD", "market": "BYMA",
        "simple_desc": "Deuda de Telecom Argentina serie TLCMO — telecomunicaciones líder del país",
        "activo": True, "nota_analista": "Serie distinta a TCOMD, diferente vencimiento y TIR",
        "fuente_retorno": "Estimación propia / BYMA",
    },
    {
        "id": "on_irsa",
        "name": "ON IRSA USD (IRCFO)",
        "category": "Bonos USD", "sub": "Corporativo",
        "ticker": "IRCFO", "color": "#7c3aed",
        "expected_return": 0.10, "volatility": 0.11, "risk_level": "medio",
        "description": "Obligación negociable de IRSA Inversiones y Representaciones en dólares. La mayor empresa inmobiliaria de Argentina: shoppings, oficinas premium y hoteles. Exposición al ciclo económico local y al real estate argentino.",
        "currency": "USD", "market": "BYMA",
        "simple_desc": "Deuda de IRSA en USD — mayor empresa inmobiliaria de Argentina",
        "activo": True, "nota_analista": "Exposición a real estate ARG, correlación con ciclo económico local",
        "fuente_retorno": "Estimación propia / BYMA",
    },
    {
        "id": "on_cresud",
        "name": "ON Cresud USD (CSDOO)",
        "category": "Bonos USD", "sub": "Corporativo",
        "ticker": "CSDOO", "color": "#65a30d",
        "expected_return": 0.10, "volatility": 0.12, "risk_level": "medio",
        "description": "Obligación negociable de Cresud S.A.C.I.F. y A. en dólares. Empresa agropecuaria con campos en Argentina, Brasil, Bolivia y Paraguay. Ingresos en USD por exportaciones agrícolas.",
        "currency": "USD", "market": "BYMA",
        "simple_desc": "Deuda de Cresud en USD — campo agropecuario en Argentina y Latinoamérica",
        "activo": True, "nota_analista": "Liquidez baja, solo agresivo",
        "fuente_retorno": "Estimación propia / BYMA",
    },

    # ══ BONOS EN PESOS — COBERTURA DUAL Y DOLLAR LINKED ══════════════════════

    {
        "id": "dual_bond",
        "name": "Bono Dual TDA27 (CER o devaluación, lo que sea mayor)",
        "category": "Pesos ARS", "sub": "Deuda Pública ARS",
        "ticker": "TDA27", "color": "#a78bfa",
        "expected_return": 0.08, "volatility": 0.12, "risk_level": "bajo-medio",
        "description": "Bono del Tesoro argentino que ajusta por el máximo entre inflación (CER) y devaluación del peso. Si el dólar sube más que la inflación, te paga con el dólar. Si la inflación supera al dólar, te paga con inflación. Doble cobertura ante incertidumbre macro.",
        "currency": "ARS", "market": "BYMA",
        "simple_desc": "Bono dual: ajusta por inflación O devaluación, lo que sea mayor — doble cobertura",
        "activo": True, "nota_analista": "Dual, buena cobertura ante incertidumbre macro",
        "fuente_retorno": "Estimación propia / BYMA",
    },
    {
        "id": "dollar_linked",
        "name": "Bono Dollar Linked TV26 (sigue al dólar oficial)",
        "category": "Pesos ARS", "sub": "Deuda Pública ARS",
        "ticker": "TV26", "color": "#38bdf8",
        "expected_return": 0.07, "volatility": 0.10, "risk_level": "bajo-medio",
        "description": "Bono del Tesoro argentino cuyo capital y renta ajustan por el tipo de cambio oficial. Si el dólar oficial sube, el bono vale más en pesos. Protege contra devaluación sin necesidad de comprar dólares directamente.",
        "currency": "ARS", "market": "BYMA",
        "simple_desc": "Bono dollar linked TV26: sigue al dólar oficial, protege contra devaluación del peso",
        "activo": True, "nota_analista": "Protección contra devaluación del tipo de cambio oficial",
        "fuente_retorno": "Estimación propia / BYMA",
    },

    # ══ CEDEARs TECNOLOGÍA ═════════════════════════════════════════════════════

    {
        "id": "aapl",
        "name": "Apple (AAPL)",
        "category": "CEDEARs",
        "sub": "Tecnología",
        "ticker": "AAPL",
        "color": "#a78bfa",
        "expected_return": 0.12,
        "volatility": 0.24,
        "risk_level": "medio",
        "description": "La empresa más grande del mundo. Hace iPhones, Macs y servicios digitales. Estable, con buen crecimiento histórico.",
        "currency": "USD",
        "market": "BYMA/NASDAQ",
        "simple_desc": "La empresa de Apple, una de las más valiosas del mundo",
    },
    {
        "id": "msft",
        "name": "Microsoft (MSFT)",
        "category": "CEDEARs",
        "sub": "Tecnología",
        "ticker": "MSFT",
        "color": "#8b5cf6",
        "expected_return": 0.13,
        "volatility": 0.23,
        "risk_level": "medio",
        "description": "Gigante tech: Windows, Office, Azure (nube) y GitHub. Muy diversificada y estable. Una de las empresas más rentables del mundo.",
        "currency": "USD",
        "market": "BYMA/NASDAQ",
        "simple_desc": "La empresa de Windows, Office y la nube Azure",
    },
    {
        "id": "googl",
        "name": "Alphabet / Google (GOOGL)",
        "category": "CEDEARs",
        "sub": "Tecnología",
        "ticker": "GOOGL",
        "color": "#7c3aed",
        "expected_return": 0.13,
        "volatility": 0.25,
        "risk_level": "medio",
        "description": "Dueña de Google, YouTube y Android. Domina publicidad digital. Gigantesca generación de caja y crecimiento sostenido.",
        "currency": "USD",
        "market": "BYMA/NASDAQ",
        "simple_desc": "La empresa detrás de Google, YouTube y Android",
    },
    {
        "id": "amzn",
        "name": "Amazon (AMZN)",
        "category": "CEDEARs",
        "sub": "Consumo/Tech",
        "ticker": "AMZN",
        "color": "#6d28d9",
        "expected_return": 0.14,
        "volatility": 0.27,
        "risk_level": "medio-alto",
        "description": "Comercio electrónico y nube (AWS). Dos negocios enormes en uno. Alto potencial de crecimiento.",
        "currency": "USD",
        "market": "BYMA/NASDAQ",
        "simple_desc": "Amazon: tienda online + la nube más grande del mundo",
    },
    {
        "id": "nvda",
        "name": "Nvidia (NVDA)",
        "category": "CEDEARs",
        "sub": "Tecnología/IA",
        "ticker": "NVDA",
        "color": "#5b21b6",
        "expected_return": 0.22,
        "volatility": 0.48,
        "risk_level": "alto",
        "description": "Fabricante de chips para inteligencia artificial. El negocio creció exponencialmente con el boom de la IA. Alta volatilidad.",
        "currency": "USD",
        "market": "BYMA/NASDAQ",
        "simple_desc": "La empresa de chips para inteligencia artificial",
    },
    {
        "id": "meli",
        "name": "MercadoLibre (MELI)",
        "category": "CEDEARs",
        "sub": "Tecnología LATAM",
        "ticker": "MELI",
        "color": "#4f46e5",
        "expected_return": 0.20,
        "volatility": 0.38,
        "risk_level": "alto",
        "description": "Líder en e-commerce y fintech en Latinoamérica. Opera en Argentina, Brasil, México. Alto potencial y alta volatilidad.",
        "currency": "USD",
        "market": "BYMA/NASDAQ",
        "simple_desc": "MercadoLibre: la empresa de comercio y pagos online más grande de Latinoamérica",
    },

    {
        "id": "meta",
        "name": "Meta / Facebook (META)",
        "category": "CEDEARs",
        "sub": "Tecnología",
        "ticker": "META",
        "color": "#1d4ed8",
        "expected_return": 0.15,
        "volatility": 0.28,
        "risk_level": "medio-alto",
        "description": "Dueña de Facebook, Instagram y WhatsApp. Domina publicidad digital global. Apuesta fuerte a la inteligencia artificial.",
        "currency": "USD",
        "market": "BYMA/NASDAQ",
        "simple_desc": "La empresa de Facebook, Instagram y WhatsApp",
    },
    {
        "id": "brk",
        "name": "Berkshire Hathaway (BRK/B)",
        "category": "CEDEARs",
        "sub": "Financiero",
        "ticker": "BRKB",
        "color": "#92400e",
        "expected_return": 0.11,
        "volatility": 0.18,
        "risk_level": "medio",
        "description": "Holding de Warren Buffett. Dueña de decenas de empresas: seguros, energía, consumo, bancos. La más diversificada del mundo en un solo activo.",
        "currency": "USD",
        "market": "BYMA/NYSE",
        "simple_desc": "El holding de Warren Buffett, muy diversificado y sólido",
    },
    {
        "id": "jpm",
        "name": "JPMorgan Chase (JPM)",
        "category": "CEDEARs",
        "sub": "Financiero",
        "ticker": "JPM",
        "color": "#1e3a5f",
        "expected_return": 0.12,
        "volatility": 0.22,
        "risk_level": "medio",
        "description": "El banco más grande de EE.UU. por activos. Muy sólido, paga dividendos y se beneficia de tasas altas. Referente del sector financiero global.",
        "currency": "USD",
        "market": "BYMA/NYSE",
        "simple_desc": "El banco más grande de EE.UU., sólido y con dividendos",
    },

    # ══ CEDEARs CONSUMO & SALUD ════════════════════════════════════════════════

    {
        "id": "ko",
        "name": "Coca-Cola (KO)",
        "category": "CEDEARs",
        "sub": "Consumo Masivo",
        "ticker": "KO",
        "color": "#dc2626",
        "expected_return": 0.08,
        "volatility": 0.14,
        "risk_level": "medio",
        "description": "Marca global de bebidas. Paga dividendos históricos, muy estable. Ideal para carteras defensivas que buscan ingreso pasivo.",
        "currency": "USD",
        "market": "BYMA/NYSE",
        "simple_desc": "Coca-Cola: estable, global y paga dividendos hace décadas",
    },
    {
        "id": "wmt",
        "name": "Walmart (WMT)",
        "category": "CEDEARs",
        "sub": "Consumo Masivo",
        "ticker": "WMT",
        "color": "#b91c1c",
        "expected_return": 0.09,
        "volatility": 0.15,
        "risk_level": "medio",
        "description": "Mayor cadena de supermercados del mundo. Muy resistente a recesiones. También tiene e-commerce creciente.",
        "currency": "USD",
        "market": "BYMA/NYSE",
        "simple_desc": "El supermercado más grande del mundo, muy estable",
    },
    {
        "id": "jnj",
        "name": "Johnson & Johnson (JNJ)",
        "category": "CEDEARs",
        "sub": "Salud",
        "ticker": "JNJ",
        "color": "#991b1b",
        "expected_return": 0.08,
        "volatility": 0.13,
        "risk_level": "bajo-medio",
        "description": "Empresa farmacéutica y de productos de salud. Muy defensiva, paga dividendos crecientes hace más de 60 años.",
        "currency": "USD",
        "market": "BYMA/NYSE",
        "simple_desc": "Farmacéutica gigante, muy estable y con dividendos históricos",
    },
    {
        "id": "pfe",
        "name": "Pfizer (PFE)",
        "category": "CEDEARs",
        "sub": "Salud",
        "ticker": "PFE",
        "color": "#7f1d1d",
        "expected_return": 0.07,
        "volatility": 0.20,
        "risk_level": "medio",
        "description": "Laboratorio farmacéutico global. Conocido por la vacuna COVID. Pipeline amplio de medicamentos.",
        "currency": "USD",
        "market": "BYMA/NYSE",
        "simple_desc": "Pfizer, uno de los laboratorios más grandes del mundo",
    },

    # ══ CEDEARs ENERGÍA ════════════════════════════════════════════════════════

    {
        "id": "xom",
        "name": "ExxonMobil (XOM)",
        "category": "CEDEARs",
        "sub": "Energía",
        "ticker": "XOM",
        "color": "#ea580c",
        "expected_return": 0.09,
        "volatility": 0.22,
        "risk_level": "medio",
        "description": "Gigante petrolero y gasífero estadounidense. Se beneficia cuando sube el precio del crudo. Paga buenos dividendos.",
        "currency": "USD",
        "market": "BYMA/NYSE",
        "simple_desc": "ExxonMobil: petróleo y gas, con buenos dividendos",
    },
    {
        "id": "tsla",
        "name": "Tesla (TSLA)",
        "category": "CEDEARs",
        "sub": "Tecnología/Autos",
        "ticker": "TSLA",
        "color": "#c2410c",
        "expected_return": 0.18,
        "volatility": 0.55,
        "risk_level": "alto",
        "description": "Líder en autos eléctricos. Alto potencial de crecimiento pero muy volátil. Puede subir o bajar 20% en semanas.",
        "currency": "USD",
        "market": "BYMA/NASDAQ",
        "simple_desc": "Tesla: autos eléctricos, muy volátil pero con alto potencial",
    },

    # ══ CEDEARs FINANZAS & INDUSTRIA ══════════════════════════════════════════

    {
        "id": "bac",
        "name": "Bank of America (BAC)",
        "category": "CEDEARs",
        "sub": "Financiero",
        "ticker": "BAC",
        "color": "#dc2626",
        "expected_return": 0.11,
        "volatility": 0.25,
        "risk_level": "medio",
        "description": "Segundo banco de EE.UU. por activos. Exposición al ciclo económico americano, banca retail y corporativa.",
        "currency": "USD",
        "market": "BYMA/NYSE",
        "simple_desc": "Bank of America, uno de los bancos más grandes del mundo",
    },
    {
        "id": "dis",
        "name": "Walt Disney (DIS)",
        "category": "CEDEARs",
        "sub": "Consumo/Entretenimiento",
        "ticker": "DIS",
        "color": "#1d4ed8",
        "expected_return": 0.10,
        "volatility": 0.25,
        "risk_level": "medio",
        "description": "La empresa del entretenimiento más famosa del mundo. Dueña de Disney+, Marvel, Star Wars, ESPN y parques temáticos.",
        "currency": "USD",
        "market": "BYMA/NYSE",
        "simple_desc": "Disney: películas, streaming, parques y Marvel",
    },

    # ══ CEDEARs — TECNOLOGÍA ADICIONAL ════════════════════════════════════════

    {
        "id": "amd",
        "name": "AMD (Advanced Micro Devices)",
        "category": "CEDEARs", "sub": "Tecnología",
        "ticker": "AMD", "color": "#ef4444",
        "expected_return": 0.22, "volatility": 0.50, "risk_level": "alto",
        "description": "Fabricante de chips rival de Nvidia e Intel. Fuerte en CPUs y GPUs para IA y data centers.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "AMD: chips para computadoras, servidores e IA",
    },
    {
        "id": "nflx",
        "name": "Netflix (NFLX)",
        "category": "CEDEARs", "sub": "Tecnología",
        "ticker": "NFLX", "color": "#dc2626",
        "expected_return": 0.18, "volatility": 0.38, "risk_level": "medio-alto",
        "description": "Líder global en streaming de video. Opera en 190 países con más de 300 millones de suscriptores.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Netflix: el streaming de series y películas más grande del mundo",
    },
    {
        "id": "orcl",
        "name": "Oracle (ORCL)",
        "category": "CEDEARs", "sub": "Tecnología",
        "ticker": "ORCL", "color": "#dc2626",
        "expected_return": 0.15, "volatility": 0.25, "risk_level": "medio",
        "description": "Gigante de software empresarial y cloud. Dominante en bases de datos. Beneficiario del boom de IA en infraestructura.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Oracle: bases de datos y cloud para empresas",
    },
    {
        "id": "crm",
        "name": "Salesforce (CRM)",
        "category": "CEDEARs", "sub": "Tecnología",
        "ticker": "CRM", "color": "#0ea5e9",
        "expected_return": 0.16, "volatility": 0.32, "risk_level": "medio-alto",
        "description": "Líder en software CRM (gestión de clientes). Principal plataforma de ventas y marketing para empresas.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Salesforce: el software de ventas empresarial más usado del mundo",
    },
    {
        "id": "adbe",
        "name": "Adobe (ADBE)",
        "category": "CEDEARs", "sub": "Tecnología",
        "ticker": "ADBE", "color": "#ef4444",
        "expected_return": 0.16, "volatility": 0.32, "risk_level": "medio-alto",
        "description": "Dueña de Photoshop, Illustrator, Premiere y Acrobat. Fuerte transición a suscripción cloud e integración de IA generativa.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Adobe: Photoshop, Premiere e IA creativa",
    },
    {
        "id": "uber",
        "name": "Uber (UBER)",
        "category": "CEDEARs", "sub": "Tecnología",
        "ticker": "UBER", "color": "#1e293b",
        "expected_return": 0.18, "volatility": 0.42, "risk_level": "medio-alto",
        "description": "Plataforma de movilidad y delivery global. Opera en 70+ países. En camino a rentabilidad sostenida.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Uber: transporte y delivery en 70 países",
    },
    {
        "id": "glob",
        "name": "Globant (GLOB)",
        "category": "CEDEARs", "sub": "Tecnología",
        "ticker": "GLOB", "color": "#10b981",
        "expected_return": 0.20, "volatility": 0.45, "risk_level": "alto",
        "description": "Empresa tecnológica argentina cotizando en NYSE. Desarrollo de software y transformación digital para clientes globales.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Globant: la tech argentina en Wall Street",
    },

    # ══ CEDEARs — FINANZAS ═════════════════════════════════════════════════════

    {
        "id": "v",
        "name": "Visa (V)",
        "category": "CEDEARs", "sub": "Financiero",
        "ticker": "V", "color": "#1d4ed8",
        "expected_return": 0.14, "volatility": 0.20, "risk_level": "medio",
        "description": "La red de pagos más grande del mundo. Cobra una comisión en cada transacción con tarjeta Visa en el planeta.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Visa: cobra en cada transacción con tarjeta en el mundo",
    },
    {
        "id": "ma",
        "name": "Mastercard (MA)",
        "category": "CEDEARs", "sub": "Financiero",
        "ticker": "MA", "color": "#ef4444",
        "expected_return": 0.14, "volatility": 0.20, "risk_level": "medio",
        "description": "Segunda red de pagos global. Modelo de negocio idéntico a Visa: cobra en cada transacción sin riesgo crediticio.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Mastercard: red de pagos global sin riesgo crediticio",
    },
    {
        "id": "gs",
        "name": "Goldman Sachs (GS)",
        "category": "CEDEARs", "sub": "Financiero",
        "ticker": "GS", "color": "#1e293b",
        "expected_return": 0.13, "volatility": 0.28, "risk_level": "medio-alto",
        "description": "Banco de inversión líder global. Opera en trading, M&A, asset management y finanzas estructuradas.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Goldman Sachs: el banco de inversión más poderoso del mundo",
    },
    {
        "id": "ms",
        "name": "Morgan Stanley (MS)",
        "category": "CEDEARs", "sub": "Financiero",
        "ticker": "MS", "color": "#1e40af",
        "expected_return": 0.13, "volatility": 0.27, "risk_level": "medio-alto",
        "description": "Banco de inversión y wealth management. Fuerte en gestión de patrimonios y banca corporativa global.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Morgan Stanley: banca de inversión y wealth management",
    },

    # ══ CEDEARs — SALUD ════════════════════════════════════════════════════════

    {
        "id": "unh",
        "name": "UnitedHealth (UNH)",
        "category": "CEDEARs", "sub": "Salud",
        "ticker": "UNH", "color": "#0ea5e9",
        "expected_return": 0.14, "volatility": 0.20, "risk_level": "medio",
        "description": "Mayor aseguradora de salud de EE.UU. Combina seguro médico con servicios de salud digitales.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "UnitedHealth: el gigante del seguro médico en EE.UU.",
    },
    {
        "id": "lly",
        "name": "Eli Lilly (LLY)",
        "category": "CEDEARs", "sub": "Salud",
        "ticker": "LLY", "color": "#c026d3",
        "expected_return": 0.18, "volatility": 0.28, "risk_level": "medio-alto",
        "description": "Farmacéutica líder en medicamentos para diabetes y obesidad. Sus fármacos Ozempic/Mounjaro revolucionaron el mercado.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Eli Lilly: lidera el mercado de medicamentos para obesidad",
    },
    {
        "id": "mrk",
        "name": "Merck (MRK)",
        "category": "CEDEARs", "sub": "Salud",
        "ticker": "MRK", "color": "#0f766e",
        "expected_return": 0.11, "volatility": 0.18, "risk_level": "bajo-medio",
        "description": "Farmacéutica global con cartera diversificada. Keytruda es el oncológico más vendido del mundo.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Merck: farmacéutica global líder en oncología",
    },

    # ══ CEDEARs — CONSUMO ══════════════════════════════════════════════════════

    {
        "id": "hd",
        "name": "Home Depot (HD)",
        "category": "CEDEARs", "sub": "Consumo",
        "ticker": "HD", "color": "#f97316",
        "expected_return": 0.13, "volatility": 0.22, "risk_level": "medio",
        "description": "Mayor cadena de mejoras del hogar del mundo. Muy correlacionada con el mercado inmobiliario estadounidense.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Home Depot: el mayor retailer de materiales para el hogar",
    },
    {
        "id": "cost",
        "name": "Costco (COST)",
        "category": "CEDEARs", "sub": "Consumo",
        "ticker": "COST", "color": "#1d4ed8",
        "expected_return": 0.14, "volatility": 0.20, "risk_level": "medio",
        "description": "Cadena de clubes de compras por membresía. Alta fidelidad de clientes y modelo de negocio excepcionalmente rentable.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Costco: el club de compras más rentable del mundo",
    },
    {
        "id": "mcd",
        "name": "McDonald's (MCD)",
        "category": "CEDEARs", "sub": "Consumo",
        "ticker": "MCD", "color": "#f59e0b",
        "expected_return": 0.11, "volatility": 0.17, "risk_level": "bajo-medio",
        "description": "Mayor cadena de comida rápida del mundo. Modelo de franquicias genera flujo de caja predecible y creciente.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "McDonald's: franquicias globales con flujo de caja predecible",
    },
    {
        "id": "nke",
        "name": "Nike (NKE)",
        "category": "CEDEARs", "sub": "Consumo",
        "ticker": "NKE", "color": "#1e293b",
        "expected_return": 0.12, "volatility": 0.24, "risk_level": "medio",
        "description": "Líder global en calzado y ropa deportiva. Marca icónica con fuerte poder de fijación de precios.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Nike: la marca deportiva más valiosa del mundo",
    },

    # ══ CEDEARs — ENERGÍA ══════════════════════════════════════════════════════

    {
        "id": "cvx",
        "name": "Chevron (CVX)",
        "category": "CEDEARs", "sub": "Energía",
        "ticker": "CVX", "color": "#1d4ed8",
        "expected_return": 0.11, "volatility": 0.25, "risk_level": "medio",
        "description": "Segunda petrolera de EE.UU. Alta generación de caja, dividendo sólido y exposición al precio del petróleo.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Chevron: petrolera global con dividendo sólido",
    },
    {
        "id": "nee",
        "name": "NextEra Energy (NEE)",
        "category": "CEDEARs", "sub": "Energía/Utilities",
        "ticker": "NEE", "color": "#16a34a",
        "expected_return": 0.10, "volatility": 0.18, "risk_level": "medio",
        "description": "Mayor empresa de energía renovable de EE.UU. Líder en eólica y solar. Paga dividendos crecientes y es muy defensiva.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "NextEra: el mayor productor de energía renovable de EE.UU.",
    },

    # ══ CEDEARs — TECNOLOGÍA/SEMICONDUCTORES ══════════════════════════════════

    {
        "id": "intc",
        "name": "Intel (INTC)",
        "category": "CEDEARs", "sub": "Tecnología",
        "ticker": "INTC", "color": "#0284c7",
        "expected_return": 0.08, "volatility": 0.32, "risk_level": "medio-alto",
        "description": "Fabricante histórico de microprocesadores. Atraviesa una reestructuración profunda para recuperar liderazgo en fabricación de chips.",
        "currency": "USD", "market": "BYMA/NASDAQ",
        "simple_desc": "Intel: fabricante de chips, en proceso de transformación",
    },
    {
        "id": "tsm",
        "name": "TSMC (TSM)",
        "category": "CEDEARs", "sub": "Tecnología",
        "ticker": "TSM", "color": "#0ea5e9",
        "expected_return": 0.18, "volatility": 0.35, "risk_level": "medio-alto",
        "description": "La fábrica de chips más avanzada del mundo. Produce los procesadores de Apple, NVIDIA, AMD y casi toda la industria tech.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "TSMC: fabrica los chips más avanzados del mundo para Apple y NVIDIA",
    },
    {
        "id": "qcom",
        "name": "Qualcomm (QCOM)",
        "category": "CEDEARs", "sub": "Tecnología",
        "ticker": "QCOM", "color": "#3b82f6",
        "expected_return": 0.14, "volatility": 0.30, "risk_level": "medio-alto",
        "description": "Líder en chips para smartphones y conectividad 5G. Tiene un negocio de licencias muy rentable además de los semiconductores.",
        "currency": "USD", "market": "BYMA/NASDAQ",
        "simple_desc": "Qualcomm: chips para celulares y la tecnología 5G",
    },
    {
        "id": "shop",
        "name": "Shopify (SHOP)",
        "category": "CEDEARs", "sub": "Tecnología",
        "ticker": "SHOP", "color": "#22c55e",
        "expected_return": 0.22, "volatility": 0.50, "risk_level": "alto",
        "description": "Plataforma líder de e-commerce para pequeñas y medianas empresas. Alto crecimiento en ingresos y expansión global.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Shopify: la plataforma de tiendas online más usada del mundo",
    },
    {
        "id": "pypl",
        "name": "PayPal (PYPL)",
        "category": "CEDEARs", "sub": "Tecnología",
        "ticker": "PYPL", "color": "#1d4ed8",
        "expected_return": 0.12, "volatility": 0.35, "risk_level": "medio-alto",
        "description": "Plataforma de pagos digitales global. Opera Venmo y Braintree. Bajo presión competitiva pero con enorme base de usuarios.",
        "currency": "USD", "market": "BYMA/NASDAQ",
        "simple_desc": "PayPal: pagos digitales y Venmo",
    },

    # ══ CEDEARs — CONSUMO DEFENSIVO ════════════════════════════════════════════

    {
        "id": "pg",
        "name": "Procter & Gamble (PG)",
        "category": "CEDEARs", "sub": "Consumo Masivo",
        "ticker": "PG", "color": "#1e40af",
        "expected_return": 0.08, "volatility": 0.13, "risk_level": "bajo-medio",
        "description": "Dueña de marcas como Pampers, Gillette, Tide y Pantene. Muy defensiva, paga dividendos crecientes hace más de 60 años.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "P&G: Pampers, Gillette, Tide — consumo masivo muy estable",
    },
    {
        "id": "pm",
        "name": "Philip Morris (PM)",
        "category": "CEDEARs", "sub": "Consumo Masivo",
        "ticker": "PM", "color": "#dc2626",
        "expected_return": 0.09, "volatility": 0.16, "risk_level": "medio",
        "description": "Tabacalera global en transición hacia productos sin humo (IQOS). Alto dividendo y flujo de caja muy estable.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Philip Morris: tabaco y IQOS, dividendo altísimo y estable",
    },
    {
        "id": "sbux",
        "name": "Starbucks (SBUX)",
        "category": "CEDEARs", "sub": "Consumo",
        "ticker": "SBUX", "color": "#15803d",
        "expected_return": 0.11, "volatility": 0.22, "risk_level": "medio",
        "description": "Cadena de cafeterías más grande del mundo. Modelo de franquicias, fuerte en EE.UU. y en expansión en China.",
        "currency": "USD", "market": "BYMA/NASDAQ",
        "simple_desc": "Starbucks: la cadena de cafeterías más grande del mundo",
    },
    {
        "id": "tgt",
        "name": "Target (TGT)",
        "category": "CEDEARs", "sub": "Consumo",
        "ticker": "TGT", "color": "#dc2626",
        "expected_return": 0.10, "volatility": 0.24, "risk_level": "medio",
        "description": "Cadena de retail en EE.UU. Mezcla de supermercado y tienda de ropa/hogar. Dividendos crecientes hace más de 50 años.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Target: retail generalista en EE.UU. con dividendos históricos",
    },

    # ══ CEDEARs — INDUSTRIAL ═══════════════════════════════════════════════════

    {
        "id": "ba",
        "name": "Boeing (BA)",
        "category": "CEDEARs", "sub": "Industrial",
        "ticker": "BA", "color": "#1e40af",
        "expected_return": 0.12, "volatility": 0.40, "risk_level": "alto",
        "description": "Fabricante de aviones comerciales y militares. Atraviesa una recuperación post-crisis de seguridad. Alta volatilidad.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Boeing: aviones comerciales y militares, en proceso de recuperación",
    },
    {
        "id": "cat",
        "name": "Caterpillar (CAT)",
        "category": "CEDEARs", "sub": "Industrial",
        "ticker": "CAT", "color": "#f59e0b",
        "expected_return": 0.13, "volatility": 0.26, "risk_level": "medio",
        "description": "Mayor fabricante de maquinaria de construcción y minería del mundo. Se beneficia de inversión en infraestructura global.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Caterpillar: maquinaria de construcción y minería a nivel mundial",
    },

    # ══ CEDEARs — GLOBAL/EMERGENTES ═══════════════════════════════════════════

    {
        "id": "baba",
        "name": "Alibaba (BABA)",
        "category": "CEDEARs", "sub": "Tecnología",
        "ticker": "BABA", "color": "#f97316",
        "expected_return": 0.14, "volatility": 0.42, "risk_level": "alto",
        "description": "El gigante chino del e-commerce y cloud. Valuación muy baja respecto a fundamentals. Riesgo regulatorio chino es el principal factor.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Alibaba: el Amazon de China, muy barato pero con riesgo político",
    },

    # ══ ETFs GLOBALES (via CEDEAR) ═════════════════════════════════════════════

    {
        "id": "spy",
        "name": "ETF S&P 500 (SPY)",
        "category": "ETFs",
        "sub": "Índice USA",
        "ticker": "SPY",
        "color": "#10d98a",
        "expected_return": 0.11,
        "volatility": 0.17,
        "risk_level": "medio",
        "description": "Replica las 500 empresas más grandes de EE.UU. Apple, Microsoft, Amazon, Google... todas juntas en una sola inversión. Muy recomendado para principiantes.",
        "currency": "USD",
        "market": "BYMA/NYSE",
        "simple_desc": "Las 500 empresas más grandes de EE.UU. en una sola compra",
    },
    {
        "id": "qqq",
        "name": "ETF Nasdaq 100 (QQQ)",
        "category": "ETFs",
        "sub": "Índice Tech USA",
        "ticker": "QQQ",
        "color": "#059669",
        "expected_return": 0.14,
        "volatility": 0.22,
        "risk_level": "medio-alto",
        "description": "Replica las 100 empresas tecnológicas del Nasdaq. Más crecimiento que el S&P 500 pero con mayor volatilidad.",
        "currency": "USD",
        "market": "BYMA/NASDAQ",
        "simple_desc": "Las 100 empresas tech más grandes de EE.UU.",
    },
    {
        "id": "eem",
        "name": "ETF Mercados Emergentes (EEM)",
        "category": "ETFs",
        "sub": "Emergentes Global",
        "ticker": "EEM",
        "color": "#047857",
        "expected_return": 0.09,
        "volatility": 0.20,
        "risk_level": "medio",
        "description": "Exposición a economías emergentes: China, India, Brasil, México, Corea. Diversificación geográfica amplia.",
        "currency": "USD",
        "market": "BYMA/NYSE",
        "simple_desc": "Acceso a economías emergentes de todo el mundo",
    },
    {
        "id": "iau",
        "name": "ETF Oro (IAU)",
        "category": "ETFs",
        "sub": "Commodities",
        "ticker": "IAU",
        "color": "#d97706",
        "expected_return": 0.06,
        "volatility": 0.14,
        "risk_level": "bajo-medio",
        "description": "Fondo que replica el precio del oro. Reserva de valor histórica, protege en momentos de crisis. No paga dividendos.",
        "currency": "USD",
        "market": "BYMA/NYSE",
        "simple_desc": "Invertir en oro sin necesidad de comprarlo físicamente",
    },

    {
        "id": "vti",
        "name": "ETF Mercado Total USA (VTI)",
        "category": "ETFs",
        "sub": "Índice USA",
        "ticker": "VTI",
        "color": "#0d9488",
        "expected_return": 0.11,
        "volatility": 0.17,
        "risk_level": "medio",
        "description": "Replica todo el mercado bursátil de EE.UU.: más de 3.800 empresas en un solo fondo. Más diversificado que el SPY.",
        "currency": "USD",
        "market": "BYMA/NYSE",
        "simple_desc": "Todo el mercado americano en una sola inversión",
    },
    {
        "id": "gld",
        "name": "ETF Oro (GLD)",
        "category": "ETFs",
        "sub": "Commodities",
        "ticker": "GLD",
        "color": "#ca8a04",
        "expected_return": 0.06,
        "volatility": 0.14,
        "risk_level": "bajo-medio",
        "description": "El ETF de oro más grande del mundo. Reserva de valor clásica, descorrelacionado de acciones. Sube en momentos de crisis e incertidumbre.",
        "currency": "USD",
        "market": "BYMA/NYSE",
        "simple_desc": "Oro físico respaldado, el refugio anti-crisis clásico",
    },

    # ══ ACCIONES ARGENTINAS ════════════════════════════════════════════════════

    {
        "id": "ypf",
        "name": "YPF (YPFD)",
        "category": "Acciones ARG",
        "sub": "Energía ARG",
        "ticker": "YPFD",
        "color": "#f59e0b",
        "expected_return": 0.18,
        "volatility": 0.45,
        "risk_level": "alto",
        "description": "Empresa estatal petrolera argentina. Muy volátil pero con alto potencial si Argentina crece. Ligada al proyecto Vaca Muerta.",
        "currency": "ARS",
        "market": "BYMA",
        "simple_desc": "La petrolera estatal argentina, ligada a Vaca Muerta",
    },
    {
        "id": "galicia",
        "name": "Banco Galicia (GGAL)",
        "category": "Acciones ARG",
        "sub": "Financiero ARG",
        "ticker": "GGAL",
        "color": "#ef4444",
        "expected_return": 0.20,
        "volatility": 0.50,
        "risk_level": "alto",
        "description": "Uno de los bancos privados más grandes de Argentina. Muy sensible al ciclo económico local. Alto riesgo y alto potencial.",
        "currency": "ARS",
        "market": "BYMA",
        "simple_desc": "Banco Galicia, uno de los mayores bancos privados argentinos",
    },
    {
        "id": "teco2",
        "name": "Telecom Argentina (TECO2)",
        "category": "Acciones ARG",
        "sub": "Telecomunicaciones ARG",
        "ticker": "TECO2",
        "color": "#3b82f6",
        "expected_return": 0.15,
        "volatility": 0.38,
        "risk_level": "alto",
        "description": "Empresa de telecomunicaciones líder en Argentina. Ofrece internet, telefonía y TV. Más defensiva que YPF o bancos.",
        "currency": "ARS",
        "market": "BYMA",
        "simple_desc": "Telecom Argentina, líder en internet y telefonía",
    },
    {
        "id": "pampa",
        "name": "Pampa Energía (PAMP)",
        "category": "Acciones ARG",
        "sub": "Energía ARG",
        "ticker": "PAMP",
        "color": "#f97316",
        "expected_return": 0.17,
        "volatility": 0.42,
        "risk_level": "alto",
        "description": "Empresa energética argentina. Genera electricidad y tiene negocios en gas. Ligada al desarrollo energético del país.",
        "currency": "ARS",
        "market": "BYMA",
        "simple_desc": "Pampa Energía, empresa de electricidad y gas argentina",
    },

    {
        "id": "vist",
        "name": "Vista Energy (VIST)",
        "category": "Acciones ARG",
        "sub": "Energía ARG",
        "ticker": "VIST",
        "color": "#b45309",
        "expected_return": 0.22,
        "volatility": 0.48,
        "risk_level": "alto",
        "description": "Empresa de petróleo y gas con foco en Vaca Muerta. Una de las de mayor crecimiento en Argentina. Cotiza en NYSE y BYMA.",
        "currency": "ARS",
        "market": "BYMA/NYSE",
        "simple_desc": "Vista Energy: petróleo de Vaca Muerta, alta proyección",
    },
    {
        "id": "bbar",
        "name": "Banco BBVA Argentina (BBAR)",
        "category": "Acciones ARG",
        "sub": "Financiero ARG",
        "ticker": "BBAR",
        "color": "#0891b2",
        "expected_return": 0.18,
        "volatility": 0.48,
        "risk_level": "alto",
        "description": "Filial argentina del BBVA, uno de los bancos privados más grandes del país. Muy sensible al ciclo económico argentino.",
        "currency": "ARS",
        "market": "BYMA",
        "simple_desc": "Banco BBVA Argentina, uno de los mayores bancos privados",
    },
    {
        "id": "loma",
        "name": "Loma Negra (LOMA)",
        "category": "Acciones ARG",
        "sub": "Industria ARG",
        "ticker": "LOMA",
        "color": "#78716c",
        "expected_return": 0.14,
        "volatility": 0.40,
        "risk_level": "alto",
        "description": "La cementera más grande de Argentina. Se beneficia del crecimiento en construcción e infraestructura. Más defensiva que bancos o petroleras.",
        "currency": "ARS",
        "market": "BYMA",
        "simple_desc": "Loma Negra: la cementera más grande de Argentina",
    },
    {
        "id": "bma",
        "name": "Banco Macro (BMA)",
        "category": "Acciones ARG", "sub": "Financiero ARG",
        "ticker": "BMA", "color": "#f59e0b",
        "expected_return": 0.25, "volatility": 0.65, "risk_level": "alto",
        "description": "Segundo banco privado de Argentina por depósitos. Fuerte presencia en el interior del país.",
        "currency": "ARS", "market": "BYMA",
        "simple_desc": "Banco Macro: el segundo banco privado de Argentina",
    },
    {
        "id": "supv",
        "name": "Supervielle (SUPV)",
        "category": "Acciones ARG", "sub": "Financiero ARG",
        "ticker": "SUPV", "color": "#ef4444",
        "expected_return": 0.22, "volatility": 0.70, "risk_level": "alto",
        "description": "Banco mediano con fuerte componente digital. Mayor volatilidad que Galicia o Macro, mayor potencial de rebote.",
        "currency": "ARS", "market": "BYMA",
        "simple_desc": "Supervielle: banco argentino con foco digital",
    },
    {
        "id": "tgs",
        "name": "Transportadora Gas del Sur (TGS)",
        "category": "Acciones ARG", "sub": "Energía ARG",
        "ticker": "TGSU2", "color": "#0ea5e9",
        "expected_return": 0.18, "volatility": 0.50, "risk_level": "alto",
        "description": "Mayor transportadora de gas natural de Argentina. Infraestructura crítica que conecta Vaca Muerta con el resto del país.",
        "currency": "ARS", "market": "BYMA",
        "simple_desc": "TGS: la arteria de gas que conecta Vaca Muerta",
    },
    {
        "id": "cepu",
        "name": "Central Puerto (CEPU)",
        "category": "Acciones ARG", "sub": "Energía ARG",
        "ticker": "CEPU", "color": "#a3e635",
        "expected_return": 0.16, "volatility": 0.45, "risk_level": "alto",
        "description": "Principal generadora de energía eléctrica de Argentina. Se beneficia de la normalización tarifaria en el sector.",
        "currency": "ARS", "market": "BYMA",
        "simple_desc": "Central Puerto: la mayor generadora eléctrica del país",
    },
    {
        "id": "alua",
        "name": "Aluar Aluminio (ALUA)",
        "category": "Acciones ARG", "sub": "Industria ARG",
        "ticker": "ALUA", "color": "#64748b",
        "expected_return": 0.18, "volatility": 0.45, "risk_level": "alto",
        "description": "Mayor productora de aluminio de Argentina. Exporta gran parte de su producción. Se beneficia de la devaluación del peso al tener ingresos en dólares.",
        "currency": "ARS", "market": "BYMA",
        "simple_desc": "Mayor productora de aluminio de Argentina, con ingresos en dólares",
    },
    {
        "id": "irsa",
        "name": "IRSA Propiedades Comerciales (IRCP)",
        "category": "Acciones ARG", "sub": "Real Estate ARG",
        "ticker": "IRCP", "color": "#8b5cf6",
        "expected_return": 0.20, "volatility": 0.55, "risk_level": "alto",
        "description": "Mayor empresa de real estate comercial de Argentina. Dueña de shoppings, oficinas y el hotel Llao Llao.",
        "currency": "ARS", "market": "BYMA",
        "simple_desc": "IRSA: el mayor propietario de shoppings y oficinas en Argentina",
    },
    {
        "id": "cres",
        "name": "Cresud (CRES)",
        "category": "Acciones ARG", "sub": "Agro ARG",
        "ticker": "CRES", "color": "#84cc16",
        "expected_return": 0.18, "volatility": 0.55, "risk_level": "alto",
        "description": "Empresa agropecuaria argentina con campos en 4 países. Dueña de IRSA y con fuerte exposición a commodities agrícolas.",
        "currency": "ARS", "market": "BYMA",
        "simple_desc": "Cresud: campos y agro en Argentina, Brasil, Bolivia y Paraguay",
    },

    # ══ NUEVAS ACCIONES ARG — Panel Merval faltante ═══════════════════════════

    {
        "id": "edn", "name": "Edenor (EDN)", "category": "Acciones ARG",
        "sub": "Utilities ARG", "ticker": "EDN", "color": "#f59e0b",
        "expected_return": 0.20, "volatility": 0.50, "risk_level": "alto",
        "description": "Distribuidora eléctrica más grande de Argentina. Se beneficia de la normalización tarifaria. Alto apalancamiento operativo con la economía local.",
        "currency": "ARS", "market": "BYMA/NYSE",
        "simple_desc": "La distribuidora eléctrica más grande de Argentina",
    },
    {
        "id": "come", "name": "Comercial del Plata (COME)", "category": "Acciones ARG",
        "sub": "Holding ARG", "ticker": "COME", "color": "#0ea5e9",
        "expected_return": 0.18, "volatility": 0.48, "risk_level": "alto",
        "description": "Holding diversificado con exposición a energía (Metrogas, Compañía General de Combustibles), real estate y servicios. Apuesta al crecimiento del mercado interno argentino.",
        "currency": "ARS", "market": "BYMA",
        "simple_desc": "Holding argentino con exposición a energía, real estate y servicios",
    },
    {
        "id": "valo", "name": "Grupo Financiero Valores (VALO)", "category": "Acciones ARG",
        "sub": "Financiero ARG", "ticker": "VALO", "color": "#6366f1",
        "expected_return": 0.22, "volatility": 0.55, "risk_level": "alto",
        "description": "Broker y banco digital argentino. Crece con el aumento del uso de instrumentos financieros en Argentina. Exposición directa al desarrollo del mercado de capitales local.",
        "currency": "ARS", "market": "BYMA",
        "simple_desc": "Broker y banco digital, crece con el mercado de capitales argentino",
    },
    {
        "id": "harg", "name": "Holcim Argentina (HARG)", "category": "Acciones ARG",
        "sub": "Construcción ARG", "ticker": "HARG", "color": "#78716c",
        "expected_return": 0.16, "volatility": 0.42, "risk_level": "alto",
        "description": "Productora de cemento y materiales de construcción. Se beneficia del crecimiento de la obra pública y privada. Filial argentina de Holcim, grupo global líder en materiales.",
        "currency": "ARS", "market": "BYMA",
        "simple_desc": "Productora de cemento, crece con la construcción argentina",
    },
    {
        "id": "txar", "name": "Ternium Argentina (TXAR)", "category": "Acciones ARG",
        "sub": "Industria ARG", "ticker": "TXAR", "color": "#6b7280",
        "expected_return": 0.16, "volatility": 0.43, "risk_level": "alto",
        "description": "Productora de acero plano en Argentina. Filial de Ternium, grupo siderúrgico regional. Abastece a la industria automotriz, la construcción y el campo.",
        "currency": "ARS", "market": "BYMA",
        "simple_desc": "Mayor productora de acero de Argentina, filial de Ternium",
    },
    {
        "id": "mirg", "name": "Mirgor (MIRG)", "category": "Acciones ARG",
        "sub": "Industria ARG", "ticker": "MIRG", "color": "#8b5cf6",
        "expected_return": 0.20, "volatility": 0.55, "risk_level": "alto",
        "description": "Fabrica equipos de climatización, electrónica y accesorios para autos en Tierra del Fuego. Se beneficia de la protección arancelaria y del crecimiento del consumo.",
        "currency": "ARS", "market": "BYMA",
        "simple_desc": "Fábrica de electrónica y climatización con protección arancelaria",
    },
    {
        "id": "moli", "name": "Molinos Río de la Plata (MOLI)", "category": "Acciones ARG",
        "sub": "Consumo ARG", "ticker": "MOLI", "color": "#a3a3a3",
        "expected_return": 0.14, "volatility": 0.38, "risk_level": "medio-alto",
        "description": "Empresa de alimentos: fideos (Matarazzo, Don Vicente), aceites (Cocinero, Lira) y arroz. Marca líder en consumo masivo, defensiva dentro del universo argentino.",
        "currency": "ARS", "market": "BYMA",
        "simple_desc": "Fideos Matarazzo y aceite Cocinero — consumo masivo argentino defensivo",
    },
    {
        "id": "cvh", "name": "Cablevisión Holding (CVH)", "category": "Acciones ARG",
        "sub": "Telecomunicaciones ARG", "ticker": "CVH", "color": "#22d3ee",
        "expected_return": 0.15, "volatility": 0.40, "risk_level": "alto",
        "description": "Holding controlante de Telecom Argentina (Fibertel, Personal, Flow). Exposición al crecimiento del mercado de telecomunicaciones e internet en Argentina.",
        "currency": "ARS", "market": "BYMA",
        "simple_desc": "Dueña de Telecom, Personal y Fibertel en Argentina",
    },
    {
        "id": "metr", "name": "Metrogas (METR)", "category": "Acciones ARG",
        "sub": "Utilities ARG", "ticker": "METR", "color": "#f97316",
        "expected_return": 0.18, "volatility": 0.44, "risk_level": "alto",
        "description": "Distribuidora de gas natural en el área metropolitana de Buenos Aires. Negocio regulado que se beneficia de la normalización tarifaria post-congelamiento.",
        "currency": "ARS", "market": "BYMA",
        "simple_desc": "Distribuidora de gas en Gran Buenos Aires, beneficiaria de la desregulación",
    },

    # ══ NUEVOS CEDEARs — Bancos y Finanzas ═══════════════════════════════════════

    {
        "id": "wfc", "name": "Wells Fargo (WFC)", "category": "CEDEARs",
        "sub": "Bancos", "ticker": "WFC", "color": "#dc2626",
        "expected_return": 0.10, "volatility": 0.28, "risk_level": "medio",
        "description": "Tercer banco más grande de EE.UU. por activos. Foco en banca retail e hipotecas. Se beneficia de tasas altas y de la normalización regulatoria post-escándalo 2016.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Tercer banco más grande de EE.UU., foco en banca retail",
    },
    {
        "id": "c", "name": "Citigroup (C)", "category": "CEDEARs",
        "sub": "Bancos", "ticker": "C", "color": "#1d4ed8",
        "expected_return": 0.11, "volatility": 0.30, "risk_level": "medio",
        "description": "Banco global con presencia en más de 160 países. En proceso de reestructuración bajo la CEO Jane Fraser. Cotiza con descuento al valor libro — potencial de rerating.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Banco global en 160 países, cotiza con descuento al libro",
    },
    {
        "id": "axp", "name": "American Express (AXP)", "category": "CEDEARs",
        "sub": "Financiero", "ticker": "AXP", "color": "#0ea5e9",
        "expected_return": 0.12, "volatility": 0.26, "risk_level": "medio",
        "description": "Red de pagos y servicios financieros premium. A diferencia de Visa/Mastercard, también presta dinero a sus tarjetahabientes. Modelo de negocio único con altos márgenes.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "American Express: tarjetas premium con modelo de negocio único",
    },
    {
        "id": "cof", "name": "Capital One (COF)", "category": "CEDEARs",
        "sub": "Financiero", "ticker": "COF", "color": "#ef4444",
        "expected_return": 0.12, "volatility": 0.32, "risk_level": "medio",
        "description": "Banco digital y de tarjetas de crédito. Pionero en data analytics para crédito al consumo. Adquirió Discover Financial, creando el mayor emisor de tarjetas de crédito de EE.UU.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Banco digital líder en tarjetas, adquirió Discover Financial",
    },
    {
        "id": "schw", "name": "Charles Schwab (SCHW)", "category": "CEDEARs",
        "sub": "Financiero", "ticker": "SCHW", "color": "#2563eb",
        "expected_return": 0.11, "volatility": 0.30, "risk_level": "medio",
        "description": "Broker y banco de inversión para el mercado retail americano. Gestiona más de USD 8 billones en activos. Beneficiario directo del auge del inversor minorista.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Charles Schwab: el broker más grande de EE.UU. para inversores minoristas",
    },
    {
        "id": "blk", "name": "BlackRock (BLK)", "category": "CEDEARs",
        "sub": "Financiero", "ticker": "BLK", "color": "#1e293b",
        "expected_return": 0.11, "volatility": 0.25, "risk_level": "medio",
        "description": "La gestora de activos más grande del mundo con más de USD 10 billones bajo gestión. Creadores de iShares (los ETFs que usa todo el mundo). Ingresos recurrentes y escalables.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "La gestora de activos más grande del mundo — creadores de iShares",
    },

    # ══ NUEVOS CEDEARs — Tech/SaaS/Cloud ═════════════════════════════════════════

    {
        "id": "pltr", "name": "Palantir (PLTR)", "category": "CEDEARs",
        "sub": "Tecnología", "ticker": "PLTR", "color": "#7c3aed",
        "expected_return": 0.20, "volatility": 0.55, "risk_level": "alto",
        "description": "Software de análisis de datos para gobiernos y empresas. Su plataforma AIP integra IA en operaciones críticas. Contratos con el Ejército de EE.UU. y grandes corporaciones.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Palantir: análisis de datos e IA para gobiernos y empresas grandes",
    },
    {
        "id": "now", "name": "ServiceNow (NOW)", "category": "CEDEARs",
        "sub": "Tecnología", "ticker": "NOW", "color": "#16a34a",
        "expected_return": 0.16, "volatility": 0.30, "risk_level": "medio-alto",
        "description": "Plataforma líder de automatización empresarial y gestión de servicios IT. Crece más del 20% anual con alta retención de clientes. El 'sistema operativo' de las grandes empresas.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "ServiceNow: el sistema operativo de automatización para empresas grandes",
    },
    {
        "id": "crwd", "name": "CrowdStrike (CRWD)", "category": "CEDEARs",
        "sub": "Tecnología", "ticker": "CRWD", "color": "#dc2626",
        "expected_return": 0.18, "volatility": 0.40, "risk_level": "alto",
        "description": "Líder en ciberseguridad basada en IA. Su plataforma Falcon protege endpoints de millones de dispositivos en tiempo real. El aumento de ciberataques impulsa su crecimiento estructural.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "CrowdStrike: líder en ciberseguridad con IA para empresas",
    },
    {
        "id": "panw", "name": "Palo Alto Networks (PANW)", "category": "CEDEARs",
        "sub": "Tecnología", "ticker": "PANW", "color": "#ea580c",
        "expected_return": 0.16, "volatility": 0.35, "risk_level": "medio-alto",
        "description": "Empresa de ciberseguridad integral: firewalls, cloud security y SIEM. Consolida el mercado fragmentado de seguridad IT. Transición a modelo de suscripción con ingresos recurrentes.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Palo Alto: plataforma integral de ciberseguridad para empresas",
    },
    {
        "id": "ddog", "name": "Datadog (DDOG)", "category": "CEDEARs",
        "sub": "Tecnología", "ticker": "DDOG", "color": "#854d0e",
        "expected_return": 0.18, "volatility": 0.42, "risk_level": "alto",
        "description": "Plataforma de monitoreo de infraestructura cloud y aplicaciones. Cada empresa que migra a la nube necesita Datadog para ver qué pasa. Crecimiento superior al 25% anual.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Datadog monitorea toda la infraestructura cloud de las empresas",
    },
    {
        "id": "net", "name": "Cloudflare (NET)", "category": "CEDEARs",
        "sub": "Tecnología", "ticker": "NET", "color": "#f97316",
        "expected_return": 0.18, "volatility": 0.45, "risk_level": "alto",
        "description": "Red de seguridad y rendimiento para internet. Protege y acelera millones de sitios web. Construyendo el 'sistema nervioso' de internet con más de 200 datacenters globales.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Cloudflare protege y acelera el tráfico de internet a escala global",
    },
    {
        "id": "ftnt", "name": "Fortinet (FTNT)", "category": "CEDEARs",
        "sub": "Tecnología", "ticker": "FTNT", "color": "#b45309",
        "expected_return": 0.14, "volatility": 0.32, "risk_level": "medio-alto",
        "description": "Proveedor de ciberseguridad para medianas y grandes empresas. FortiGate es el firewall más desplegado del mundo. Margen operativo superior al 25% con modelo de hardware+software.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Fortinet: el firewall más usado del mundo para empresas",
    },
    {
        "id": "coin", "name": "Coinbase (COIN)", "category": "CEDEARs",
        "sub": "Tecnología", "ticker": "COIN", "color": "#2563eb",
        "expected_return": 0.25, "volatility": 0.70, "risk_level": "alto",
        "description": "El exchange de criptomonedas más grande de EE.UU. regulado. Se beneficia de los ciclos alcistas de crypto y del avance de la regulación favorable. Alta volatilidad ligada al precio de Bitcoin.",
        "currency": "USD", "market": "BYMA/NASDAQ",
        "simple_desc": "Coinbase: el exchange de crypto más grande y regulado de EE.UU.",
    },
    {
        "id": "sq", "name": "Block (SQ)", "category": "CEDEARs",
        "sub": "Tecnología", "ticker": "SQ", "color": "#18181b",
        "expected_return": 0.16, "volatility": 0.48, "risk_level": "alto",
        "description": "Empresa de Jack Dorsey: Square (pagos para negocios), Cash App (pagos P2P), y TBD (bitcoin). Ecosistema financiero integrado para individuos y pequeños negocios.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Block (Square + Cash App): ecosistema de pagos para negocios y personas",
    },
    {
        "id": "hood", "name": "Robinhood (HOOD)", "category": "CEDEARs",
        "sub": "Financiero", "ticker": "HOOD", "color": "#16a34a",
        "expected_return": 0.20, "volatility": 0.60, "risk_level": "alto",
        "description": "App de inversión que democratizó el trading en EE.UU. con comisiones cero. Crece en criptomonedas y opciones. Alta volatilidad ligada al sentimiento del inversor retail.",
        "currency": "USD", "market": "BYMA/NASDAQ",
        "simple_desc": "Robinhood: la app que popularizó el trading gratuito en EE.UU.",
    },
    {
        "id": "rblx", "name": "Roblox (RBLX)", "category": "CEDEARs",
        "sub": "Tecnología", "ticker": "RBLX", "color": "#dc2626",
        "expected_return": 0.18, "volatility": 0.55, "risk_level": "alto",
        "description": "Plataforma de juegos y metaverso con 60+ millones de usuarios activos diarios, mayoritariamente menores de 17 años. Economía virtual con moneda propia (Robux).",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Roblox: plataforma de juegos y metaverso con 60M usuarios diarios",
    },
    {
        "id": "snow", "name": "Snowflake (SNOW)", "category": "CEDEARs",
        "sub": "Tecnología", "ticker": "SNOW", "color": "#38bdf8",
        "expected_return": 0.18, "volatility": 0.50, "risk_level": "alto",
        "description": "Plataforma de datos en la nube. Permite a las empresas almacenar, analizar y compartir datos entre nubes. El 'hub de datos' del ecosistema cloud empresarial.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Snowflake: la plataforma de datos en la nube para empresas grandes",
    },

    # ══ NUEVOS CEDEARs — Pharma / Biotech ════════════════════════════════════════

    {
        "id": "abbv", "name": "AbbVie (ABBV)", "category": "CEDEARs",
        "sub": "Salud", "ticker": "ABBV", "color": "#7e22ce",
        "expected_return": 0.11, "volatility": 0.22, "risk_level": "medio",
        "description": "Gigante farmacéutico creador de Humira (el medicamento más vendido de la historia). Transición exitosa hacia Skyrizi y Rinvoq. Dividendo superior al 3% con 50+ años de incrementos.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "AbbVie fabrica Humira y paga dividendo superior al 3% hace décadas",
    },
    {
        "id": "bmy", "name": "Bristol-Myers Squibb (BMY)", "category": "CEDEARs",
        "sub": "Salud", "ticker": "BMY", "color": "#1d4ed8",
        "expected_return": 0.09, "volatility": 0.22, "risk_level": "medio",
        "description": "Empresa farmacéutica con foco en oncología e inmunología. Opdivo y Eliquis son sus productos estrella. Cotiza con descuento al sector por vencimientos de patentes.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Bristol-Myers: oncología e inmunología con descuento al sector",
    },
    {
        "id": "gild", "name": "Gilead Sciences (GILD)", "category": "CEDEARs",
        "sub": "Salud", "ticker": "GILD", "color": "#0f766e",
        "expected_return": 0.10, "volatility": 0.22, "risk_level": "medio",
        "description": "Líder en antivirales: inventó el tratamiento para el HIV y desarrolló Remdesivir para COVID. Pipeline sólido en oncología. Cotiza a múltiplos bajos con dividendo estable.",
        "currency": "USD", "market": "BYMA/NASDAQ",
        "simple_desc": "Gilead inventó el tratamiento del HIV — antivirales líderes con dividendo",
    },
    {
        "id": "amgn", "name": "Amgen (AMGN)", "category": "CEDEARs",
        "sub": "Salud", "ticker": "AMGN", "color": "#0369a1",
        "expected_return": 0.10, "volatility": 0.22, "risk_level": "medio",
        "description": "Pioneer en biotecnología. Produce medicamentos para cáncer, artritis y enfermedades cardiovasculares. MariTide, su candidato para obesidad, puede ser un catalizador enorme.",
        "currency": "USD", "market": "BYMA/NASDAQ",
        "simple_desc": "Amgen: biotecnología pionera con candidato para obesidad en pipeline",
    },
    {
        "id": "mrna", "name": "Moderna (MRNA)", "category": "CEDEARs",
        "sub": "Salud", "ticker": "MRNA", "color": "#0891b2",
        "expected_return": 0.15, "volatility": 0.55, "risk_level": "alto",
        "description": "Empresa de ARNm que revolucionó las vacunas con COVID-19. Desarrolla vacunas contra influenza, RSV, VIH y cáncer personalizado. Alto riesgo/retorno por pipeline no diversificado.",
        "currency": "USD", "market": "BYMA/NASDAQ",
        "simple_desc": "Moderna inventó las vacunas de ARNm y trabaja en cáncer personalizado",
    },
    {
        "id": "regn", "name": "Regeneron (REGN)", "category": "CEDEARs",
        "sub": "Salud", "ticker": "REGN", "color": "#4338ca",
        "expected_return": 0.12, "volatility": 0.28, "risk_level": "medio",
        "description": "Biotecnológica con Dupixent (biológico más vendido en dermatología y asma) y Eylea (oftalmología). Crecimiento sostenido con pipeline fuerte en oncología.",
        "currency": "USD", "market": "BYMA/NASDAQ",
        "simple_desc": "Regeneron hace Dupixent — el biológico más vendido en dermatología",
    },
    {
        "id": "vrtx", "name": "Vertex Pharmaceuticals (VRTX)", "category": "CEDEARs",
        "sub": "Salud", "ticker": "VRTX", "color": "#0e7490",
        "expected_return": 0.13, "volatility": 0.26, "risk_level": "medio",
        "description": "Monopolio en fibrosis quística con Trikafta. Expande hacia enfermedades renales, dolor y diabetes tipo 1. Sólida posición de caja sin deuda y con alta rentabilidad.",
        "currency": "USD", "market": "BYMA/NASDAQ",
        "simple_desc": "Vertex tiene monopolio en fibrosis quística y expande a nuevas enfermedades",
    },

    # ══ NUEVOS CEDEARs — Consumo / Viajes ════════════════════════════════════════

    {
        "id": "low", "name": "Lowe's (LOW)", "category": "CEDEARs",
        "sub": "Consumo", "ticker": "LOW", "color": "#1d4ed8",
        "expected_return": 0.11, "volatility": 0.24, "risk_level": "medio",
        "description": "Segunda cadena de ferreterías y mejoras del hogar de EE.UU. tras Home Depot. Se beneficia del envejecimiento del parque habitacional americano y la cultura DIY.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Lowe's: la segunda ferretería más grande de EE.UU. — rival de Home Depot",
    },
    {
        "id": "tjx", "name": "TJX Companies (TJX)", "category": "CEDEARs",
        "sub": "Consumo", "ticker": "TJX", "color": "#dc2626",
        "expected_return": 0.11, "volatility": 0.21, "risk_level": "bajo-medio",
        "description": "Dueña de TJ Maxx, Marshalls y HomeGoods. Vende ropa y artículos para el hogar con descuento. Negocio contracíclico: crece más cuando la economía va mal.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "TJ Maxx y Marshalls: descuentos en ropa — negocio que crece en crisis",
    },
    {
        "id": "abnb", "name": "Airbnb (ABNB)", "category": "CEDEARs",
        "sub": "Consumo", "ticker": "ABNB", "color": "#f43f5e",
        "expected_return": 0.14, "volatility": 0.40, "risk_level": "medio-alto",
        "description": "Marketplace de alojamiento con 7 millones de propiedades en 220 países. Generó rentabilidad real por primera vez en 2022. Se beneficia del boom del turismo post-pandemia.",
        "currency": "USD", "market": "BYMA/NASDAQ",
        "simple_desc": "Airbnb: 7 millones de propiedades en 220 países — turismo global",
    },
    {
        "id": "bkng", "name": "Booking Holdings (BKNG)", "category": "CEDEARs",
        "sub": "Consumo", "ticker": "BKNG", "color": "#2563eb",
        "expected_return": 0.13, "volatility": 0.28, "risk_level": "medio",
        "description": "Dueña de Booking.com, Kayak y Priceline. Domina el mercado global de reservas online de hoteles con márgenes altísimos y flujo de caja predecible.",
        "currency": "USD", "market": "BYMA/NASDAQ",
        "simple_desc": "Booking.com y Kayak: dominan las reservas de viaje online en el mundo",
    },
    {
        "id": "mar", "name": "Marriott International (MAR)", "category": "CEDEARs",
        "sub": "Consumo", "ticker": "MAR", "color": "#991b1b",
        "expected_return": 0.11, "volatility": 0.27, "risk_level": "medio",
        "description": "La cadena hotelera más grande del mundo con 30 marcas (Marriott, Sheraton, W, Ritz-Carlton). Modelo de franquicia con ingresos recurrentes sin riesgo de propiedad.",
        "currency": "USD", "market": "BYMA/NASDAQ",
        "simple_desc": "Marriott tiene 30 marcas hoteleras — modelo de franquicia sin riesgo de propiedad",
    },
    {
        "id": "hlt", "name": "Hilton (HLT)", "category": "CEDEARs",
        "sub": "Consumo", "ticker": "HLT", "color": "#0369a1",
        "expected_return": 0.11, "volatility": 0.26, "risk_level": "medio",
        "description": "Segunda cadena hotelera del mundo con Hilton, Hampton y Conrad entre sus 18 marcas. Modelo asset-light de franquicias con alta generación de caja y programa de fidelidad líder.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Hilton: 18 marcas hoteleras con modelo de franquicia puro",
    },
    {
        "id": "ccl", "name": "Carnival Corporation (CCL)", "category": "CEDEARs",
        "sub": "Consumo", "ticker": "CCL", "color": "#0f766e",
        "expected_return": 0.13, "volatility": 0.45, "risk_level": "alto",
        "description": "La empresa de cruceros más grande del mundo con Carnival, Princess y Costa. En recuperación post-COVID con demanda récord. Endeudada pero generando caja positiva.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Carnival: la empresa de cruceros más grande del mundo, en recuperación",
    },
    {
        "id": "rcl", "name": "Royal Caribbean (RCL)", "category": "CEDEARs",
        "sub": "Consumo", "ticker": "RCL", "color": "#1e40af",
        "expected_return": 0.14, "volatility": 0.45, "risk_level": "alto",
        "description": "Segunda empresa de cruceros del mundo. Más premium que Carnival. Las reservas para 2024-2026 están en máximos históricos. Se beneficia del boom del turismo experiencial.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Royal Caribbean: cruceros premium con reservas en máximos históricos",
    },
    {
        "id": "dkng", "name": "DraftKings (DKNG)", "category": "CEDEARs",
        "sub": "Consumo", "ticker": "DKNG", "color": "#16a34a",
        "expected_return": 0.18, "volatility": 0.55, "risk_level": "alto",
        "description": "Líder en apuestas deportivas online en EE.UU. Se beneficia de la legalización progresiva en nuevos estados. Negocio con alto costo de adquisición pero retención fuerte.",
        "currency": "USD", "market": "BYMA/NASDAQ",
        "simple_desc": "DraftKings: líder en apuestas deportivas online en EE.UU.",
    },
    {
        "id": "ebay", "name": "eBay (EBAY)", "category": "CEDEARs",
        "sub": "Consumo", "ticker": "EBAY", "color": "#e11d48",
        "expected_return": 0.09, "volatility": 0.25, "risk_level": "medio",
        "description": "Marketplace de comercio electrónico C2C y B2C con 130 millones de compradores activos. Negocio maduro con alto flujo de caja y recompras agresivas. Alternativa defensiva al ecommerce.",
        "currency": "USD", "market": "BYMA/NASDAQ",
        "simple_desc": "eBay: marketplace maduro con 130M compradores y recompras agresivas",
    },

    # ══ NUEVOS CEDEARs — Media / Telecom ═════════════════════════════════════════

    {
        "id": "spot", "name": "Spotify (SPOT)", "category": "CEDEARs",
        "sub": "Tecnología", "ticker": "SPOT", "color": "#16a34a",
        "expected_return": 0.16, "volatility": 0.40, "risk_level": "alto",
        "description": "La plataforma de música en streaming más grande del mundo con 600M usuarios. Expansión a podcasts y audiolibros. En transición hacia rentabilidad con mejora de márgenes.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Spotify: 600 millones de usuarios en música y podcasts, camino a la rentabilidad",
    },
    {
        "id": "t", "name": "AT&T (T)", "category": "CEDEARs",
        "sub": "Telecomunicaciones", "ticker": "T", "color": "#00a8e0",
        "expected_return": 0.08, "volatility": 0.20, "risk_level": "bajo-medio",
        "description": "Operadora de telecomunicaciones más grande de EE.UU. Dividendo superior al 5%. Post-desinversión de WarnerMedia, foco en conectividad con fuerte generación de caja.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "AT&T: el mayor operador de telecom de EE.UU. con dividendo superior al 5%",
    },
    {
        "id": "vz", "name": "Verizon (VZ)", "category": "CEDEARs",
        "sub": "Telecomunicaciones", "ticker": "VZ", "color": "#cd0000",
        "expected_return": 0.08, "volatility": 0.18, "risk_level": "bajo-medio",
        "description": "Segunda operadora de telecom de EE.UU. Red 5G más extensa del país. Dividendo superior al 6% con historial de 20 años consecutivos de pagos. Perfil defensivo.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Verizon: red 5G líder en EE.UU. con dividendo superior al 6%",
    },
    {
        "id": "cmcsa", "name": "Comcast (CMCSA)", "category": "CEDEARs",
        "sub": "Telecomunicaciones", "ticker": "CMCSA", "color": "#1d4ed8",
        "expected_return": 0.09, "volatility": 0.22, "risk_level": "medio",
        "description": "Cable, internet, NBC Universal y Sky (Europa). El proveedor de internet más grande de EE.UU. con ingresos muy predecibles. Dueño de Universal Studios y Peacock.",
        "currency": "USD", "market": "BYMA/NASDAQ",
        "simple_desc": "Comcast: el mayor proveedor de internet de EE.UU. más NBC Universal",
    },

    # ══ NUEVOS CEDEARs — Industrial / Defensa ════════════════════════════════════

    {
        "id": "rtx", "name": "RTX Corporation (RTX)", "category": "CEDEARs",
        "sub": "Industrial", "ticker": "RTX", "color": "#1e3a5f",
        "expected_return": 0.11, "volatility": 0.22, "risk_level": "medio",
        "description": "Ex-Raytheon Technologies. Fabrica motores de aviones (Pratt & Whitney) y sistemas de defensa (misiles Patriot). Cartera de pedidos récord por el aumento del gasto militar global.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "RTX fabrica motores Pratt & Whitney y misiles Patriot — defensa récord",
    },
    {
        "id": "lmt", "name": "Lockheed Martin (LMT)", "category": "CEDEARs",
        "sub": "Industrial", "ticker": "LMT", "color": "#0f172a",
        "expected_return": 0.10, "volatility": 0.20, "risk_level": "medio",
        "description": "Mayor contratista de defensa del mundo. Fabrica el F-35, misiles y sistemas espaciales. El aumento del gasto en defensa de los países de la OTAN es un viento de cola estructural.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Lockheed: el mayor fabricante de defensa del mundo, F-35 y misiles",
    },
    {
        "id": "de", "name": "John Deere (DE)", "category": "CEDEARs",
        "sub": "Industrial", "ticker": "DE", "color": "#15803d",
        "expected_return": 0.11, "volatility": 0.24, "risk_level": "medio",
        "description": "Líder mundial en maquinaria agrícola y de construcción. Integra IA y autonomía en sus tractores. Dominio de mercado en EE.UU. con ciclo favorable para el agro global.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "John Deere: tractores inteligentes con IA — domina el agro mundial",
    },
    {
        "id": "hon", "name": "Honeywell (HON)", "category": "CEDEARs",
        "sub": "Industrial", "ticker": "HON", "color": "#dc2626",
        "expected_return": 0.10, "volatility": 0.21, "risk_level": "medio",
        "description": "Conglomerado industrial en automatización, aeroespacial y materiales de rendimiento. Ingresos muy diversificados y predecibles. Dividendo creciente desde hace décadas.",
        "currency": "USD", "market": "BYMA/NASDAQ",
        "simple_desc": "Honeywell: automatización e industrial diversificado con dividendo estable",
    },
    {
        "id": "ups", "name": "UPS (UPS)", "category": "CEDEARs",
        "sub": "Industrial", "ticker": "UPS", "color": "#78350f",
        "expected_return": 0.09, "volatility": 0.22, "risk_level": "medio",
        "description": "Mayor empresa de logística y mensajería del mundo. Dividendo superior al 4%. En transformación hacia paquetes de mayor valor con margen. Infraestructura imposible de replicar.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "UPS: logística mundial con dividendo superior al 4%",
    },
    {
        "id": "fdx", "name": "FedEx (FDX)", "category": "CEDEARs",
        "sub": "Industrial", "ticker": "FDX", "color": "#7c3aed",
        "expected_return": 0.11, "volatility": 0.26, "risk_level": "medio",
        "description": "Red de mensajería express y logística global. En proceso de reestructuración post-COVID para mejorar márgenes. Se beneficia del e-commerce y del comercio internacional.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "FedEx: logística express global — se beneficia del e-commerce",
    },
    {
        "id": "ge", "name": "GE Aerospace (GE)", "category": "CEDEARs",
        "sub": "Industrial", "ticker": "GE", "color": "#2563eb",
        "expected_return": 0.13, "volatility": 0.28, "risk_level": "medio",
        "description": "GE enfocada en motores de aviación civil y militar tras la ruptura del conglomerado. Cartera de pedidos histórica con el boom del tráfico aéreo post-pandemia.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "GE Aerospace: motores de aviación con cartera de pedidos histórica",
    },

    # ══ NUEVOS CEDEARs — Energía ══════════════════════════════════════════════════

    {
        "id": "oxy", "name": "Occidental Petroleum (OXY)", "category": "CEDEARs",
        "sub": "Energía", "ticker": "OXY", "color": "#ea580c",
        "expected_return": 0.12, "volatility": 0.35, "risk_level": "medio-alto",
        "description": "Productora de petróleo y gas con exposición directa a Permian Basin. La acción favorita de Warren Buffett en energía — Berkshire acumuló más del 27% del capital.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Occidental Petroleum: la apuesta energética favorita de Warren Buffett",
    },
    {
        "id": "slb", "name": "SLB (SLB)", "category": "CEDEARs",
        "sub": "Energía", "ticker": "SLB", "color": "#a16207",
        "expected_return": 0.12, "volatility": 0.30, "risk_level": "medio",
        "description": "La mayor empresa de servicios para la industria petrolera del mundo. Provee tecnología y servicios de perforación a productores en todo el mundo. Se beneficia del superciclo de inversión en energía.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "SLB: la mayor empresa de servicios de perforación petrolera del mundo",
    },
    {
        "id": "cop", "name": "ConocoPhillips (COP)", "category": "CEDEARs",
        "sub": "Energía", "ticker": "COP", "color": "#92400e",
        "expected_return": 0.11, "volatility": 0.30, "risk_level": "medio",
        "description": "La mayor productora independiente de petróleo y gas de EE.UU. Bajo costo de producción, dividendo variable ligado al precio del crudo, y balance sólido sin deuda excesiva.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "ConocoPhillips: mayor productora independiente de petróleo de EE.UU.",
    },

    # ══ NUEVOS CEDEARs — Semiconductores ═════════════════════════════════════════

    {
        "id": "asml", "name": "ASML (ASML)", "category": "CEDEARs",
        "sub": "Tecnología", "ticker": "ASML", "color": "#0c4a6e",
        "expected_return": 0.15, "volatility": 0.30, "risk_level": "medio-alto",
        "description": "Monopolio absoluto en litografía EUV para chips avanzados. Sin ASML no existe ningún chip de última generación. TSMC, Samsung e Intel son clientes cautivos. Barreras de entrada imposibles.",
        "currency": "USD", "market": "BYMA/NASDAQ",
        "simple_desc": "ASML: el único proveedor de máquinas que hacen chips avanzados — monopolio absoluto",
    },
    {
        "id": "mu", "name": "Micron Technology (MU)", "category": "CEDEARs",
        "sub": "Tecnología", "ticker": "MU", "color": "#1d4ed8",
        "expected_return": 0.14, "volatility": 0.40, "risk_level": "alto",
        "description": "Mayor productor de memoria DRAM y NAND de EE.UU. Ciclo altamente volátil ligado a la demanda de semiconductores. El boom de IA aumenta la demanda de HBM3 (memoria para GPUs).",
        "currency": "USD", "market": "BYMA/NASDAQ",
        "simple_desc": "Micron: memoria RAM para IA y data centers — ciclo volátil pero alcista",
    },
    {
        "id": "amat", "name": "Applied Materials (AMAT)", "category": "CEDEARs",
        "sub": "Tecnología", "ticker": "AMAT", "color": "#4f46e5",
        "expected_return": 0.13, "volatility": 0.30, "risk_level": "medio-alto",
        "description": "Equipos para la fabricación de semiconductores: deposición, grabado y metrología. Junto con ASML y Lam Research, domina el segmento de equipos que nadie puede reemplazar.",
        "currency": "USD", "market": "BYMA/NASDAQ",
        "simple_desc": "Applied Materials: máquinas indispensables para fabricar semiconductores",
    },
    {
        "id": "avgo", "name": "Broadcom (AVGO)", "category": "CEDEARs",
        "sub": "Tecnología", "ticker": "AVGO", "color": "#c2410c",
        "expected_return": 0.14, "volatility": 0.30, "risk_level": "medio-alto",
        "description": "Semiconductor y software de infraestructura. Fabrica chips de red, WiFi y conectividad para Apple e hyperscalers. VMware (adquirida) convierte a Broadcom en lider de infraestructura cloud.",
        "currency": "USD", "market": "BYMA/NASDAQ",
        "simple_desc": "Broadcom: chips para Apple y data centers + VMware para la nube empresarial",
    },

    # ══ NUEVOS CEDEARs — Auto / EV ════════════════════════════════════════════════

    {
        "id": "f", "name": "Ford Motor (F)", "category": "CEDEARs",
        "sub": "Industrial", "ticker": "F", "color": "#1d4ed8",
        "expected_return": 0.10, "volatility": 0.35, "risk_level": "medio-alto",
        "description": "Fabricante de autos con fuerte posición en pickup trucks (F-Series, el auto más vendido de EE.UU.). Transición hacia eléctricos con Ford Pro (camionetas comerciales) como punta de lanza.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Ford: el F-150 es el auto más vendido de EE.UU. — transición a eléctricos",
    },
    {
        "id": "gm", "name": "General Motors (GM)", "category": "CEDEARs",
        "sub": "Industrial", "ticker": "GM", "color": "#1e293b",
        "expected_return": 0.11, "volatility": 0.32, "risk_level": "medio-alto",
        "description": "Fabricante de autos con Chevrolet, GMC, Cadillac y Buick. Cotiza con múltiplos de empresa en quiebra a pesar de ganancias récord. Cruze Robotaxi y el pipeline EV son los catalizadores.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "GM: Chevrolet y Cadillac — cotiza barato con Cruise y EVs como catalizadores",
    },
    {
        "id": "rivn", "name": "Rivian (RIVN)", "category": "CEDEARs",
        "sub": "Tecnología", "ticker": "RIVN", "color": "#16a34a",
        "expected_return": 0.20, "volatility": 0.65, "risk_level": "alto",
        "description": "Startup de vehículos eléctricos con pickup R1T, SUV R1S y furgonetas para Amazon. Alta volatilidad de empresa pre-rentabilidad. Amazon posee ~16% y es su mayor cliente comercial.",
        "currency": "USD", "market": "BYMA/NASDAQ",
        "simple_desc": "Rivian: pickups y SUVs eléctricos — Amazon como socio estratégico",
    },
    {
        "id": "nio", "name": "NIO (NIO)", "category": "CEDEARs",
        "sub": "Tecnología", "ticker": "NIO", "color": "#ef4444",
        "expected_return": 0.20, "volatility": 0.70, "risk_level": "alto",
        "description": "Fabricante chino de EVs de lujo. Tecnología de batería intercambiable (battery swap) diferencial. Alto riesgo por competencia de BYD, quema de caja y geopolítica China-EE.UU.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "NIO: EVs de lujo chinos con tecnología de batería intercambiable",
    },

    # ══ NUEVOS CEDEARs — Utilities ════════════════════════════════════════════════

    {
        "id": "so", "name": "Southern Company (SO)", "category": "CEDEARs",
        "sub": "Utilities", "ticker": "SO", "color": "#d97706",
        "expected_return": 0.08, "volatility": 0.16, "risk_level": "bajo",
        "description": "Eléctrica regulada en el sur de EE.UU. Dividendo superior al 3.5% con 75+ años de pagos ininterrumpidos. Primera utilidad americana en operar una planta nuclear nueva en décadas.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Southern Company: eléctrica regulada con 75 años de dividendos ininterrumpidos",
    },
    {
        "id": "d", "name": "Dominion Energy (D)", "category": "CEDEARs",
        "sub": "Utilities", "ticker": "D", "color": "#0369a1",
        "expected_return": 0.08, "volatility": 0.17, "risk_level": "bajo",
        "description": "Eléctrica y gasífera regulada en Virginia y Carolina del Norte. Dividendo superior al 4.5%. En proceso de simplificación del portfolio. Proveedor crítico de data centers en Virginia.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Dominion Energy: utilities en Virginia con dividendo 4.5% y data centers",
    },

    # ══ NUEVOS CEDEARs — REITs ════════════════════════════════════════════════════

    {
        "id": "amt", "name": "American Tower (AMT)", "category": "CEDEARs",
        "sub": "Real Estate", "ticker": "AMT", "color": "#7c3aed",
        "expected_return": 0.10, "volatility": 0.22, "risk_level": "medio",
        "description": "El mayor REIT de infraestructura de comunicaciones del mundo con 220.000+ torres de telecom. Contratos a largo plazo con AT&T, Verizon y T-Mobile con escaladores de inflación.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "American Tower: dueño de 220.000 torres de celular — alquiler garantizado",
    },
    {
        "id": "pld", "name": "Prologis (PLD)", "category": "CEDEARs",
        "sub": "Real Estate", "ticker": "PLD", "color": "#0369a1",
        "expected_return": 0.10, "volatility": 0.24, "risk_level": "medio",
        "description": "Mayor REIT de logística del mundo con 1.000 millones de m² de depósitos. Clientes: Amazon, FedEx, DHL. Los depósitos cerca de ciudades son el activo más escaso del e-commerce.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Prologis: 1.000M m² de depósitos para Amazon y el e-commerce global",
    },
    {
        "id": "o", "name": "Realty Income (O)", "category": "CEDEARs",
        "sub": "Real Estate", "ticker": "O", "color": "#15803d",
        "expected_return": 0.09, "volatility": 0.18, "risk_level": "bajo-medio",
        "description": "El REIT de dividendo mensual más conocido del mundo. 'The Monthly Dividend Company' — 30 años de dividendos crecientes pagados cada mes. Inquilinos como Walmart, 7-Eleven y Dollar General.",
        "currency": "USD", "market": "BYMA/NYSE",
        "simple_desc": "Realty Income paga dividendo mensual hace 30 años — inquilinos son Walmart y 7-Eleven",
    },

]

# ─── Índice por ID ─────────────────────────────────────────────────────────────
ASSET_INDEX = {a["id"]: a for a in ASSET_UNIVERSE}

# ─── Liquidez en BYMA ──────────────────────────────────────────────────────────
# alta  = volumen alto, rescate inmediato o mismo día
# media = volumen medio o mercado alternativo (exchanges, ONs)
# baja  = poco volumen en BYMA, solo para agresivos con horizonte ≥5 años
_LIQUIDITY_LEVELS = {
    "alta":  {
        # Pesos e instrumentos locales
        "cash_pesos","money_market","plazo_fijo","fci_t0","lecap",
        "cer_tx26","cer_tx28","fci_renta_pesos","mep",
        # Soberanos USD más líquidos (AL30/GD30 operan >$10M/día en BYMA)
        "al30","gd30","al35","gd35","gd29","gd41",
        # CEDEARs de alto volumen en BYMA
        "spy","qqq","aapl","meli","ypf","galicia","bma","msft","nvda","v","ma",
        "intc","tsm","pg",
        "wfc","c","axp","abbv","amgn","avgo","asml","ge","rtx","lmt","de","cop","oxy","ups","vz","t",
    },
    "media": {
        # Soberanos con algo menos de volumen
        "gd38",
        # ONs corporativas
        "on_ypf","on_corp","on_tecpetrol","on_tgs","on_macro",
        "on_meli","on_telecom","on_genneia","on_vista","on_pampa",
        "on_tgs2","on_arcor","on_telecom2","on_irsa",
        "dual_bond","dollar_linked",
        # Bono CER largo plazo
        "cer_dicp",
        # FCIs USD y ARS adicionales
        "fci_usd_rf","fci_usd_ahorro","fci_latam",
        "fci_acciones","fci_cedears","fci_mixto",
        # ETFs alternativos
        "gld","iau","vti","eem",
        # CEDEARs de volumen medio en BYMA
        "googl","amzn","meta","brk","jpm","bac","tsla","ko","wmt","jnj",
        "pfe","xom","dis","amd","nflx","orcl","crm","adbe","uber","glob",
        "gs","ms","unh","lly","mrk","hd","cost","mcd","nke","cvx",
        "qcom","shop","pypl","pm","sbux","tgt","ba","cat","baba","nee",
        # Acciones ARG de liquidez media en BYMA
        "tgs","cepu","alua","bbar","loma","pampa","vist","teco2","supv",
        # CEDEARs nuevos
        "cof","schw","blk","pltr","now","crwd","panw","ddog","net","ftnt","coin","sq",
        "hood","rblx","snow","bmy","gild","mrna","regn","vrtx","low","tjx","abnb","bkng",
        "mar","hlt","ccl","rcl","dkng","ebay","spot","cmcsa","hon","fdx","slb",
        "mu","amat","f","gm","rivn","nio","so","d","amt","pld","o",
        # ARG nuevas
        "edn","come","valo","harg","txar","mirg","moli","cvh","metr",
    },
}
for _a in ASSET_UNIVERSE:
    for _lev, _ids in _LIQUIDITY_LEVELS.items():
        if _a["id"] in _ids:
            _a["liquidity"] = _lev
            break
    else:
        _a["liquidity"] = "baja"


# ─── Plantillas de cartera por perfil ─────────────────────────────────────────
# Máximo de posiciones por perfil (tarea 1 + 3)
_MAX_POSITIONS = {
    "conservador": 5,
    "estable":     7,
    "moderado":    8,
    "agresivo":    12,
}

# Peso máximo global por activo individual (post-Markowitz, post-score-caps)
_MAX_WEIGHT_GLOBAL = {
    "conservador": 0.30,
    "estable":     0.25,
    "moderado":    0.20,
    "agresivo":    0.15,
}

PORTFOLIO_TEMPLATES = {
    "conservador": {
        "expected_cagr": 0.073,
        "expected_volatility": 0.07,
        "description": "Prioriza la seguridad y la liquidez. Ideal para quien no quiere arriesgar su capital.",
        "summary": "Su cartera está diseñada para preservar el valor del capital con el menor riesgo posible. Dólares legales, bonos de empresas sólidas y algo de acciones globales para crecimiento moderado.",
        "allocations": {
            "money_market": 0.12,   # liquidez ARS
            "lecap":        0.07,   # pesos a tasa fija del Tesoro
            "mep":          0.18,   # dólares legales por la bolsa
            "on_corp":      0.18,   # bonos de empresas privadas en USD
            "iau":          0.20,   # oro — cobertura global
            "spy":          0.25,   # mercado global
        },
    },
    "estable": {
        "expected_cagr": 0.082,
        "expected_volatility": 0.09,
        "description": "Mejor que un plazo fijo, sin sustos. Para quien quiere protegerse de la inflación con algo de crecimiento.",
        "summary": "Su cartera está diseñada para superar al plazo fijo sin exponerse a riesgos significativos. Combina dólares seguros, bonos de empresas sólidas y exposición moderada a acciones globales.",
        "allocations": {
            "mep":          0.18,   # dólares legales, base sólida
            "on_corp":      0.18,   # renta fija en USD de empresas privadas
            "money_market": 0.10,   # liquidez en pesos
            "lecap":        0.10,   # pesos a tasa fija
            "spy":          0.25,   # exposición al mercado global
            "iau":          0.19,   # oro — cobertura global
        },
    },
    "moderado": {
        "expected_cagr": 0.105,
        "expected_volatility": 0.14,
        "description": "Equilibrio entre crecimiento y protección. Mezcla inversiones seguras con algo de riesgo controlado.",
        "summary": "Su cartera equilibra estabilidad y crecimiento. Una base sólida en activos seguros complementada con exposición a acciones globales que potencian el rendimiento a mediano plazo.",
        "allocations": {
            "spy":          0.28,   # columna vertebral: 500 mayores empresas de EE.UU.
            "money_market": 0.10,   # liquidez en pesos
            "mep":          0.12,   # dólares base
            "on_corp":      0.12,   # renta fija en USD
            "qqq":          0.22,   # las 100 mayores empresas tech de EE.UU.
            "nvda":         0.16,   # posición equity global top-score
        },
    },
    "agresivo": {
        "expected_cagr": 0.165,
        "expected_volatility": 0.28,
        "description": "Maximiza el crecimiento a largo plazo, aceptando que puede haber caídas fuertes en el camino.",
        "summary": "Su cartera apunta al máximo crecimiento. Asume caídas de corto plazo a cambio de mejores resultados a largo plazo. Tecnología global diversificada vía ETFs, energía argentina y exposición a activos de alto potencial.",
        "allocations": {
            "qqq":     0.30,   # Nasdaq 100: ya incluye NVDA, MSFT, AAPL, META, AMZN
            "mep":     0.18,   # base en dólares
            "ypf":     0.14,   # energía argentina: Vaca Muerta
            "galicia": 0.11,   # financiero argentino
            "al30":    0.09,   # bono soberano USD
            "eem":     0.09,   # mercados emergentes: diversificación geográfica
            "meli":    0.09,   # MercadoLibre: tech latam (no está en QQQ ni SPY)
        },
    },
}


# ─── Buckets de construcción por perfil ───────────────────────────────────────
# Cada bucket define la CATEGORÍA que ocupa, su peso objetivo, cuántas posiciones
# puede aportar y qué activos son candidatos.
#
# score_src:
#   "equity" → usa scores Finviz (con ARG adjustment y min_score por perfil)
#   "bond"   → usa scores de bond_scorer (ranking relativo, sin min_score absoluto)
#   None     → activo estructural fijo, no filtrable por score
#
# La selección dentro del bucket: top-N por score, ponderados por score.
# Si no hay scores disponibles: igual ponderación entre los candidatos.

_BUCKET_DEFS: Dict[str, list] = {
    "conservador": [
        # 5 posiciones — máximo teórico según Evans & Archer (1968)
        {"id": "liquidez",  "target": 0.12, "max_pos": 1, "score_src": None,
         "candidates": ["money_market"]},
        {"id": "cobertura", "target": 0.18, "max_pos": 1, "score_src": None,
         "candidates": ["mep"]},
        {"id": "rf",        "target": 0.28, "max_pos": 1, "score_src": "bond",
         "candidates": ["lecap", "cer_tx26", "cer_tx28", "dual_bond", "dollar_linked",
                         "on_corp", "on_ypf", "on_tecpetrol", "on_tgs", "on_macro",
                         "on_tgs2", "on_arcor", "on_telecom2",
                         "al30", "gd30", "al35", "gd35",
                         "fci_usd_rf", "fci_usd_ahorro"]},
        {"id": "defensivo", "target": 0.22, "max_pos": 1, "score_src": "equity",
         "candidates": ["iau", "gld"]},
        {"id": "globales",  "target": 0.20, "max_pos": 1, "score_src": "equity",
         "candidates": ["spy", "vti"]},
    ],
    "estable": [
        # 7 posiciones
        {"id": "liquidez",  "target": 0.10, "max_pos": 1, "score_src": None,
         "candidates": ["money_market"]},
        {"id": "cobertura", "target": 0.18, "max_pos": 1, "score_src": None,
         "candidates": ["mep"]},
        {"id": "rf_pesos",  "target": 0.10, "max_pos": 1, "score_src": "bond",
         "candidates": ["lecap", "cer_tx26", "cer_tx28", "cer_dicp", "dual_bond", "dollar_linked"]},
        {"id": "rf_usd",    "target": 0.18, "max_pos": 1, "score_src": "bond",
         "candidates": ["on_corp", "on_ypf", "on_tecpetrol", "on_tgs", "on_macro",
                         "on_tgs2", "on_arcor", "on_telecom2", "on_irsa", "on_cresud",
                         "al30", "gd30", "al35", "gd35",
                         "fci_usd_rf", "fci_usd_ahorro", "on_meli", "on_telecom",
                         "on_genneia", "on_vista", "on_pampa", "gd29", "gd41"]},
        {"id": "globales",  "target": 0.22, "max_pos": 1, "score_src": "equity",
         "candidates": ["spy", "vti", "qqq"]},
        {"id": "defensivo", "target": 0.12, "max_pos": 1, "score_src": "equity",
         "candidates": ["iau", "gld"]},
        {"id": "equity_g",  "target": 0.10, "max_pos": 1, "score_src": "equity",
         "candidates": ["msft", "nvda", "tsm", "meta", "googl", "avgo", "mu", "gild", "vrtx"]},
    ],
    "moderado": [
        # 7 posiciones — ~38% ARG
        {"id": "liquidez",      "target": 0.10, "max_pos": 1, "score_src": None,
         "candidates": ["money_market"]},
        {"id": "cobertura",     "target": 0.12, "max_pos": 1, "score_src": None,
         "candidates": ["mep"]},
        {"id": "rf_usd",        "target": 0.12, "max_pos": 1, "score_src": "bond",
         "candidates": ["on_corp", "on_ypf", "on_tgs", "on_macro",
                         "on_tgs2", "on_arcor", "on_telecom2", "on_irsa", "on_cresud",
                         "al30", "gd30", "al35", "gd35",
                         "on_meli", "on_telecom", "on_genneia", "on_vista", "on_pampa",
                         "gd29", "gd41", "fci_usd_rf"]},
        {"id": "etf_global",    "target": 0.28, "max_pos": 2, "score_src": "equity",
         "candidates": ["spy", "qqq", "vti", "fci_cedears", "fci_mixto"]},
        {"id": "equity_global", "target": 0.22, "max_pos": 1, "score_src": "equity",
         "candidates": ["nvda", "amd", "msft", "meta", "googl", "amzn", "aapl",
                         "tsm", "v", "ma", "unh", "lly", "cost", "nflx", "orcl",
                         "crm", "qcom", "pg", "pm", "cat",
                         "wfc", "c", "axp", "abbv", "amgn", "avgo", "asml", "ge", "rtx", "lmt", "de", "cop",
                         "now", "crwd", "panw", "vrtx", "regn", "low", "tjx", "bkng", "mar", "vz", "t", "hon", "ups", "blk"]},
        {"id": "equity_arg",    "target": 0.16, "max_pos": 1, "score_src": "equity",
         "candidates": ["ypf", "galicia", "bma", "tgs", "cepu", "pampa",
                         "vist", "meli", "alua", "irsa",
                         "edn", "come", "metr", "moli", "harg", "txar",
                         "fci_acciones", "fci_cedears"]},
    ],
    "agresivo": [
        # 8 posiciones
        {"id": "cobertura",     "target": 0.18, "max_pos": 1, "score_src": None,
         "candidates": ["mep"]},
        {"id": "rf_usd",        "target": 0.09, "max_pos": 1, "score_src": "bond",
         "candidates": ["on_corp", "on_ypf", "on_tgs", "on_macro",
                         "on_tgs2", "on_arcor", "on_telecom2", "on_irsa", "on_cresud",
                         "al30", "gd30", "al35", "gd35", "gd38",
                         "on_meli", "on_telecom", "on_genneia", "on_vista", "on_pampa",
                         "gd29", "gd41"]},
        {"id": "etf_global",    "target": 0.25, "max_pos": 2, "score_src": "equity",
         "candidates": ["qqq", "spy", "vti", "eem"]},
        {"id": "equity_global", "target": 0.28, "max_pos": 3, "score_src": "equity",
         "candidates": ["nvda", "amd", "msft", "meta", "googl", "amzn", "meli",
                         "aapl", "tsla", "nflx", "v", "ma", "unh", "lly",
                         "crm", "adbe", "uber", "glob", "gs", "cost",
                         "tsm", "qcom", "shop", "pypl", "baba", "cat", "intc",
                         "wfc", "c", "axp", "cof", "schw", "blk", "pltr", "now", "crwd", "panw", "ddog", "net",
                         "ftnt", "coin", "sq", "rblx", "snow", "abbv", "amgn", "mrna", "regn", "vrtx", "bmy",
                         "low", "tjx", "abnb", "bkng", "mar", "hlt", "ccl", "rcl", "dkng", "spot",
                         "rtx", "lmt", "de", "hon", "ge", "fdx", "ups", "oxy", "slb", "cop",
                         "asml", "mu", "amat", "avgo", "f", "gm", "rivn", "nio", "amt", "pld", "o",
                         "vz", "t", "cmcsa", "ebay"]},
        {"id": "equity_arg",    "target": 0.20, "max_pos": 2, "score_src": "equity",
         "candidates": ["ypf", "galicia", "bma", "supv", "tgs", "cepu",
                         "pampa", "vist", "bbar", "alua", "irsa", "cres",
                         "loma", "teco2",
                         "edn", "come", "valo", "harg", "txar", "mirg", "moli", "cvh", "metr",
                         "fci_acciones", "fci_cedears"]},
    ],
}


def _build_from_buckets(
    risk: str,
    eq_scores: dict,
    bond_scores: dict,
) -> dict:
    """
    Construye la asignación base usando el framework de scoring.

    Por cada bucket del perfil:
    - Filtra candidatos por min_score (solo equity; bonos siempre pasan).
    - Elige top-N por score.
    - Pondera cada activo proporcionalmente a su score dentro del bucket.
    - Escala al peso objetivo del bucket.

    Si los scores están vacíos recae en peso igual entre candidatos.
    """
    allocs: dict = {}
    min_eq = MIN_SCORE_BY_RISK.get(risk, 40)

    for bucket in _BUCKET_DEFS[risk]:
        cands  = [c for c in bucket["candidates"] if c in ASSET_INDEX]
        target = bucket["target"]
        max_p  = bucket["max_pos"]
        src    = bucket.get("score_src")

        if not cands:
            continue

        # Determinar fuente de score y aplicar filtro de mínimo
        if src == "equity" and eq_scores:
            scores = eq_scores
            cands  = [c for c in cands if c not in scores or scores[c] >= min_eq]
        elif src == "bond" and bond_scores:
            scores = bond_scores
        else:
            scores = {}

        if not cands:
            continue

        # Ranking por score → top N
        ranked = sorted(cands, key=lambda c: scores.get(c, 0), reverse=True) if scores else cands
        top    = ranked[:max_p]

        # Peso proporcional al score dentro del bucket, respetando caps por perfil
        total_s = sum(scores.get(c, 50) for c in top) if scores else 0
        for c in top:
            raw_w = (target * (scores.get(c, 50) / total_s)) if total_s > 0 else (target / len(top))
            if src == "equity" and scores:
                max_w = get_max_weight(scores.get(c), risk, c)
                allocs[c] = min(raw_w, max_w) if max_w > 0 else 0.0
            else:
                allocs[c] = raw_w

    # Normalizar al 100% por si algún bucket quedó vacío
    total = sum(allocs.values())
    if total > 0:
        allocs = {k: v / total for k, v in allocs.items()}

    return allocs


def _adjust_for_horizon(allocations: dict, horizon: int, risk: str) -> dict:
    """Ajusta ponderaciones según horizonte temporal."""
    adj = dict(allocations)

    if horizon <= 2:
        # Corto plazo: más liquidez, menos equity volátil
        risky = ["ypf", "galicia", "pampa", "teco2", "qqq", "meli", "nvda", "tsla"]
        safe  = ["money_market", "plazo_fijo", "fci_t0", "mep", "lecap"]
        rescued = 0.0
        for k in risky:
            if k in adj and adj[k] > 0.04:
                cut = adj[k] * 0.4
                adj[k] -= cut
                rescued += cut
        safe_present = [k for k in safe if k in adj]
        if safe_present and rescued > 0:
            share = rescued / len(safe_present)
            for k in safe_present:
                adj[k] += share

    elif horizon >= 8:
        # Largo plazo: más equity, menos cash
        growth = [g for g in ["spy", "qqq", "nvda"] if g in adj]
        freed_total = 0.0
        for k in ["money_market", "plazo_fijo", "fci_t0", "lecap"]:
            if k in adj:
                freed = adj[k] * 0.4
                adj[k] -= freed
                freed_total += freed
        if growth and freed_total > 0:
            share = freed_total / len(growth)
            for k in growth:
                adj[k] += share

    total = sum(adj.values())
    return {k: v / total for k, v in adj.items() if v > 0.005}


def _adjust_for_emergency(allocations: dict, has_emergency: bool) -> dict:
    """Si no tiene fondo de emergencia, aumenta liquidez."""
    if has_emergency:
        return allocations
    adj = dict(allocations)
    boost = 0.06
    liquid = "money_market" if "money_market" in adj else "plazo_fijo"
    if liquid in adj:
        adj[liquid] += boost
        # Recortar proporcional al resto
        rest_total = sum(v for k, v in adj.items() if k != liquid)
        for k in adj:
            if k != liquid:
                adj[k] *= (1 - boost) / (rest_total / sum(adj.values()))
    total = sum(adj.values())
    return {k: v / total for k, v in adj.items()}


# ─── Reglas de solapamiento ────────────────────────────────────────────────────
# Top holdings reales de cada ETF (datos 2025). Si el ETF está en la cartera,
# agregar el stock individualmente duplica la exposición sin que el usuario lo sepa.
_OVERLAP_RULES = {
    "spy": {
        # Top 8 de SPY: AAPL 7%, MSFT 6%, NVDA 6%, AMZN 4%, META 3%, GOOGL 3%, TSLA 2%, BRK-B 2%
        "excludes": ["aapl", "msft", "nvda", "amzn", "meta", "googl", "tsla", "brk"],
        "reason":   "SPY ya incluye estas empresas entre sus mayores posiciones — agregarlas individualmente duplica la exposición",
    },
    "vti": {
        # VTI = mercado total EE.UU., composición similar a SPY en el top
        "excludes": ["aapl", "msft", "nvda", "amzn", "meta", "googl", "tsla"],
        "reason":   "VTI ya incluye estas empresas entre sus mayores posiciones",
    },
    "qqq": {
        # Top 8 de QQQ: MSFT 9%, AAPL 9%, NVDA 8%, AMZN 5%, META 5%, GOOGL 5%, TSLA 3%, COST 3%
        "excludes": ["aapl", "msft", "nvda", "amzn", "meta", "googl", "tsla", "cost", "nflx", "adbe"],
        "reason":   "QQQ ya incluye estas empresas en su cartera — agregarlas individualmente duplica la exposición",
    },
}


def _detect_overlaps(positions: list) -> list:
    """Detecta solapamientos entre ETFs y CEDEARs individuales."""
    ids = {p["id"] for p in positions}
    warnings = []
    for etf_id, rule in _OVERLAP_RULES.items():
        if etf_id in ids:
            conflicts = [c for c in rule["excludes"] if c in ids]
            if conflicts:
                warnings.append({
                    "etf":       ASSET_INDEX[etf_id]["name"],
                    "conflicts": [ASSET_INDEX[c]["name"] for c in conflicts],
                    "reason":    rule["reason"],
                })
    return warnings


_VOLATILE_ASSETS = {
    "nvda", "tsla", "amd", "tsm", "shop", "baba", "pypl",
    "meta", "qqq", "cepu", "tgs", "galicia", "bma", "ypf",
}
_LIQUID_SAFE = ["money_market", "mep", "lecap"]
_ETF_IDS     = {"spy", "qqq", "vti", "iau", "gld", "eem"}

_ARG_INDIVIDUAL_IDS = {
    "ypf", "vist", "galicia", "bma", "bbar", "supv", "pampa",
    "tgs", "cepu", "loma", "teco2", "irsa", "cres", "alua",
    "edn", "come", "valo", "harg", "txar", "mirg", "moli", "cvh", "metr",
}


def get_max_weight(score: int | None, profile: str, asset_id: str) -> float:
    """
    Peso máximo permitido para un activo dado su score Finviz y perfil.
    Retorna 0.0 si el activo debe excluirse del perfil.
    score=None → activo no scorable (bonos, MM, MEP) → sin límite por score.

    CONSERVADOR: solo ETFs; score>=70→10%, score 50-69→5%, <50→0%
    ESTABLE:     ETFs→15%/8%/0%; globales individuales→8%/5%/0%; ARG→0%
    MODERADO:    score>=70→15%, 50-69→8%, <50→0%; individual cap 8%; ETF cap 20%
    AGRESIVO:    score>=70→20%, 50-69→12%, 40-49→5%, <40→0%; individual cap 15%; ETF cap 25%
    """
    if score is None:
        if asset_id in _ARG_INDIVIDUAL_IDS:
            if profile == "conservador": return 0.0
            if profile == "estable":     return 0.03
            if profile == "moderado":    return 0.05
            if profile == "agresivo":    return 0.08
        return 1.0  # bonos, MM, MEP — sin límite por score

    is_etf        = asset_id in _ETF_IDS
    is_arg_ind    = asset_id in _ARG_INDIVIDUAL_IDS

    if profile == "conservador":
        if not is_etf:
            return 0.0
        if score >= 70: return 0.10
        if score >= 50: return 0.05
        return 0.0

    if profile == "estable":
        if is_arg_ind:
            return 0.0
        if is_etf:
            if score >= 70: return 0.15
            if score >= 50: return 0.08
            return 0.0
        if score >= 70: return 0.08
        if score >= 50: return 0.05
        return 0.0

    if profile == "moderado":
        if score < 50: return 0.0
        if is_etf:
            return min(0.15 if score >= 70 else 0.08, 0.20)
        return min(0.15 if score >= 70 else 0.08, 0.08)

    if profile == "agresivo":
        if score < 40: return 0.0
        if score < 50: return 0.05
        if is_etf:
            return min(0.20 if score >= 70 else 0.12, 0.25)
        return min(0.20 if score >= 70 else 0.12, 0.15)

    return 1.0


def _apply_score_caps(allocs: dict, risk: str, eq_scores: dict) -> dict:
    """
    Enforcement final: recorta cada activo equity a su límite score/perfil.
    El exceso se redistribuye (iterativamente) al siguiente activo de mayor score
    que tenga capacidad; si no hay ninguno, va a los activos estructurales
    (bonos, MEP, liquidez) que no tienen límite por score.
    """
    adj = dict(allocs)

    equity_sorted = sorted(
        [aid for aid in adj if aid in eq_scores],
        key=lambda a: eq_scores[a],
        reverse=True,
    )

    # Excluir activos con max_w=0 y redistribuir al resto
    for aid in list(equity_sorted):
        if get_max_weight(eq_scores[aid], risk, aid) == 0.0:
            excess = adj.pop(aid, 0.0)
            equity_sorted = [x for x in equity_sorted if x != aid]
            rest_total = sum(adj.values())
            if rest_total > 0 and excess > 0:
                for k in adj:
                    adj[k] += excess * (adj[k] / rest_total)

    # Iteración convergente: recortar exceso y redistribuir
    for _ in range(20):                      # max 20 rondas → siempre converge
        any_excess = False
        for i, aid in enumerate(equity_sorted):
            if aid not in adj:
                continue
            max_w = get_max_weight(eq_scores[aid], risk, aid)
            w = adj[aid]
            if w <= max_w + 1e-9:
                continue
            excess = w - max_w
            adj[aid] = max_w
            any_excess = True

            # 1. Siguiente equity de mayor score que aún tenga capacidad
            next_eq = [
                equity_sorted[j] for j in range(i + 1, len(equity_sorted))
                if equity_sorted[j] in adj
                and adj[equity_sorted[j]] < get_max_weight(
                    eq_scores[equity_sorted[j]], risk, equity_sorted[j]
                ) - 1e-9
            ]
            # 2. Si no hay, ir a activos estructurales (sin score Finviz)
            structural = [k for k in adj if k not in eq_scores]
            candidates = next_eq or structural or [k for k in adj if k != aid]

            cand_total = sum(adj[k] for k in candidates)
            if cand_total > 0:
                for k in candidates:
                    adj[k] += excess * (adj[k] / cand_total)
            elif candidates:
                per = excess / len(candidates)
                for k in candidates:
                    adj[k] += per

        if not any_excess:
            break

    total = sum(adj.values())
    if total > 0:
        adj = {k: v / total for k, v in adj.items()}
    return adj


def _adjust_for_experience(allocs: dict, experience: str) -> dict:
    """
    Principiantes sustituyen acciones individuales por ETFs o liquidez.
    Solo actúa si el usuario declaró conocimiento cero o básico.
    """
    is_beginner = any(s in experience for s in [
        "Prácticamente nada",
        "Solo conozco el plazo fijo",
    ])
    if not is_beginner:
        return allocs

    individuals = {
        k for k in allocs
        if ASSET_INDEX.get(k, {}).get("category") in ("CEDEARs", "Acciones ARG")
        and k not in _ETF_IDS
    }
    if not individuals:
        return allocs

    rescued = sum(allocs[k] for k in individuals)
    adj = {k: v for k, v in allocs.items() if k not in individuals}

    targets = [k for k in ("spy", "qqq", "vti") if k in adj] \
           or [k for k in _LIQUID_SAFE if k in adj]

    if targets:
        share = rescued / len(targets)
        for k in targets:
            adj[k] = adj.get(k, 0) + share

    total = sum(adj.values())
    return {k: v / total for k, v in adj.items()} if total > 0 else allocs


def _adjust_for_income_stability(allocs: dict, income: str) -> dict:
    """
    Ingresos inestables: sube liquidez recortando los activos más volátiles.
    Irregulares → -25% de volátiles; Variables → -12%.
    """
    if "Irregulares" in income:
        cut_pct = 0.25
    elif "Varían bastante" in income:
        cut_pct = 0.12
    else:
        return allocs

    adj = dict(allocs)
    rescued = 0.0
    for k in _VOLATILE_ASSETS:
        if k in adj and adj[k] > 0.05:
            cut = adj[k] * cut_pct
            adj[k] -= cut
            rescued += cut

    liquid_present = [k for k in _LIQUID_SAFE if k in adj]
    if liquid_present and rescued > 0:
        share = rescued / len(liquid_present)
        for k in liquid_present:
            adj[k] += share

    total = sum(adj.values())
    return {k: v / total for k, v in adj.items()} if total > 0 else allocs


def _apply_overlap_exclusion(allocations: dict) -> dict:
    """Excluye activos que solapan con ETFs presentes en la cartera."""
    ids = set(allocations.keys())
    to_remove = set()
    for etf_id, rule in _OVERLAP_RULES.items():
        if etf_id in ids:
            for conflicting in rule["excludes"]:
                if conflicting in ids:
                    to_remove.add(conflicting)
    if not to_remove:
        return allocations
    filtered = {k: v for k, v in allocations.items() if k not in to_remove}
    total = sum(filtered.values())
    return {k: v / total for k, v in filtered.items()}


def _filter_by_liquidity(allocations: dict, risk: str, horizon: int) -> dict:
    """Elimina activos de baja liquidez para perfiles conservador, estable y moderado."""
    allow_baja = (risk == "agresivo" and horizon >= 5)
    if allow_baja:
        return allocations
    filtered = {k: v for k, v in allocations.items()
                if ASSET_INDEX.get(k, {}).get("liquidity", "baja") != "baja"}
    if not filtered:
        return allocations
    total = sum(filtered.values())
    return {k: v / total for k, v in filtered.items()}


def _apply_score_filter(allocations: dict, scores: dict, risk: str) -> dict:
    """
    Excluye activos cuyo score Finviz está por debajo del mínimo del perfil.
    Activos sin score (bonos, MM, MEP) pasan siempre — no son scorables vía Finviz.
    """
    min_score = MIN_SCORE_BY_RISK.get(risk, 40)
    filtered = {
        asset_id: w
        for asset_id, w in allocations.items()
        if asset_id not in scores or scores[asset_id] >= min_score
    }
    if not filtered:
        return allocations  # fallback: no filtrar si todos quedan excluidos
    total = sum(filtered.values())
    return {k: v / total for k, v in filtered.items()}


def _trim_to_max(allocations: dict, max_pos: int, scores: dict = None) -> dict:
    """
    Mantiene las top N posiciones por Sharpe ajustado por score Finviz.
    Si scores está vacío o un activo no tiene score, usa los valores hardcodeados.
    """
    if len(allocations) <= max_pos:
        return allocations
    risk_free = 0.05

    def sharpe(asset_id: str) -> float:
        a     = ASSET_INDEX.get(asset_id, {})
        r     = a.get("expected_return", 0)
        v     = a.get("volatility", 0.1)
        score = (scores or {}).get(asset_id)
        if score is not None:
            r = r * return_factor(score)
            v = v * vol_factor(score)
        return (r - risk_free) / v if v > 0 else 0

    top_ids = sorted(allocations, key=sharpe, reverse=True)[:max_pos]
    trimmed  = {k: allocations[k] for k in top_ids}
    total    = sum(trimmed.values())
    return {k: v / total for k, v in trimmed.items()}


_STRUCTURAL_IDS = {
    "money_market", "plazo_fijo", "fci_t0", "cash_pesos", "fci_renta_pesos",
    "mep", "lecap", "cer_tx26", "cer_tx28", "cer_dicp", "al30", "gd30", "al35", "gd35", "gd38",
    "on_corp", "on_ypf", "on_tecpetrol", "on_tgs", "on_macro",
    # FCIs USD (structural — renta fija)
    "fci_usd_rf", "fci_usd_ahorro", "fci_latam",
    # ONs adicionales
    "on_meli", "on_telecom", "on_genneia", "on_vista", "on_pampa",
    # ONs nuevas
    "on_tgs2", "on_arcor", "on_telecom2", "on_irsa", "on_cresud",
    # Bonos pesos nuevos
    "dual_bond", "dollar_linked",
    # Soberanos adicionales
    "gd29", "gd41",
}


def select_top_assets(
    allocs: dict,
    risk: str,
    eq_scores: dict,
) -> dict:
    """
    Aplica límite global de posiciones por perfil (Evans & Archer, 1968).

    Lógica:
    1. Activos estructurales (liquidez, bonos, MEP) siempre se mantienen.
    2. Equity sin score mínimo requerido es eliminado; su peso redistribuido.
    3. Si el total de posiciones excede _MAX_POSITIONS[risk], se eliminan
       los equity de menor score hasta llegar al límite.
    4. Se aplica el cap máximo por activo (_MAX_WEIGHT_GLOBAL) y renormaliza.
    """
    max_pos    = _MAX_POSITIONS.get(risk, 12)
    min_score  = MIN_SCORE_BY_RISK.get(risk, 40)
    max_w      = _MAX_WEIGHT_GLOBAL.get(risk, 0.30)

    structural = {k: v for k, v in allocs.items() if k in _STRUCTURAL_IDS}
    equity     = {k: v for k, v in allocs.items() if k not in _STRUCTURAL_IDS}

    # 1. Filtrar equity por score mínimo
    passing, failing = {}, {}
    for aid, w in equity.items():
        score = eq_scores.get(aid)
        if score is None or score >= min_score:
            passing[aid] = w
        else:
            failing[aid] = w

    # Redistribuir failing equity → passing equity (proporcional)
    if failing and passing:
        fail_total = sum(failing.values())
        pass_total = sum(passing.values())
        if pass_total > 0:
            for aid in passing:
                passing[aid] += fail_total * (passing[aid] / pass_total)

    # 2. Aplicar límite global de posiciones
    slots_left = max_pos - len(structural)
    if slots_left < 1:
        slots_left = 1

    if len(passing) > slots_left:
        # Ordenar por score desc, luego por peso desc como desempate
        def sort_key(aid):
            s = eq_scores.get(aid, 0) or 0
            return (s, passing[aid])
        ranked = sorted(passing, key=sort_key, reverse=True)
        kept   = set(ranked[:slots_left])
        excess_w = sum(v for k, v in passing.items() if k not in kept)
        trimmed  = {k: v for k, v in passing.items() if k in kept}
        # Redistribuir exceso → equity mantenido
        if trimmed and excess_w > 0:
            trim_total = sum(trimmed.values())
            for aid in trimmed:
                trimmed[aid] += excess_w * (trimmed[aid] / trim_total)
        passing = trimmed

    # 3. Aplicar cap global por activo
    result = {**structural, **passing}
    total  = sum(result.values())
    if total > 0:
        result = {k: v / total for k, v in result.items()}

    # Aplicar cap y renormalizar iterativamente
    for _ in range(10):
        over   = {k: v for k, v in result.items() if v > max_w}
        if not over:
            break
        excess = sum(v - max_w for v in over.values())
        for k in over:
            result[k] = max_w
        rest_total = sum(v for k, v in result.items() if k not in over)
        if rest_total > 0:
            for k in result:
                if k not in over:
                    result[k] += excess * (result[k] / rest_total)

    total = sum(result.values())
    return {k: v / total for k, v in result.items()} if total > 0 else result


_EQUITY_CATEGORIES = {"CEDEARs", "Acciones ARG"}


def _adjust_for_sector_valuations(
    allocs: dict,
    asset_sectors: dict,
    signals: dict,
) -> dict:
    """
    Ajusta pesos de equity según la valuación histórica del sector.

    Para cada activo de renta variable con señal de sector conocida:
      - señal > 0 (sector barato vs historia) → sube el peso hasta +15%
      - señal < 0 (sector caro vs historia)   → baja el peso hasta -15%

    Bonos, liquidez y MEP no se tocan.
    Renormaliza al final para que la suma siga siendo 1.

    Si no hay señales (datos insuficientes) retorna allocs sin cambios.
    """
    if not signals:
        return allocs

    adj = dict(allocs)
    ajustes_log = []

    for asset_id, weight in allocs.items():
        asset = ASSET_INDEX.get(asset_id, {})
        if asset.get("category") not in _EQUITY_CATEGORIES:
            continue
        if asset_id in _ETF_IDS:
            continue

        sector = asset_sectors.get(asset_id)
        if not sector:
            continue
        signal = signals.get(sector, 0.0)
        if signal == 0.0:
            continue

        # Ajuste amortiguado: señal × 0.5, clampeado a ±15% del peso original
        delta = weight * signal * 0.5
        delta = max(-weight * 0.15, min(weight * 0.15, delta))
        adj[asset_id] = max(0.0, weight + delta)

        if abs(delta) > 0.001:
            ajustes_log.append(
                f"  {asset_id:<10} sector={sector:<22} señal={signal:+.2f} "
                f"peso {weight:.3f}→{adj[asset_id]:.3f}"
            )

    if ajustes_log:
        print("  [sector_val] Ajustes por valuación histórica:")
        for line in ajustes_log:
            print(line)

    total = sum(adj.values())
    if total > 0:
        adj = {k: v / total for k, v in adj.items()}
    return adj


def _razon_en_cartera(asset_id: str, risk: str, horizon: int) -> str:
    """Una frase en lenguaje simple explicando por qué este activo está en la cartera."""
    _RAZONES = {
        # Liquidez
        "cash_pesos":   "Reserva de liquidez — disponible al instante, sin costo ni espera",
        "money_market": "Rinde más que el banco todos los días de forma automática; rescate el mismo día",
        "plazo_fijo":   "Tasa garantizada en pesos, sin sorpresas — ideal para capital que no necesita moverse en 30 días",
        "fci_t0":       "Renta fija de corto plazo: rescate el mismo día hábil con mejor rendimiento que el banco",
        "fci_renta":    "Fondo diversificado en pesos que crece de forma automática sin ninguna acción adicional",
        # Cobertura
        "mep":          "Sus pesos se convierten en dólares legales, sin necesidad de operar en mercados informales — protección directa contra la devaluación",
        "dolar_mep":    "Sus pesos se convierten en dólares legales, sin necesidad de operar en mercados informales — protección directa contra la devaluación",
        # ETFs globales
        "spy":  "Las 500 empresas más grandes del mundo en una sola compra — Apple, Google, Amazon, todas juntas",
        "qqq":  "Las 100 empresas de tecnología más grandes: Microsoft, NVIDIA, Apple — el motor de la economía digital",
        "vti":  "Todo el mercado americano (4.000+ empresas) en un solo instrumento — la diversificación máxima",
        "iau":  "Oro: sube cuando todo lo demás cae — es el ancla histórica de las carteras en épocas de crisis",
        "gld":  "Oro físico en formato digital — la reserva de valor más antigua del mundo, protege contra la inflación global",
        "eem":  "India, Brasil, Corea — los países que van a crecer más en los próximos 20 años, todos juntos",
        # CEDEARs tech
        "aapl":  "Apple: más de 2.000 millones de personas usan sus productos todos los días y renuevan cada 2 años",
        "msft":  "Microsoft: el 90% de las empresas del mundo usan sus servicios — negocio estable y predecible",
        "nvda":  "NVIDIA hace los chips que corren toda la inteligencia artificial del mundo — domina el mercado",
        "amzn":  "Amazon vende de todo Y es el dueño de la nube donde viven Netflix, Airbnb y miles de empresas",
        "meta":  "Facebook, Instagram y WhatsApp: 4 de cada 5 personas en internet los usan todos los días",
        "googl": "Google controla el 90% de las búsquedas; cada vez que alguien busca algo, Google cobra",
        "tsla":  "Tesla es la empresa que está redefiniendo cómo se fabrican y venden los autos en el mundo",
        "nflx":  "Netflix tiene 260 millones de suscriptores que pagan todos los meses sin falta",
        "amd":   "AMD fabrica los procesadores que compiten con Intel y NVIDIA — con ganancia de mercado sostenida",
        # CEDEARs finanzas
        "v":    "Visa cobra una comisión en cada compra con tarjeta en el mundo — 200+ países, sin riesgo de crédito",
        "ma":   "Mastercard: mismo modelo que Visa, dos empresas que dominan los pagos globales juntas",
        "jpm":  "JPMorgan: el banco más grande de EE.UU., sobrevivió 2008 y salió más fuerte que antes",
        "gs":   "Goldman Sachs: el banco de inversión más reconocido del mundo, gana con cada gran operación",
        "brk":  "Berkshire Hathaway: Warren Buffett eligió cada empresa — diversificación con criterio de décadas",
        # CEDEARs salud
        "unh":  "UnitedHealth es el seguro médico más grande de EE.UU. — sector defensivo que crece sin parar",
        "lly":  "Eli Lilly fabrica los medicamentos para diabetes y obesidad más usados del mundo — demanda récord",
        "mrk":  "Merck tiene una de las mejores carteras de vacunas y oncología del mercado farmacéutico global",
        "jnj":  "Johnson & Johnson: el laboratorio más diversificado del mundo, paga dividendos hace 60 años",
        "pfe":  "Pfizer: la vacuna COVID le abrió la puerta a pipeline de oncología y antivirales de próxima generación",
        # CEDEARs consumo
        "ko":   "Coca-Cola vende en 200 países, paga dividendos hace 60 años — la marca más reconocida del mundo",
        "wmt":  "Walmart es el mayor empleador privado del mundo y sigue creciendo en e-commerce",
        "mcd":  "McDonald's gana dinero con las franquicias, no con las hamburguesas — modelo de negocio irrompible",
        "cost": "Costco: los socios pagan para poder comprar ahí — lealtad de cliente que ningún competidor tiene",
        "pg":   "Procter & Gamble hace jabón, shampoo y pañales — productos que la gente compra siempre, en crisis o no",
        "ko":   "Coca-Cola: la marca más reconocida del mundo, vende en 200 países, paga dividendos hace 60 años",
        "hd":   "Home Depot crece con cada casa que se construye o refacciona en EE.UU.",
        "nke":  "Nike es la marca deportiva más importante del mundo — fidelidad de marca y márgenes altos",
        # CEDEARs energía
        "xom":  "ExxonMobil: una de las empresas de petróleo más grandes del mundo, con dividendo sólido",
        "cvx":  "Chevron: petróleo y gas con posición financiera muy sólida — uno de los dividendos más confiables",
        # CEDEARs emergentes/especiales
        "meli": "MercadoLibre es el Amazon de Latinoamérica — domina e-commerce y pagos en toda la región",
        "baba": "Alibaba es el Amazon de China — precio muy castigado con potencial de recuperación",
        "tsm":  "TSMC fabrica los chips más avanzados del mundo para Apple, NVIDIA y AMD — monopolio tecnológico",
        "qcom": "Qualcomm hace los chips de cada celular Android — dominan el mercado de semiconductores móviles",
        "shop": "Shopify es la plataforma donde los pequeños negocios compiten con Amazon",
        "uber": "Uber está en 70 países y crece con delivery además de transporte — dos negocios en uno",
        "glob": "Globant es la empresa argentina de tecnología que trabaja para Disney, Google y FIFA",
        # Acciones ARG
        "ypf":     "YPF extrae el petróleo de Vaca Muerta — Argentina va a ser uno de los mayores exportadores de energía",
        "vist":    "Vista Energy explota Vaca Muerta de forma privada y eficiente — crecimiento sostenido",
        "galicia": "Banco Galicia: el banco privado más sólido de Argentina, crece con la economía",
        "bma":     "Banco Macro: fuerte en el interior del país, bien capitalizado y con bajo riesgo crediticio",
        "bbar":    "BBVA Argentina: banco sólido con respaldo internacional de uno de los mayores grupos del mundo",
        "supv":    "Supervielle: banco mediano con foco en consumo y PyMEs, posicionado para el crédito que viene",
        "pampa":   "Pampa Energía genera el 10% de la electricidad de Argentina — infraestructura crítica",
        "tgs":     "TGS opera el gasoducto que conecta Vaca Muerta con Buenos Aires — monopolio natural",
        "cepu":    "Central Puerto: la mayor generadora eléctrica térmica del país, se beneficia de la desregulación",
        "loma":    "Loma Negra produce el cemento que necesita toda la obra pública y privada de Argentina",
        "teco2":   "Telecom Argentina: internet y celular para millones de hogares — demanda que no para",
        "irsa":    "IRSA es el dueño de los shoppings más importantes del país — apuesta al consumo argentino",
        "cres":    "Cresud: campo argentino y propiedades urbanas — doble exposición al agro y los bienes raíces",
        # Bonos
        "al30":    "Bono soberano argentino en dólares 2030 — alto rendimiento con riesgo soberano; apostar a que Argentina paga",
        "gd30":    "Global 30: el bono más líquido de Argentina, con rendimiento muy alto y respaldo bajo ley NY",
        "al35":    "Bono soberano 2035 — más plazo implica mayor rendimiento potencial si Argentina normaliza",
        "gd35":    "Global 35: mayor rendimiento que el GD30, con respaldo bajo ley de Nueva York",
        "gd38":    "Global 38: el bono de mayor duración — para quien apuesta fuerte al largo plazo argentino",
        "lecap":    "LECAP: letra del Tesoro a tasa fija en pesos — vencimiento en meses, sin riesgo de precio",
        "cer_tx26": "TX26: bono corto ajustado por inflación — si la inflación sube, su capital también sube; vence 2026",
        "cer_tx28": "TX28: bono ajustado por inflación con más plazo — protege sus pesos y ofrece algo más de rendimiento que TX26",
        "cer_dicp": "DICP: bono largo CER — el mayor rendimiento del tramo en pesos, ideal para quienes pueden esperar más de 5 años",
        "on_ypf":  "Bono corporativo YPF en dólares — paga interés en USD respaldado por los activos de Vaca Muerta",
        "on_tgs":  "Bono TGS en dólares — monopolio natural de gasoductos respaldando la deuda",
        "on_macro":"Bono Banco Macro en dólares — banco argentino sólido con buen historial de pago",
        "on_corp": "ONs corporativas en dólares (YPF, TGS, Tecpetrol) — empresas privadas con mejor historial de pago que el Estado",
        # ARG nuevas
        "alua":  "Aluar produce el aluminio que exporta Argentina — ingresos en dólares protegen del peso",
        "edn":   "Edenor distribuye electricidad en Buenos Aires — beneficiaria directa de la normalización tarifaria",
        "come":  "Holding argentino diversificado en energía y real estate — exposición amplia al mercado interno",
        "valo":  "Grupo Financiero Valores crece con el mercado de capitales argentino en pleno desarrollo",
        "harg":  "Holcim produce el cemento de la obra pública y privada argentina — crece con la construcción",
        "txar":  "Ternium Argentina produce el acero para la industria automotriz y la construcción local",
        "mirg":  "Mirgor fabrica en Tierra del Fuego con protección arancelaria — crece con el consumo local",
        "moli":  "Molinos (Matarazzo, Cocinero) — consumo masivo defensivo dentro del universo argentino",
        "cvh":   "Cablevisión Holding controla Telecom y Personal — telecomunicaciones esenciales en Argentina",
        "metr":  "Metrogas distribuye gas en el área metropolitana — normalización tarifaria como catalizador",
        # CEDEARs nuevos — Bancos
        "wfc":   "Wells Fargo es el tercer banco más grande de EE.UU. y se beneficia de tasas altas",
        "c":     "Citigroup opera en 160 países — cotiza con descuento al libro con potencial de rerating",
        "axp":   "American Express cobra comisiones premium en cada compra — clientes de alta renta no cancelan",
        "cof":   "Capital One adquirió Discover — creando el mayor emisor de tarjetas de crédito de EE.UU.",
        "schw":  "Charles Schwab gestiona USD 8 billones — crece con cada inversor que abre su primera cuenta",
        "blk":   "BlackRock gestiona más de USD 10 billones — los ETFs iShares son los más usados del mundo",
        # CEDEARs nuevos — Tech/Cloud
        "pltr":  "Palantir es el software de análisis que usa el Ejército de EE.UU. y las grandes corporaciones",
        "now":   "ServiceNow automatiza los procesos internos de las grandes empresas — retención de clientes casi perfecta",
        "crwd":  "CrowdStrike protege contra ciberataques con IA — cada empresa grande necesita su plataforma",
        "panw":  "Palo Alto Networks es el firewall empresarial más completo — consolida el mercado de seguridad",
        "ddog":  "Datadog monitorea toda la infraestructura cloud — indispensable cuando las empresas migran a la nube",
        "net":   "Cloudflare protege y acelera millones de sitios web — la autopista de internet más eficiente",
        "ftnt":  "Fortinet tiene el firewall más desplegado del mundo en empresas medianas y grandes",
        "coin":  "Coinbase es el exchange de crypto más regulado de EE.UU. — crece con cada ciclo alcista de Bitcoin",
        "sq":    "Block (Square + Cash App) conecta negocios y personas en un ecosistema de pagos integrado",
        "hood":  "Robinhood popularizó el trading gratuito en EE.UU. — crece con crypto y opciones",
        "rblx":  "Roblox tiene 60 millones de usuarios diarios — la plataforma donde juegan las nuevas generaciones",
        "snow":  "Snowflake es el hub de datos en la nube que todas las grandes empresas necesitan hoy",
        # CEDEARs nuevos — Pharma
        "abbv":  "AbbVie hace Humira y paga dividendo superior al 3% — farmacéutica defensiva con pipeline sólido",
        "bmy":   "Bristol-Myers tiene Opdivo y Eliquis — oncología e inmunología con descuento al sector",
        "gild":  "Gilead inventó el tratamiento del HIV y desarrolla antivirales de nueva generación",
        "amgn":  "Amgen es pionera en biotecnología con pipeline en obesidad que puede ser el próximo catalizador",
        "mrna":  "Moderna inventó las vacunas de ARNm — trabaja en cáncer personalizado y otras enfermedades",
        "regn":  "Regeneron hace Dupixent, el biológico más vendido en dermatología y asma — crecimiento sostenido",
        "vrtx":  "Vertex tiene monopolio en fibrosis quística y expande a diabetes y enfermedades renales",
        # CEDEARs nuevos — Consumo/Viajes
        "low":   "Lowe's vende materiales de construcción a millones de hogares americanos que mejoran su casa",
        "tjx":   "TJ Maxx vende ropa con descuento — negocio que crece más en crisis que en épocas de bonanza",
        "abnb":  "Airbnb conecta 7 millones de propiedades con viajeros en 220 países — el hotel sin hoteles",
        "bkng":  "Booking.com domina las reservas de viaje online con márgenes altísimos y flujo de caja predecible",
        "mar":   "Marriott cobra royalties a 30 marcas hoteleras sin arriesgar capital propio — franquicia pura",
        "hlt":   "Hilton opera 18 marcas sin tener que comprar los hoteles — el modelo de franquicia más eficiente",
        "ccl":   "Carnival tiene la flota de cruceros más grande del mundo y reservas en máximos históricos",
        "rcl":   "Royal Caribbean ofrece cruceros premium con experiencias que la gente no deja de reservar",
        "dkng":  "DraftKings lidera las apuestas deportivas online a medida que cada estado americano las legaliza",
        "ebay":  "eBay tiene 130 millones de compradores activos y recompra sus acciones de forma agresiva",
        # CEDEARs nuevos — Media/Telecom
        "spot":  "Spotify tiene 600 millones de usuarios y está en camino a márgenes de software puro",
        "t":     "AT&T es el mayor operador de EE.UU. con dividendo superior al 5% después de vender WarnerMedia",
        "vz":    "Verizon tiene la red 5G más extensa de EE.UU. y paga dividendo superior al 6% hace décadas",
        "cmcsa": "Comcast provee internet a millones de hogares americanos y es dueño de Universal Studios",
        # CEDEARs nuevos — Industrial/Defensa
        "rtx":   "RTX fabrica motores Pratt & Whitney y misiles Patriot — el gasto militar global es un viento de cola",
        "lmt":   "Lockheed es el mayor fabricante de defensa del mundo — cada país de la OTAN es su cliente",
        "de":    "John Deere pone IA en tractores — el agro mundial no puede funcionar sin sus máquinas",
        "hon":   "Honeywell automatiza fábricas y aviones con tecnología que nadie más puede reemplazar",
        "ups":   "UPS entrega millones de paquetes al día con una red que tardó 100 años en construirse",
        "fdx":   "FedEx conecta empresas con clientes en todo el mundo — la columna vertebral del e-commerce",
        "ge":    "GE Aerospace fabrica los motores de avión con la mayor cartera de pedidos de su historia",
        # CEDEARs nuevos — Energía
        "oxy":   "Occidental Petroleum produce petróleo barato en Permian — Warren Buffett acumuló más del 27%",
        "slb":   "SLB provee la tecnología de perforación que la industria petrolera necesita para extraer crudo",
        "cop":   "ConocoPhillips es la mayor productora independiente de petróleo de EE.UU. sin deuda excesiva",
        # CEDEARs nuevos — Semis
        "asml":  "ASML es el único proveedor de máquinas para chips avanzados — monopolio que nadie puede romper",
        "mu":    "Micron fabrica la memoria para GPUs de IA — el boom de inteligencia artificial impulsa su demanda",
        "amat":  "Applied Materials fabrica equipos para hacer semiconductores — sin ellos no hay chips nuevos",
        "avgo":  "Broadcom hace chips para Apple y data centers — más VMware, el sistema de toda nube empresarial",
        # CEDEARs nuevos — Auto/EV
        "f":     "Ford vende más pickups que nadie en EE.UU. y transiciona hacia eléctricos comerciales",
        "gm":    "General Motors cotiza como si fuera a quebrar pero genera ganancias récord — descuento extremo",
        "rivn":  "Rivian hace las furgonetas eléctricas de Amazon — apuesta de alto riesgo/retorno en EVs",
        "nio":   "NIO fabrica EVs de lujo en China con tecnología de batería única — alto riesgo geopolítico",
        # CEDEARs nuevos — Utilities
        "so":    "Southern Company lleva electricidad a millones de hogares del sur de EE.UU. hace 75 años",
        "d":     "Dominion Energy provee electricidad a los data centers de Virginia — demanda que no para de crecer",
        # CEDEARs nuevos — REITs
        "amt":   "American Tower alquila torres de celular a AT&T y Verizon — cada 5G instalado paga más renta",
        "pld":   "Prologis alquila depósitos a Amazon y FedEx — la escasez de espacio logístico es estructural",
        "o":     "Realty Income paga dividendo mensual hace 30 años — el 'bono con upside' del inversor conservador",
        # FCIs USD
        "fci_usd_rf":    "Fondo en USD que invierte en ONs corporativas — dolarizate sin elegir bonos individuales",
        "fci_usd_ahorro":"Fondo ahorro en USD de muy corto plazo — alternativa al colchón con rendimiento",
        "fci_latam":     "Deuda latinoamericana: Brasil, México, Chile y Argentina en un solo fondo",
        # FCIs ARS
        "fci_acciones":  "Fondo de acciones argentinas — gestor profesional selecciona el mejor Merval",
        "fci_cedears":   "Fondo de CEDEARs: exposición global en pesos con cobertura cambiaria automática",
        "fci_mixto":     "Fondo mixto: bonos + acciones, el gestor ajusta la mezcla según el mercado",
        # ONs adicionales
        "on_meli":       "MercadoLibre paga en USD con ingresos regionales — menor riesgo soberano que el Estado",
        "on_telecom":    "Telecom: infraestructura crítica, contratos en USD, barreras de entrada imposibles",
        "on_genneia":    "Energía renovable con contratos CAMMESA en dólares — beneficiada por la transición global",
        "on_vista":      "Vista produce petróleo en Vaca Muerta y cobra en USD — crecimiento de producción record",
        "on_pampa":      "Pampa Energía: el mayor holding eléctrico del país con contratos regulados en USD",
        # Soberanos adicionales
        "gd29":          "GD29: bono soberano en USD con vencimiento 2029 y protección ley Nueva York",
        "gd41":          "GD41: la apuesta más larga al crédito argentino — máximo upside si baja el riesgo país",
        # ONs nuevas
        "on_tgs2":       "TGS opera el principal gasoducto del país — segunda serie ON en dólares con mayor plazo y cupón",
        "on_arcor":      "Arcor exporta a 120 países y genera USD propios — ON respaldada por el grupo agroindustrial más grande de Argentina",
        "on_telecom2":   "Telecom (segunda serie): infraestructura crítica de telecomunicaciones con contratos en dólares",
        "on_irsa":       "IRSA posee los shoppings premium de Argentina — flujo en USD de arrendamientos dolarizados",
        "on_cresud":     "Cresud: campo argentino y propiedades urbanas, ON de mayor rendimiento para inversor agresivo",
        # Bonos pesos nuevos
        "dual_bond":     "Bono Dual TDA27: paga el mayor entre inflación CER o devaluación — protege contra cualquier escenario",
        "dollar_linked": "Bono Dollar Linked TV26: replica el tipo de cambio oficial — protege si se acelera la devaluación",
    }
    base = _RAZONES.get(asset_id)
    if base:
        return base
    cat = ASSET_INDEX.get(asset_id, {}).get("category", "")
    if "ETF" in cat:
        return "Diversificación instantánea: una sola operación da exposición a decenas de empresas a la vez"
    if cat == "CEDEARs":
        return "Acción de empresa internacional que puede comprar desde Argentina en pesos o dólares"
    if cat == "Acciones ARG":
        return "Empresa argentina que crece con el país — exposición directa a la economía local"
    return ASSET_INDEX.get(asset_id, {}).get("simple_desc", "")


def generate_risk_scenarios(portfolio: dict, mkt_ctx: dict | None = None) -> list[dict]:
    """
    Genera escenarios de riesgo dinámicos según la composición de la cartera.
    Cada escenario: {title, icon, severity, body, tip}.
    severity: "bajo" | "medio" | "alto"
    """
    positions = portfolio["positions"]
    mkt = mkt_ctx or portfolio.get("market_context", {}) or {}

    ars_w  = sum(p["weight"] for p in positions if p.get("currency") == "ARS")
    sov_w  = sum(p["weight"] for p in positions if p.get("bond_type") == "soberano_usd"
                 or p.get("id") in {"al30", "gd30", "al35", "gd35", "gd38"})
    arg_eq = sum(p["weight"] for p in positions if p.get("category") == "Acciones ARG")
    eq_w   = sum(p["weight"] for p in positions if p.get("category") in
                 {"CEDEARs", "Acciones ARG", "ETFs Globales", "ETFs"})
    tech_ids = {"nvda", "aapl", "msft", "googl", "meta", "amzn", "tsla", "amd", "qqq", "nflx"}
    tech_w = sum(p["weight"] for p in positions
                 if "Tecno" in p.get("sub", "") or p.get("id") in tech_ids)
    liq_w  = sum(p["weight"] for p in positions
                 if p.get("id") in {"cash_pesos", "money_market", "fci_t0", "mep"})

    rp_bps = mkt.get("riesgo_pais_bps")
    arg_total = ars_w + arg_eq + sov_w
    scenarios: list[dict] = []

    if arg_total >= 0.15:
        rp_str = f" (EMBI+ actual: {rp_bps:,.0f} bps)" if rp_bps else ""
        scenarios.append({
            "title":    "Riesgo soberano argentino",
            "icon":     "🇦🇷",
            "severity": "alto" if (sov_w > 0.10 or rp_bps and rp_bps >= 700) else "medio",
            "body": (
                f"El {arg_total*100:.0f}% de la cartera está expuesto a eventos macroeconómicos "
                f"argentinos{rp_str}. Un shock político, corrida cambiaria o evento de deuda "
                "afectaría pesos, acciones locales y bonos soberanos al mismo tiempo."
            ),
            "tip": "Aumentar exposición a activos USD sin correlación local (ETFs globales, ONs con ingresos dolarizados) reduce este riesgo.",
        })

    if ars_w >= 0.20:
        scenarios.append({
            "title":    "Devaluación del peso",
            "icon":     "💱",
            "severity": "alto" if ars_w > 0.45 else "medio",
            "body": (
                f"Con {ars_w*100:.0f}% en pesos, una devaluación abrupta erosionaría ese bloque "
                "en USD. Históricamente Argentina registró saltos cambiarios del 30%–100% "
                "en menos de 24 horas (2018, 2019, 2023). El plazo fijo no se protege entre renovaciones."
            ),
            "tip": "LECAP y bonos CER indexados cubren parcialmente contra inflación, pero no contra devaluación abrupta.",
        })

    if eq_w >= 0.20 or sov_w >= 0.05:
        scenarios.append({
            "title":    "Suba de tasas globales (Reserva Federal)",
            "icon":     "🏦",
            "severity": "medio",
            "body": (
                f"Con {eq_w*100:.0f}% en acciones/ETFs y {sov_w*100:.0f}% en bonos, "
                "una política monetaria restrictiva de la Fed comprimiría los múltiplos de valuación "
                "y subiría el costo de refinanciamiento. En 2022 el NASDAQ cayó 33% por este motivo."
            ),
            "tip": "Mantener el horizonte de inversión y no reaccionar a correcciones de corto plazo.",
        })

    if tech_w >= 0.25:
        scenarios.append({
            "title":    "Concentración en tecnología",
            "icon":     "💻",
            "severity": "alto" if tech_w > 0.45 else "medio",
            "body": (
                f"El {tech_w*100:.0f}% en tecnología genera alta correlación interna. "
                "Si hay rotación sectorial, regulación antimonopolio o corrección de valuaciones "
                "de IA, todos estos activos caerían simultáneamente."
            ),
            "tip": "Diversificar hacia salud, consumo masivo o energía reduce la correlación y suaviza la volatilidad.",
        })

    if liq_w < 0.05 and eq_w > 0.30:
        scenarios.append({
            "title":    "Liquidez de emergencia insuficiente en cartera",
            "icon":     "⚠️",
            "severity": "bajo",
            "body": (
                f"Solo {liq_w*100:.0f}% en activos de rescate inmediato. "
                "Si necesitara el capital en menos de 5 días hábiles durante una corrección, "
                "podría verse forzado a vender acciones o ETFs a precios desfavorables."
            ),
            "tip": "Separar 3–6 meses de gastos fuera de la cartera antes de invertir, como colchón de emergencia.",
        })

    if rp_bps is not None and rp_bps >= 800 and sov_w > 0:
        scenarios.append({
            "title":    "Riesgo de reestructuración soberana",
            "icon":     "🌡️",
            "severity": "alto",
            "body": (
                f"Con el riesgo país en {rp_bps:,.0f} bps, los bonos soberanos descuentan estrés. "
                "Históricamente por encima de 1.000 bps el riesgo de reestructuración aumenta "
                "significativamente — como ocurrió en 2019 (1.800 bps) y 2020 (reestructuración efectiva)."
            ),
            "tip": "Privilegiar ONs corporativas de empresas con ingresos en USD (TGS, Pampa, YPF) sobre bonos soberanos.",
        })

    return scenarios[:5]


def build_portfolio(profile: dict) -> dict:
    """
    Construye la cartera personalizada según el perfil del inversor.

    Flujo:
    1. Carga scores Finviz (equity) y bond_scorer (bonos).
    2. Aplica descuentos regulatorios ARG sobre scores de acciones locales.
    3. _build_from_buckets(): elige los mejores activos por score dentro de
       cada categoría (bucket) y los pondera proporcionalmente a su score.
    4. Ajusta por horizonte temporal y fondo de emergencia.
    5. Excluye solapamientos ETF/CEDEAR.
    """
    risk     = profile["risk_profile"]
    template = PORTFOLIO_TEMPLATES[risk]
    horizon  = profile.get("horizon", 5)

    # ── 1. Cargar scores y sectores ───────────────────────────────────────────
    eq_scores              = load_equity_scores()          # Finviz → acciones y ETFs
    bond_scores, _mkt_ctx  = _load_bond_live()             # bonos con overlay riesgo país live
    asset_sectors          = load_asset_sectors()          # asset_id → sector_framework
    eq_full                = load_equity_full()            # bloques + ratios completos por activo

    # ── 2. Capa ARG: descuento regulatorio sobre scores de acciones locales ──
    if eq_scores:
        for asset_id, score_val in list(eq_scores.items()):
            sector = asset_sectors.get(asset_id, "default")
            adj    = apply_argentina_adjustment(score_val, asset_id, sector)
            if adj["descuento"] > 0:
                eq_scores[asset_id] = adj["score_adj"]

    # ── 3. Construir asignación base score-driven ─────────────────────────────
    allocs = _build_from_buckets(risk, eq_scores, bond_scores)

    # Fallback al template hardcodeado si la construcción quedó vacía
    if not allocs:
        allocs = dict(template["allocations"])

    # ── 4. Ajustes por perfil del inversor ───────────────────────────────────
    allocs = _adjust_for_horizon(allocs, horizon, risk)

    has_emergency = ("más de" in profile.get("emergency_fund", "").lower()
                     or "6 meses" in profile.get("emergency_fund", "").lower())
    allocs = _adjust_for_emergency(allocs, has_emergency)

    # ── 5. Ajustes por experiencia e ingresos ────────────────────────────────
    allocs = _adjust_for_experience(allocs, profile.get("experience", ""))
    allocs = _adjust_for_income_stability(allocs, profile.get("income_stability", ""))

    # ── 5b. Ajuste dinámico por valuación histórica de sector ─────────────────
    try:
        from memory_manager import get_sector_valuation_signals
        sector_signals = get_sector_valuation_signals()
        allocs = _adjust_for_sector_valuations(allocs, asset_sectors, sector_signals)
    except Exception:
        pass

    # ── 5c. Optimización Markowitz sobre la porción equity ────────────────────
    # Reemplaza los pesos heurísticos de acciones/ETFs por pesos óptimos
    # calculados con la matriz de covarianza histórica (yfinance, 1 año).
    # Falla silenciosamente: si yfinance no está disponible o hay pocos datos,
    # la cartera conserva los pesos score-driven del paso anterior.
    try:
        from modules.optimizer import optimize_equity_slice
        _EQ_CATS = {"CEDEARs", "Acciones ARG", "ETFs Globales", "ETFs"}
        equity_ids = [
            aid for aid in allocs
            if ASSET_INDEX.get(aid, {}).get("category") in _EQ_CATS
        ]
        if len(equity_ids) >= 2:
            opt_weights = optimize_equity_slice(equity_ids, risk)
            if opt_weights:
                # Mantener el peso total asignado a equity; redistribuir internamente
                total_eq_weight = sum(allocs[aid] for aid in equity_ids)
                for aid, opt_w in opt_weights.items():
                    allocs[aid] = opt_w * total_eq_weight
                # Renormalizar toda la cartera
                total = sum(allocs.values())
                if total > 0:
                    allocs = {k: v / total for k, v in allocs.items()}
    except Exception:
        pass

    # ── 6. Filtros estructurales ──────────────────────────────────────────────
    allocs = _filter_by_liquidity(allocs, risk, horizon)
    allocs = _apply_overlap_exclusion(allocs)

    # ── 6b. Caps por score/perfil — enforcement final post-Markowitz ──────────
    # Reemplaza el hard-cap fijo del 25%: ahora cada activo tiene su propio
    # límite basado en su score Finviz y el perfil del usuario.
    allocs = _apply_score_caps(allocs, risk, eq_scores)
    allocs = select_top_assets(allocs, risk, eq_scores)

    # Construir posiciones
    positions = []
    for asset_id, weight in allocs.items():
        if asset_id in ASSET_INDEX and weight > 0.005:
            asset           = dict(ASSET_INDEX[asset_id])
            asset["weight"] = round(weight, 4)
            # Adjuntar score y breakdown de bloques si existe en Finviz
            if asset_id in eq_full:
                fd = eq_full[asset_id]
                asset["score"]   = fd["score"]
                asset["bloques"] = fd["bloques"]
                asset["ratios"]  = fd["ratios"]
            if asset_id in BOND_DEFS:
                _defn  = BOND_DEFS[asset_id]
                _btype = _defn.get("type", "")
                asset["bond_type"]     = _btype
                asset["bond_duration"] = _defn.get("duration_est")
                asset["bond_score"]    = bond_scores.get(asset_id)
                _rp    = _mkt_ctx.get("riesgo_pais_bps")
                _usyld = {
                    "5y":  _mkt_ctx.get("us_treasury_5y")  or 4.0,
                    "10y": _mkt_ctx.get("us_treasury_10y") or 4.4,
                }
                if _btype == "soberano_usd" and _rp is not None:
                    asset["bond_tir"] = round(_implied_sovereign_tir(_defn["duration_est"], _rp, _usyld), 2)
                elif _btype == "on_corp" and _rp is not None:
                    _spread = _ON_CREDIT_SPREADS_BPS.get(asset_id, 0)
                    asset["bond_tir"] = round(
                        _implied_sovereign_tir(_defn["duration_est"], _rp, _usyld) + _spread / 100, 2
                    )
                elif _btype == "lecap":
                    _lc = _mkt_ctx.get("active_lecap")
                    asset["bond_tir"] = _lc.get("tna_est") if _lc else _defn.get("tir_est")
                else:
                    asset["bond_tir"] = _defn.get("tir_est")
            positions.append(asset)

    positions.sort(key=lambda x: x["weight"], reverse=True)

    # ── LECAP: actualizar nombre/descripción con el ticker vigente ────────────
    active_lc = _mkt_ctx.get("active_lecap") or get_active_lecap()
    for pos in positions:
        if pos["id"] == "lecap":
            if active_lc:
                ticker   = active_lc["ticker"]
                expiry   = active_lc["expiry"]
                days_lft = active_lc["days_left"]
                pos["name"]        = f"LECAP {ticker} (vence {expiry.strftime('%d/%m/%Y')})"
                pos["ticker"]      = ticker
                pos["simple_desc"] = (
                    f"{ticker}: letra del Tesoro a tasa fija — vence en {days_lft} días. "
                    f"Comprala en IOL o PPI como si fuera una acción."
                )
                pos["description"] = (
                    f"Letra Capitalizable del Tesoro argentino, serie {ticker}. "
                    f"Vencimiento: {expiry.strftime('%d/%m/%Y')} ({days_lft} días). "
                    f"Se compra a precio de mercado en IOL, PPI o Balanz. "
                    f"Rinde la TNA descontada en el precio. Riesgo: contraparte soberana argentina."
                )
            else:
                # Sin LECAP activa — el activo queda como placeholder
                pos["name"]        = "LECAP (pendiente de nueva emisión)"
                pos["simple_desc"] = "Aguardar próxima licitación del Tesoro para invertir en letras a tasa fija."

    # Adjuntar razón personalizada por activo
    for pos in positions:
        pos["razon_en_cartera"] = _razon_en_cartera(pos["id"], risk, horizon)

    # Detectar solapamientos para advertir al usuario
    overlaps = _detect_overlaps(positions)

    # ── Métricas base ─────────────────────────────────────────────────────────
    expected_cagr = sum(p["weight"] * p["expected_return"] for p in positions)
    expected_vol  = sum(p["weight"] * p["volatility"]      for p in positions)

    category_exposure: Dict[str, float] = {}
    sector_exposure:   Dict[str, float] = {}
    currency_exposure: Dict[str, float] = {}

    for p in positions:
        category_exposure[p["category"]] = category_exposure.get(p["category"], 0) + p["weight"]
        sector_exposure[p["sub"]]        = sector_exposure.get(p["sub"], 0)        + p["weight"]
        currency_exposure[p["currency"]] = currency_exposure.get(p["currency"], 0) + p["weight"]

    pesos_pct = sum(p["weight"] for p in positions if p["currency"] == "ARS") * 100
    usd_pct   = 100 - pesos_pct

    n = len(positions)
    diversification = "alta" if n >= 10 else ("media" if n >= 6 else "baja")

    # ── Métricas cuantitativas avanzadas ──────────────────────────────────────
    # Beta de portfolio: promedio ponderado de betas individuales.
    # Activos sin beta (bonos, pesos) contribuyen con 0 (descorrelacionados del mercado).
    beta_portfolio = 0.0
    for p in positions:
        beta_raw = p.get("ratios", {}).get("beta") if p.get("ratios") else None
        if beta_raw is not None:
            try:
                beta_portfolio += p["weight"] * float(beta_raw)
            except (TypeError, ValueError):
                pass

    # Sharpe ratio estimado: (retorno_esperado - tasa_libre_riesgo) / volatilidad
    # Tasa libre de riesgo: rendimiento del T-Bill 3M EE.UU. (~4.5% anual, base USD)
    _RISK_FREE = 0.045
    sharpe_ratio = (
        (expected_cagr - _RISK_FREE) / expected_vol
        if expected_vol > 0 else 0.0
    )

    # Índice de Herfindahl-Hirschman (HHI): concentración de la cartera
    # HHI = Σ w_i²  → 0 = diversificación perfecta, 1 = todo en un activo
    # HHI < 0.15 = alta diversificación | 0.15–0.25 = moderada | > 0.25 = concentrada
    hhi = sum(p["weight"] ** 2 for p in positions)
    if hhi < 0.15:
        hhi_label = "Alta diversificación"
    elif hhi < 0.25:
        hhi_label = "Diversificación moderada"
    else:
        hhi_label = "Cartera concentrada"

    # Score promedio ponderado de los activos scorables
    eq_score_total = sum(
        p["weight"] * p.get("score", 0)
        for p in positions if p.get("score", 0) > 0
    )
    eq_weight_total = sum(p["weight"] for p in positions if p.get("score", 0) > 0)
    avg_score = round(eq_score_total / eq_weight_total) if eq_weight_total > 0 else None

    return {
        "risk_profile":        risk,
        "positions":           positions,
        "expected_cagr":       round(expected_cagr, 4),
        "expected_volatility": round(expected_vol, 4),
        "category_exposure":   category_exposure,
        "sector_exposure":     sector_exposure,
        "currency_exposure":   currency_exposure,
        "description":         template["description"],
        "summary":             template["summary"],
        "pesos_pct":           round(pesos_pct, 1),
        "usd_pct":             round(usd_pct, 1),
        "diversification":     diversification,
        "profile":             profile,
        "overlaps":            overlaps,
        # Métricas cuantitativas
        "beta_portfolio":      round(beta_portfolio, 2),
        "sharpe_ratio":        round(sharpe_ratio, 2),
        "hhi":                 round(hhi, 3),
        "hhi_label":           hhi_label,
        "avg_score":           avg_score,
        "market_context":      _mkt_ctx,
    }
