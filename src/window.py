import asyncio
from PIL import Image, ImageFilter
from PySide6.QtCore import Qt, QTimer, QPointF
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QPainterPath, QCursor, QLinearGradient,
)
from PySide6.QtWidgets import QWidget, QApplication, QLabel, QMenu

from .theme import W, H, M, WIN_W, WIN_H, BG_GRADIENT_TOP, BG_GRADIENT_BOTTOM, ACCENT
from .config import Config
from .spotify import SpotifySession, ms
from .widgets import AlbumArt, RingVisualizer, ProgressBar, Equalizer, ControlButton, pil2px


def _blur_bg(pil_img):
    img = pil_img.resize((W, H), Image.Resampling.LANCZOS)
    img = img.filter(ImageFilter.GaussianBlur(radius=28))
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 170))
    return pil2px(Image.alpha_composite(img.convert("RGBA"), overlay))


class MiniPlayer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setFixedSize(WIN_W, WIN_H)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._bg_px = None
        self._spotify = SpotifySession()
        self._cfg = Config()
        self._tick = 0
        self._scroll_offset = 0
        self._scroll_step = 0

        self._build_ui()
        self._apply_position()
        self._start_loop()

    def _build_ui(self):
        self._cover = AlbumArt(self)
        self._ring = RingVisualizer(self)
        self._progress = ProgressBar(self)
        self._eq = Equalizer(self)

        self._title = QLabel("Abriendo Spotify...", self)
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title.setStyleSheet("color:#fff;font-size:14px;font-weight:bold;background:transparent;")

        self._artist = QLabel("Nexus Mini Player", self)
        self._artist.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._artist.setStyleSheet("color:rgba(255,255,255,0.5);font-size:11px;background:transparent;")

        self._time_left = QLabel("0:00", self)
        self._time_left.setStyleSheet("color:rgba(255,255,255,0.25);font-size:9px;background:transparent;")

        self._time_right = QLabel("0:00", self)
        self._time_right.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._time_right.setStyleSheet("color:rgba(255,255,255,0.25);font-size:9px;background:transparent;")

        self._btn_prev = ControlButton("◂", 40)
        self._btn_play = ControlButton("▶", 46, play=True)
        self._btn_next = ControlButton("▸", 40)

        self._btn_prev.setParent(self)
        self._btn_play.setParent(self)
        self._btn_next.setParent(self)

        self._btn_prev.clicked.connect(lambda: self._cmd("prev"))
        self._btn_play.clicked.connect(lambda: self._cmd("play"))
        self._btn_next.clicked.connect(lambda: self._cmd("next"))
        self._progress.on_seek(lambda p: self._seek(p))

        cx = M + (W - 200) // 2
        cy = M + 52
        self._ring.move(M + (W - 240) // 2, M + 32)
        self._cover.move(cx, cy)
        self._title.setGeometry(M + 16, M + 260, W - 32, 22)
        self._artist.setGeometry(M + 16, M + 282, W - 32, 18)
        self._time_left.setGeometry(M + 16, M + 306, (W - 32) // 2 - 4, 14)
        self._time_right.setGeometry(M + (W - 32) // 2 + 20, M + 306, (W - 32) // 2 - 4, 14)
        self._progress.setGeometry(M + 16, M + 322, W - 32, 14)

        cw = 40 + 4 + 46 + 4 + 40
        cx = M + (W - cw) // 2
        self._btn_prev.move(cx, M + 345)
        self._btn_play.move(cx + 44, M + 342)
        self._btn_next.move(cx + 94, M + 345)
        self._eq.setGeometry(M + 16, M + 380, W - 32, 22)

    def _cmd(self, action):
        asyncio.run_coroutine_threadsafe(self._spotify.control(action), self._spotify._loop)

    def _seek(self, pct):
        snap = self._spotify.snapshot()
        if snap.duration_ms <= 0:
            return
        self._progress.set(pct)
        asyncio.run_coroutine_threadsafe(
            self._spotify.seek(int(snap.duration_ms * pct)), self._spotify._loop
        )

    def _update_cover(self):
        try:
            img = self._spotify.consume_cover()
            if img:
                self._cover.set_album(img)
                self._bg_px = _blur_bg(img)
                self.update()
        except Exception:
            pass

    def _loop(self):
        self._tick += 1
        if self._tick >= 10:
            self._tick = 0
            asyncio.run_coroutine_threadsafe(self._spotify.refresh(), self._spotify._loop)
            self._update_cover()

        snap = self._spotify.snapshot()

        title = snap.title
        lim = 26
        if len(title) > lim:
            self._scroll_step += 1
            lp = title + "     "
            if self._scroll_step >= 5:
                self._scroll_step = 0
                self._scroll_offset = (self._scroll_offset + 1) % len(lp)
            title = (lp * 2)[self._scroll_offset:self._scroll_offset + lim]
        else:
            self._scroll_offset = 0

        self._title.setText(title)
        self._title.setToolTip(snap.title)
        self._artist.setText(snap.artist)
        self._artist.setToolTip(snap.artist)
        self._time_left.setText(ms(snap.position_ms))
        self._time_right.setText(ms(snap.duration_ms))
        self._progress.set(self._spotify.progress_pct() / 100)
        self._btn_play.setText("⏸" if snap.playing else "▶")

        self._ring.set_data(self._spotify.fake_frequencies(36), snap.playing)
        self._eq.set_data(self._spotify.fake_frequencies(32), snap.playing)
        self._eq.tick()

        QTimer.singleShot(40, self._loop)

    def _start_loop(self):
        self._loop()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        for i in range(12):
            o = 4 + i
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(0, 0, 0, 18 - i))
            p.drawRoundedRect(M - o, M - o + 6, W + o * 2, H + o * 2, 20, 20)

        path = QPainterPath()
        path.addRoundedRect(M, M, W, H, 18, 18)
        p.setClipPath(path)

        if self._bg_px:
            p.drawPixmap(M, M, W, H, self._bg_px)
        else:
            g = QLinearGradient(M, M, M, H + M)
            g.setColorAt(0.0, BG_GRADIENT_TOP)
            g.setColorAt(1.0, BG_GRADIENT_BOTTOM)
            p.fillRect(M, M, W, H, QBrush(g))

        status = self._status_color()
        if status:
            p.setClipping(False)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(status))
            p.drawEllipse(QPointF(M + W - 12, M + 12), 4, 4)
            p.setBrush(QColor(status).lighter(180))
            p.drawEllipse(QPointF(M + W - 12, M + 12), 2, 2)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint()
        elif e.button() == Qt.MouseButton.RightButton:
            self._show_menu()

    def mouseMoveEvent(self, e):
        if e.buttons() & Qt.MouseButton.LeftButton and hasattr(self, "_drag_pos"):
            delta = e.globalPosition().toPoint() - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = e.globalPosition().toPoint()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._cfg.save(self.x(), self.y(), self._is_topmost())

    def _is_topmost(self):
        return bool(self.windowFlags() & Qt.WindowType.WindowStaysOnTopHint)

    def _show_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu{background:#121418;color:#fff;border:1px solid #1C1F26;"
            "padding:4px;border-radius:8px}"
            "QMenu::item:selected{background:#1C1F26;}"
        )
        menu.addAction(
            "✓ Siempre encima" if self._is_topmost() else "Siempre encima",
            self._toggle_topmost,
        )
        menu.addSeparator()
        menu.addAction("Cerrar", self._close_app)
        menu.exec(QCursor.pos())

    def _toggle_topmost(self):
        flags = self.windowFlags()
        if flags & Qt.WindowType.WindowStaysOnTopHint:
            self.setWindowFlags(flags & ~Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(flags | Qt.WindowType.WindowStaysOnTopHint)
        self.show()

    def _apply_position(self):
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = self._cfg.x if self._cfg.x is not None else geo.right() - self.width() - 30
            y = self._cfg.y if self._cfg.y is not None else geo.bottom() - self.height() - 30
            self.move(max(0, x), max(0, y))

    def _status_color(self):
        snap = self._spotify.snapshot()
        if snap.error and "No hay sesión" in snap.error:
            return "#FF4444"
        return "#00CECE" if snap.playing else "#666666"

    def mouseDoubleClickEvent(self, e):
        if self._cover.geometry().contains(e.position().toPoint()):
            self._cmd("play")

    def _close_app(self):
        self._cfg.save(self.x(), self.y(), self._is_topmost())
        self._spotify.close()
        QApplication.quit()



