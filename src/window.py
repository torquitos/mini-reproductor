import logging

from PySide6.QtCore import Qt, QTimer, QPointF
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QPainterPath, QCursor, QLinearGradient, QRadialGradient,
)
from PySide6.QtWidgets import QWidget, QApplication, QLabel, QMenu

from .theme import W, H, M, WIN_W, WIN_H, COVER, RADIUS, BG_BASE, BG_BASE_DARK, DEFAULT_ACCENT
from .config import Config
from .spotify import SpotifySession, ms
from .widgets import AlbumArt, ProgressBar, Equalizer, ControlButton, CloseButton, VolumeButton

LOGGER = logging.getLogger("nexus")

INFO_X = M + COVER + 18
INFO_W = W - COVER - 18


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
        self.setMouseTracking(True)

        self._accent = QColor(*DEFAULT_ACCENT)
        self._spotify = SpotifySession()
        self._cfg = Config()
        self._tick = 0
        self._scroll_offset = 0
        self._scroll_step = 0
        self._hovering = False

        self._build_ui()
        self._apply_position()
        self._start_loop()

    def _build_ui(self):
        self._cover = AlbumArt(self)
        self._cover.move(M, M)

        self._progress = ProgressBar(self)
        self._eq = Equalizer(self)

        self._status_label = QLabel("ESPERANDO", self)
        self._status_label.setStyleSheet(
            "color:rgba(255,255,255,0.4);font-size:9px;font-weight:600;"
            "letter-spacing:1px;background:transparent;"
        )

        self._title = QLabel("Abriendo Spotify...", self)
        self._title.setStyleSheet(
            "color:#fff;font-size:16px;font-weight:650;background:transparent;"
        )

        self._artist = QLabel("Nexus Mini Player", self)
        self._artist.setStyleSheet(
            "color:rgba(255,255,255,0.5);font-size:12px;background:transparent;"
        )

        self._time_left = QLabel("0:00", self)
        self._time_left.setStyleSheet(
            "color:rgba(255,255,255,0.38);font-size:10px;background:transparent;"
        )
        self._time_right = QLabel("0:00", self)
        self._time_right.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._time_right.setStyleSheet(
            "color:rgba(255,255,255,0.38);font-size:10px;background:transparent;"
        )

        self._btn_prev = ControlButton("prev", 30)
        self._btn_play = ControlButton("play", 40, play=True)
        self._btn_next = ControlButton("next", 30)
        self._btn_prev.setParent(self)
        self._btn_play.setParent(self)
        self._btn_next.setParent(self)

        self._btn_prev.clicked.connect(lambda: self._cmd("prev"))
        self._btn_play.clicked.connect(lambda: self._cmd("play"))
        self._btn_next.clicked.connect(lambda: self._cmd("next"))
        self._progress.on_seek(self._seek)

        self._status_label.setGeometry(INFO_X, M + 8, INFO_W, 13)
        self._title.setGeometry(INFO_X, M + 22, INFO_W, 22)
        self._artist.setGeometry(INFO_X, M + 44, INFO_W, 16)

        self._progress.setGeometry(INFO_X, M + 66, INFO_W, 14)
        self._time_left.setGeometry(INFO_X, M + 81, INFO_W // 2, 12)
        self._time_right.setGeometry(INFO_X + INFO_W // 2, M + 81, INFO_W // 2, 12)

        ctrl_y = M + 96
        play_size, side_size = 40, 30
        gap = 22
        center_x = INFO_X + INFO_W // 2
        self._btn_play.move(center_x - play_size // 2, ctrl_y)
        self._btn_prev.move(center_x - play_size // 2 - gap - side_size, ctrl_y + 5)
        self._btn_next.move(center_x + play_size // 2 + gap, ctrl_y + 5)

        self._eq.setGeometry(INFO_X, M + COVER - 24, INFO_W, 18)

        self._btn_close = CloseButton(18, self)
        self._btn_volume = VolumeButton(18, self)
        self._btn_close.move(M + W - 18 - 6, M + 6)
        self._btn_volume.move(M + W - 18 - 6 - 18 - 6, M + 6)
        self._btn_close.clicked.connect(self._close_app)
        self._btn_volume.on_change(self._spotify.set_volume)
        self._btn_close.hide()
        self._btn_volume.set_level(None)

    def _cmd(self, action):
        self._spotify.run_coroutine(self._spotify.control(action))

    def _seek(self, pct):
        snap = self._spotify.snapshot()
        if snap.duration_ms <= 0:
            return
        self._progress.set(pct)
        self._spotify.run_coroutine(self._spotify.seek(int(snap.duration_ms * pct)))

    def _update_cover(self):
        try:
            img = self._spotify.consume_cover()
            if img:
                self._cover.set_album(img)
        except Exception as exc:
            LOGGER.warning("No se pudo actualizar la carátula: %s", exc)

    def _apply_accent(self, rgb):
        if (rgb[0], rgb[1], rgb[2]) == (self._accent.red(), self._accent.green(), self._accent.blue()):
            return
        self._accent = QColor(*rgb)
        self._progress.set_accent(rgb)
        self._eq.set_accent(rgb)
        self._btn_play.set_accent(rgb)

    def _loop(self):
        self._tick += 1
        if self._tick >= 10:
            self._tick = 0
            self._spotify.run_coroutine(self._spotify.refresh())
            self._update_cover()
            self._btn_volume.set_level(self._spotify.get_volume())

        snap = self._spotify.snapshot()
        self._apply_accent(snap.accent_color)

        title = snap.title
        lim = 24
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
        self._btn_play._icon = "pause" if snap.playing else "play"
        self._btn_play.update()

        if snap.error == "sin_soporte":
            self._status_label.setText("NO DISPONIBLE")
        elif snap.error == "sin_sesion":
            self._status_label.setText("DESCONECTADO")
        elif snap.playing:
            self._status_label.setText("REPRODUCIENDO")
        else:
            self._status_label.setText("EN PAUSA")

        self._eq.set_data(self._spotify.fake_frequencies(20), snap.playing)
        self._eq.tick()
        self.update()

        QTimer.singleShot(40, self._loop)

    def _start_loop(self):
        self._loop()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        for i in range(10):
            o = 3 + i
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(0, 0, 0, 14 - i))
            p.drawRoundedRect(M - o, M - o + 4, W + o * 2, H + o * 2, RADIUS + 4, RADIUS + 4)

        path = QPainterPath()
        path.addRoundedRect(M, M, W, H, RADIUS, RADIUS)
        p.setClipPath(path)

        g = QLinearGradient(M, M, M + W, M + H)
        g.setColorAt(0.0, BG_BASE)
        g.setColorAt(1.0, BG_BASE_DARK)
        p.fillRect(M, M, W, H, QBrush(g))

        tint = QRadialGradient(M + W, M, W * 0.7)
        c1 = QColor(self._accent)
        c1.setAlpha(45)
        c2 = QColor(self._accent)
        c2.setAlpha(0)
        tint.setColorAt(0.0, c1)
        tint.setColorAt(1.0, c2)
        p.fillRect(M, M, W, H, QBrush(tint))

        p.setClipping(False)
        self._paint_status_dot(p)

    def _paint_status_dot(self, p):
        if self._hovering:
            return
        snap = self._spotify.snapshot()
        if snap.error:
            color = QColor("#FF5C5C")
        elif snap.playing:
            color = self._accent
        else:
            color = QColor("#6B6E76")
        cx, cy = M + W - 12, M + 12
        glow = QColor(color)
        glow.setAlpha(70)
        p.setBrush(glow)
        p.drawEllipse(QPointF(cx, cy), 7, 7)
        p.setBrush(color)
        p.drawEllipse(QPointF(cx, cy), 3.5, 3.5)

        if self._is_topmost():
            pin_color = QColor(255, 255, 255, 140)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(pin_color)
            px, py = M + W - 32, M + 12
            p.drawEllipse(QPointF(px, py - 2), 2.2, 2.2)
            pen = QPen(pin_color, 1.6)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            p.drawLine(QPointF(px, py), QPointF(px, py + 4))

    def enterEvent(self, e):
        self._hovering = True
        self._btn_close.show()
        self._btn_volume.set_hover_visible(True)
        self.update()

    def leaveEvent(self, e):
        self._hovering = False
        self._btn_close.hide()
        self._btn_volume.set_hover_visible(False)
        self.update()

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
            "QMenu{background:#17181D;color:#fff;border:1px solid #262830;"
            "padding:4px;border-radius:8px}"
            "QMenu::item:selected{background:#262830;}"
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
        if not screen:
            return
        geo = screen.availableGeometry()
        default_x = geo.right() - self.width() - 30
        default_y = geo.bottom() - self.height() - 30

        x, y = self._cfg.x, self._cfg.y
        if x is None or y is None or not self._position_is_visible(x, y):
            x, y = default_x, default_y
        self.move(max(0, x), max(0, y))

    def _position_is_visible(self, x: int, y: int) -> bool:
        """Evita que el widget quede atrapado fuera de pantalla si se guardó la
        posición con un monitor que luego se desconectó (ej. laptop + monitor externo)."""
        rect = self.frameGeometry()
        rect.moveTo(x, y)
        for screen in QApplication.screens():
            if screen.availableGeometry().intersects(rect):
                return True
        return False

    def mouseDoubleClickEvent(self, e):
        if self._cover.geometry().contains(e.position().toPoint()):
            self._cmd("play")

    def close_app(self):
        self._cfg.save(self.x(), self.y(), self._is_topmost())
        self._spotify.close()
        QApplication.quit()

    def _close_app(self):
        self.close_app()
