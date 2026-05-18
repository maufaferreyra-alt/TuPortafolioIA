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

    # ─── ETFs (fondos del exterior que cotizan como CEDEARs) ───
    # tipo "etf": se compran como CEDEARs en Argentina, pero los
    # separamos para que en la cartera del usuario figuren como fondos
    # diversificados, igual que en la cartera sugerida.
    {"ticker": "SPY",  "nombre": "ETF S&P 500", "tipo": "etf"},
    {"ticker": "VOO",  "nombre": "ETF Vanguard S&P 500", "tipo": "etf"},
    {"ticker": "QQQ",  "nombre": "ETF Nasdaq 100", "tipo": "etf"},
    {"ticker": "EEM",  "nombre": "ETF Mercados Emergentes", "tipo": "etf"},
    {"ticker": "EWZ",  "nombre": "ETF Brasil", "tipo": "etf"},
    {"ticker": "GLD",  "nombre": "ETF Oro", "tipo": "etf"},
    {"ticker": "IAU",  "nombre": "ETF Oro iShares", "tipo": "etf"},
    {"ticker": "SLV",  "nombre": "ETF Plata", "tipo": "etf"},
    {"ticker": "XLE",  "nombre": "ETF Energía", "tipo": "etf"},
    {"ticker": "XLF",  "nombre": "ETF Sector Financiero", "tipo": "etf"},
    {"ticker": "XLK",  "nombre": "ETF Sector Tecnología", "tipo": "etf"},
    {"ticker": "ARKK", "nombre": "ETF ARK Innovation", "tipo": "etf"},
    {"ticker": "DIA",  "nombre": "ETF Dow Jones", "tipo": "etf"},
    {"ticker": "IWM",  "nombre": "ETF Russell 2000", "tipo": "etf"},

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
    # NOTA: para las acciones (empresas) la descripción es de 2 frases:
    # qué hace la empresa + un dato concreto. Los ETFs, bonos, FCIs,
    # letras y MEP mantienen su descripción de una línea.
    "AAPL":  "Fabrica el iPhone, la Mac, el iPad y los AirPods, además de servicios como App Store e iCloud. Es una de las empresas más valiosas del mundo y tiene una base de clientes enorme y fiel.",
    "MSFT":  "Dueña de Windows y Office, los programas más usados del planeta. Hoy buena parte de su crecimiento viene de la nube Azure y de su apuesta a la inteligencia artificial.",
    "GOOGL": "La empresa madre de Google, YouTube, Android y Chrome. Gana sobre todo con publicidad online, un mercado en el que domina a nivel mundial.",
    "AMZN":  "El mayor comercio electrónico del mundo. Además, su división de nube (AWS) es la más grande del planeta y aporta gran parte de las ganancias.",
    "META":  "Dueña de Facebook, Instagram, WhatsApp y Messenger. Gana con publicidad y apuesta fuerte al metaverso y a la inteligencia artificial.",
    "TSLA":  "El fabricante de autos eléctricos más valioso del mundo. También produce baterías y sistemas de energía solar, y desarrolla conducción autónoma.",
    "NVDA":  "Fabrica los chips gráficos que mueven la inteligencia artificial. Es el corazón del boom de la IA y una de las empresas más valiosas del mundo.",
    "NFLX":  "La plataforma de streaming de series y películas más grande del mundo. Produce sus propios contenidos y suma cientos de millones de suscriptores.",
    "AMD":   "Diseña procesadores y chips gráficos para computadoras y centros de datos. Es el gran rival de Intel y de NVIDIA.",
    "INTC":  "Pionera de los microprocesadores que llevan adentro la mayoría de las PC. Hoy busca recuperar terreno frente a competidores que la pasaron.",
    "CRM":   "Líder mundial en software para gestionar clientes y ventas. Las empresas le pagan una suscripción para usar sus herramientas en la nube.",
    "ORCL":  "Gigante histórico del software empresarial, conocido por sus bases de datos. Hoy también crece fuerte en servicios de nube.",
    "ADBE":  "Dueña de Photoshop, Illustrator y el formato PDF. Es el referente del software creativo y cobra a sus usuarios por suscripción.",
    "CSCO":  "Fabrica los equipos de red — routers y switches — que mantienen funcionando internet. Le vende sobre todo a empresas y operadores.",
    "QCOM":  "Diseña los chips que dan conectividad a casi todos los celulares. Cobra regalías por sus patentes en cada teléfono que las usa.",
    "IBM":   "Una de las empresas de tecnología más veteranas del mundo. Hoy se enfoca en nube, consultoría e inteligencia artificial para empresas.",
    # ── CEDEARs: Consumo y entretenimiento ──
    "DIS":  "El gigante del entretenimiento: películas, parques temáticos y el streaming Disney+. Es dueña de marcas como Marvel, Pixar y Star Wars.",
    "KO":   "La marca de bebidas más reconocida del planeta. Vende su línea de gaseosas, aguas y jugos en prácticamente todos los países.",
    "PEP":  "Dueña de Pepsi, pero también de snacks como Lay's y Doritos y de bebidas como Gatorade. El negocio de snacks le pesa tanto como el de bebidas.",
    "MCD":  "La cadena de comida rápida más grande del mundo. Buena parte de su negocio son franquicias e inmuebles, no solo vender hamburguesas.",
    "SBUX": "La cadena de cafeterías más grande del mundo. Tiene miles de locales y un programa de fidelidad con millones de clientes.",
    "NKE":  "La marca de indumentaria y calzado deportivo más valiosa del mundo. Vende en todo el planeta y cada vez más por sus canales propios.",
    "WMT":  "La cadena de supermercados más grande de Estados Unidos. Su escala enorme le permite precios bajos, y crece también en venta online.",
    "PG":   "Fabrica productos de uso diario presentes en casi todos los hogares. Es dueña de marcas como Gillette, Pampers, Ariel y Pantene.",
    "COST": "Cadena de venta mayorista en la que se compra por membresía. Sus socios son muy fieles y renuevan año tras año.",
    "HD":   "La mayor cadena de Estados Unidos de materiales para el hogar y la construcción. Su negocio sigue de cerca al mercado inmobiliario.",
    "TGT":  "Una de las grandes cadenas minoristas de Estados Unidos. Compite con Walmart, con un perfil de tienda algo más cuidado.",
    "ABNB": "La plataforma de alquileres temporarios más grande del mundo. Conecta anfitriones con viajeros y cobra una comisión por cada reserva.",
    "UBER": "Líder global de la movilidad por app: viajes en auto y delivery de comida. Opera en miles de ciudades de todo el mundo.",
    "SPOT": "La plataforma de música en streaming más grande del mundo. Gana con suscripciones premium y con publicidad en su versión gratuita.",
    # ── CEDEARs: Financiero ──
    "JPM":  "El banco más grande de Estados Unidos por tamaño. Hace de todo: banca para personas, para empresas e inversión en Wall Street.",
    "BAC":  "Uno de los bancos más grandes de Estados Unidos, con decenas de millones de clientes. Su negocio depende mucho de las tasas de interés.",
    "C":    "Banco estadounidense con la presencia internacional más amplia entre sus pares. Opera en decenas de países.",
    "WFC":  "Uno de los bancos más tradicionales de Estados Unidos, muy enfocado en banca para personas y pymes. Tiene una enorme red de sucursales.",
    "GS":   "El banco de inversión más prestigioso de Wall Street. Asesora grandes operaciones y opera activamente en los mercados financieros.",
    "MS":   "Banco de inversión de primer nivel, fuerte en la gestión de patrimonios. Administra el dinero de clientes de alto poder adquisitivo.",
    "V":    "Opera la red de pagos con tarjeta más usada del mundo. No presta dinero: gana una pequeña comisión por cada transacción que pasa por su red.",
    "MA":   "La segunda red global de pagos con tarjeta. Como Visa, gana con cada transacción sin asumir el riesgo de prestar.",
    "PYPL": "Pionera de los pagos digitales en internet. Permite pagar y cobrar online, y es dueña de la app Venmo.",
    "AXP":  "Conocida por sus tarjetas premium y su programa de puntos. A diferencia de Visa, también presta dinero a sus tarjetahabientes.",
    # ── CEDEARs: Salud / Farma ──
    "JNJ":  "Una de las farmacéuticas más sólidas del mundo. Desarrolla medicamentos y equipos médicos, y es famosa por aumentar su dividendo cada año.",
    "PFE":  "Laboratorio farmacéutico global, muy conocido por su vacuna contra el COVID. Desarrolla medicamentos para una amplia variedad de enfermedades.",
    "MRNA": "Biotecnológica que popularizó las vacunas de ARN mensajero con su vacuna contra el COVID. Apuesta esa tecnología a futuros tratamientos.",
    "UNH":  "La mayor empresa de salud de Estados Unidos. Combina seguros médicos con servicios de atención para millones de personas.",
    "ABT":  "Empresa de salud diversificada: equipos médicos, tests de diagnóstico, medicamentos y nutrición. Conocida por sus monitores de glucosa.",
    "MRK":  "Laboratorio farmacéutico líder en tratamientos contra el cáncer. Uno de sus medicamentos oncológicos es de los más vendidos del mundo.",
    # ── CEDEARs: Energía e industria ──
    "XOM":  "Una de las petroleras más grandes del mundo. Produce petróleo y gas, los refina y los vende; su resultado depende del precio del crudo.",
    "CVX":  "Gigante petrolero estadounidense integrado, del pozo al surtidor. Es de las empresas que más dividendo reparte de su sector.",
    "BA":   "Uno de los dos grandes fabricantes de aviones del mundo, junto con Airbus. Le vende a aerolíneas de todo el planeta y también a defensa.",
    "CAT":  "El mayor fabricante de maquinaria pesada para construcción y minería. Sus ventas son un termómetro de cómo viene la economía mundial.",
    "GE":   "Histórica industrial estadounidense que se reorganizó en los últimos años. Hoy se enfoca en motores de avión y en equipos de energía.",
    "F":    "Automotriz estadounidense centenaria, dueña de la pickup más vendida de EE.UU. Está invirtiendo fuerte para sumar modelos eléctricos.",
    "GM":   "La mayor automotriz de Estados Unidos, dueña de Chevrolet, GMC y Cadillac. Apuesta a la transición hacia los autos eléctricos.",
    # ── CEDEARs: Latinoamérica ──
    "MELI": "El mayor comercio electrónico de Latinoamérica. Además tiene Mercado Pago, su brazo financiero, que crece tan fuerte como la tienda online.",
    "BABA": "El gigante del comercio electrónico de China. También tiene un negocio de nube grande y participa en logística y finanzas.",
    "PBR":  "La petrolera controlada por el Estado de Brasil. Es una de las mayores productoras de petróleo de la región y suele repartir buen dividendo.",
    "VALE": "Una de las mineras de hierro más grandes del mundo, de Brasil. Su resultado depende del precio del hierro y de la demanda de China.",
    "ITUB": "El banco privado más grande de Brasil. Atiende a millones de clientes y es una de las mayores empresas de la bolsa brasileña.",
    # ── Acciones argentinas: Bancos ──
    "GGAL": "Uno de los bancos privados más grandes de Argentina. Su grupo controla el Banco Galicia y la billetera Naranja X, con millones de clientes.",
    "BMA":  "Banco privado argentino con la red de sucursales más extendida del interior del país. Es fuerte en provincias donde otros bancos casi no llegan.",
    "BBAR": "La operación local del banco español BBVA, uno de los grandes bancos privados del país. Atiende a personas y empresas con banca tradicional y digital.",
    "SUPV": "Banco argentino de tamaño mediano, con foco en personas y pymes. Es de los más chicos entre los bancos que cotizan en bolsa.",
    "BHIP": "Banco argentino históricamente ligado al crédito para la vivienda. Hoy ofrece también banca para personas y empresas.",
    "VALO": "Grupo financiero argentino enfocado en el mercado de capitales. Opera el Banco de Valores, especializado en administrar fondos y operar bonos.",
    # ── Acciones argentinas: Energía ──
    "YPFD":  "La principal petrolera de Argentina, de control estatal. Produce, refina y vende combustibles, y es clave en el desarrollo de Vaca Muerta.",
    "PAMP":  "La mayor empresa energética independiente del país. Genera electricidad, produce petróleo y gas, y participa en la petroquímica.",
    "TGSU2": "Transporta gas natural por el sur y centro del país con una extensa red de gasoductos. También procesa gas y produce líquidos en Bahía Blanca.",
    "TGNO4": "Opera la red de gasoductos que abastece de gas natural al norte y centro de Argentina. Conecta los yacimientos del norte con los grandes centros de consumo.",
    "EDN":   "La mayor distribuidora de electricidad del país. Lleva luz a millones de hogares de la zona norte y oeste del Gran Buenos Aires.",
    "CEPU":  "La mayor generadora privada de electricidad de Argentina. Opera centrales térmicas, hidroeléctricas y parques de energía renovable.",
    "TRAN":  "Opera la red de alta tensión que transporta la electricidad por todo el país. Es el nexo entre las centrales que la generan y las distribuidoras.",
    "METR":  "La principal distribuidora de gas natural del área metropolitana de Buenos Aires. Abastece a millones de hogares, comercios e industrias.",
    "CAPX":  "Empresa argentina de energía integrada: produce petróleo y gas, y genera electricidad. Concentra buena parte de su actividad en Neuquén.",
    # ── Acciones argentinas: Industria y materiales ──
    "TXAR": "La principal productora de acero del país, parte del grupo Ternium. Provee acero a la industria automotriz, la construcción y los electrodomésticos.",
    "ALUA": "La única productora de aluminio primario de Argentina. Su planta en Puerto Madryn abastece al mercado local y exporta a varios países.",
    "LOMA": "La mayor cementera de Argentina. Su negocio sigue de cerca el ritmo de la obra pública y la construcción privada.",
    "MIRG": "Empresa argentina que fabrica electrónica, climatización para autos y equipos. Tiene fuerte presencia industrial en Tierra del Fuego.",
    "BYMA": "La empresa que opera la bolsa de valores de Argentina. Gana con la actividad del mercado: cuanto más se opera, mejor le va.",
    # ── Acciones argentinas: Agro / Real Estate ──
    "CRES": "Empresa agropecuaria argentina con campos propios en el país y la región. También participa del negocio inmobiliario a través de IRSA.",
    "IRSA": "La mayor desarrolladora de inmuebles comerciales de Argentina. Es dueña de shoppings y edificios de oficinas emblemáticos de Buenos Aires.",
    "AGRO": "Fabricante argentino de maquinaria agrícola, especializado en sembradoras. Su negocio depende del ánimo del campo para invertir.",
    # ── Acciones argentinas: Telecom / Otros ──
    "TECO2": "La mayor empresa de telecomunicaciones del país. Es dueña de la marca de celulares Personal y del servicio de internet y TV Flow.",
    "COME":  "Grupo argentino con negocios diversificados en energía, agro, construcción y servicios. Es un holding que participa en varias empresas.",
    "MOLI":  "Una de las mayores empresas de alimentos de Argentina. Es dueña de marcas conocidas como Lucchetti, Gallo, Matarazzo y Vienissima.",
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
