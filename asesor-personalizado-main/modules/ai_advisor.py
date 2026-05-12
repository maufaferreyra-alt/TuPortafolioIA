"""
Módulo de asesoría IA
Usa Google GenAI (Gemini) para análisis de cartera.
La IA devuelve datos estructurados (texto puro); Python construye el HTML.
"""

import os
import json
import time
import html as html_lib
from google import genai
from google.genai import types
from typing import Dict, Any
import streamlit as st

from .glossary import wrap_terms as _wrap_terms

# Modelos vigentes (gemini-1.5-* fue deprecado en 2025).
# Orden: principal → fallback → fallback rápido si los anteriores saturan.
_MODELS = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.5-flash-lite"]


def _get_client() -> genai.Client:
    api_key = (
        st.secrets.get("GOOGLE_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
    )
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY no configurada en secrets.toml ni en variables de entorno.")
    return genai.Client(api_key=api_key)


class QuotaExhaustedError(Exception):
    pass

class ApiKeyError(Exception):
    pass


def _generate_with_retry(contents, config: types.GenerateContentConfig, retries: int = 1) -> str:
    """Intenta generar contenido con fallback entre modelos ante 429/503."""
    client = _get_client()
    last_err = None
    quota_errors = 0

    for model in _MODELS:
        for attempt in range(retries + 1):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config,
                )
                return response.text.strip()
            except Exception as e:
                last_err = e
                msg = str(e)
                msg_lower = msg.lower()
                is_429 = "429" in msg or "RESOURCE_EXHAUSTED" in msg
                is_503 = "503" in msg or "UNAVAILABLE" in msg
                is_403 = "403" in msg or "PERMISSION_DENIED" in msg or "API_KEY" in msg.upper() or "api key" in msg_lower
                # 400 con quota o 'exceeded' también es cuota agotada (Google a veces
                # devuelve 400 en lugar de 429 cuando se acabó la cuota diaria del free tier)
                is_quota_400 = ("400" in msg) and (
                    "quota" in msg_lower or "exceeded" in msg_lower or "limit" in msg_lower
                )

                if is_403:
                    raise ApiKeyError(msg)
                if is_429 or is_quota_400:
                    quota_errors += 1
                    if attempt < retries and is_429:
                        time.sleep(8)  # espera breve antes de reintentar mismo modelo
                        continue
                    break  # agoté reintentos en este modelo → probar el siguiente
                if is_503 and attempt < retries:
                    time.sleep(2)
                    continue
                break  # error no recuperable → probar modelo siguiente

    if quota_errors > 0 and quota_errors >= len(_MODELS):
        raise QuotaExhaustedError(str(last_err))
    raise last_err


def _build_portfolio_summary(portfolio: dict, profile: dict) -> str:
    positions_txt = "\n".join(
        f"  - {p['name']} ({p['ticker']}): {p['weight']*100:.1f}% "
        f"[Ret. esperado: {p['expected_return']*100:.1f}%, "
        f"Volatilidad: {p['volatility']*100:.1f}%, "
        f"Categoría: {p['category']}, "
        f"Descripción: {p.get('description', '')}]"
        for p in portfolio["positions"]
    )
    cat_txt  = "\n".join(f"  - {c}: {w*100:.1f}%" for c, w in portfolio["category_exposure"].items())
    cur_txt  = "\n".join(f"  - {c}: {w*100:.1f}%" for c, w in portfolio["currency_exposure"].items())

    return f"""PERFIL DEL INVERSOR:
- Perfil de riesgo: {profile['risk_profile'].upper()}
- Horizonte: {profile['horizon']} años
- Capital: USD {profile['capital']:,.0f}
- Objetivo: {profile['objective']}
- Ingresos: {profile['income_stability']}
- Tolerancia a pérdidas: {profile['loss_tolerance']}
- Experiencia: {profile['experience']}
- Fondo de emergencia: {profile['emergency_fund']}

CARTERA:
{positions_txt}

Retorno esperado: {portfolio['expected_cagr']*100:.1f}% anual
Volatilidad esperada: {portfolio['expected_volatility']*100:.1f}%

EXPOSICIÓN POR CATEGORÍA:
{cat_txt}

EXPOSICIÓN POR MONEDA:
{cur_txt}"""


