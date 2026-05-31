import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
from radar_core import MotorRadar
import os
import time
from pynput import keyboard
import subprocess
import math

class MiniSpotifyWidgetApp:
    def __init__(self):
        self.window = tk.Tk()

        self.ancho = 380
        self.alto = 110
        self.window.geometry(f"{self.ancho}x{self.alto}")
        self.window.configure(bg="#050508")

        # Eliminar bordes de Windows y habilitar transparencia
        self.window.overrideredirect(True)
        self.window.wm_attributes('-transparentcolor', '#050508')
        self.window.attributes('-topmost', True)

        try:
            img_inv = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
            self.ruta_ico = "temp_mini.ico"
            img_inv.save(self.ruta_ico, format="ICO")
            self.window.iconbitmap(self.ruta_ico)
        except:
            self.ruta_ico = None

        # Posición: esquina inferior derecha, encima de la barra de tareas
        sw = self.window.winfo_screenwidth()
        sh = self.window.winfo_screenheight()
        self.window.geometry(f"+{sw - (self.ancho + 30)}+{sh - (self.alto + 60)}")

        self.radar = MotorRadar()

        self.canvas = tk.Canvas(
            self.window, width=self.ancho, height=self.alto,
            bg="#050508", bd=0, highlightthickness=0
        )
        self.canvas.pack()

        # Variables de animación
        self.frames_gif = []
        self.index_frame = 0
        self.cargar_gif_avatar("lofi.gif")
        
        # Scroll animado para títulos largos
        self.offset_scroll = 0
        self.velocidad_scroll = 1
        self.pausar_scroll = False
        self.tiempo_pausa_scroll = 0
        
        # Animación de cambio de canción
        self.animacion_cambio = 0
        self.alpha_titulo = 1.0
        self.ultima_cancion = ""
        
        # Carátula del álbum
        self.caratura_actual = None
        self.caratura_tk = None
        
        # Atajo de teclado global
        self.ventana_visible = True
        self._setup_hotkey()

        # Fondo principal con efecto glow
        self.fondo_id = self.canvas.create_rectangle(
            5, 5, self.ancho - 5, self.alto - 5,
            fill="#0B0813", outline="#FF3366", width=1
        )

        # Avatar GIF animado
        if self.frames_gif:
            self.sprite_id = self.canvas.create_image(45, 50, image=self.frames_gif[0])
        else:
            self.sprite_id = self.canvas.create_rectangle(
                25, 30, 65, 70, fill="#1A1224", outline="#A655FF"
            )

        # Círculo de neón alrededor del avatar
        self.canvas.create_oval(22, 27, 68, 73, fill="", outline="#9A4BFF", width=1)

        # Textos de canción y artista
        self.text_titulo_id = self.canvas.create_text(
            85, 33, text="Abriendo Spotify...",
            fill="#FFFFFF", font=("Segoe UI", 9, "bold"), anchor="w", width=200
        )
        self.text_artista_id = self.canvas.create_text(
            85, 52, text="Nexus Media Core",
            fill="#A655FF", font=("Segoe UI", 8), anchor="w", width=200
        )

        # LED de estado (verde = reproduciendo, rojo = pausado)
        self.led_estado = self.canvas.create_oval(
            350, 18, 358, 26, fill="#2F2546", outline=""
        )

        # Barra de progreso de la canción
        self.barra_progreso_bg = self.canvas.create_rectangle(
            85, 68, 360, 72, fill="#1A1224", outline="#555555", width=1
        )
        self.barra_progreso = self.canvas.create_rectangle(
            85, 68, 85, 72, fill="#FF3366", outline=""
        )

        # Botones de control (▶ ⏸ ⏭)
        self.crear_botones_control()

        # Arrastrar ventana con clic izquierdo
        self.canvas.bind("<Button-1>", self.iniciar_arrastre)
        self.canvas.bind("<B1-Motion>", self.arrastrar)
        # Menú contextual con clic derecho
        self.canvas.bind("<Button-3>", self.desplegar_menu)

        self.menu = tk.Menu(
            self.window, tearoff=0, bg="#0B0813", fg="white",
            activebackground="#FF3366", bd=0
        )
        self.menu.add_command(label="❌ Cerrar Mini Widget", command=self.cerrar_todo)
        self.menu.add_command(label="👁️ Mostrar/Ocultar", command=self.toggle_ventana)

        self.tick_contador = 0
        self.tiempo_ultimo_update = time.time()
        self.actualizar_widget_loop()
        self.window.mainloop()

    def _setup_hotkey(self):
        """Configura el atajo de teclado Ctrl+Shift+M para mostrar/ocultar"""
        try:
            listener = keyboard.GlobalHotKeys({
                '<ctrl>+<shift>+m': self.toggle_ventana
            })
            listener.start()
        except Exception as e:
            print(f"[Hotkey] No se pudo configurar: {e}")

    def toggle_ventana(self):
        """Muestra/oculta la ventana"""
        if self.ventana_visible:
            self.window.withdraw()
            self.ventana_visible = False
        else:
            self.window.deiconify()
            self.ventana_visible = True

    def crear_botones_control(self):
        """Crea los botones de control (play, pause, next)"""
        # Botón play/pause
        self.btn_play_pause = self.canvas.create_text(
            330, 88, text="▶", fill="#FF3366", font=("Segoe UI", 14), 
            anchor="center"
        )
        self.canvas.tag_bind(self.btn_play_pause, "<Button-1>", self.toggle_play_pause)

        # Botón siguiente
        self.btn_siguiente = self.canvas.create_text(
            350, 88, text="⏭", fill="#FF3366", font=("Segoe UI", 14), 
            anchor="center"
        )
        self.canvas.tag_bind(self.btn_siguiente, "<Button-1>", lambda e: self.control_spotify("siguiente"))

    def toggle_play_pause(self, event):
        """Alterna entre play y pause"""
        self.control_spotify("toggle")

    def control_spotify(self, accion):
        """Envía comandos a Spotify mediante teclas multimedia"""
        try:
            if accion == "toggle":
                # Simular tecla de espacio (play/pause en Spotify)
                os.system('PowerShell -Command "Add-Type –AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait(\' \')"')
            elif accion == "siguiente":
                # Tecla siguiente (Ctrl+Right)
                os.system('PowerShell -Command "Add-Type –AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait(\'^{RIGHT}\')"')
            elif accion == "anterior":
                # Tecla anterior (Ctrl+Left)
                os.system('PowerShell -Command "Add-Type –AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait(\'^{LEFT}\')"')
        except Exception as e:
            print(f"Error en control: {e}")

    def cargar_gif_avatar(self, ruta_gif):
        """Carga los frames del GIF animado"""
        if not os.path.exists(ruta_gif):
            return
        try:
            gif = Image.open(ruta_gif)
            while True:
                frame = gif.copy().convert("RGBA").resize((44, 44), Image.Resampling.NEAREST)
                self.frames_gif.append(ImageTk.PhotoImage(frame))
                gif.seek(len(self.frames_gif))
        except EOFError:
            pass
        except Exception as e:
            print(f"[GIF] {e}")

    def dibujar_glow(self):
        """Dibuja un efecto glow animado en el borde"""
        t = time.time() * 2
        intensidad = int(128 + 127 * abs(math.sin(t)))
        color_glow = f"#{intensidad:02x}{100:02x}{intensidad:02x}"
        
        self.canvas.itemconfig(self.fondo_id, outline=color_glow)

    def actualizar_caratura(self):
        """Descarga y actualiza la carátula del álbum"""
        try:
            img = self.radar.obtener_caratura_album((64, 64))
            if img:
                self.caratura_actual = img
                self.caratura_tk = ImageTk.PhotoImage(img)
                self.canvas.create_image(285, 50, image=self.caratura_tk, tags="caratura")
        except Exception as e:
            print(f"[Caratura] {e}")

    def actualizar_barra_progreso(self):
        """Actualiza la barra de progreso de la canción"""
        try:
            progreso = self.radar.obtener_porcentaje_progreso()
            ancho_barra = int((progreso / 100) * (360 - 85))
            self.canvas.coords(
                self.barra_progreso,
                85, 68, 85 + ancho_barra, 72
            )
        except Exception:
            pass

    def animar_cambio_cancion(self):
        """Anima la aparición del nuevo título"""
        if self.radar.obtener_cancion_cambio():
            self.animacion_cambio = 10
            self.alpha_titulo = 0.3

        if self.animacion_cambio > 0:
            self.alpha_titulo = min(1.0, self.alpha_titulo + 0.1)
            self.animacion_cambio -= 1

    def scroll_titulo(self, titulo):
        """Aplica scroll animado si el título es muy largo"""
        if len(titulo) <= 26:
            self.offset_scroll = 0
            return titulo
        
        titulo_largo = titulo + "  •  "
        if self.pausar_scroll:
            if time.time() - self.tiempo_pausa_scroll > 2:
                self.pausar_scroll = False
                self.offset_scroll = 0
            else:
                return titulo[:24] + "..."
        
        self.offset_scroll = (self.offset_scroll + self.velocidad_scroll) % len(titulo_largo)
        return titulo_largo[self.offset_scroll:self.offset_scroll + 24]

    def actualizar_widget_loop(self):
        """Loop principal de actualización del widget"""
        # 1. Animar GIF avatar
        if self.frames_gif:
            self.index_frame = (self.index_frame + 1) % len(self.frames_gif)
            self.canvas.itemconfig(self.sprite_id, image=self.frames_gif[self.index_frame])

        # 2. Efecto glow en el borde
        self.dibujar_glow()

        # 3. Sincronizar con Spotify cada ~12 ticks (≈ 420 ms)
        self.tick_contador += 1
        if self.tick_contador >= 12:
            self.tick_contador = 0
            titulo, artista = self.radar.actualizar_metadatos_spotify()
            
            # Aplicar scroll animado
            titulo_mostrado = self.scroll_titulo(titulo)
            
            self.canvas.itemconfig(self.text_titulo_id, text=titulo_mostrado)
            self.canvas.itemconfig(self.text_artista_id, text=artista)
            
            # Actualizar carátula del álbum
            self.canvas.delete("caratura")
            self.actualizar_caratura()

        # 4. Animar cambio de canción
        self.animar_cambio_cancion()

        # 5. Actualizar barra de progreso
        self.actualizar_barra_progreso()

        # 6. LED + ecualizador
        self.canvas.delete("onda_mini")
        if self.radar.reproduciendo:
            self.canvas.itemconfig(self.btn_play_pause, text="⏸")
            self.canvas.itemconfig(self.led_estado, fill="#00FF66")

            # Ecualizador: 8 barras dentro del área segura (x: 282–338)
            num_barras = 8
            alturas = self.radar.obtener_frecuencias_simuladas(num_barras)
            for i, h in enumerate(alturas):
                h = max(2, int(h // 1.8))
                x = 283 + (i * 7)
                cy = 25  # Centro vertical de las barras
                self.canvas.create_line(
                    x, cy - h, x, cy + h,
                    fill="#FF3366", width=2, tags="onda_mini"
                )
        else:
            self.canvas.itemconfig(self.btn_play_pause, text="▶")
            self.canvas.itemconfig(self.led_estado, fill="#FF3366")

        self.window.after(35, self.actualizar_widget_loop)

    def iniciar_arrastre(self, event):
        """Inicia el arrastre de la ventana"""
        self.x_mouse = event.x
        self.y_mouse = event.y

    def arrastrar(self, event):
        """Arrastra la ventana"""
        x = self.window.winfo_x() + (event.x - self.x_mouse)
        y = self.window.winfo_y() + (event.y - self.y_mouse)
        self.window.geometry(f"+{x}+{y}")

    def desplegar_menu(self, event):
        """Despliega el menú contextual"""
        self.menu.post(event.x_root, event.y_root)

    def cerrar_todo(self):
        """Cierra la aplicación y limpia archivos temporales"""
        if self.ruta_ico and os.path.exists(self.ruta_ico):
            try:
                os.remove(self.ruta_ico)
            except:
                pass
        self.window.quit()

if __name__ == "__main__":
    MiniSpotifyWidgetApp()
