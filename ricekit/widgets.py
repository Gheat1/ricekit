"""Reusable widgets: vim-navigable lists, drag-to-resize splitters, motion."""

from __future__ import annotations

from typing import Callable

from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.widgets import OptionList, Static


def pop_in(widget, duration: float = 0.15) -> None:
    """Fade a freshly mounted container into place.

    Opacity only, on purpose: offset/slide animation isn't supported for
    ScalarOffset in textual 8.x. 150ms out_cubic still reads as motion.
    """
    widget.styles.opacity = 0.0
    widget.styles.animate("opacity", 1.0, duration=duration, easing="out_cubic")


class NavList(OptionList):
    """OptionList with vim navigation. Use disabled options as group headers —
    keyboard navigation skips them automatically."""

    BINDINGS = [
        Binding("j", "cursor_down", show=False),
        Binding("k", "cursor_up", show=False),
        Binding("g", "first", show=False),
        Binding("G", "last", show=False),
    ]

    DEFAULT_CSS = """
    NavList {
        background: transparent;
        border: none;
        padding: 0 1;
        scrollbar-size-vertical: 1;
    }
    NavList:focus { background: transparent; border: none; }
    NavList > .option-list--option-highlighted { background: $kit-cursor; }
    NavList:focus > .option-list--option-highlighted { background: $kit-cursor; }
    """


class KitScroll(VerticalScroll):
    """Focusable scroll container with vim keys (detail panes, docs, logs).

    Anything you mount into this dynamically MUST have `height: auto` in CSS —
    containers default to fr-height and make the scroll area under-measure
    its content (scrolling then stops before the end).
    """

    can_focus = True
    BINDINGS = [
        Binding("j", "scroll_down", show=False),
        Binding("k", "scroll_up", show=False),
    ]

    DEFAULT_CSS = """
    KitScroll { scrollbar-size-vertical: 1; }
    """


class Splitter(Static):
    """A full-height drag handle between panels.

    Drag to resize `target` (a CSS selector); double-click resets to the
    stylesheet default. Pass `on_resized(target_selector, width_or_None)`
    to persist layout. `invert=True` for handles on the *left* edge of the
    panel they resize (dragging left grows it).
    """

    can_focus = False
    ALLOW_SELECT = False  # a drag here resizes; it must not start text selection

    DEFAULT_CSS = """
    Splitter { width: 1; height: 1fr; }
    Splitter:hover, Splitter.dragging { background: $kit-border; }
    """

    def __init__(
        self,
        target: str,
        invert: bool = False,
        min_width: int = 16,
        max_width: int = 100,
        on_resized: Callable[[str, int | None], None] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._target = target
        self._invert = invert
        self._min = min_width
        self._max = max_width
        self._on_resized = on_resized
        self._drag_x: int | None = None
        self._start_w: int = 0

    def on_mouse_down(self, event) -> None:
        # outer_size, not size: `size` is the content box, so bordered
        # targets would drift by the border width every drag
        self._drag_x = event.screen_x
        self._start_w = self.app.query_one(self._target).outer_size.width
        self.capture_mouse()
        self.add_class("dragging")

    def on_mouse_move(self, event) -> None:
        if self._drag_x is None:
            return
        delta = event.screen_x - self._drag_x
        if self._invert:
            delta = -delta
        cap = min(self._max, self.app.size.width - 50)
        width = max(self._min, min(self._start_w + delta, cap))
        self.app.query_one(self._target).styles.width = width

    def on_mouse_up(self, event) -> None:
        if self._drag_x is None:
            return
        self._drag_x = None
        self.release_mouse()
        self.remove_class("dragging")
        if self._on_resized is not None:
            width = self.app.query_one(self._target).outer_size.width
            self._on_resized(self._target, width)

    def on_click(self, event) -> None:
        if getattr(event, "chain", 1) == 2:
            self.app.query_one(self._target).styles.width = None
            if self._on_resized is not None:
                self._on_resized(self._target, None)
