"""
Persistencia local de la cartera y respuestas del usuario.

Usa streamlit-local-storage para guardar datos en el navegador del
usuario. Sin auth, sin DB.

Datos guardados:
- Respuestas del cuestionario (capital, horizonte, perfil, etc.)
- Cartera generada (positions, métricas, haircut)
- Timestamp de creación

Expiración: 30 días. Después de eso, los datos macro (MEP, scoring,
riesgo país) ya no son representativos del mercado actual y la
cartera puede no reflejar la realidad.
"""

import json
from datetime import datetime, timedelta

import streamlit as st
from streamlit_local_storage import LocalStorage

# NOTA: NO crear LocalStorage() acá como singleton de módulo.
# Causa raíz del bug de persistencia que arreglamos:
#   El singleton se construye 1 vez por proceso del servidor. El
#   constructor lee el localStorage del navegador en ese momento y
#   guarda el resultado en un caché interno. getItem() NUNCA vuelve a
#   consultar el navegador — solo lee el caché. Si el caché quedó
#   vacío (timing del componente Streamlit), queda vacío toda la vida
#   del proceso → cargar_estado() devuelve None para siempre.
#
# El fix: app.py crea la instancia 1 vez por sesión en st.session_state,
# y llama refreshItems() en cada run del script. Las funciones de este
# módulo usan _get_storage() para acceder a esa instancia ya refrescada.

SCHEMA_VERSION = "1.0"
STORAGE_KEY = "tuportafolioia_data_v1"
DIAS_EXPIRACION = 30


def _get_storage() -> LocalStorage | None:
    """
    Devuelve la instancia de LocalStorage de la sesión actual.

    Debe haber sido inicializada en app.py al inicio de cada run del
    script. Si por algún motivo no existe (orden de importación raro,
    test sin Streamlit, etc.), devuelve None y las funciones públicas
    de este módulo degradan a no-op silencioso (con log).
    """
    try:
        return st.session_state.get("_local_storage")
    except Exception:
        return None


def guardar_estado(
    answers: dict,
    profile: dict,
    portfolio: dict,
    user_portfolio_activos: list | None = None,
) -> bool:
    """Guarda en localStorage las respuestas + cartera generada."""
    try:
        data = {
            "schema_version": SCHEMA_VERSION,
            "guardado_en": datetime.now().isoformat(),
            "answers": _serialize(answers),
            "profile": _serialize(profile),
            "portfolio": _serialize(portfolio),
            "user_portfolio_activos": _serialize(user_portfolio_activos or []),
        }

        data_str = json.dumps(data, default=str, ensure_ascii=False)
        ls = _get_storage()
        if ls is None:
            print("[storage] LocalStorage no inicializado (app.py debió hacerlo)")
            return False
        ls.setItem(STORAGE_KEY, data_str)
        return True

    except Exception as e:
        print(f"[storage] Error guardando: {e}")
        return False


