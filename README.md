# 🎵 Mini Reproductor Spotify Widget

Un elegante widget flotante para Windows que muestra la canción actual de Spotify con controles y visualización en tiempo real.

## ✨ Características

### Visualización
- 🎬 **GIF animado** como avatar personalizable
- 🎨 **Efecto glow** dinámico en el borde
- 📊 **Ecualizador en tiempo real** con 8 barras
- 📈 **Barra de progreso** de la canción
- 🖼️ **Carátula del álbum** descargada automáticamente
- 📜 **Scroll animado** para títulos largos
- ✨ **Animaciones suaves** al cambiar de canción

### Funcionalidad
- ▶️ **Botones de control**: Play/Pause y Siguiente
- ⌨️ **Atajo global**: `Ctrl+Shift+M` para mostrar/ocultar
- 🎯 **Sincronización en tiempo real** con Spotify
- 🖱️ **Arrastrable** por cualquier parte
- 📌 **Siempre visible** encima de otras ventanas

### Estado
- 🟢 LED verde cuando está reproduciendo
- 🔴 LED rojo cuando está pausado

## 📋 Requisitos

- Windows 10/11
- Python 3.8+
- Spotify instalado y ejecutándose
- lofi.gif en la misma carpeta que app.pyw

## 🚀 Instalación

```bash
# Clonar el repositorio
git clone https://github.com/torquitos/mini-reproductor.git
cd mini-reproductor

# Crear entorno virtual (opcional pero recomendado)
python -m venv venv
venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

## 🎮 Uso

```bash
# Ejecutar la aplicación
python app.pyw
```

O ejecutar directamente desde el Explorador:
- Doble clic en `app.pyw`
- El widget aparecerá en la esquina inferior derecha

### Controles

| Acción | Resultado |
|--------|-----------|
| **Clic izquierdo + arrastrar** | Mover widget |
| **Botón ▶/⏸** | Play/Pause |
| **Botón ⏭** | Siguiente canción |
| **Ctrl+Shift+M** | Mostrar/Ocultar |
| **Clic derecho** | Menú contextual |

## 📁 Estructura

```
mini-reproductor/
├── app.pyw              # Aplicación principal (UI)
├── radar_core.py        # Núcleo de Spotify (backend)
├── lofi.gif             # Avatar animado
├── requirements.txt     # Dependencias
├── .gitignore           # Configuración de git
└── README.md            # Este archivo
```

## ⚙️ Configuración

### Avatar personalizado

Reemplaza `lofi.gif` con tu propio GIF animado:

1. Crea un GIF de ~44x44 píxeles (cualquier tamaño funciona)
2. Guárdalo como `lofi.gif` en la carpeta del proyecto
3. Reinicia la aplicación

### Tamaño y posición

Edita en `app.pyw`:

```python
self.ancho = 380    # Ancho del widget
self.alto = 110     # Alto del widget
```

## 🛠️ Troubleshooting

### "No encuentra Spotify"
- Asegúrate de que Spotify esté abierto
- Verifica que tengas una canción reproduciendo
- Reinicia Spotify

### El widget no se mueve/controla
- Puede que `pynput` tenga permisos limitados
- Ejecuta Python como administrador

### La carátula no aparece
- Verifica tu conexión de internet
- La carátula requiere conexión para descargar

### Error con `winsdk`
```bash
# Instala explícitamente:
pip install winsdk
```

## 📦 Dependencias

- **Pillow**: Manejo de imágenes y GIFs
- **winsdk**: Acceso a controles multimedia de Windows
- **pynput**: Atajos de teclado globales

## 🎯 Futuros mejoras

- [ ] Seleccionar tema de colores
- [ ] Reproducción local (MP3, FLAC, etc.)
- [ ] Estadísticas de escucha
- [ ] Integración con Last.fm
- [ ] Soporte para otros reproductores (YouTube Music, etc.)

## 📝 Licencia

MIT - Siéntete libre de usar, modificar y distribuir.

## 🤝 Contribuciones

Las contribuciones son bienvenidas! Abre un issue o pull request.

---

**Hecho con ❤️ por [torquitos](https://github.com/torquitos)**
