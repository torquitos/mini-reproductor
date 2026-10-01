import json
import logging
import os
from pathlib import Path

LOGGER = logging.getLogger("nexus")

APP_DATA_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "NexusMiniPlayer"
APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_PATH = APP_DATA_DIR / "config.json"


class Config:
    def __init__(self):
        self.x: int | None = None
        self.y: int | None = None
        self.topmost: bool = False
        self._load()

    def _load(self):
        try:
            if CONFIG_PATH.exists():
                with CONFIG_PATH.open("r") as f:
                    data = json.load(f)
                self.x = data.get("x")
                self.y = data.get("y")
                self.topmost = data.get("topmost", False)
        except Exception as exc:
            LOGGER.warning("No se pudo cargar config.json: %s", exc)

    def save(self, x: int, y: int, topmost: bool):
        self.x = x
        self.y = y
        self.topmost = topmost
        try:
            with CONFIG_PATH.open("w") as f:
                json.dump({"x": x, "y": y, "topmost": topmost}, f, indent=2)
        except Exception as exc:
            LOGGER.warning("No se pudo guardar config.json: %s", exc)
