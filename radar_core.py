import random
import time
import math
import asyncio
import threading
import urllib.request
import os
from io import BytesIO
from PIL import Image

class MotorRadar:
    def __init__(self):
        self.reproduciendo = False
        self.tiempo_inicio = time.time()
        self.cancion_actual = "Abriendo Spotify..."
        self.artista_actual = "NEXUS MEDIA"
        self.duracion_ms = 0
        self.posicion_ms = 0
        self.url_album = None
        self.ultima_cancion = None
        self._lock = threading.Lock()
        # Un solo event loop reutilizable en un hilo separado
        self._loop = asyncio.new_event_loop()
        self._hilo = threading.Thread(target=self._arrancar_loop, daemon=True)
        self._hilo.start()

    def _arrancar_loop(self):
        """Corre el event loop de asyncio en un hilo dedicado"""
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def actualizar_metadatos_spotify(self):
        """Conecta con los controles globales de Windows para leer Spotify"""
        try:
            future = asyncio.run_coroutine_threadsafe(self._obtener_info(), self._loop)
            future.result(timeout=2)  # Esperar máximo 2 segundos
        except Exception:
            pass
        return self.cancion_actual, self.artista_actual

    async def _obtener_info(self):
        """Obtiene información completa de la canción actual incluyendo carátula"""
        try:
            from winsdk.windows.media.control import (
                GlobalSystemMediaTransportControlsSessionManager as SessionManager
            )
            manager = await SessionManager.request_async()
            sesion = manager.get_current_session()
            if sesion:
                propiedades = await sesion.try_get_media_properties_async()
                playback_status = sesion.get_playback_info().playback_status
                timeline = sesion.get_timeline_properties()
                
                with self._lock:
                    self.cancion_actual = propiedades.title or "Sin título"
                    self.artista_actual = propiedades.artist or "Artista desconocido"
                    self.reproduciendo = (playback_status == 4)  # 4 = Playing
                    self.duracion_ms = timeline.end_time.total_milliseconds() if timeline.end_time else 0
                    self.posicion_ms = timeline.position.total_milliseconds() if timeline.position else 0
                    
                    # Obtener carátula del álbum
                    try:
                        thumbnail = await propiedades.thumbnail_async()
                        if thumbnail:
                            self.url_album = thumbnail.absolute_uri
                    except Exception:
                        self.url_album = None
            else:
                with self._lock:
                    self.cancion_actual = "Esperando Spotify..."
                    self.artista_actual = "Dale Play en la App"
                    self.reproduciendo = False
                    self.url_album = None
        except Exception:
            with self._lock:
                self.cancion_actual = "Esperando Spotify..."
                self.artista_actual = "Dale Play en la App"
                self.reproduciendo = False
                self.url_album = None

    def obtener_frecuencias_simuladas(self, num_barras):
        """Genera ecualizador simulado basado en tiempo y estado de reproducción"""
        if not self.reproduciendo:
            return [2 for _ in range(num_barras)]
        
        frecuencias = []
        t = time.time() - self.tiempo_inicio
        for i in range(num_barras):
            bajos = math.sin(t * 4.8) * 18 if i < 4 else 0
            melodia = math.cos(t * 2.5 + i * 0.4) * 12
            ruido = random.randint(0, 4)
            altura = max(3, int(abs(bajos) + abs(melodia) + ruido))
            if i > num_barras * 0.75:
                altura = int(altura * 0.3)
            frecuencias.append(min(30, altura))
        return frecuencias

    def obtener_caratura_album(self, tamanio=(64, 64)):
        """Descarga y retorna la carátula del álbum como imagen PIL"""
        if not self.url_album:
            return None
        
        try:
            with urllib.request.urlopen(self.url_album, timeout=3) as response:
                img_data = response.read()
                img = Image.open(BytesIO(img_data)).convert("RGBA")
                img.thumbnail(tamanio, Image.Resampling.LANCZOS)
                return img
        except Exception as e:
            print(f"[Album] Error descargando carátula: {e}")
            return None

    def obtener_porcentaje_progreso(self):
        """Retorna el porcentaje de progreso de la canción (0-100)"""
        if self.duracion_ms <= 0:
            return 0
        return min(100, int((self.posicion_ms / self.duracion_ms) * 100))

    def obtener_cancion_cambio(self):
        """Detecta si cambió de canción"""
        cambio = self.cancion_actual != self.ultima_cancion
        self.ultima_cancion = self.cancion_actual
        return cambio
