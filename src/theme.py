from PySide6.QtGui import QColor

# Layout horizontal compacto: carátula a la izquierda, info + controles a la derecha.
W = 420
H = 166
M = 18

WIN_W = W + M * 2
WIN_H = H + M * 2

COVER = H  # la carátula es cuadrada y ocupa todo el alto disponible
RADIUS = 20
COVER_RADIUS = 16

# Base neutra; el acento real se calcula por canción a partir de la carátula (ver spotify.extract_accent_color).
BG_BASE = QColor("#131419")
BG_BASE_DARK = QColor("#0E0F13")
DEFAULT_ACCENT = (201, 91, 69)
TEXT = "#FFFFFF"
TEXT_DIM = "rgba(255,255,255,0.55)"
TEXT_MUTED = "rgba(255,255,255,0.32)"
PROGRESS_BG = "rgba(255,255,255,0.12)"
BTN_SECONDARY = "rgba(255,255,255,0.75)"
BTN_HOVER_BG = "rgba(255,255,255,0.10)"
MENU_BG = "#17181D"
MENU_BORDER = "#262830"
MENU_HOVER = "#262830"
