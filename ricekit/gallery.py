"""ricekit-gallery — a live demo of every piece of the kit.

Also serves as the kit's integration test: if the gallery runs, the
themes, palette, widgets, and modals all compose.
"""

from __future__ import annotations

import sys

from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, OptionList, Static
from textual.widgets.option_list import Option

from ricekit import __version__, icons
from ricekit.app import KitApp
from ricekit.modals import HelpModal, PickerModal
from ricekit.palette import palette
from ricekit.storage import AppDirs
from ricekit.widgets import KitScroll, NavList, Splitter, pop_in

DIRS = AppDirs("ricekit-gallery")

HELP_SECTIONS = [
    ("navigate", [("j / k / arrows", "move"), ("enter", "show a demo"), ("esc", "close modal")]),
    ("kit", [("t", "cycle the five kit themes"), ("ctrl+p", "palette → Change theme (live preview)"),
             ("p", "open a PickerModal"), ("?", "this help")]),
    ("layout", [("drag the divider", "resize the sidebar"), ("double-click it", "reset")]),
    ("app", [("q", "quit")]),
]

DEMOS = ["palette", "icons", "state glyphs", "bars", "widgets", "philosophy"]


class Gallery(KitApp):
    TITLE = "ricekit gallery"

    BINDINGS = [
        Binding("t", "cycle_kit_theme", "theme"),
        Binding("p", "picker_demo", "picker"),
        Binding("question_mark", "help", "help"),
        Binding("q", "quit", "quit"),
    ]

    CSS = """
    #side {
        width: 26;
        margin: 0 0 0 1;
        border: round $kit-border;
        border-title-color: $kit-border-alt;
    }
    #side:focus-within { border: round $kit-border-focus; }
    #stage {
        width: 1fr;
        margin: 0 1 0 0;
        border: round $kit-border;
        border-title-color: $kit-border-alt;
    }
    #stage-body { height: auto; padding: 1 2; }
    """

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical(id="side"):
                yield NavList(id="demos")
            yield Splitter("#side", min_width=18, max_width=40,
                           on_resized=self._layout_changed, id="split")
            with Vertical(id="stage"):
                with KitScroll(id="stage-scroll"):
                    yield Static(id="stage-body")
        yield Footer()

    def on_mount(self) -> None:
        state = DIRS.load_state()
        self.init_kit(theme=state.get("theme"))
        side = self.query_one("#side")
        side.border_title = f" {icons.STAR} ricekit {__version__} "
        if w := state.get("side_w"):
            side.styles.width = int(w)
        self.query_one("#stage").border_title = " gallery "
        demos = self.query_one("#demos", NavList)
        demos.add_options([Option(Text(f" {d}"), id=d) for d in DEMOS])
        demos.highlighted = 0
        demos.focus()
        self._show("palette")

    def _layout_changed(self, target: str, width: int | None) -> None:
        DIRS.save_state({"side_w": width})

    def on_kit_theme_changed(self) -> None:
        # re-render palette-dependent content; persist unless previewing
        current = self.query_one("#demos", NavList).highlighted or 0
        self._show(DEMOS[current])
        if not self.kit_theme_previewing:
            DIRS.save_state({"theme": self.theme})

    # ── demo panes ────────────────────────────────────────────────────
    @on(OptionList.OptionHighlighted, "#demos")
    def _pick(self, event: OptionList.OptionHighlighted) -> None:
        if event.option.id:
            self._show(event.option.id)

    def _show(self, demo: str) -> None:
        body = Text()
        if demo == "palette":
            body.append("the swappable chrome palette\n\n", style=f"bold {palette.text}")
            for role in ("text", "sub", "dim", "faint", "vfaint", "blue", "lav",
                         "peach", "green", "red", "mauve", "yellow"):
                value = getattr(palette, role)
                body.append("  ██ ", style=value)
                body.append(f"palette.{role}".ljust(18), style=palette.sub)
                body.append(f"{value}\n", style=palette.dim)
            body.append("\nswitch to the system theme (t) and watch these\n"
                        "become your terminal's own ANSI colors.", style=palette.dim)
        elif demo == "icons":
            body.append("nerd-font icons (as \\uXXXX escapes)\n\n", style=f"bold {palette.text}")
            names = [n for n in dir(icons) if n.isupper() and isinstance(getattr(icons, n), str)
                     and n not in ("BULLET", "DOT_SEP")]
            for name in sorted(names):
                body.append(f"  {getattr(icons, name)}  ", style=palette.blue)
                body.append(f"icons.{name}\n", style=palette.sub)
        elif demo == "state glyphs":
            body.append("workflow-state circles (plain unicode)\n\n", style=f"bold {palette.text}")
            colors = {"triage": palette.mauve, "backlog": palette.dim,
                      "unstarted": palette.sub, "started": palette.yellow,
                      "review": palette.green, "completed": palette.blue,
                      "canceled": palette.dim}
            for state, glyph in icons.STATE_GLYPHS.items():
                body.append(f"  {glyph}  ", style=colors.get(state, palette.sub))
                body.append(f"{state}\n", style=palette.sub)
        elif demo == "bars":
            body.append("mini bar gauges\n\n", style=f"bold {palette.text}")
            for label, lit in (("urgent", 3), ("high", 3), ("medium", 2), ("low", 1), ("none", 0)):
                body.append("  ")
                body.append_text(icons.bars(lit, palette.sub, palette.vfaint))
                body.append(f"  {label}\n", style=palette.sub)
        elif demo == "widgets":
            body.append("what you're looking at\n\n", style=f"bold {palette.text}")
            for name, desc in (
                ("NavList", "vim keys, quiet cursor via $kit-cursor"),
                ("Splitter", "drag the divider left of this pane; double-click resets"),
                ("KitScroll", "focusable scrolling with j/k"),
                ("PickerModal", "press p"),
                ("ThemeModal", "ctrl+p → Change theme — previews as you scroll"),
                ("HelpModal", "press ?"),
                ("pop_in", "every modal fades in (~150ms)"),
            ):
                body.append(f"  {name.ljust(14)}", style=palette.blue)
                body.append(f"{desc}\n", style=palette.sub)
        elif demo == "philosophy":
            body.append("the short version\n\n", style=f"bold {palette.text}")
            for line in (
                "cache first — render instantly, refresh in the background",
                "rounded borders, titles in the border, one accent at a time",
                "chrome colors are roles, data colors are data",
                "keyboard first, everything clickable anyway",
                "motion is a fade, 150ms, out_cubic — never more",
                "themes restyle chrome only; clear + system respect the rice",
            ):
                body.append(f"  {icons.CHECK} ", style=palette.green)
                body.append(f"{line}\n", style=palette.sub)
            body.append("\nfull document: DESIGN.md", style=palette.dim)
        self.query_one("#stage-body", Static).update(body)
        self.query_one("#stage").border_subtitle = f" {demo} "

    # ── modal demos ───────────────────────────────────────────────────
    def action_picker_demo(self) -> None:
        opts = []
        for i, (glyph, label) in enumerate([
            (icons.CHECK_CIRCLE, "ship it"),
            (icons.CLOCK, "later"),
            (icons.CROSS_CIRCLE, "never"),
        ]):
            row = Text()
            row.append(f"{glyph} ", style=(palette.green, palette.yellow, palette.red)[i])
            row.append(label, style=palette.text)
            opts.append(Option(row, id=label))

        def done(choice: str | None) -> None:
            if choice:
                self.notify(f"{icons.CHECK} you picked: {choice}")

        self.push_screen(PickerModal("a PickerModal", opts), done)

    def action_help(self) -> None:
        if isinstance(self.screen, HelpModal):
            return
        self.push_screen(HelpModal(HELP_SECTIONS, title=f"{icons.KEYBOARD}  ricekit gallery"))


def main() -> None:
    if "--version" in sys.argv or "-v" in sys.argv:
        print(f"ricekit {__version__}")
        return
    Gallery().run()


if __name__ == "__main__":
    main()
