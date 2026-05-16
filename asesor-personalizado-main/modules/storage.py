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
from streamlit_local_storage import LocalStorage

_local_storage = LocalStorage()

SCHEMA_VERSION = "1.0"
STORAGE_KEY = "tuportafolioia_data_v1"
DIAS_EXPIRACION = 30


def guardar_estado(answers: dict, profile: dict, portfolio: dict) -> bool:
    """Guarda en localStorage las respuestas + cartera generada."""
    try:
        data = {
            "schema_version": SCHEMA_VERSION,
            "guardado_en": datetime.now().isoformat(),
            "answers": _serialize(answers),
            "profile": _serialize(profile),
            "portfolio": _serialize(portfolio),
        }

        data_str = json.dumps(data, default=str, ensure_ascii=False)
        _local_storage.setItem(STORAGE_KEY, data_str)
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
        data_str = _local_storage.getItem(STORAGE_KEY)

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

        return {
            "answers":     data.get("answers", {}),
            "profile":     data.get("profile", {}),
            "portfolio":   data.get("portfolio", {}),
            "guardado_en": data.get("guardado_en"),
        }

    except Exception as e:
        print(f"[storage] Error cargando: {e}")
        return None


def limpiar_estado() -> bool:
    """Borra todo lo guardado."""
    try:
        _local_storage.deleteItem(STORAGE_KEY)
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