def cargar_estado() -> dict | None:
    """
    Carga el estado guardado desde localStorage.

    Returns dict si hay datos válidos.
    Returns None si no hay nada O si expiró (>30 días).
    """
    try:
        ls = _get_storage()
        if ls is None:
            return None
        data_str = ls.getItem(STORAGE_KEY)

        if not data_str:
            return None

        data = json.loads(data_str)

        # Validar versión del esquema
        if data.get("schema_version") != SCHEMA_VERSION:
            print("[storage] Esquema viejo, descartando")
            limpiar_estado()
            return None

        # Validar expiración (30 días)
        if data.get("guardado_en"):
            guardado = datetime.fromisoformat(data["guardado_en"])
            antiguedad = datetime.now() - guardado
            if antiguedad > timedelta(days=DIAS_EXPIRACION):
                print(f"[storage] Datos expirados ({antiguedad.days} días)")
                limpiar_estado()
                return None

        # ── Migración silenciosa: entries con precio_actual_ars contaminado ──
        # En el bug del 6A inicial, el modo simple guardaba
        # precio_actual_ars = monto_invertido_ars (una "unidad virtual" =
        # monto total). Eso después en modo unidades generaba cálculos x40000%.
        # Detectamos esa firma específica y limpiamos.
        activos_raw = data.get("user_portfolio_activos", [])
        activos_migrados = []
        for a in activos_raw:
            if not isinstance(a, dict):
                continue
            precio_actual = a.get("precio_actual_ars")
            monto = a.get("monto_invertido_ars", 0)
            # Firma del bug: precio_actual existe, precio_compra no,
            # y precio_actual ≈ monto_invertido (una "unidad virtual").
            tiene_bug = (
                precio_actual is not None
                and monto > 0
                and not a.get("precio_compra_ars")
                and abs(precio_actual - monto) < 0.01
            )
            if tiene_bug:
                print(f"[storage] Migrando entry contaminada: {a.get('ticker')}")
                a["precio_actual_ars"] = None
                a["precio_compra_ars"] = None
            activos_migrados.append(a)

        return {
            "answers":     data.get("answers", {}),
            "profile":     data.get("profile", {}),
            "portfolio":   data.get("portfolio", {}),
            "user_portfolio_activos": activos_migrados,
            "guardado_en": data.get("guardado_en"),
        }

    except Exception as e:
        print(f"[storage] Error cargando: {e}")
        return None


def limpiar_estado() -> bool:
    """Borra todo lo guardado."""
    try:
        ls = _get_storage()
        if ls is None:
            print("[storage] LocalStorage no inicializado")
            return False
        ls.deleteItem(STORAGE_KEY)
        return True
    except Exception as e:
        print(f"[storage] Error limpiando: {e}")
        return False


def tiene_estado_guardado() -> bool:
    """True si hay algo guardado Y no expiró."""
    return cargar_estado() is not None


def antiguedad_estado() -> tuple[str, int] | None:
    """
    Devuelve tupla (texto, días) de hace cuánto se guardó.
    Ej: ("hace 2 horas", 0), ("hace 5 días", 5), ("hace 1 mes", 30)

    Returns None si no hay nada guardado o expiró.
    """
    estado = cargar_estado()
    if not estado or not estado.get("guardado_en"):
        return None

    try:
        guardado = datetime.fromisoformat(estado["guardado_en"])
        delta = datetime.now() - guardado

        segundos = int(delta.total_seconds())
        dias = delta.days

        if segundos < 60:
            texto = "hace un momento"
        elif segundos < 3600:
            minutos = segundos // 60
            texto = f"hace {minutos} minuto{'s' if minutos != 1 else ''}"
        elif segundos < 86400:
            horas = segundos // 3600
            texto = f"hace {horas} hora{'s' if horas != 1 else ''}"
        elif segundos < 604800:
            d = segundos // 86400
            texto = f"hace {d} día{'s' if d != 1 else ''}"
        elif segundos < 2592000:
            semanas = segundos // 604800
            texto = f"hace {semanas} semana{'s' if semanas != 1 else ''}"
        else:
            meses = segundos // 2592000
            texto = f"hace {meses} mes{'es' if meses != 1 else ''}"

        return (texto, dias)
    except Exception:
        return None


def datos_muy_viejos() -> bool:
    """
    True si los datos están guardados pero tienen más de 15 días.
    A los 15+ días los datos macro (MEP, etc.) ya pueden ser distintos
    y vale la pena sugerir regenerar.

    Si pasaron >30 días, cargar_estado() ya los descartó.
    """
    info = antiguedad_estado()
    if not info:
        return False
    _, dias = info
    return dias >= 15


def _serialize(obj):
    """Hace serializable cualquier dict."""
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_serialize(v) for v in obj]
    elif isinstance(obj, (int, float, str, bool, type(None))):
        return obj
    else:
        return str(obj)
