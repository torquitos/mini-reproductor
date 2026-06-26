import sys
import logging

from PySide6.QtCore import Qt
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtWidgets import QApplication

from .window import MiniPlayer

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    filename="nexus.log",
    filemode="a",
)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    player = MiniPlayer()
    player.show()

    toggle = QShortcut(QKeySequence("Ctrl+Shift+M"), player)
    toggle.setContext(Qt.ShortcutContext.ApplicationShortcut)
    toggle.activated.connect(lambda: player.setVisible(not player.isVisible()))

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
