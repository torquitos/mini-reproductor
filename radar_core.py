import random
import time
import math
import asyncio
import threading

class MotorRadar:
    def __init__(self):
        self.reproduciendo = False
        self.tiempo_inicio = time.time()
        self.cancion_actual = "Abriendo Spotify..."
        self.artista_actual = "NEXUS MEDIA"
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
        try:
            from winsdk.windows.media.control import (
                GlobalSystemMediaTransportControlsSessionManager as SessionManager
            )
            manager = await SessionManager.request_async()
            sesion = manager.get_current_session()
            if sesion:
                propiedades = await sesion.try_get_media_properties_async()
                with self._lock:
                    self.cancion_actual = propiedades.title or "Sin título"
                    self.artista_actual = propiedades.artist or "Artista desconocido"
                    playback_status = sesion.get_playback_info().playback_status
                    self.reproduciendo = (playback_status == 4)  # 4 = Playing
            else:
                with self._lock:
                    self.cancion_actual = "Esperando Spotify..."
                    self.artista_actual = "Dale Play en la App"
                    self.reproduciendo = False
        except Exception:
            with self._lock:
                self.cancion_actual = "Esperando Spotify..."
                self.artista_actual = "Dale Play en la App"
                self.reproduciendo = False

    def obtener_frecuencias_simuladas(self, num_barras):
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
