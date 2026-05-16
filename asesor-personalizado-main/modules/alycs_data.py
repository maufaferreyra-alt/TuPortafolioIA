"""
Datos de las ALyCs (Agentes de Liquidación y Compensación) argentinos
más usados por retail. Información estática actualizada a 2026.

Las "ventajas" y "desventajas" están escritas en lenguaje cotidiano,
NO técnico, para usuarios que no saben invertir.
"""

ALYCS = [
    {
        "id": "cocos",
        "nombre": "Cocos Capital",
        "logo_emoji": "🥥",  # placeholder hasta tener imagen real
        "color": "#7c3aed",
        "tagline": "El broker más amigable para quien empieza",

        "comision_cedears":  "0.5% por operación",
        "comision_bonos":    "0.3% por operación",
        "custodia":          "Sin costo",
        "minimo_apertura":   "Sin mínimo",
        "plataforma":        "App + Web",

        "ventajas": [
            "La app es la más fácil de usar — ideal si nunca invertiste",
            "No te cobra nada por tener tu plata ahí (custodia gratis)",
            "Podés empezar con poca plata, no piden mínimo",
        ],
        "desventajas": [
            "No tiene asesores humanos asignados, todo es por chat",
            "Es relativamente nuevo, menos historia que los tradicionales",
        ],

        "url_apertura": "https://cocos.capital",
        "tiene_asesor_humano": False,
        "mejor_para": "Empezar a invertir sin saber mucho",
    },
    {
        "id": "bullmarket",
        "nombre": "Bull Market",
        "logo_emoji": "🐂",
        "color": "#22c55e",
        "tagline": "Plataforma sólida, buena para crecer",

        "comision_cedears":  "0.5% por operación",
        "comision_bonos":    "0.3% por operación",
        "custodia":          "Sin costo (a partir de $500.000)",
        "minimo_apertura":   "Sin mínimo",
        "plataforma":        "App + Web",

        "ventajas": [
            "Plataforma muy estable, casi nunca falla",
            "Tienen mucha información y videos educativos",
            "Buen servicio de soporte si tenés dudas",
        ],
        "desventajas": [
            "La app es un poco más compleja que la de Cocos",
            "Cobran custodia si tu cuenta tiene menos de $500.000",
        ],

        "url_apertura": "https://www.bullmarketbrokers.com",
        "tiene_asesor_humano": True,
        "mejor_para": "Crecer una vez que ya entendiste lo básico",
    },
    {
        "id": "balanz",
        "nombre": "Balanz",
        "logo_emoji": "⚖️",
        "color": "#3b82f6",
        "tagline": "Tradicional, full service con asesor humano",

        "comision_cedears":  "0.6% por operación",
        "comision_bonos":    "0.3% por operación",
        "custodia":          "0.025% mensual",
        "minimo_apertura":   "Sin mínimo",
        "plataforma":        "App + Web + Asesor",

        "ventajas": [
            "Te asignan un asesor humano para que te guíe",
            "Hacen análisis e informes propios del mercado",
            "Bueno si querés invertir más de $1.000.000",
        ],
        "desventajas": [
            "Cobran custodia mensual (un porcentaje chico de tu plata)",
            "La comisión es un poco más alta que Cocos o Bull Market",
        ],

        "url_apertura": "https://balanz.com",
        "tiene_asesor_humano": True,
        "mejor_para": "Querés que alguien te asesore activamente",
    },
    {
        "id": "iol",
        "nombre": "InvertirOnline (IOL)",
        "logo_emoji": "💼",
        "color": "#f59e0b",
        "tagline": "El más conocido y usado en Argentina",

        "comision_cedears":  "0.6% por operación",
        "comision_bonos":    "0.3% por operación",
        "custodia":          "0.025% mensual",
        "minimo_apertura":   "Sin mínimo",
        "plataforma":        "App + Web",

        "ventajas": [
            "Es el broker más usado, encontrás mucha info online",
            "Plataforma con muchas funciones para usuarios avanzados",
            "Es del Grupo Supervielle, una empresa grande y conocida",
        ],
        "desventajas": [
            "La interfaz puede ser confusa para principiantes",
            "Cobran custodia mensual, aunque sea poca plata",
        ],

        "url_apertura": "https://www.invertironline.com",
        "tiene_asesor_humano": True,
        "mejor_para": "Tener una opción conocida y respaldada",
    },
    {
        "id": "ppi",
        "nombre": "Portfolio Personal (PPI)",
        "logo_emoji": "📊",
        "color": "#06b6d4",
        "tagline": "Profesional, para inversores con experiencia",

        "comision_cedears":  "0.6% por operación",
        "comision_bonos":    "0.3% por operación",
        "custodia":          "Consultar (varía por cuenta)",
        "minimo_apertura":   "Recomendado $500.000+",
        "plataforma":        "App + Web + Asesor",

        "ventajas": [
            "Tienen muy buenos análisis de mercado argentino",
            "Te asignan asesor humano dedicado",
            "Buena opción para inversiones más grandes",
        ],
        "desventajas": [
            "Pensado para gente que ya sabe — interfaz técnica",
            "Mejor si tenés al menos $500.000 para empezar",
        ],

        "url_apertura": "https://www.portfoliopersonal.com",
        "tiene_asesor_humano": True,
        "mejor_para": "Ya tenés experiencia y querés acompañamiento profesional",
    },
    {
        "id": "adcap",
        "nombre": "Adcap Securities",
        "logo_emoji": "🎯",
        "color": "#ec4899",
        "tagline": "Boutique, atención personalizada",

        "comision_cedears":  "A negociar con asesor",
        "comision_bonos":    "A negociar con asesor",
        "custodia":          "A negociar con asesor",
        "minimo_apertura":   "Recomendado $1.000.000+",
        "plataforma":        "Web + Asesor (la app es básica)",

        "ventajas": [
            "Atención muy personalizada, casi como banca privada",
            "Buenos para inversiones más grandes y complejas",
            "Tienen productos exclusivos no disponibles en otros lados",
        ],
        "desventajas": [
            "No es ideal para principiantes",
            "Conviene tener al menos $1.000.000 para que valga la pena",
        ],

        "url_apertura": "https://www.adcap.com.ar",
        "tiene_asesor_humano": True,
        "mejor_para": "Inversiones medianas-grandes con asesoramiento boutique",
    },
]


