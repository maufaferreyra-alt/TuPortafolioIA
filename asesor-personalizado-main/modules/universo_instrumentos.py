"""
Universo de activos disponibles para que el usuario pueda agregar.
En el 6B se conectará con APIs reales. En el 6A es estático.

Cada activo tiene: ticker, nombre, tipo (matchea con TIPOS_INSTRUMENTO).

NOTA: este es un MVP estático. En producción se cargaría desde
las APIs (data912 + ArgentinaDatos + DolarAPI) o desde la DB
del scoring de Finviz que ya tenés.
"""

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

    # ─── CEDEARs (los más líquidos) ───
    {"ticker": "AAPL", "nombre": "Apple Inc.", "tipo": "cedear"},
    {"ticker": "MSFT", "nombre": "Microsoft", "tipo": "cedear"},
    {"ticker": "GOOGL", "nombre": "Alphabet (Google)", "tipo": "cedear"},
    {"ticker": "AMZN", "nombre": "Amazon", "tipo": "cedear"},
    {"ticker": "META", "nombre": "Meta Platforms (Facebook)", "tipo": "cedear"},
    {"ticker": "TSLA", "nombre": "Tesla", "tipo": "cedear"},
    {"ticker": "NVDA", "nombre": "NVIDIA", "tipo": "cedear"},
    {"ticker": "NFLX", "nombre": "Netflix", "tipo": "cedear"},
    {"ticker": "DIS", "nombre": "Walt Disney", "tipo": "cedear"},
    {"ticker": "KO", "nombre": "Coca-Cola", "tipo": "cedear"},
    {"ticker": "JPM", "nombre": "JPMorgan Chase", "tipo": "cedear"},
    {"ticker": "BAC", "nombre": "Bank of America", "tipo": "cedear"},
    {"ticker": "WMT", "nombre": "Walmart", "tipo": "cedear"},
    {"ticker": "PG", "nombre": "Procter & Gamble", "tipo": "cedear"},
    {"ticker": "JNJ", "nombre": "Johnson & Johnson", "tipo": "cedear"},
    {"ticker": "V", "nombre": "Visa", "tipo": "cedear"},
    {"ticker": "MA", "nombre": "Mastercard", "tipo": "cedear"},
    {"ticker": "BABA", "nombre": "Alibaba", "tipo": "cedear"},
    {"ticker": "MELI", "nombre": "Mercado Libre", "tipo": "cedear"},
    {"ticker": "PYPL", "nombre": "PayPal", "tipo": "cedear"},
    # ETFs como CEDEARs
    {"ticker": "SPY", "nombre": "ETF S&P 500", "tipo": "cedear"},
    {"ticker": "QQQ", "nombre": "ETF Nasdaq 100", "tipo": "cedear"},
    {"ticker": "EEM", "nombre": "ETF Mercados Emergentes", "tipo": "cedear"},
    {"ticker": "GLD", "nombre": "ETF Oro", "tipo": "cedear"},
    {"ticker": "IAU", "nombre": "ETF Oro iShares", "tipo": "cedear"},
    {"ticker": "VOO", "nombre": "ETF Vanguard S&P 500", "tipo": "cedear"},

    # ─── Acciones argentinas ───
    {"ticker": "YPFD", "nombre": "YPF", "tipo": "accion_arg"},
    {"ticker": "GGAL", "nombre": "Grupo Galicia", "tipo": "accion_arg"},
    {"ticker": "PAMP", "nombre": "Pampa Energía", "tipo": "accion_arg"},
    {"ticker": "TXAR", "nombre": "Ternium Argentina", "tipo": "accion_arg"},
    {"ticker": "BMA", "nombre": "Banco Macro", "tipo": "accion_arg"},
    {"ticker": "BBAR", "nombre": "BBVA Argentina", "tipo": "accion_arg"},
    {"ticker": "TGSU2", "nombre": "Transportadora Gas del Sur", "tipo": "accion_arg"},
    {"ticker": "CRES", "nombre": "Cresud", "tipo": "accion_arg"},
    {"ticker": "EDN", "nombre": "Edenor", "tipo": "accion_arg"},
    {"ticker": "ALUA", "nombre": "Aluar", "tipo": "accion_arg"},
    {"ticker": "CEPU", "nombre": "Central Puerto", "tipo": "accion_arg"},
    {"ticker": "MIRG", "nombre": "Mirgor", "tipo": "accion_arg"},
    {"ticker": "TRAN", "nombre": "Transener", "tipo": "accion_arg"},
    {"ticker": "VALO", "nombre": "Valores Continental", "tipo": "accion_arg"},

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


def buscar_activos(query: str, tipo: str = None, limit: int = 8) -> list[dict]:
    """
    Busca activos por ticker o nombre (case-insensitive).
    Si tipo se provee, filtra solo ese tipo.

    Devuelve hasta `limit` matches ordenados por:
    1. Match exacto de ticker
    2. Match prefix de ticker
    3. Match contiene en nombre
    """
    if not query:
        # Sin query, devolver los primeros del tipo
        return [a for a in UNIVERSO_INSTRUMENTOS if not tipo or a["tipo"] == tipo][:limit]

    query_upper = query.upper().strip()
    query_lower = query.lower().strip()

    matches_exactos = []
    matches_prefix = []
    matches_contiene = []

    for activo in UNIVERSO_INSTRUMENTOS:
        if tipo and activo["tipo"] != tipo:
            continue

        ticker_upper = activo["ticker"].upper()
        nombre_lower = activo["nombre"].lower()

        if ticker_upper == query_upper:
            matches_exactos.append(activo)
        elif ticker_upper.startswith(query_upper):
            matches_prefix.append(activo)
        elif query_lower in nombre_lower or query_upper in ticker_upper:
            matches_contiene.append(activo)

    return (matches_exactos + matches_prefix + matches_contiene)[:limit]


def get_activo_por_ticker(ticker: str) -> dict | None:
    """Devuelve un activo del universo por su ticker."""
    for a in UNIVERSO_INSTRUMENTOS:
        if a["ticker"].upper() == ticker.upper():
            return a
    return None
