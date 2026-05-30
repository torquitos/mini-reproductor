import tkinter as tk
from PIL import Image, ImageTk
from radar_core import MotorRadar
import os

class MiniSpotifyWidgetApp:
    def __init__(self):
        self.window = tk.Tk()

        self.ancho = 360
        self.alto = 90
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

        # Fondo principal
        self.canvas.create_rectangle(
            5, 5, self.ancho - 5, self.alto - 5,
            fill="#0B0813", outline="#FF3366", width=1
        )

        # Avatar GIF animado
        self.frames_gif = []
        self.index_frame = 0
        self.cargar_gif_avatar("lofi.gif")

        if self.frames_gif:
            self.sprite_id = self.canvas.create_image(45, 45, image=self.frames_gif[0])
        else:
            self.sprite_id = self.canvas.create_rectangle(
                25, 25, 65, 65, fill="#1A1224", outline="#A655FF"
            )

        # Círculo de neón alrededor del avatar
        self.canvas.create_oval(22, 22, 68, 68, fill="", outline="#9A4BFF", width=1)

        # Textos de canción y artista
        self.text_titulo_id = self.canvas.create_text(
            85, 33, text="Abriendo Spotify...",
            fill="#FFFFFF", font=("Segoe UI", 10, "bold"), anchor="w", width=190
        )
        self.text_artista_id = self.canvas.create_text(
            85, 52, text="Nexus Media Core",
            fill="#A655FF", font=("Segoe UI", 8, "bold"), anchor="w", width=190
        )

        # LED de estado (verde = reproduciendo, rojo = pausado)
        self.led_estado = self.canvas.create_oval(
            332, 18, 340, 26, fill="#2F2546", outline=""
        )

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

        self.tick_contador = 0
        self.actualizar_widget_loop()
        self.window.mainloop()

    def cargar_gif_avatar(self, ruta_gif):
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

    def actualizar_widget_loop(self):
        # 1. Animar GIF avatar
        if self.frames_gif:
            self.index_frame = (self.index_frame + 1) % len(self.frames_gif)
            self.canvas.itemconfig(self.sprite_id, image=self.frames_gif[self.index_frame])

        # 2. Sincronizar con Spotify cada ~12 ticks (≈ 420 ms)
        self.tick_contador += 1
        if self.tick_contador >= 12:
            self.tick_contador = 0
            titulo, artista = self.radar.actualizar_metadatos_spotify()
            if len(titulo) > 26:
                titulo = titulo[:24] + "..."
            self.canvas.itemconfig(self.text_titulo_id, text=titulo)
            self.canvas.itemconfig(self.text_artista_id, text=artista)

        # 3. LED + ecualizador
        self.canvas.delete("onda_mini")
        if self.radar.reproduciendo:
            self.canvas.itemconfig(self.led_estado, fill="#00FF66")

            # Ecualizador: 8 barras dentro del área segura (x: 282–338)
            num_barras = 8
            alturas = self.radar.obtener_frecuencias_simuladas(num_barras)
            for i, h in enumerate(alturas):
                h = max(2, int(h // 1.8))
                x = 283 + (i * 7)
                cy = 55  # Centro vertical de las barras
                self.canvas.create_line(
                    x, cy - h, x, cy + h,
                    fill="#FF3366", width=2, tags="onda_mini"
                )
        else:
            self.canvas.itemconfig(self.led_estado, fill="#FF3366")

        self.window.after(35, self.actualizar_widget_loop)

    def iniciar_arrastre(self, event):
        self.x_mouse = event.x
        self.y_mouse = event.y

    def arrastrar(self, event):
        x = self.window.winfo_x() + (event.x - self.x_mouse)
        y = self.window.winfo_y() + (event.y - self.y_mouse)
        self.window.geometry(f"+{x}+{y}")

    def desplegar_menu(self, event):
        self.menu.post(event.x_root, event.y_root)

    def cerrar_todo(self):
        if self.ruta_ico and os.path.exists(self.ruta_ico):
            try:
                os.remove(self.ruta_ico)
            except:
                pass
        self.window.quit()

if __name__ == "__main__":
    MiniSpotifyWidgetApp()