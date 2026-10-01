import sys
import logging
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QShortcut, QKeySequence, QIcon
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu

from .window import MiniPlayer
from .config import APP_DATA_DIR

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    filename=str(APP_DATA_DIR / "nexus.log"),
    filemode="a",
)

ICON_PATH = Path(__file__).resolve().parent.parent / "assets" / "icon.ico"


def _build_tray(app, player):
    if not QSystemTrayIcon.isSystemTrayAvailable():
        return None

    tray = QSystemTrayIcon(QIcon(str(ICON_PATH)), app)
    tray.setToolTip("Nexus Mini Player")

    menu = QMenu()
    toggle_action = menu.addAction("Mostrar / ocultar")
    toggle_action.triggered.connect(lambda: player.setVisible(not player.isVisible()))
    menu.addSeparator()
    quit_action = menu.addAction("Cerrar")
    quit_action.triggered.connect(player.close_app)

    tray.setContextMenu(menu)
    tray.activated.connect(
        lambda reason: player.setVisible(not player.isVisible())
        if reason == QSystemTrayIcon.ActivationReason.Trigger
        else None
    )
    tray.show()
    return tray


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setQuitOnLastWindowClosed(False)

    player = MiniPlayer()
    player.show()

    tray = _build_tray(app, player)

    toggle = QShortcut(QKeySequence("Ctrl+Shift+M"), player)
    toggle.setContext(Qt.ShortcutContext.ApplicationShortcut)
    toggle.activated.connect(lambda: player.setVisible(not player.isVisible()))

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