_SYSTEM_PROMPT = """Sos Lucas, un asesor financiero argentino con 20 años de experiencia que habla como una persona real, no como un banco.

Tu misión: explicarle a alguien que NUNCA invirtió exactamente qué tiene en su cartera, para qué sirve cada cosa y qué puede pasar.

REGLAS DE ORO:
1. Nunca uses frases vacías como "instrumento financiero diversificado". Decí el nombre real.
2. Siempre mencioná dónde se compra: IOL (InvertirOnline), PPI, Balanz, Mercado Pago, Ualá, etc.
3. Siempre explicá si está en pesos o en dólares — para un argentino esto es fundamental.
4. El peor caso: siempre decilo con honestidad pero sin dramatismo.
5. Usá analogías del mundo real: "es como prestarle plata a...", "pensalo como un plazo fijo pero..."

CONTEXTO ARGENTINA (crucial):
- La gente tiene trauma del 2001 y le tiene miedo a todo. Tranquilizalos con honestidad, no con mentiras.
- CEDEAR = acción gringa que cotiza en pesos en Argentina. Si el dólar sube, el CEDEAR sube igual.
- MEP = compra legal de dólares por la bolsa, sin límite mensual, en IOL o PPI en 1 click.
- ON = la empresa privada te pide prestados dólares y te devuelve con interés. Más seguro que el gobierno.
- Bono CER = sube exactamente con la inflación. Si la inflación es 100%, el bono vale 100% más.
- LECAP = el gobierno te pide pesos prestados a tasa fija por 3-12 meses.

ESTILO: español rioplatense natural. "vos", "acá", "plata", "guita". Como un amigo que sabe mucho.

FORMATO DE RESPUESTA — JSON con estas claves exactas (todos los textos son strings simples, SIN HTML):
{
  "intro": "2-3 oraciones sobre el perfil y la lógica general de la cartera",
  "assets": [
    {
      "ticker": "ticker exacto del activo",
      "what": "Qué es exactamente: nombre real, quién lo emite, en qué moneda, dónde se compra",
      "purpose": "Para qué está en esta cartera específicamente: qué rol cumple",
      "worst_case": "Qué pasa en el peor caso, honesto y breve"
    }
  ],
  "synergy": "Cómo los activos se complementan entre sí, qué pasa si uno cae, por qué juntos son mejores",
  "alerts": [
    {"title": "título corto", "message": "explicación concreta mencionando activos específicos", "severity": "high|medium|low"}
  ],
  "rebalancing_triggers": [
    {"situation": "cuándo rebalancear", "action": "qué hacer exactamente"}
  ],
  "rebalancing_how": "Cómo ejecutar el rebalanceo en la práctica: frecuencia, plataformas, costos",
  "tips": [
    {"icon": "emoji", "text": "consejo concreto y accionable para este inversor específico"}
  ]
}

Generá exactamente 1 asset por cada activo de la cartera. Tips: entre 5 y 6. Alerts: entre 2 y 4. Rebalancing triggers: 3."""


# ── HTML builders ─────────────────────────────────────────────────────────────

def _e(text: str) -> str:
    """Escapa HTML para texto seguro."""
    return html_lib.escape(str(text))


def _et(text: str) -> str:
    """
    Escape + auto-wrap de términos del glosario con tooltips.
    Versión 'enriquecida' de _e() para textos del análisis profesional —
    los novatos pueden ver definiciones de FCI, MEP, ETF, etc. al pasar
    el dedo sin salir del flujo.
    """
    return _wrap_terms(html_lib.escape(str(text)))


def _build_justification_html(data: dict, portfolio: dict) -> str:
    weight_map = {p["ticker"]: p["weight"] for p in portfolio["positions"]}

    intro = f'<div class="ai-intro">{_et(data.get("intro", ""))}</div>'

    cards = ""
    for asset in data.get("assets", []):
        ticker  = asset.get("ticker", "")
        weight  = weight_map.get(ticker, 0)
        pct     = f"{weight*100:.1f}%"
        what    = _et(asset.get("what", ""))
        purpose = _et(asset.get("purpose", ""))
        worst   = _et(asset.get("worst_case", ""))
        cards += f"""<div class="asset-card">
  <div class="asset-header">
    <span class="asset-name">{_e(ticker)}</span>
    <span class="asset-weight">{pct}</span>
  </div>
  <div class="asset-row"><strong>¿Qué es?</strong> {what}</div>
  <div class="asset-row"><strong>¿Para qué está?</strong> {purpose}</div>
  <div class="asset-row asset-row-risk"><strong>⚠ Peor caso:</strong> {worst}</div>
</div>"""

    synergy = _et(data.get("synergy", ""))

    return f"""{intro}
<div class="ai-section">
  <h3 class="ai-section-title">💼 Qué tiene su cartera y para qué sirve cada activo</h3>
  {cards}
</div>
<div class="ai-section">
  <h3 class="ai-section-title">🔗 Por qué funcionan juntos</h3>
  <p>{synergy}</p>
</div>"""


