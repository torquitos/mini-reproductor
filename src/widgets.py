import math

from PIL import Image, ImageDraw
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import (
    QPainter, QColor, QPen, QPixmap, QImage, QPainterPath, QCursor, QLinearGradient,
)
from PySide6.QtWidgets import QLabel, QWidget, QPushButton

from .theme import COVER, COVER_RADIUS, DEFAULT_ACCENT


def pil2px(pil):
    if pil.mode != "RGBA":
        pil = pil.convert("RGBA")
    data = pil.tobytes("raw", "BGRA")
    return QPixmap.fromImage(QImage(data, pil.width, pil.height, QImage.Format.Format_ARGB32))


def _rounded_mask(size, radius):
    m = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(m)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    return m


class AlbumArt(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(COVER, COVER)
        self._pix = None

    def set_album(self, pil_img):
        if not pil_img:
            self._pix = None
            self.update()
            return
        img = pil_img.resize((COVER, COVER), Image.Resampling.LANCZOS)
        out = Image.new("RGBA", (COVER, COVER), (0, 0, 0, 0))
        out.paste(img, mask=_rounded_mask(COVER, COVER_RADIUS))
        self._pix = pil2px(out)
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), COVER_RADIUS, COVER_RADIUS)
        p.setClipPath(path)

        if self._pix:
            p.drawPixmap(self.rect(), self._pix)

            fade = QLinearGradient(0, 0, self.width(), 0)
            fade.setColorAt(0.0, QColor(10, 9, 12, 0))
            fade.setColorAt(0.6, QColor(10, 9, 12, 0))
            fade.setColorAt(1.0, QColor(10, 9, 12, 215))
            p.fillRect(self.rect(), fade)

            # Muchas portadas oficiales de Spotify traen su logo estampado en la
            # franja inferior de la imagen (no algo que el widget agregue). Oscurece
            # esa franja casi del todo para que deje de notarse sin recortar la carátula.
            bottom_fade = QLinearGradient(0, self.height() * 0.72, 0, self.height())
            bottom_fade.setColorAt(0.0, QColor(8, 7, 10, 0))
            bottom_fade.setColorAt(0.5, QColor(8, 7, 10, 190))
            bottom_fade.setColorAt(1.0, QColor(8, 7, 10, 245))
            p.fillRect(self.rect(), bottom_fade)
            return

        p.fillRect(self.rect(), QColor("#1C1E25"))
        cx, cy = self.width() / 2, self.height() / 2 - 10

        pen = QPen(QColor(255, 255, 255, 70), 2.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        note_r = 9
        p.drawEllipse(QPointF(cx - 6, cy + 14), note_r * 0.55, note_r * 0.4)
        p.drawLine(QPointF(cx - 1, cy + 12), QPointF(cx - 1, cy - 14))
        p.drawLine(QPointF(cx - 1, cy - 14), QPointF(cx + 10, cy - 9))

        p.setPen(QColor(255, 255, 255, 90))
        font = p.font()
        font.setPointSize(9)
        p.setFont(font)
        p.drawText(
            QRectF(0, cy + 28, self.width(), 20),
            Qt.AlignmentFlag.AlignCenter,
            "Sin reproducción",
        )


class ProgressBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(14)
        self._display = 0.0
        self._target = 0.0
        self._callback = None
        self._accent = QColor(*DEFAULT_ACCENT)

    def set(self, pct):
        self._target = pct
        self.update()

    def set_accent(self, rgb):
        self._accent = QColor(*rgb)

    def on_seek(self, cb):
        self._callback = cb

    def _x2pct(self, x):
        w = self.width()
        return max(0.0, min(1.0, (x - 2) / (w - 4))) if w > 4 else 0.0

    def mousePressEvent(self, e):
        if self._callback:
            self._callback(self._x2pct(e.position().x()))

    def mouseMoveEvent(self, e):
        if e.buttons() & Qt.MouseButton.LeftButton and self._callback:
            self._callback(self._x2pct(e.position().x()))

    def paintEvent(self, e):
        self._display += (self._target - self._display) * 0.25

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        y = h / 2
        x1, x2 = 2.0, w - 2.0

        pen = QPen(QColor("#FFFFFF"), 3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.setOpacity(0.12)
        p.drawLine(QPointF(x1, y), QPointF(x2, y))
        p.setOpacity(1.0)

        px = x1 + (x2 - x1) * self._display
        if px > x1:
            pen = QPen(self._accent, 3)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            p.drawLine(QPointF(x1, y), QPointF(px, y))

        p.setBrush(self._accent)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(px, y), 4.5, 4.5)


class Equalizer(QWidget):
    """Visualizador decorativo de barras (no refleja audio real)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(18)
        self._bars = 20
        self._freqs = [2] * self._bars
        self._playing = False
        self._phase = 0.0
        self._accent = QColor(*DEFAULT_ACCENT)

    def set_data(self, freqs, playing):
        self._freqs = freqs
        self._playing = playing

    def set_accent(self, rgb):
        self._accent = QColor(*rgb)

    def tick(self):
        self._phase += 0.06
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        n = self._bars
        bw = max(2, int(w / n) - 2)
        base = float(self.height())

        for i in range(n):
            v = self._freqs[i] if len(self._freqs) > i else 2
            if self._playing:
                bh = min(14, int(v * 0.4 + abs(math.sin(self._phase + i * 0.5)) * 4))
            else:
                bh = 1 + (i % 3)
            x = i * (bw + 2) + bw / 2

            pen = QPen(self._accent, max(1, bw - 1))
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            p.setOpacity(0.25 if not self._playing else 0.75)
            p.drawLine(QPointF(x, base), QPointF(x, base - bh))


class CloseButton(QPushButton):
    """Botón de cerrar, discreto, visible solo al pasar el mouse sobre el widget."""

    def __init__(self, size: int = 20, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFlat(True)
        self.setStyleSheet("QPushButton{background:transparent;border:none;}")

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        hovered = self.underMouse()

        if hovered:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(255, 80, 80, 200))
            p.drawEllipse(QRectF(0, 0, w, h))
            fg = QColor("#FFFFFF")
        else:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(255, 255, 255, 30))
            p.drawEllipse(QRectF(0, 0, w, h))
            fg = QColor(255, 255, 255, 200)

        pen = QPen(fg, 1.6)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        m = w * 0.3
        p.drawLine(QPointF(m, m), QPointF(w - m, h - m))
        p.drawLine(QPointF(w - m, m), QPointF(m, h - m))


class VolumeButton(QWidget):
    """Icono de volumen: la rueda del mouse encima sube/baja el volumen de la app activa."""

    def __init__(self, size: int = 20, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._level = 1.0
        self._available = True
        self._hover_visible = False
        self._on_change = None

    def set_level(self, level: float | None):
        self._available = level is not None
        if level is not None:
            self._level = level
        self.setVisible(self._available and self._hover_visible)
        self.update()

    def set_hover_visible(self, visible: bool):
        """Controlado por la ventana: solo se muestra al pasar el mouse Y si hay
        audio local que controlar (reproducción remota como Spotify Connect no
        tiene volumen que ajustar desde esta PC)."""
        self._hover_visible = visible
        self.setVisible(self._available and visible)

    def on_change(self, cb):
        self._on_change = cb

    def wheelEvent(self, e):
        if not self._available or not self._on_change:
            return
        delta = 0.05 if e.angleDelta().y() > 0 else -0.05
        self._level = max(0.0, min(1.0, self._level + delta))
        self._on_change(self._level)
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        fg = QColor(255, 255, 255, 200 if self._available else 60)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(fg)

        cx, cy = w * 0.32, h / 2
        body_w, body_h = w * 0.22, h * 0.34
        path = QPainterPath()
        path.addRect(QRectF(cx - body_w, cy - body_h / 2, body_w, body_h))
        tip_w = w * 0.22
        path.moveTo(cx, cy - body_h / 2)
        path.lineTo(cx + tip_w, cy - h * 0.32)
        path.lineTo(cx + tip_w, cy + h * 0.32)
        path.lineTo(cx, cy + body_h / 2)
        path.closeSubpath()
        p.drawPath(path)

        if self._level > 0.02:
            pen = QPen(fg, 1.4)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            arc_rect = QRectF(cx + tip_w - 2, cy - h * 0.38, h * 0.5, h * 0.76)
            p.drawArc(arc_rect, -50 * 16, 100 * 16)
            if self._level > 0.55:
                arc_rect2 = QRectF(cx + tip_w + 2, cy - h * 0.46, h * 0.64, h * 0.92)
                p.drawArc(arc_rect2, -45 * 16, 90 * 16)


class ControlButton(QPushButton):
    """Botón circular con icono vectorial dibujado a mano (no depende de fuentes del sistema)."""

    def __init__(self, icon: str, size: int, play: bool = False):
        super().__init__()
        self._icon = icon
        self._play = play
        self._accent = QColor(*DEFAULT_ACCENT)
        self.setFixedSize(size, size)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFlat(True)
        self.setStyleSheet("QPushButton{background:transparent;border:none;}")

    def set_accent(self, rgb):
        self._accent = QColor(*rgb)
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        hovered = self.underMouse()

        if self._play:
            bg = QColor(self._accent)
            fg = QColor("#0A0B0E")
            if hovered:
                bg = bg.lighter(112)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(bg)
            p.drawEllipse(QRectF(0, 0, w, h))
        else:
            fg = QColor(255, 255, 255, 235 if hovered else 180)
            if hovered:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QColor(255, 255, 255, 18))
                p.drawEllipse(QRectF(0, 0, w, h))

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(fg)

        if self._icon == "play":
            s = w * 0.22
            path = QPainterPath()
            path.moveTo(cx - s * 0.6, cy - s)
            path.lineTo(cx - s * 0.6, cy + s)
            path.lineTo(cx + s * 0.9, cy)
            path.closeSubpath()
            p.drawPath(path)
        elif self._icon == "pause":
            bw = w * 0.09
            gap = w * 0.08
            bh = h * 0.34
            p.drawRoundedRect(QRectF(cx - gap - bw, cy - bh / 2, bw, bh), 1.5, 1.5)
            p.drawRoundedRect(QRectF(cx + gap, cy - bh / 2, bw, bh), 1.5, 1.5)
        elif self._icon in ("next", "prev"):
            s = w * 0.16
            flip = -1 if self._icon == "prev" else 1
            path = QPainterPath()
            path.moveTo(cx - s * 0.7 * flip, cy - s)
            path.lineTo(cx - s * 0.7 * flip, cy + s)
            path.lineTo(cx + s * 0.9 * flip, cy)
            path.closeSubpath()
            p.drawPath(path)
            bar_w = w * 0.07
            p.drawRoundedRect(
                QRectF(cx + s * 0.9 * flip - (bar_w if flip > 0 else 0), cy - s, bar_w, s * 2),
                1.0, 1.0,
            )
