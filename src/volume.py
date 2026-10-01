import logging

try:
    from pycaw.pycaw import AudioUtilities
except ImportError:
    AudioUtilities = None

LOGGER = logging.getLogger("nexus")


def _process_name(app_user_model_id: str) -> str:
    """'Spotify.exe' -> 'spotify.exe'; algunas apps reportan el AUMID completo
    (ej. 'Microsoft.YourPhone_8wekyb3d8bbwe!App'), de ahí solo tomamos el nombre
    de proceso si parece un .exe, si no devolvemos vacío."""
    name = app_user_model_id.strip()
    if name.lower().endswith(".exe"):
        return name.lower()
    return ""


def _find_session(app_user_model_id: str):
    if AudioUtilities is None:
        return None
    target = _process_name(app_user_model_id)
    if not target:
        return None
    try:
        for session in AudioUtilities.GetAllSessions():
            if session.Process and session.Process.name().lower() == target:
                return session
    except Exception as exc:
        LOGGER.debug("No se pudo enumerar sesiones de audio: %s", exc)
    return None


def get_volume(app_user_model_id: str) -> float | None:
    """Volumen (0.0-1.0) del proceso que alimenta la sesión multimedia activa, o None
    si no se pudo determinar (pycaw no disponible, o la app no tiene sesión de audio propia)."""
    session = _find_session(app_user_model_id)
    if session is None or session.SimpleAudioVolume is None:
        return None
    try:
        return float(session.SimpleAudioVolume.GetMasterVolume())
    except Exception as exc:
        LOGGER.debug("No se pudo leer el volumen: %s", exc)
        return None


def set_volume(app_user_model_id: str, value: float) -> bool:
    session = _find_session(app_user_model_id)
    if session is None or session.SimpleAudioVolume is None:
        return False
    try:
        session.SimpleAudioVolume.SetMasterVolume(max(0.0, min(1.0, value)), None)
        return True
    except Exception as exc:
        LOGGER.debug("No se pudo cambiar el volumen: %s", exc)
        return False
