"""Modal building blocks: picker, theme picker with live preview, help sheet."""

from __future__ import annotations

from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import OptionList, Static
from textual.widgets.option_list import Option

from ricekit.palette import palette
from ricekit.widgets import NavList, pop_in


class PickerModal(ModalScreen):
    """Generic list picker: dismisses with the selected option's id (or None)."""

    BINDINGS = [Binding("escape", "cancel", show=False)]

    DEFAULT_CSS = """
    PickerModal { align: center middle; background: $kit-overlay; }
    PickerModal #kit-picker-box {
        width: 44; height: auto; max-height: 80%;
        background: $kit-modal-bg; border: round $kit-border-focus; padding: 1 1;
    }
    PickerModal #kit-picker-title { padding: 0 1 1 1; text-style: bold; }
    PickerModal #kit-picker-list { height: auto; max-height: 16; }
    """

    def __init__(self, title: str, options: list[Option]) -> None:
        super().__init__()
        self._title = title
        self._options = options

    def compose(self) -> ComposeResult:
        with Vertical(id="kit-picker-box"):
            yield Static(Text(self._title, style=f"bold {palette.sub}"), id="kit-picker-title")
            yield NavList(*self._options, id="kit-picker-list")

    def on_mount(self) -> None:
        pop_in(self.query_one("#kit-picker-box"))
        self.query_one("#kit-picker-list").focus()

    @on(OptionList.OptionSelected)
    def _selected(self, event: OptionList.OptionSelected) -> None:
        self.dismiss(event.option.id)

    def action_cancel(self) -> None:
        self.dismiss(None)


class ThemeModal(ModalScreen):
    """Theme picker — highlighting a theme previews it live across the app.

    While this modal is on screen, `KitApp.kit_theme_previewing` is True;
    persistence hooks should check it (commit fires one final change with
    the flag off).
    """

    BINDINGS = [Binding("escape", "cancel", show=False)]

    DEFAULT_CSS = """
    ThemeModal { align: center middle; background: $kit-overlay; }
    ThemeModal #kit-theme-box {
        width: 40; height: auto; max-height: 85%;
        background: $kit-modal-bg; border: round $kit-border-focus; padding: 1 1;
    }
    ThemeModal #kit-theme-title { padding: 0 1 1 1; text-style: bold; }
    ThemeModal #kit-theme-list { height: auto; max-height: 18; }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="kit-theme-box"):
            yield Static(
                Text("theme · scroll to preview", style=f"bold {palette.sub}"),
                id="kit-theme-title",
            )
            yield NavList(id="kit-theme-list")

    def _row(self, name: str, active: str) -> Option:
        row = Text("  ")
        on_it = name == active
        row.append("● " if on_it else "○ ", style=palette.blue if on_it else palette.dim)
        row.append(name, style=palette.text if on_it else palette.sub)
        return Option(row, id=name)

    def on_mount(self) -> None:
        from ricekit.themes import KIT_THEME_NAMES

        pop_in(self.query_one("#kit-theme-box"))
        app = self.app
        setattr(app, "kit_theme_previewing", True)
        self._original = app.theme
        ol = self.query_one("#kit-theme-list", NavList)
        opts = [Option(Text(" kit", style=f"bold {palette.sub}"), disabled=True)]
        index_of: dict[str, int] = {}
        for name in KIT_THEME_NAMES:
            index_of[name] = len(opts)
            opts.append(self._row(name, self._original))
        extra = sorted(n for n in app.available_themes if n not in KIT_THEME_NAMES)
        if extra:
            opts.append(Option(Text(" "), disabled=True))
            opts.append(Option(Text(" textual", style=f"bold {palette.sub}"), disabled=True))
            for name in extra:
                index_of[name] = len(opts)
                opts.append(self._row(name, self._original))
        ol.add_options(opts)
        ol.highlighted = index_of.get(self._original, 1)
        ol.focus()

    @on(OptionList.OptionHighlighted, "#kit-theme-list")
    def _preview(self, event: OptionList.OptionHighlighted) -> None:
        if event.option.id:
            self.app.theme = event.option.id

    @on(OptionList.OptionSelected, "#kit-theme-list")
    def _select(self, event: OptionList.OptionSelected) -> None:
        setattr(self.app, "kit_theme_previewing", False)
        if event.option.id:
            self.app.theme = event.option.id
            # re-fire so persistence hooks see the final (non-preview) change
            self.app.theme_changed_signal.publish(self.app.current_theme)
        self.dismiss(True)

    def action_cancel(self) -> None:
        setattr(self.app, "kit_theme_previewing", False)
        self.app.theme = self._original
        self.dismiss(False)


class HelpModal(ModalScreen):
    """Keybinding cheatsheet. `sections` is [(title, [(key, description), …]), …]."""

    BINDINGS = [
        Binding("escape", "close_modal", show=False),
        Binding("question_mark", "close_modal", show=False),
        Binding("q", "close_modal", show=False),
    ]

    DEFAULT_CSS = """
    HelpModal { align: center middle; background: $kit-overlay; }
    HelpModal #kit-help-box {
        width: 64; height: auto; max-height: 90%;
        background: $kit-modal-bg; border: round $kit-border-focus; padding: 1 2;
    }
    HelpModal #kit-help-body { height: auto; max-height: 30; scrollbar-size-vertical: 1; }
    """

    def __init__(self, sections: list[tuple[str, list[tuple[str, str]]]], title: str = "keys") -> None:
        super().__init__()
        self._sections = sections
        self._title = title

    def compose(self) -> ComposeResult:
        from ricekit.widgets import KitScroll

        with Vertical(id="kit-help-box"):
            yield Static(Text(self._title, style=f"bold {palette.sub}"))
            with KitScroll(id="kit-help-body"):
                yield Static(self._render_sections(), id="kit-help-text")

    def _render_sections(self) -> Text:
        # (not `_render` — that's a real internal method on every Widget)
        body = Text()
        key_w = max(
            (len(k) for _, rows in self._sections for k, _ in rows), default=8
        )
        for i, (section, rows) in enumerate(self._sections):
            if i:
                body.append("\n")
            body.append(f"\n {section}\n", style=f"bold {palette.dim}")
            for key, desc in rows:
                body.append(f"   {key.ljust(key_w + 2)}", style=palette.blue)
                body.append(f"{desc}\n", style=palette.sub)
        return body

    def on_mount(self) -> None:
        pop_in(self.query_one("#kit-help-box"))

    def action_close_modal(self) -> None:
        self.dismiss(None)
