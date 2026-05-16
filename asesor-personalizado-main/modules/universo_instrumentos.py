"""
Universo de activos disponibles para que el usuario pueda agregar.
En el 6B se conectará con APIs reales. En el 6A es estático.

Cada activo tiene: ticker, nombre, tipo (matchea con TIPOS_INSTRUMENTO).

NOTA: este es un MVP estático. En producción se cargaría desde
las APIs (data912 + ArgentinaDatos + DolarAPI) o desde la DB
del scoring de Finviz que ya tenés.
"""

import unicodedata

UNIVERSO_INSTRUMENTOS = [
    # ─── Bonos soberanos ───
    {"ticker": "AL30", "nombre": "Bonar 2030", "tipo": "bono"},
    {"ticker": "AL35", "nombre": "Bonar 2035", "tipo": "bono"},
    {"ticker": "AL41", "nombre": "Bonar 2041", "tipo": "bono"},
    {"ticker": "GD30", "nombre": "Global 2030 (ley NY)", "tipo": "bono"},
    {"ticker": "GD35", "nombre": "Global 2035 (ley NY)", "tipo": "bono"},
    {"ticker": "GD38", "nombre": "Global 2038 (ley NY)", "tipo": "bono"},
    {"ticker": "GD41", "nombre": "Global 2041 (ley NY)", "tipo": "bono"},
    {"ticker": "AE38", "nombre": "Bonar 2038", "tipo": "bono"},
    {"ticker": "AL29", "nombre": "Bonar 2029", "tipo": "bono"},
    {"ticker": "GD29", "nombre": "Global 2029 (ley NY)", "tipo": "bono"},

    # ─── CEDEARs: ETFs (fondos globales que cotizan en Argentina) ───
    {"ticker": "SPY",  "nombre": "ETF S&P 500", "tipo": "cedear"},
    {"ticker": "VOO",  "nombre": "ETF Vanguard S&P 500", "tipo": "cedear"},
    {"ticker": "QQQ",  "nombre": "ETF Nasdaq 100", "tipo": "cedear"},
    {"ticker": "EEM",  "nombre": "ETF Mercados Emergentes", "tipo": "cedear"},
    {"ticker": "EWZ",  "nombre": "ETF Brasil", "tipo": "cedear"},
    {"ticker": "GLD",  "nombre": "ETF Oro", "tipo": "cedear"},
    {"ticker": "IAU",  "nombre": "ETF Oro iShares", "tipo": "cedear"},
    {"ticker": "SLV",  "nombre": "ETF Plata", "tipo": "cedear"},
    {"ticker": "XLE",  "nombre": "ETF Energía", "tipo": "cedear"},
    {"ticker": "XLF",  "nombre": "ETF Sector Financiero", "tipo": "cedear"},
    {"ticker": "XLK",  "nombre": "ETF Sector Tecnología", "tipo": "cedear"},
    {"ticker": "ARKK", "nombre": "ETF ARK Innovation", "tipo": "cedear"},
    {"ticker": "DIA",  "nombre": "ETF Dow Jones", "tipo": "cedear"},
    {"ticker": "IWM",  "nombre": "ETF Russell 2000", "tipo": "cedear"},

    # ─── CEDEARs: Tecnología ───
    {"ticker": "AAPL", "nombre": "Apple Inc.", "tipo": "cedear"},
    {"ticker": "MSFT", "nombre": "Microsoft", "tipo": "cedear"},
    {"ticker": "GOOGL","nombre": "Alphabet (Google)", "tipo": "cedear"},
    {"ticker": "AMZN", "nombre": "Amazon", "tipo": "cedear"},
    {"ticker": "META", "nombre": "Meta Platforms (Facebook)", "tipo": "cedear"},
    {"ticker": "TSLA", "nombre": "Tesla", "tipo": "cedear"},
    {"ticker": "NVDA", "nombre": "NVIDIA", "tipo": "cedear"},
    {"ticker": "NFLX", "nombre": "Netflix", "tipo": "cedear"},
    {"ticker": "AMD",  "nombre": "Advanced Micro Devices", "tipo": "cedear"},
    {"ticker": "INTC", "nombre": "Intel", "tipo": "cedear"},
    {"ticker": "CRM",  "nombre": "Salesforce", "tipo": "cedear"},
    {"ticker": "ORCL", "nombre": "Oracle", "tipo": "cedear"},
    {"ticker": "ADBE", "nombre": "Adobe", "tipo": "cedear"},
    {"ticker": "CSCO", "nombre": "Cisco Systems", "tipo": "cedear"},
    {"ticker": "QCOM", "nombre": "Qualcomm", "tipo": "cedear"},
    {"ticker": "IBM",  "nombre": "IBM", "tipo": "cedear"},

    # ─── CEDEARs: Consumo y entretenimiento ───
    {"ticker": "DIS",  "nombre": "Walt Disney", "tipo": "cedear"},
    {"ticker": "KO",   "nombre": "Coca-Cola", "tipo": "cedear"},
    {"ticker": "PEP",  "nombre": "PepsiCo", "tipo": "cedear"},
    {"ticker": "MCD",  "nombre": "McDonald's", "tipo": "cedear"},
    {"ticker": "SBUX", "nombre": "Starbucks", "tipo": "cedear"},
    {"ticker": "NKE",  "nombre": "Nike", "tipo": "cedear"},
    {"ticker": "WMT",  "nombre": "Walmart", "tipo": "cedear"},
    {"ticker": "PG",   "nombre": "Procter & Gamble", "tipo": "cedear"},
    {"ticker": "COST", "nombre": "Costco", "tipo": "cedear"},
    {"ticker": "HD",   "nombre": "Home Depot", "tipo": "cedear"},
    {"ticker": "TGT",  "nombre": "Target", "tipo": "cedear"},
    {"ticker": "ABNB", "nombre": "Airbnb", "tipo": "cedear"},
    {"ticker": "UBER", "nombre": "Uber", "tipo": "cedear"},
    {"ticker": "SPOT", "nombre": "Spotify", "tipo": "cedear"},

    # ─── CEDEARs: Financiero ───
    {"ticker": "JPM",  "nombre": "JPMorgan Chase", "tipo": "cedear"},
    {"ticker": "BAC",  "nombre": "Bank of America", "tipo": "cedear"},
    {"ticker": "C",    "nombre": "Citigroup", "tipo": "cedear"},
    {"ticker": "WFC",  "nombre": "Wells Fargo", "tipo": "cedear"},
    {"ticker": "GS",   "nombre": "Goldman Sachs", "tipo": "cedear"},
    {"ticker": "MS",   "nombre": "Morgan Stanley", "tipo": "cedear"},
    {"ticker": "V",    "nombre": "Visa", "tipo": "cedear"},
    {"ticker": "MA",   "nombre": "Mastercard", "tipo": "cedear"},
    {"ticker": "PYPL", "nombre": "PayPal", "tipo": "cedear"},
    {"ticker": "AXP",  "nombre": "American Express", "tipo": "cedear"},

    # ─── CEDEARs: Salud / Farma ───
    {"ticker": "JNJ",  "nombre": "Johnson & Johnson", "tipo": "cedear"},
    {"ticker": "PFE",  "nombre": "Pfizer", "tipo": "cedear"},
    {"ticker": "MRNA", "nombre": "Moderna", "tipo": "cedear"},
    {"ticker": "UNH",  "nombre": "UnitedHealth", "tipo": "cedear"},
    {"ticker": "ABT",  "nombre": "Abbott Laboratories", "tipo": "cedear"},
    {"ticker": "MRK",  "nombre": "Merck", "tipo": "cedear"},

    # ─── CEDEARs: Energía e industria ───
    {"ticker": "XOM",  "nombre": "Exxon Mobil", "tipo": "cedear"},
    {"ticker": "CVX",  "nombre": "Chevron", "tipo": "cedear"},
    {"ticker": "BA",   "nombre": "Boeing", "tipo": "cedear"},
    {"ticker": "CAT",  "nombre": "Caterpillar", "tipo": "cedear"},
    {"ticker": "GE",   "nombre": "General Electric", "tipo": "cedear"},
    {"ticker": "F",    "nombre": "Ford Motor", "tipo": "cedear"},
    {"ticker": "GM",   "nombre": "General Motors", "tipo": "cedear"},

    # ─── CEDEARs: Latinoamérica ───
    {"ticker": "MELI", "nombre": "Mercado Libre", "tipo": "cedear"},
    {"ticker": "BABA", "nombre": "Alibaba", "tipo": "cedear"},
    {"ticker": "PBR",  "nombre": "Petrobras (Brasil)", "tipo": "cedear"},
    {"ticker": "VALE", "nombre": "Vale (Brasil)", "tipo": "cedear"},
    {"ticker": "ITUB", "nombre": "Itaú Unibanco (Brasil)", "tipo": "cedear"},

    # ─── Acciones argentinas: Bancos ───
    {"ticker": "GGAL", "nombre": "Grupo Galicia", "tipo": "accion_arg"},
    {"ticker": "BMA",  "nombre": "Banco Macro", "tipo": "accion_arg"},
    {"ticker": "BBAR", "nombre": "BBVA Argentina", "tipo": "accion_arg"},
    {"ticker": "SUPV", "nombre": "Banco Supervielle", "tipo": "accion_arg"},
    {"ticker": "BHIP", "nombre": "Banco Hipotecario", "tipo": "accion_arg"},
    {"ticker": "VALO", "nombre": "Valores Continental", "tipo": "accion_arg"},

    # ─── Acciones argentinas: Energía ───
    {"ticker": "YPFD", "nombre": "YPF", "tipo": "accion_arg"},
    {"ticker": "PAMP", "nombre": "Pampa Energía", "tipo": "accion_arg"},
    {"ticker": "TGSU2","nombre": "Transportadora Gas del Sur", "tipo": "accion_arg"},
    {"ticker": "TGNO4","nombre": "Transportadora Gas del Norte", "tipo": "accion_arg"},
    {"ticker": "EDN",  "nombre": "Edenor", "tipo": "accion_arg"},
    {"ticker": "CEPU", "nombre": "Central Puerto", "tipo": "accion_arg"},
    {"ticker": "TRAN", "nombre": "Transener", "tipo": "accion_arg"},
    {"ticker": "METR", "nombre": "Metrogas", "tipo": "accion_arg"},
    {"ticker": "CAPX", "nombre": "Capex (Energía)", "tipo": "accion_arg"},

    # ─── Acciones argentinas: Industria y materiales ───
    {"ticker": "TXAR", "nombre": "Ternium Argentina", "tipo": "accion_arg"},
    {"ticker": "ALUA", "nombre": "Aluar", "tipo": "accion_arg"},
    {"ticker": "LOMA", "nombre": "Loma Negra", "tipo": "accion_arg"},
    {"ticker": "MIRG", "nombre": "Mirgor", "tipo": "accion_arg"},
    {"ticker": "BYMA", "nombre": "BYMA (Bolsa)", "tipo": "accion_arg"},

    # ─── Acciones argentinas: Agro / Real Estate ───
    {"ticker": "CRES", "nombre": "Cresud", "tipo": "accion_arg"},
    {"ticker": "IRSA", "nombre": "IRSA (Real Estate)", "tipo": "accion_arg"},
    {"ticker": "AGRO", "nombre": "Agrometal", "tipo": "accion_arg"},

    # ─── Acciones argentinas: Telecom / Otros ───
    {"ticker": "TECO2","nombre": "Telecom Argentina", "tipo": "accion_arg"},
    {"ticker": "COME", "nombre": "Sociedad Comercial del Plata", "tipo": "accion_arg"},
    {"ticker": "MOLI", "nombre": "Molinos Río de la Plata", "tipo": "accion_arg"},

    # ─── ONs (Obligaciones Negociables) ───
    {"ticker": "YPFDS", "nombre": "ON YPF Clase XIII", "tipo": "on"},
    {"ticker": "PMCNO", "nombre": "ON Pan American Energy", "tipo": "on"},
    {"ticker": "TGSU2O", "nombre": "ON Transportadora Gas del Sur", "tipo": "on"},
    {"ticker": "VISTAO", "nombre": "ON Vista Energy", "tipo": "on"},
    {"ticker": "TLCN", "nombre": "ON Telecom Argentina", "tipo": "on"},
    {"ticker": "PAEMO", "nombre": "ON Pampa Energía 2027", "tipo": "on"},

    # ─── FCIs ───
    {"ticker": "FCI-MM-COCOS", "nombre": "Cocos Money Market", "tipo": "fci"},
    {"ticker": "FCI-MM-BALANZ", "nombre": "Balanz Money Market", "tipo": "fci"},
    {"ticker": "FCI-MM-IOL", "nombre": "IOL Money Market", "tipo": "fci"},
    {"ticker": "FCI-RF-COCOS", "nombre": "Cocos Renta Fija", "tipo": "fci"},
    {"ticker": "FCI-RF-BALANZ", "nombre": "Balanz Renta Fija", "tipo": "fci"},
    {"ticker": "FCI-MIXTO", "nombre": "Fondo Mixto Pesos", "tipo": "fci"},

    # ─── Letras ───
    {"ticker": "S30Y6", "nombre": "LECAP S30Y6", "tipo": "letra"},
    {"ticker": "S31L6", "nombre": "LECAP S31L6", "tipo": "letra"},
    {"ticker": "S29G6", "nombre": "LECAP S29G6", "tipo": "letra"},
    {"ticker": "T2X6", "nombre": "BONCAP T2X6", "tipo": "letra"},

    # ─── MEP / Dólar ───
    {"ticker": "MEP", "nombre": "Dólar MEP", "tipo": "mep"},
    {"ticker": "AL30D", "nombre": "Dólar MEP vía AL30", "tipo": "mep"},
    {"ticker": "GD30D", "nombre": "Dólar MEP vía GD30", "tipo": "mep"},
]