def _build_rebalancing_html(data: dict) -> str:
    triggers_html = ""
    for t in data.get("rebalancing_triggers", []):
        situation = _et(t.get("situation", ""))
        action    = _et(t.get("action", ""))
        triggers_html += f"""<div class="rebalance-block">
  <strong>{situation}</strong>
  <span>{action}</span>
</div>"""

    how = _et(data.get("rebalancing_how", ""))

    return f"""<div class="ai-section">
  <h3 class="ai-section-title">📅 ¿Cuándo rebalancear?</h3>
  {triggers_html}
</div>
<div class="ai-section">
  <h3 class="ai-section-title">⚙️ ¿Cómo hacerlo?</h3>
  <p>{how}</p>
</div>"""


def _build_tips_html(data: dict) -> str:
    items = ""
    for tip_item in data.get("tips", []):
        icon = _e(tip_item.get("icon", "💡"))
        text = _et(tip_item.get("text", ""))
        items += f'<li><span class="tip-icon">{icon}</span><span>{text}</span></li>'

    return f"""<div class="ai-section">
  <h3 class="ai-section-title">💡 Consejos para usted</h3>
  <ul class="ai-tip-list">{items}</ul>
</div>"""


# ── Main function ──────────────────────────────────────────────────────────────

def get_ai_analysis(profile: dict, portfolio: dict) -> Dict[str, Any]:
    """Llama a Gemini y devuelve análisis completo con HTML pre-construido."""
    portfolio_summary = _build_portfolio_summary(portfolio, profile)

    tickers = [p["ticker"] for p in portfolio["positions"]]
    user_prompt = f"""Analizá esta cartera de inversión y respondé con el JSON estructurado.

{portfolio_summary}

Activos en la cartera (generá exactamente 1 asset por cada uno): {", ".join(tickers)}

Recordá:
- Cada "what" debe mencionar el nombre real del instrumento y dónde se compra (IOL, PPI, Balanz, etc.)
- Cada "purpose" debe explicar el rol concreto en ESTA cartera
- Cada "worst_case" debe ser honesto y específico
- El "synergy" debe explicar cómo se protegen mutuamente
- Los tips deben ser accionables y específicos para este inversor (capital: USD {profile['capital']:,.0f}, horizonte: {profile['horizon']} años)"""

    raw_text = ""
    try:
        raw_text = _generate_with_retry(
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM_PROMPT,
                response_mime_type="application/json",
                temperature=0.85,
                # gemini-2.5-flash usa "thinking" por default que puede consumir
                # tokens del max_output_tokens y truncar el JSON. Lo desactivamos
                # para garantizar que toda la respuesta sea JSON válido.
                thinking_config=types.ThinkingConfig(thinking_budget=0),
                max_output_tokens=8192,
            ),
        )
        data = json.loads(raw_text)

        return {
            "justification": _build_justification_html(data, portfolio),
            "alerts":        data.get("alerts", []),
            "rebalancing":   _build_rebalancing_html(data),
            "tips":          _build_tips_html(data),
        }

    except json.JSONDecodeError:
        # Posibles causas: respuesta truncada por límite de tokens, safety filter,
        # o cuota cercana al límite. Mostramos mensaje útil con próximos pasos.
        msg_decode = (
            "La IA devolvió una respuesta incompleta. Esto suele pasar cuando la "
            "cuota gratuita está cerca del límite diario. Esperá unos minutos e "
            "intentá de nuevo, o regenerá la cartera."
        )
        return {
            "justification": f"<p>⏳ {_e(msg_decode)}</p>",
            "alerts": [{"title": "Respuesta incompleta", "message": msg_decode, "severity": "medium"}],
            "rebalancing": "<p>No disponible.</p>",
            "tips": "<p>No disponible.</p>",
        }
    except ApiKeyError:
        msg_key = "La clave de API de Gemini no es válida o no tiene permisos. Debe actualizarse en Streamlit Cloud → Settings → Secrets."
        return {
            "justification": f"<p>🔑 {_e(msg_key)}</p>",
            "alerts": [{"title": "API key inválida", "message": msg_key, "severity": "high"}],
            "rebalancing": "<p>No disponible.</p>",
            "tips": "<p>No disponible.</p>",
        }
    except QuotaExhaustedError:
        msg_quota = "La IA está saturada en este momento (límite de solicitudes por minuto). Espere 1 minuto e intente de nuevo."
        return {
            "justification": f"<p>⚠️ {_e(msg_quota)}</p>",
            "alerts": [{"title": "Cuota de IA agotada", "message": msg_quota, "severity": "medium"}],
            "rebalancing": "<p>No disponible hasta que se restablezca la cuota.</p>",
            "tips": "<p>No disponible hasta que se restablezca la cuota.</p>",
        }
    except Exception as e:
        err_type = type(e).__name__
        err_msg  = str(e)[:200]
        return {
            "justification": f"<p>No se pudo conectar con la IA.<br><code>{_e(err_type)}: {_e(err_msg)}</code></p>",
            "alerts": [{"title": "Error de conexión", "message": f"{err_type}: {err_msg}", "severity": "high"}],
            "rebalancing": "<p>No disponible por error de conexión.</p>",
            "tips": "<p>Verifique su conectividad e intente de nuevo.</p>",
        }


