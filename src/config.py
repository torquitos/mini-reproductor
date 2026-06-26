import json
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"


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
        except Exception:
            pass

    def save(self, x: int, y: int, topmost: bool):
        self.x = x
        self.y = y
        self.topmost = topmost
        try:
            with CONFIG_PATH.open("w") as f:
                json.dump({"x": x, "y": y, "topmost": topmost}, f, indent=2)
        except Exception:
            pass
