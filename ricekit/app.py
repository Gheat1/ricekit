"""KitApp — the base App that wires the whole kit together."""

from __future__ import annotations

from textual.app import App
from textual.color import Color

from ricekit.modals import ThemeModal
from ricekit.palette import palette
from ricekit.themes import KIT_THEMES, KIT_THEME_NAMES


class KitApp(App):
    """App base with the kit's theme machinery.

    Call `self.init_kit(theme=...)` from your `on_mount`. Then:

    - the five kit themes are registered and one is active
    - `App.ansi_color` flips automatically for ansi-background themes
      (clear, system, ansi-dark, …) so the terminal background shows
    - the shared `palette` swaps to ANSI colors under the `system` theme
    - `action_change_theme` opens the live-preview ThemeModal (this also
      replaces the command palette's built-in "Change theme" flow)
    - `action_cycle_kit_theme` cycles the five kit themes (bind it to `t`)
    - override `on_kit_theme_changed()` to re-render palette-dependent
      content and persist the choice — check `self.kit_theme_previewing`
      before persisting
    """

    kit_theme_previewing: bool = False

    def get_css_variables(self) -> dict[str, str]:
        # kit-* variables must exist even before our themes register (the
        # stylesheet is parsed while the default textual theme is active),
        # and when a non-kit builtin theme is active
        variables = super().get_css_variables()
        theme = next((t for t in KIT_THEMES if t.name == self.theme), KIT_THEMES[0])
        for name, value in theme.variables.items():
            variables.setdefault(name, value)
        return variables

    def init_kit(self, theme: str | None = None) -> None:
        for t in KIT_THEMES:
            self.register_theme(t)
        self.theme_changed_signal.subscribe(self, self._kit_theme_changed)
        if theme and theme in self.available_themes:
            self.theme = theme
        else:
            self.theme = KIT_THEME_NAMES[0]
        self._kit_apply()

    def _kit_theme_is_ansi(self) -> bool:
        theme = self.available_themes.get(self.theme)
        if theme is None or theme.background is None:
            return False
        try:
            return Color.parse(theme.background).ansi is not None
        except Exception:
            return False

    def _kit_apply(self) -> None:
        self.ansi_color = self._kit_theme_is_ansi()
        palette.set_ansi(self.theme == "system")

    def _kit_theme_changed(self, _theme) -> None:
        self._kit_apply()
        self.on_kit_theme_changed()

    def on_kit_theme_changed(self) -> None:
        """Override me: re-render Rich-text chrome, persist self.theme
        (skip persisting while `self.kit_theme_previewing` is True)."""

    def action_cycle_kit_theme(self) -> None:
        idx = (
            KIT_THEME_NAMES.index(self.theme)
            if self.theme in KIT_THEME_NAMES
            else -1
        )
        self.theme = KIT_THEME_NAMES[(idx + 1) % len(KIT_THEME_NAMES)]

    def action_change_theme(self) -> None:
        # overrides App.action_change_theme, so the command palette's
        # "Change theme" command opens the live-preview picker too
        if isinstance(self.screen, ThemeModal):
            return
        self.push_screen(ThemeModal())
