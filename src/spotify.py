import asyncio
import logging
import math
import random
import threading
import time
from dataclasses import dataclass
from io import BytesIO

from PIL import Image

from . import volume as volume_ctl

try:
    from winsdk.windows.media.control import (
        GlobalSystemMediaTransportControlsSessionManager as SessionManager,
        GlobalSystemMediaTransportControlsSessionPlaybackStatus as PlaybackStatus,
    )
    from winsdk.windows.storage.streams import DataReader
except ImportError:
    SessionManager = None
    PlaybackStatus = None
    DataReader = None


LOGGER = logging.getLogger("nexus")


@dataclass
class TrackInfo:
    title: str = "Nexus Mini Player"
    artist: str = "Abre Spotify, YouTube Music o Apple Music"
    playing: bool = False
    duration_ms: int = 0
    position_ms: int = 0
    cover: Image.Image | None = None
    accent_color: tuple[int, int, int] = (201, 91, 69)
    app_id: str = ""
    error: str = ""


def extract_accent_color(img: Image.Image) -> tuple[int, int, int]:
    """Elige un color vivo y representativo de la carátula (no el promedio, que da grises apagados)."""
    small = img.convert("RGB").resize((48, 48), Image.Resampling.BILINEAR)
    palette_img = small.quantize(colors=6, method=Image.Quantize.MEDIANCUT)
    palette = palette_img.getpalette()
    counts = sorted(palette_img.getcolors(), reverse=True)

    best = None
    best_score = -1.0
    for count, idx in counts:
        r, g, b = palette[idx * 3: idx * 3 + 3]
        mx, mn = max(r, g, b), min(r, g, b)
        lightness = (mx + mn) / 2 / 255
        saturation = 0 if mx == mn else (mx - mn) / (255 - abs(mx + mn - 255))
        if lightness < 0.12 or lightness > 0.92:
            continue
        score = saturation * 0.8 + (count / len(small.getdata())) * 0.2
        if score > best_score:
            best_score = score
            best = (r, g, b)

    if best is None and counts:
        _, idx = counts[0]
        best = tuple(palette[idx * 3: idx * 3 + 3])
    return best or (201, 91, 69)