def generar_mensaje_para_asesor(portfolio: dict, profile: dict) -> str:
    """
    Arma el texto que el usuario puede copiar y pegar al asesor del broker.
    Tono: el usuario hablando a su asesor humano.
    """
    # El profiler guarda el rótulo del perfil en "profile_label"; si falta,
    # se cae al risk_profile crudo.
    perfil_label = profile.get("profile_label") or profile.get("risk_profile", "Inversor")
    capital = profile.get("capital_original", profile.get("capital", 0))
    currency = profile.get("currency", "ARS")
    horizonte = profile.get("horizon", 5)

    # Capital formateado
    if currency == "ARS":
        capital_str = f"${capital:,.0f} ARS"
    else:
        capital_str = f"USD ${capital:,.0f}"

    # Composición resumida (por categoría)
    posiciones = portfolio.get("positions", [])
    cat_weights = {}
    for pos in posiciones:
        cat = pos.get("category", "Otros")
        cat_weights[cat] = cat_weights.get(cat, 0) + pos.get("weight", 0)

    composicion_lineas = []
    for cat, peso in sorted(cat_weights.items(), key=lambda x: -x[1]):
        composicion_lineas.append(f"   • {cat}: {peso*100:.0f}%")
    composicion_str = "\n".join(composicion_lineas)

    # Activos individuales
    activos_str = ""
    if posiciones:
        activos_lineas = []
        for pos in posiciones[:10]:  # primeros 10 para no saturar
            ticker = pos.get("ticker", "")
            name = pos.get("name", "").split("(")[0].strip()
            peso = pos.get("weight", 0) * 100
            if ticker:
                activos_lineas.append(f"   • {name} ({ticker}): {peso:.1f}%")
            else:
                activos_lineas.append(f"   • {name}: {peso:.1f}%")
        activos_str = "\n".join(activos_lineas)

    mensaje = f"""Hola, generé una propuesta de cartera con TuPortafolioIA que quería revisar con vos.

Mis datos:
   • Perfil: {perfil_label}
   • Capital a invertir: {capital_str}
   • Horizonte: {horizonte} año{'s' if horizonte != 1 else ''}

Distribución por categoría:
{composicion_str}

Activos sugeridos:
{activos_str}

Me gustaría que veamos juntos:
   1. Si la cartera tiene sentido para mi situación
   2. Cómo ejecutarla en la plataforma
   3. Cuándo y cómo revisarla en el tiempo

¿Podemos coordinar una llamada o reunión?

Gracias."""

    return mensaje