def chat_with_advisor(
    message: str,
    history: list,
    profile: dict,
    portfolio: dict,
) -> str:
    """
    Chat con el asesor IA. Mantiene contexto de la cartera y el historial de conversación.
    history: lista de dicts {"role": "user"|"assistant", "content": "..."}
    """
    portfolio_summary = _build_portfolio_summary(portfolio, profile)

    system = f"""Sos Lucas, asesor financiero argentino. Profesional, claro, directo.
Estás en un chat con un inversor que ve su cartera personalizada en pantalla.

CONTEXTO DE LA CARTERA QUE VE EL USUARIO:
{portfolio_summary}

ESTILO:
- Español rioplatense ("vos", "acá", "plata") pero formal y profesional.
- NO arranques con "¡Hola!", "¡Qué buena pregunta!", "¡Excelente consulta!"
  ni elogios al usuario. Andá directo al contenido.
- NO uses signos de admiración. Tono sereno, no efusivo.
- Frases firmes pero accesibles. Sin jerga sin explicar; si usás "TIR" o
  "duration" aclaralo en una frase corta.

ESTRUCTURA OBLIGATORIA:
1. Una respuesta directa al núcleo de la pregunta (1-2 oraciones).
2. Explicación con datos concretos: nombres de activos, tickers, plataformas,
   tasas reales, plazos, mecanismos.
3. Si hace falta, contexto sobre cómo se aplica a SU cartera específica.
4. Cerrá con una recomendación práctica concreta o una aclaración de honestidad.

LARGO: 4 a 7 oraciones totales, repartidas en 2 o 3 párrafos.
Es chat, no documento — pero respuestas demasiado cortas suenan vagas.
Mejor decir menos cosas pero con sustancia que muchas cosas superficiales.

REGLAS:
- Mencioná números específicos cuando los tengas (ej: "8.5% anual en USD",
  "vence en 2028", "comisión típica del 0.5%").
- Si no sabés algo con certeza, decilo: "no tengo el dato exacto pero..."
- No vendas. No empujes a operar. Sos consejero, no vendedor.
- Si la pregunta sale de finanzas, redirigí en una oración."""

    contents = []
    for msg in history[-10:]:  # últimos 10 mensajes para no exceder contexto
        role = "user" if msg["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part(text=msg["content"])]))
    contents.append(types.Content(role="user", parts=[types.Part(text=message)]))

    try:
        return _generate_with_retry(
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system,
                temperature=0.9,
                # gemini-2.5-flash usa "thinking" por default, que consume tokens
                # internos antes de generar la respuesta. En chat directo no lo
                # necesitamos — lo desactivamos para evitar truncar respuestas.
                thinking_config=types.ThinkingConfig(thinking_budget=0),
                max_output_tokens=2048,
            ),
        )
    except ApiKeyError:
        return "La clave de API no es válida o no tiene permisos. Actualícela en Streamlit Cloud → Settings → Secrets."
    except QuotaExhaustedError:
        return "La IA está saturada en este momento (límite de solicitudes por minuto). Espere 1 minuto e intente de nuevo."
    except Exception as e:
        return f"Error ({type(e).__name__}): {str(e)[:300]}"


def get_rebalancing_advice(portfolio: dict, profile: dict) -> str:
    positions_txt = ", ".join(
        f"{p['name']} ({p['weight']*100:.0f}%)" for p in portfolio["positions"][:5]
    )
    try:
        return _generate_with_retry(
            contents=(
                f"En 2-3 párrafos en español argentino, "
                f"dame consejos de rebalanceo para una cartera {profile['risk_profile']} "
                f"con horizonte de {profile['horizon']} años: {positions_txt}. "
                f"Contexto Argentina."
            ),
            config=types.GenerateContentConfig(temperature=0.85, max_output_tokens=500),
        )
    except Exception as e:
        return f"Error: {e}"