# Aliases populares: el usuario escribe algo común, encontramos el ticker
_ALIASES_POPULARES = {
    "galicia":   ["GGAL"],
    "macro":     ["BMA"],
    "bbva":      ["BBAR"],
    "pampa":     ["PAMP"],
    "ypf":       ["YPFD", "YPFDS"],
    "tesla":     ["TSLA"],
    "apple":     ["AAPL"],
    "amazon":    ["AMZN"],
    "microsoft": ["MSFT"],
    "google":    ["GOOGL"],
    "facebook":  ["META"],
    "meta":      ["META"],
    "netflix":   ["NFLX"],
    "disney":    ["DIS"],
    "nvidia":    ["NVDA"],
    "coca":      ["KO"],
    "coca-cola": ["KO"],
    "cocacola":  ["KO"],
    "mercadolibre": ["MELI"],
    "meli":      ["MELI"],
    "paypal":    ["PYPL"],
    "alibaba":   ["BABA"],
    "jp morgan": ["JPM"],
    "jpmorgan":  ["JPM"],
    "bank of america": ["BAC"],
    "walmart":   ["WMT"],
    "p&g":       ["PG"],
    "procter":   ["PG"],
    "johnson":   ["JNJ"],
    "visa":      ["V"],
    "mastercard": ["MA"],
    "boeing":    ["BA"],
    "exxon":     ["XOM"],
    "chevron":   ["CVX"],
    "pfizer":    ["PFE"],
    "moderna":   ["MRNA"],
    "intel":     ["INTC"],
    "amd":       ["AMD"],
    "salesforce": ["CRM"],
    "uber":      ["UBER"],
    "airbnb":    ["ABNB"],
    "spotify":   ["SPOT"],
    "energia":   ["PAMP", "EDN", "TRAN", "CEPU"],
    "energía":   ["PAMP", "EDN", "TRAN", "CEPU"],
    "banco":     ["GGAL", "BMA", "BBAR"],
    "bancos":    ["GGAL", "BMA", "BBAR"],
    # Bonos populares
    "bonar":     ["AL30", "AL29", "AL35", "AL41"],
    "global":    ["GD29", "GD30", "GD35", "GD38", "GD41"],
    # ETFs
    "sp500":     ["SPY", "VOO"],
    "s&p":       ["SPY", "VOO"],
    "s&p 500":   ["SPY", "VOO"],
    "nasdaq":    ["QQQ"],
    "oro":       ["GLD", "IAU"],
    "emergentes": ["EEM"],
}


