"""Text effects: the letter wave and the braille spinner.

One shared ticker at ~8fps (0.12s) drives both; render only while a sweep
or spin is active — idle frames should cost nothing.
"""

from __future__ import annotations

from rich.markup import escape

SPINNER_FRAMES = "\u280b\u2819\u2839\u2838\u283c\u2834\u2826\u2827\u2807\u280f"

FX_TICK = 0.12  # seconds per animation frame
FX_REST_TICKS = 26  # pause between wave sweeps (~3s)


def wave_markup(s: str, pos: int, base: str, hi: str) -> str:
    """One traveling letter, bolded + capitalized: gheatmc -> Gheatmc -> gHeatmc.

    `pos` is the index of the highlighted letter (-1 or out of range = no
    highlight). Advance pos on a timer; after the sweep, rest FX_REST_TICKS.
    """
    out = []
    for i, ch in enumerate(s):
        e = escape(ch)
        if i == pos:
            out.append(f"[bold {hi}]{e.upper()}[/]")
        else:
            out.append(f"[{base}]{e}[/]")
    return "".join(out)


class Wave:
    """Sweep/rest state machine for wave_markup.

    tick() returns True when a re-render is needed this frame.
    """

    def __init__(self, length: int, rest_ticks: int = FX_REST_TICKS) -> None:
        self.length = length
        self.rest_ticks = rest_ticks
        self.pos = -1
        self._rest = 0

    def tick(self) -> bool:
        if self._rest > 0:
            self._rest -= 1
            return False
        self.pos += 1
        if self.pos >= self.length:
            self.pos = -1
            self._rest = self.rest_ticks
        return True
