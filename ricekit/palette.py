"""The chrome palette — every UI color that isn't data.

Reference `palette.<role>` at render time (never bake into import-time
constants) so switching to the ANSI palette restyles a live app.
"""

from __future__ import annotations

TRUECOLOR = {
    "text": "#cdd6f4",
    "sub": "#a6adc8",
    "dim": "#6c7086",
    "faint": "#45475a",
    "vfaint": "#313244",
    "blue": "#89b4fa",
    "lav": "#b4befe",
    "peach": "#fab387",
    "green": "#a6e3a1",
    "red": "#f38ba8",
    "mauve": "#cba6f7",
    "yellow": "#f9e2af",
}

# terminal-native equivalents, used by the `system` theme
ANSI = {
    "text": "default",
    "sub": "white",
    "dim": "bright_black",
    "faint": "bright_black",
    "vfaint": "bright_black",
    "blue": "blue",
    "lav": "bright_blue",
    "peach": "yellow",
    "green": "green",
    "red": "red",
    "mauve": "magenta",
    "yellow": "yellow",
}


class Palette:
    """Swappable color roles for text chrome (rich styles, not CSS)."""

    text: str
    sub: str
    dim: str
    faint: str
    vfaint: str
    blue: str
    lav: str
    peach: str
    green: str
    red: str
    mauve: str
    yellow: str

    def __init__(self) -> None:
        self.set_ansi(False)

    def set_ansi(self, ansi: bool) -> None:
        self.__dict__.update(ANSI if ansi else TRUECOLOR)
        self.is_ansi = ansi


palette = Palette()
"""The shared palette instance. `from ricekit import palette`."""
