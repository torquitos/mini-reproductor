import asyncio
import logging
import math
import random
import threading
import time
from dataclasses import dataclass
from io import BytesIO

from PIL import Image

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
    title: str = "Abriendo Spotify..."
    artist: str = "Nexus Mini Player"
    playing: bool = False
    duration_ms: int = 0
    position_ms: int = 0
    cover: Image.Image | None = None
    error: str = ""


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

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def close(self):
        if self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)

    async def _get_session(self):
        if SessionManager is None:
            return None
        try:
            manager = await SessionManager.request_async()
            for session in manager.get_sessions():
                app_id = (session.source_app_user_model_id or "").lower()
                if "spotify" in app_id:
                    return session
            return manager.get_current_session()
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

    async def refresh(self):
        if SessionManager is None:
            return
        session = await self._get_session()
        if not session:
            with self._lock:
                self._info = TrackInfo(
                    title="Esperando Spotify...",
                    artist="Dale play en Spotify",
                    error="No hay sesión activa",
                )
            return
        try:
            props = await session.try_get_media_properties_async()
            playback = session.get_playback_info()
            timeline = session.get_timeline_properties()

            title = props.title or "Sin título"
            artist = props.artist or "Artista desconocido"
            playing = self._is_playing(playback.playback_status)
            duration = self._ms(timeline.end_time)
            position = self._ms(timeline.position)

            new_cover = None
            if title != self._last_title:
                new_cover = await self._read_cover(props.thumbnail)

            with self._lock:
                self._info = TrackInfo(
                    title=title,
                    artist=artist,
                    playing=playing,
                    duration_ms=duration,
                    position_ms=position,
                    cover=new_cover if new_cover is not None else self._info.cover,
                )
                self._cover_updated = new_cover is not None
                self._last_title = title
                self._last_refresh = time.time()
        except Exception as exc:
            LOGGER.debug("Refresh failed: %s", exc)

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
