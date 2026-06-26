import math

from PIL import Image, ImageDraw
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import (
    QPainter, QColor, QPen, QPixmap, QImage, QPainterPath, QCursor, QFont,
)
from PySide6.QtWidgets import QLabel, QWidget, QPushButton

from .theme import (
    COVER, RING, ACCENT, VIZ_CYAN, VIZ_PINK,
)


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
        out.paste(img, mask=_rounded_mask(COVER, 16))
        self._pix = pil2px(out)
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 16, 16)
        p.setClipPath(path)
        if self._pix:
            p.drawPixmap(self.rect(), self._pix)
        else:
            p.fillRect(self.rect(), QColor("#121418"))
            p.setPen(QColor(255, 255, 255, 60))
            p.setFont(QFont("Segoe UI", 36))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "♪")


class RingVisualizer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(RING, RING)
        self._freqs = [2] * 36
        self._playing = False
        self._bars = 36

    def set_data(self, freqs, playing):
        self._freqs = freqs
        self._playing = playing
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx = cy = RING // 2
        ri = RING // 2 - 18
        n = self._bars

        for i in range(n):
            angle = math.radians(i * (360.0 / n) - 90)
            v = self._freqs[i] if self._playing else 2
            h = max(1, min(12, v * 0.3 + 1))
            ro = ri + h
            ratio = i / n

            if ratio < 0.4:
                color = VIZ_CYAN
            elif ratio < 0.7:
                t = (ratio - 0.4) / 0.3
                r, g, b = 0, int(206 * (1 - t * 0.4)), int(206 * (1 - t * 0.3))
                color = QColor(r, g, b)
            else:
                color = VIZ_PINK

            x1 = cx + ri * math.cos(angle)
            y1 = cy + ri * math.sin(angle)
            x2 = cx + ro * math.cos(angle)
            y2 = cy + ro * math.sin(angle)

            pen = QPen(QColor(color.red(), color.green(), color.blue(), 30), 6)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))

            pen = QPen(color, 2.5)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))


class ProgressBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(14)
        self._display = 0.0
        self._target = 0.0
        self._callback = None

    def set(self, pct):
        self._target = pct
        self.update()

    def on_seek(self, cb):
        self._callback = cb

    def _x2pct(self, x):
        w = self.width()
        return max(0.0, min(1.0, (x - 4) / (w - 8))) if w > 8 else 0.0

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
        x1, x2 = 4.0, w - 4.0

        pen = QPen(QColor("#FFFFFF"), 2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.setOpacity(0.08)
        p.drawLine(QPointF(x1, y), QPointF(x2, y))
        p.setOpacity(1.0)

        px = x1 + (x2 - x1) * self._display
        if px > x1:
            pen = QPen(QColor(ACCENT), 2)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            p.drawLine(QPointF(x1, y), QPointF(px, y))
        p.setBrush(QColor(ACCENT))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(px, y), 3.5, 3.5)


class Equalizer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(22)
        self._bars = 32
        self._freqs = [2] * self._bars
        self._playing = False
        self._phase = 0.0

    def set_data(self, freqs, playing):
        self._freqs = freqs
        self._playing = playing

    def tick(self):
        self._phase += 0.06
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        n = self._bars
        bw = max(2, int(w / n) - 1)
        base = 19.0

        for i in range(n):
            v = self._freqs[i] if len(self._freqs) > i else 2
            if self._playing:
                bh = min(16, int(v * 0.5 + abs(math.sin(self._phase + i * 0.5)) * 5))
            else:
                bh = 1 + (i % 3)
            x = i * (bw + 1) + bw / 2
            ratio = i / n

            if ratio < 0.4:
                c = QColor(ACCENT)
            elif ratio < 0.7:
                t = (ratio - 0.4) / 0.3
                r = int(t * 170)
                g = int(206 * (1 - t * 0.4))
                b = int(206 * (1 - t * 0.3))
                c = QColor(r, g, b)
            else:
                c = VIZ_PINK

            pen = QPen(c, bw)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            p.drawLine(QPointF(x, base), QPointF(x, base - bh))


class ControlButton(QPushButton):
    def __init__(self, text, size, play=False):
        super().__init__(text)
        self.setFixedSize(size, size)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        r = size // 2
        if play:
            self.setStyleSheet(
                f"QPushButton{{background:#00CECE;color:#000;font-weight:bold;"
                f"border-radius:{r}px;font-size:17px;}}"
                f"QPushButton:hover{{background:#00FFFF;}}"
            )
        else:
            self.setStyleSheet(
                f"QPushButton{{background:transparent;color:rgba(255,255,255,0.6);"
                f"border-radius:{r}px;font-size:15px;}}"
                f"QPushButton:hover{{background:rgba(255,255,255,0.08);}}"
            )