class SpotifySession:
    def __init__(self):
        self._loop = asyncio.new_event_loop()
        self._lock = threading.Lock()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

        self._info = TrackInfo()
        self._last_title = None
        self._cover_updated = False
        self._last_refresh = time.time()
        self._refreshing = False

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def close(self):
        if self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)

    def run_coroutine(self, coro):
        return asyncio.run_coroutine_threadsafe(coro, self._loop)

    async def _get_session(self):
        """Devuelve la sesión multimedia a mostrar: Nexus no está atado a Spotify,
        lee cualquier app que registre su sesión con Windows (Spotify, YouTube Music,
        Apple Music, el navegador, etc.) y prioriza la que esté sonando en este momento."""
        if SessionManager is None:
            return None
        try:
            manager = await SessionManager.request_async()
            sessions = list(manager.get_sessions())
            if not sessions:
                return None

            for session in sessions:
                if self._is_playing(session.get_playback_info().playback_status):
                    return session

            current = manager.get_current_session()
            if current:
                return current
            return sessions[0]
        except Exception:
            return None

    async def control(self, action: str):
        session = await self._get_session()
        if not session:
            return False
        try:
            if action == "play":
                await session.try_toggle_play_pause_async()
            elif action == "next":
                await session.try_skip_next_async()
            elif action == "prev":
                await session.try_skip_previous_async()
            return True
        except Exception as exc:
            LOGGER.warning("Control failed: %s", exc)
            return False

    async def seek(self, position_ms: int):
        session = await self._get_session()
        if not session:
            return False
        try:
            ticks = int(max(0, position_ms) * 10000)
            await session.try_change_playback_position_async(ticks)
            return True
        except Exception as exc:
            LOGGER.warning("Seek failed: %s", exc)
            return False

    def get_volume(self) -> float | None:
        """Volumen (0.0-1.0) del proceso que alimenta la sesión activa. Esto no viene
        de GSMTC (la API de 'now playing' no expone volumen): se lee del mezclador de
        audio de Windows (pycaw), buscando el proceso por su nombre de app."""
        app_id = self.snapshot().app_id
        if not app_id:
            return None
        return volume_ctl.get_volume(app_id)

    def set_volume(self, value: float) -> bool:
        app_id = self.snapshot().app_id
        if not app_id:
            return False
        return volume_ctl.set_volume(app_id, value)

    async def refresh(self):
        if SessionManager is None:
            with self._lock:
                self._info = TrackInfo(
                    title="Windows Media no disponible",
                    artist="Esta versión de Windows no soporta esta función",
                    error="sin_soporte",
                )
            return
        if self._refreshing:
            return
        self._refreshing = True
        try:
            session = await self._get_session()
            if not session:
                with self._lock:
                    self._info = TrackInfo(
                        title="Nada reproduciéndose",
                        artist="Abre Spotify, YouTube Music o Apple Music",
                        error="sin_sesion",
                    )
                    self._last_refresh = time.time()
                return
            try:
                props = await session.try_get_media_properties_async()
                playback = session.get_playback_info()
                timeline = session.get_timeline_properties()

                title = props.title or "Sin título"
                artist = props.artist or "Artista desconocido"
                playing = self._is_playing(playback.playback_status)
                duration = self._ms(timeline.end_time)
                reported_position = self._ms(timeline.position)
                position = self._reconcile_position(title, playing, reported_position)

                app_id = session.source_app_user_model_id or ""

                new_cover = None
                new_accent = None
                if title != self._last_title:
                    new_cover = await self._read_cover(props.thumbnail)
                    if new_cover is not None:
                        new_accent = extract_accent_color(new_cover)

                with self._lock:
                    self._info = TrackInfo(
                        title=title,
                        artist=artist,
                        playing=playing,
                        duration_ms=duration,
                        position_ms=position,
                        cover=new_cover if new_cover is not None else self._info.cover,
                        accent_color=new_accent if new_accent is not None else self._info.accent_color,
                        app_id=app_id,
                    )
                    self._cover_updated = new_cover is not None
                    self._last_title = title
                    self._last_refresh = time.time()
            except Exception as exc:
                LOGGER.debug("Refresh failed: %s", exc)
        finally:
            self._refreshing = False

    def _reconcile_position(self, title: str, playing: bool, reported_ms: int) -> int:
        """GSMTC/Spotify no siempre reporta la posición en tiempo real: a veces manda
        un valor desactualizado unos segundos, que luego "corrige" de golpe. Eso se ve
        como la barra retrocediendo y saltando. Para evitarlo, solo confiamos en el
        valor nuevo si es coherente con lo que ya veníamos extrapolando nosotros."""
        if title != self._last_title:
            return reported_ms

        with self._lock:
            prev = self._info
            elapsed = time.time() - self._last_refresh
            predicted = prev.position_ms + (elapsed * 1000 if prev.playing else 0)

        if not playing:
            return reported_ms
        if reported_ms >= predicted - 400:
            return reported_ms
        # El dato reportado quedó atrás de nuestra extrapolación: probablemente está
        # desactualizado (Spotify aún no empujó el valor real). Seguimos extrapolando.
        return int(predicted)

    async def _read_cover(self, thumbnail_ref):
        if not thumbnail_ref or DataReader is None:
            return None
        try:
            stream = await thumbnail_ref.open_read_async()
            reader = DataReader(stream.get_input_stream_at(0))
            await reader.load_async(stream.size)
            buf = bytearray(stream.size)
            reader.read_bytes(buf)
            img = Image.open(BytesIO(bytes(buf))).convert("RGBA")
            img.thumbnail((320, 320), Image.Resampling.LANCZOS)
            return img
        except Exception:
            return None

    def _is_playing(self, status):
        if PlaybackStatus is not None:
            try:
                return status == PlaybackStatus.PLAYING
            except AttributeError:
                pass
        return int(status) == 4

    def _ms(self, value):
        if value is None:
            return 0
        try:
            if hasattr(value, "total_milliseconds"):
                return max(0, int(value.total_milliseconds()))
        except Exception:
            pass
        try:
            if hasattr(value, "total_seconds"):
                return max(0, int(value.total_seconds() * 1000))
        except Exception:
            pass
        try:
            if hasattr(value, "duration"):
                return max(0, int(value.duration / 10000))
        except Exception:
            pass
        try:
            v = max(0, float(value))
            return int(v / 10000) if v > 10_000_000 else int(v)
        except Exception:
            pass
        return 0

    def snapshot(self) -> TrackInfo:
        with self._lock:
            info = self._info
            pos = info.position_ms
            if info.playing:
                pos += (time.time() - self._last_refresh) * 1000
            if info.duration_ms > 0:
                pos = min(pos, info.duration_ms)
            return TrackInfo(
                title=info.title,
                artist=info.artist,
                playing=info.playing,
                duration_ms=info.duration_ms,
                position_ms=pos,
                cover=info.cover,
                accent_color=info.accent_color,
                app_id=info.app_id,
                error=info.error,
            )

    def progress_pct(self) -> float:
        info = self.snapshot()
        if info.duration_ms <= 0:
            return 0.0
        return min(100, (info.position_ms / info.duration_ms) * 100)

    def time_formatted(self):
        info = self.snapshot()
        return ms(info.position_ms), ms(info.duration_ms)

    def consume_cover(self):
        with self._lock:
            if not self._cover_updated:
                return None
            self._cover_updated = False
            return self._info.cover

    def fake_frequencies(self, count: int):
        if not self._info.playing:
            return [3 + (i % 3) * 2 for i in range(count)]
        t = time.time() - self._last_refresh
        freqs = []
        for i in range(count):
            ratio = i / count
            lows = abs(math.sin(t * 3.2 + ratio * 0.5)) * 22 * (1 - ratio * 0.6)
            mids = abs(math.cos(t * 5.1 + i * 0.6)) * 14 * (1 - abs(ratio - 0.5) * 0.5)
            highs = abs(math.sin(t * 7.8 + i * 0.9 - t * 0.3)) * 8 * ratio
            beat = abs(math.sin(t * 1.8)) * 6 * (0.5 + 0.5 * abs(math.sin(t * 0.7)))
            noise = random.randint(0, 3)
            freqs.append(min(35, max(2, int(lows + mids + highs + beat + noise))))
        return freqs


def ms(ms_val: int) -> str:
    s = max(0, int(ms_val / 1000))
    return f"{s // 60}:{s % 60:02d}"