def _normalizar(texto: str) -> str:
    """Normaliza texto: minúsculas, sin tildes, sin espacios extra."""
    if not texto:
        return ""
    # Quitar tildes
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return texto.lower().strip()


def buscar_activos(query: str, tipo: str = None, limit: int = 12) -> list[dict]:
    """
    Búsqueda mejorada de activos del universo.

    Prioridades:
    1. Match exacto de ticker
    2. Match en aliases populares
    3. Match prefix de ticker
    4. Match contains en nombre normalizado (sin tildes)
    5. Match contains en ticker
    """
    if not query:
        return [a for a in UNIVERSO_INSTRUMENTOS if not tipo or a["tipo"] == tipo][:limit]

    query_normalizado = _normalizar(query)
    query_upper = query.upper().strip()

    # Filtrar por tipo si corresponde
    candidatos = [a for a in UNIVERSO_INSTRUMENTOS if not tipo or a["tipo"] == tipo]

    matches_exactos = []
    matches_alias = []
    matches_prefix = []
    matches_contains_nombre = []
    matches_contains_ticker = []
    ya_agregados = set()

    def _agregar(activo, lista):
        if activo["ticker"] not in ya_agregados:
            lista.append(activo)
            ya_agregados.add(activo["ticker"])

    # 1. Match exacto de ticker
    for activo in candidatos:
        if activo["ticker"].upper() == query_upper:
            _agregar(activo, matches_exactos)

    # 2. Match en aliases populares
    if query_normalizado in _ALIASES_POPULARES:
        tickers_alias = _ALIASES_POPULARES[query_normalizado]
        for activo in candidatos:
            if activo["ticker"].upper() in tickers_alias:
                _agregar(activo, matches_alias)

    # 3. Match prefix de ticker
    for activo in candidatos:
        if activo["ticker"].upper().startswith(query_upper):
            _agregar(activo, matches_prefix)

    # 4. Match contains en nombre normalizado
    for activo in candidatos:
        nombre_normalizado = _normalizar(activo["nombre"])
        if query_normalizado in nombre_normalizado:
            _agregar(activo, matches_contains_nombre)

    # 5. Match contains en ticker
    for activo in candidatos:
        if query_upper in activo["ticker"].upper():
            _agregar(activo, matches_contains_ticker)

    resultado = (
        matches_exactos + matches_alias + matches_prefix +
        matches_contains_nombre + matches_contains_ticker
    )
    return resultado[:limit]


def get_activo_por_ticker(ticker: str) -> dict | None:
    """Devuelve un activo del universo por su ticker."""
    for a in UNIVERSO_INSTRUMENTOS:
        if a["ticker"].upper() == ticker.upper():
            return a
    return None
