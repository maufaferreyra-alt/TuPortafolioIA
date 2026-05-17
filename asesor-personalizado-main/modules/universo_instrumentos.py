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


# ── Descripciones educativas por activo (Bloque 6A pulido) ──────────
# Una frase corta por activo, tono cercano y sin jerga, para mostrar
# debajo del nombre en las cards del portafolio del usuario (estilo
# "Composición de su cartera"). Indexadas por ticker.
_DESCRIPCIONES_ACTIVOS = {
    # ── Bonos soberanos ──
    "AL30": "Deuda del Estado argentino en dólares, ley local — vence en 2030",
    "AL35": "Deuda del Estado argentino en dólares, ley local — vence en 2035",
    "AL41": "Deuda del Estado argentino en dólares, ley local — el más largo de la serie",
    "GD30": "Deuda argentina en dólares bajo ley de Nueva York — vence en 2030",
    "GD35": "Deuda argentina en dólares bajo ley de Nueva York — vence en 2035",
    "GD38": "Deuda argentina en dólares bajo ley de Nueva York — vence en 2038",
    "GD41": "Deuda argentina en dólares bajo ley de Nueva York — el más largo de la serie",
    "AE38": "Deuda del Estado argentino en dólares, ley local — vence en 2038",
    "AL29": "Deuda del Estado argentino en dólares, ley local — vence en 2029",
    "GD29": "Deuda argentina en dólares bajo ley de Nueva York — el más corto de la serie",
    # ── ETFs (CEDEARs de fondos) ──
    "SPY":  "Las 500 empresas más grandes de EE.UU. en una sola compra",
    "VOO":  "Las 500 mayores empresas de EE.UU., con costos muy bajos",
    "QQQ":  "Las 100 tecnológicas más grandes — Apple, Microsoft, NVIDIA y más",
    "EEM":  "Acciones de países en desarrollo de todo el mundo",
    "EWZ":  "Las principales empresas de la bolsa brasileña en un solo paquete",
    "GLD":  "Sigue el precio del oro — refugio clásico cuando hay incertidumbre",
    "IAU":  "Sigue el precio del oro, con costos más bajos que el GLD",
    "SLV":  "Sigue el precio de la plata — metal precioso y a la vez industrial",
    "XLE":  "Las grandes petroleras y energéticas de EE.UU. agrupadas",
    "XLF":  "Bancos y aseguradoras de EE.UU. en una sola compra",
    "XLK":  "Las empresas de tecnología de EE.UU. agrupadas en un fondo",
    "ARKK": "Apuesta a empresas de innovación disruptiva — mucho riesgo, mucho potencial",
    "DIA":  "Las 30 grandes industriales históricas de EE.UU.",
    "IWM":  "2000 empresas chicas de EE.UU. — más riesgo, más potencial de crecimiento",
    # ── CEDEARs: Tecnología ──
    "AAPL":  "Fabrica el iPhone, la Mac y servicios — de las empresas más valiosas del mundo",
    "MSFT":  "Windows, Office y la nube Azure — gigante del software para empresas",
    "GOOGL": "Dueña de Google, YouTube y Android — domina la búsqueda y la publicidad online",
    "AMZN":  "El mayor comercio electrónico del mundo y líder en servicios de nube",
    "META":  "Dueña de Facebook, Instagram y WhatsApp — gigante de las redes sociales",
    "TSLA":  "Autos eléctricos y baterías — la automotriz más valiosa del mundo",
    "NVDA":  "Los chips que mueven la inteligencia artificial — corazón del boom de la IA",
    "NFLX":  "La plataforma de streaming de series y películas más grande del mundo",
    "AMD":   "Diseña procesadores y chips gráficos — rival directo de Intel y NVIDIA",
    "INTC":  "Pionera de los microprocesadores — busca recuperar terreno en la industria de chips",
    "CRM":   "Software de gestión de clientes líder para empresas",
    "ORCL":  "Bases de datos y software empresarial — gigante histórico de la tecnología",
    "ADBE":  "Photoshop, PDF y herramientas creativas — referente del software de diseño",
    "CSCO":  "Equipos de red que mantienen conectado a internet",
    "QCOM":  "Los chips que dan conectividad a casi todos los celulares del mundo",
    "IBM":   "Veterana de la tecnología — hoy enfocada en nube e inteligencia artificial",
    # ── CEDEARs: Consumo y entretenimiento ──
    "DIS":  "Películas, parques y streaming — el gigante del entretenimiento",
    "KO":   "La marca de bebidas más reconocida del planeta",
    "PEP":  "Bebidas y snacks — dueña de Pepsi, Gatorade y Lay's",
    "MCD":  "La cadena de comida rápida más grande del mundo",
    "SBUX": "La cadena de cafeterías líder a nivel global",
    "NKE":  "La marca de indumentaria deportiva más valiosa del mundo",
    "WMT":  "La cadena de supermercados más grande de EE.UU.",
    "PG":   "Productos de uso diario — dueña de Gillette, Pampers y Ariel",
    "COST": "Venta mayorista por membresía — clientes muy fieles",
    "HD":   "La mayor cadena de materiales para el hogar y la construcción de EE.UU.",
    "TGT":  "Cadena minorista de EE.UU. — competidora directa de Walmart",
    "ABNB": "La plataforma de alquileres temporarios más grande del mundo",
    "UBER": "Viajes y delivery — líder global de la movilidad por app",
    "SPOT": "La plataforma de música en streaming más grande del mundo",
    # ── CEDEARs: Financiero ──
    "JPM":  "El banco más grande de EE.UU. por tamaño de activos",
    "BAC":  "Uno de los bancos más grandes de EE.UU., con millones de clientes",
    "C":    "Banco global con fuerte presencia internacional",
    "WFC":  "Uno de los bancos más tradicionales de EE.UU.",
    "GS":   "El banco de inversión más prestigioso de Wall Street",
    "MS":   "Banco de inversión y gestión de patrimonios de primer nivel",
    "V":    "La red de pagos con tarjeta más usada del mundo",
    "MA":   "Red global de pagos — gana con cada transacción con tarjeta",
    "PYPL": "Pionera de los pagos digitales en internet",
    "AXP":  "Tarjetas premium y servicios financieros para clientes de alto poder",
    # ── CEDEARs: Salud / Farma ──
    "JNJ":  "Farmacéutica y productos de salud — de las más sólidas del sector",
    "PFE":  "Laboratorio farmacéutico global — conocida por su vacuna contra el COVID",
    "MRNA": "Biotecnológica que popularizó las vacunas de ARN mensajero",
    "UNH":  "La mayor aseguradora de salud de EE.UU.",
    "ABT":  "Equipos médicos, diagnósticos y nutrición",
    "MRK":  "Laboratorio farmacéutico líder en tratamientos contra el cáncer",
    # ── CEDEARs: Energía e industria ──
    "XOM":  "Una de las petroleras más grandes del mundo",
    "CVX":  "Gigante petrolero estadounidense, integrado desde el pozo al surtidor",
    "BA":   "Uno de los dos grandes fabricantes de aviones del mundo",
    "CAT":  "Maquinaria pesada para construcción y minería — termómetro de la economía",
    "GE":   "Histórica industrial de EE.UU. — hoy enfocada en aviación y energía",
    "F":    "Automotriz estadounidense centenaria",
    "GM":   "La mayor automotriz de EE.UU. — dueña de Chevrolet",
    # ── CEDEARs: Latinoamérica ──
    "MELI": "El mayor comercio electrónico y fintech de Latinoamérica",
    "BABA": "El gigante del comercio electrónico de China",
    "PBR":  "La petrolera estatal de Brasil",
    "VALE": "Una de las mineras de hierro más grandes del mundo, de Brasil",
    "ITUB": "El banco privado más grande de Brasil",
    # ── Acciones argentinas: Bancos ──
    "GGAL": "Uno de los bancos privados más grandes de Argentina",
    "BMA":  "Banco argentino con fuerte presencia en el interior del país",
    "BBAR": "La filial argentina del banco español BBVA",
    "SUPV": "Banco argentino de tamaño mediano",
    "BHIP": "Banco argentino históricamente ligado al crédito para vivienda",
    "VALO": "Grupo financiero argentino ligado al mercado de capitales",
    # ── Acciones argentinas: Energía ──
    "YPFD":  "La principal petrolera de Argentina, de control estatal",
    "PAMP":  "La mayor empresa energética independiente de Argentina",
    "TGSU2": "Transporta y distribuye gas natural en el sur del país",
    "TGNO4": "Transporta gas natural en el norte y centro del país",
    "EDN":   "La mayor distribuidora de electricidad de Argentina",
    "CEPU":  "La mayor generadora privada de electricidad del país",
    "TRAN":  "Opera la red de alta tensión que lleva electricidad por todo el país",
    "METR":  "La principal distribuidora de gas natural del área metropolitana",
    "CAPX":  "Empresa argentina integrada de energía — petróleo, gas y electricidad",
    # ── Acciones argentinas: Industria y materiales ──
    "TXAR": "La principal productora de acero de Argentina",
    "ALUA": "La única productora de aluminio del país",
    "LOMA": "La mayor cementera de Argentina",
    "MIRG": "Fabricante argentino de electrónica y autopartes",
    "BYMA": "La empresa que opera la Bolsa de valores argentina",
    # ── Acciones argentinas: Agro / Real Estate ──
    "CRES": "Empresa agropecuaria argentina con campos en la región",
    "IRSA": "La mayor desarrolladora de shoppings y oficinas de Argentina",
    "AGRO": "Fabricante argentino de maquinaria agrícola — sembradoras y más",
    # ── Acciones argentinas: Telecom / Otros ──
    "TECO2": "La mayor empresa de telecomunicaciones del país — dueña de Personal y Flow",
    "COME":  "Grupo argentino con negocios en energía, agro y construcción",
    "MOLI":  "Empresa argentina de alimentos — dueña de marcas como Lucchetti y Gallo",
    # ── ONs (Obligaciones Negociables) ──
    "YPFDS":  "Préstamo a YPF que paga interés en dólares — respaldado por la petrolera",
    "PMCNO":  "Deuda de Pan American Energy, una de las mayores petroleras del país",
    "TGSU2O": "Deuda de la transportista de gas — paga interés en dólares",
    "VISTAO": "Deuda de Vista, productora de petróleo de Vaca Muerta",
    "TLCN":   "Deuda de Telecom — préstamo a la telefónica que paga interés",
    "PAEMO":  "Deuda de Pampa Energía con vencimiento en 2027",
    # ── FCIs ──
    "FCI-MM-COCOS":  "Fondo de liquidez de Cocos — rinde algo todos los días, rescate inmediato",
    "FCI-MM-BALANZ": "Fondo de liquidez de Balanz — para la plata que podés necesitar ya",
    "FCI-MM-IOL":    "Fondo de liquidez de InvertirOnline — disponible al instante",
    "FCI-RF-COCOS":  "Fondo de Cocos que invierte en bonos — más rendimiento, algo más de riesgo",
    "FCI-RF-BALANZ": "Fondo de Balanz en bonos — pensado para horizontes un poco más largos",
    "FCI-MIXTO":     "Combina bonos y acciones — equilibrio entre riesgo y rendimiento",
    # ── Letras ──
    "S30Y6": "Letra del Tesoro en pesos a tasa fija — vencimiento corto",
    "S31L6": "Letra del Tesoro en pesos a tasa fija — vencimiento corto",
    "S29G6": "Letra del Tesoro en pesos a tasa fija — vencimiento corto",
    "T2X6":  "Bono del Tesoro en pesos que capitaliza intereses — corto plazo",
    # ── MEP / Dólar ──
    "MEP":   "Dólares legales comprados a través de la bolsa",
    "AL30D": "Dólar MEP operado con el bono AL30 — la vía más usada",
    "GD30D": "Dólar MEP operado con el bono GD30 — alternativa con bono ley NY",
}


def get_descripcion(ticker: str) -> str:
    """
    Devuelve la descripción educativa de un activo por su ticker.
    Cadena vacía si no hay descripción registrada para ese ticker.
    """
    if not ticker:
        return ""
    return _DESCRIPCIONES_ACTIVOS.get(ticker.upper().strip(), "")


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
