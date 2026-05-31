# 🎵 Nexus Mini Player

> Widget flotante para Windows que muestra en tiempo real la canción que escuchas en Spotify — con carátula, ecualizador y controles de reproducción.


## ✨ Características

| Visual | Funcionalidad |
|--------|--------------|
| 🖼️ Carátula del álbum en tiempo real | ▶️ Botones Play / Pause / Siguiente |
| 📊 Ecualizador animado con 8 barras | ⌨️ Atajo `Ctrl+Shift+M` para mostrar/ocultar |
| ✨ Efecto glow dinámico en el borde | 🖱️ Widget arrastrable por la pantalla |
| 📜 Scroll automático en títulos largos | 📌 Siempre visible encima de otras ventanas |
| 📈 Barra de progreso de la canción | 🔴🟢 LED de estado de reproducción |
| 🎬 Avatar GIF animado personalizable | 🔄 Animación de fade al cambiar canción |

---

## 🚀 Instalación

```bash
# 1. Clona el repositorio
git clone https://github.com/torquitos/nexus-mini-player.git
cd nexus-mini-player

# 2. (Opcional) Crea un entorno virtual
python -m venv venv
venv\Scripts\activate

# 3. Instala las dependencias
pip install -r requirements.txt

# 4. Ejecuta el widget
python app.pyw
```

> También puedes hacer **doble clic** en `app.pyw` desde el Explorador de archivos — la consola no aparece.

---

## 🎮 Controles

| Acción | Resultado |
|--------|-----------|
| `Clic izquierdo + arrastrar` | Mover el widget |
| `Botón ▶ / ⏸` | Play / Pause |
| `Botón ⏭` | Siguiente canción |
| `Ctrl + Shift + M` | Mostrar / Ocultar |
| `Clic derecho` | Menú contextual (cerrar) |

---

## 📁 Estructura del proyecto

```
nexus-mini-player/
├── app.pyw           # Interfaz principal (Tkinter)
├── radar_core.py     # Backend: lectura de Spotify + ecualizador
├── lofi.gif          # Avatar animado (personalizable)
├── requirements.txt  # Dependencias
├── .gitignore
└── README.md
```

---

## ⚙️ Personalización

**Cambiar el avatar GIF**
Reemplaza `lofi.gif` con cualquier GIF — el widget lo recorta en círculo automáticamente.

**Cambiar tamaño del widget** — edita en `app.pyw`:
```python
ANCHO = 380   # píxeles de ancho
ALTO  = 100   # píxeles de alto
```

---

## 🛠️ Troubleshooting

**Spotify no es detectado**
- Asegúrate de que Spotify esté abierto y reproduciendo
- Reinicia Spotify y vuelve a ejecutar el widget

**Error con `winsdk`**
```bash
pip install winsdk
```

**La carátula no aparece**
- Requiere que Spotify tenga acceso a internet
- Si persiste, el widget muestra el GIF como respaldo automáticamente

---

## 📦 Dependencias

| Librería | Uso |
|----------|-----|
| `Pillow` | Manejo de imágenes, GIFs y carátulas |
| `winsdk` | Acceso a los controles multimedia de Windows |

---

## 🗺️ Roadmap

- [ ] Selector de tema de colores
- [ ] Soporte para YouTube Music y otros reproductores
- [ ] Estadísticas de escucha
- [ ] Integración con Last.fm

---

## 📝 Licencia

MIT — úsalo, modifícalo y distribúyelo libremente.

---

<div align="center">
  Hecho con ❤️ por <a href="https://github.com/torquitos">torquitos</a>
</div>
