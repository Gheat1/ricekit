"""The five kit themes and their CSS variable contract.

Every theme defines the same `kit-*` variables, plus explicit scrollbar and
text-selection colors (Textual derives both from `primary` otherwise, which
makes them identical murky blue). App stylesheets should use:

    border: round $kit-border;            /* resting chrome            */
    border: round $kit-border-focus;      /* focused panel             */
    border: round $kit-border-alt;        /* secondary emphasis        */
    background: $kit-modal-bg;            /* modal boxes               */
    background: $kit-cursor;              /* list-cursor rows          */
    background: $kit-overlay;             /* modal screen dim layer    */

`clear` and `system` use ansi_default backgrounds: pair them with
`KitApp`, which flips `App.ansi_color` so the terminal's own background
(and palette, for `system`) shows through.
"""

from __future__ import annotations

from textual.theme import Theme

_ACCENTS = dict(success="#a6e3a1", warning="#f9e2af", error="#f38ba8", dark=True)

KIT_THEMES: list[Theme] = [
    Theme(
        name="mocha",
        primary="#89b4fa", secondary="#cba6f7", accent="#f5c2e7",
        background="#1e1e2e", surface="#313244", panel="#181825",
        foreground="#cdd6f4", **_ACCENTS,
        variables={
            "kit-border": "#45475a",
            "kit-border-focus": "#89b4fa",
            "kit-border-alt": "#b4befe",
            "kit-modal-bg": "#181825",
            "kit-cursor": "#3e4869",
            "kit-overlay": "black 40%",
            "scrollbar": "#313244",
            "scrollbar-hover": "#45475a",
            "scrollbar-active": "#585b70",
            "scrollbar-background": "#181825",
            "screen-selection-background": "#b4befe 35%",
            "input-selection-background": "#b4befe 35%",
        },
    ),
    Theme(
        name="void",
        primary="#89b4fa", secondary="#cba6f7", accent="#f5c2e7",
        background="#000000", surface="#101018", panel="#070709",
        foreground="#cdd6f4", **_ACCENTS,
        variables={
            "kit-border": "#26262e",
            "kit-border-focus": "#89b4fa",
            "kit-border-alt": "#b4befe",
            "kit-modal-bg": "#0a0a10",
            "kit-cursor": "#1e2a4a",
            "kit-overlay": "black 40%",
            "scrollbar": "#1e1e28",
            "scrollbar-hover": "#2c2c38",
            "scrollbar-active": "#3c3c4a",
            "scrollbar-background": "#0a0a10",
            "screen-selection-background": "#b4befe 30%",
            "input-selection-background": "#b4befe 30%",
        },
    ),
    Theme(
        name="onyx",
        primary="#9aa5b5", secondary="#7d8494", accent="#b8c0cc",
        background="#0e0e11", surface="#1b1b20", panel="#131317",
        foreground="#d4d6dd", **_ACCENTS,
        variables={
            "kit-border": "#33333c",
            "kit-border-focus": "#9aa5b5",
            "kit-border-alt": "#b8c0cc",
            "kit-modal-bg": "#141419",
            "kit-cursor": "#2b303b",
            "kit-overlay": "black 40%",
            "scrollbar": "#2a2a32",
            "scrollbar-hover": "#3a3a44",
            "scrollbar-active": "#4a4a56",
            "scrollbar-background": "#131317",
            "screen-selection-background": "#b8c0cc 30%",
            "input-selection-background": "#b8c0cc 30%",
        },
    ),
    # no background at all — the terminal's own background (and any
    # blur/transparency it has) shows through; muted grey-slate chrome
    Theme(
        name="clear",
        primary="#8a93a5", secondary="#6f7787", accent="#a9b1c0",
        background="ansi_default", surface="ansi_default", panel="ansi_default",
        foreground="#cdd6f4", **_ACCENTS,
        variables={
            "kit-border": "#3c3f4a",
            "kit-border-focus": "#8a93a5",
            "kit-border-alt": "#a9b1c0",
            "kit-modal-bg": "#16161d",
            "kit-cursor": "#282c38",
            "kit-overlay": "transparent",
            "scrollbar": "#3c3f4a",
            "scrollbar-hover": "#4a4e5a",
            "scrollbar-active": "#5a5f6d",
            "scrollbar-background": "transparent",
            "screen-selection-background": "#3f4655",
            "input-selection-background": "#3f4655",
        },
    ),
    # the terminal's own ANSI palette + no background: a custom kitty /
    # alacritty / ghostty theme becomes the app theme
    Theme(
        name="system",
        primary="ansi_blue", secondary="ansi_magenta", accent="ansi_cyan",
        background="ansi_default", surface="ansi_default", panel="ansi_default",
        foreground="ansi_default",
        success="ansi_green", warning="ansi_yellow", error="ansi_red", dark=True,
        variables={
            "kit-border": "ansi_bright_black",
            "kit-border-focus": "ansi_blue",
            "kit-border-alt": "ansi_bright_blue",
            "kit-modal-bg": "ansi_black",
            "kit-cursor": "ansi_bright_black",
            "kit-overlay": "transparent",
            "scrollbar": "ansi_bright_black",
            "scrollbar-hover": "ansi_bright_black",
            "scrollbar-active": "ansi_blue",
            "scrollbar-background": "ansi_default",
            "screen-selection-background": "ansi_cyan",
            "screen-selection-foreground": "ansi_black",
            "input-selection-background": "ansi_cyan",
        },
    ),
]

KIT_THEME_NAMES = [t.name for t in KIT_THEMES]
