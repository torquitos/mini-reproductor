# Nexus Mini Player

Widget flotante para Windows que muestra lo que está sonando en Spotify: carátula, título, artista, barra de progreso animada y controles básicos.

## Captura

```
  ┌─────────────────────────────┐
  │  ●  ┌──────────────────┐    │
  │     │  ♪  (carátula)   │    │
  │     └──────────────────┘    │
  │  Canción Actual             │
  │  Artista                    │
  │  0:00 ───●───────── 3:30   │
  │    ◂    ▶    ▸              │
  │   ▄▄▆▇█▇▆▄▄▆▇████▇▆▄▄▆▇   │
  └─────────────────────────────┘
```

## Características

| Visual | Funcionalidad |
|--------|---------------|
| Carátula del álbum en tiempo real | Doble clic en carátula → play/pause |
| Anillo ecualizador animado alrededor de la carátula | Play / pause / anterior / siguiente |
| Barra de progreso con animación suave | Seek clickeable en la barra |
| Ecualizador decorativo en la parte inferior | Atajo `Ctrl + Shift + M` para mostrar/ocultar (global) |
| Tooltip con título y artista completo | Menú contextual con clic derecho |
| Punto de estado (verde/gris/rojo) | Modo siempre encima configurable |
| Widget compacto, arrastrable | Recuerda la última posición |

## Instalación

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.pyw
```

También puedes abrir `app.pyw` con doble clic después de instalar las dependencias.

## Controles

| Acción | Resultado |
|--------|-----------|
| Clic izquierdo + arrastrar | Mover el widget |
| Doble clic en carátula | Reproducir o pausar |
| `Play` / `Pause` | Reproducir o pausar |
| `<<` / `>>` | Canción anterior o siguiente |
| Clic en barra de progreso | Adelantar o retroceder |
| `Ctrl + Shift + M` | Mostrar u ocultar (funciona aunque el widget no tenga foco) |
| Clic derecho | Abrir menú contextual |

## Estructura del proyecto

```
nexus-mini-player/
├── src/
│   ├── main.py       Punto de entrada + hotkey global
│   ├── window.py     Ventana flotante principal
│   ├── widgets.py    Carátula, ring, barra de progreso, ecualizador, botones
│   ├── spotify.py    Lectura y control de Spotify vía winsdk
│   ├── theme.py      Colores, dimensiones, constantes visuales
│   └── config.py     Carga/guarda posición y configuración
├── app.pyw           Acceso directo (doble clic)
├── requirements.txt  Dependencias
└── config.json       Se crea automáticamente
```

## Troubleshooting

**Spotify no aparece**

- Abre Spotify y reproduce una canción.
- Si sigue igual, reinicia Spotify y vuelve a abrir el widget.
- Revisa `nexus.log` para ver el último error.

**Error con dependencias**

```bash
pip install -r requirements.txt
```

**La carátula no aparece**

- Algunas sesiones multimedia de Windows tardan en entregar la carátula.
- Cambia de canción o reinicia Spotify.
