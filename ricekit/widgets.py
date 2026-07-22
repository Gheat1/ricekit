"""Reusable widgets: vim-navigable lists, drag-to-resize splitters, an
overflow-safe footer, motion."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from textual import events
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.widget import Widget
from textual.widgets import Footer, OptionList, Static

if TYPE_CHECKING:
    from textual.screen import Screen


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


class KitFooter(Footer):
    """A `Footer` that guarantees zero horizontal overflow.

    DESIGN.md's doctrine is "Footer shows the ~7 keys that matter" — every
    app hand-picks which of its own `Binding`s get `show=True` and hopes
    the count and the terminal width cooperate. Stock `Footer` is a plain
    `ScrollableContainer` with an invisible scrollbar
    (`scrollbar-size: 0 0`), so when they don't cooperate the excess just
    scrolls off screen with no visual indication anything is missing.

    This subclass composes exactly like stock `Footer` — same children,
    same CSS, `compact=True` by default instead of `False` — then, once
    layout is known (on mount and on every resize), measures the real
    arranged width of its children against the available width. If it
    doesn't fit, it hides (never removes) trailing children in DOM order —
    the ones from bindings declared latest in `BINDINGS`, the same
    priority stock `Footer` already renders in — one at a time, until the
    rest fits. Widening the terminal reveals hidden keys again; nothing is
    ever a one-way hide. The docked command-palette key is budgeted for
    but is never itself a trim candidate.

    This does not try to show more than the app marked `show=True` — it
    only ever hides. An app that already fits inside ~7 keys should see
    this do nothing at any reasonable width.
    """

    def __init__(
        self,
        *children: Widget,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
        show_command_palette: bool = True,
        compact: bool = True,
    ) -> None:
        super().__init__(
            *children,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
            show_command_palette=show_command_palette,
            compact=compact,
        )

    def on_mount(self) -> None:
        super().on_mount()
        self.call_after_refresh(self._enforce_no_overflow)

    def on_resize(self, event: events.Resize) -> None:
        self._enforce_no_overflow()

    def bindings_changed(self, screen: Screen) -> None:
        # Fires on mount (once bindings are known) and whenever the active
        # bindings change; the base class recomposes after a refresh — chain
        # our check onto the same refresh so it sees the real children.
        super().bindings_changed(screen)
        self.call_after_refresh(self._enforce_no_overflow)

    def _enforce_no_overflow(self) -> None:
        """Trim trailing flow children until nothing overflows.

        `self.arrange()` gives a real `DockArrangeResult` computed from the
        current DOM — the same math Textual itself uses to derive
        `virtual_size`/`max_scroll_x` — without waiting on the reactive
        pipeline to catch up, so this can run synchronously in a tight
        loop. The arrangement cache is keyed on child count, not on
        `display`, so it has to be cleared by hand after every toggle.
        """
        if not self.is_mounted or not self.is_attached:
            return
        size = self.size
        if size.width <= 0:
            return

        # Only children in normal flow are trim candidates — the docked
        # command-palette key is a fixed fixture, budgeted for below but
        # never hidden.
        candidates = [child for child in self.children if child.styles.dock == "none"]
        if not candidates:
            return

        # Un-hide everything first: this is what lets a resize back to a
        # wider terminal bring previously-hidden keys back, instead of
        # leaving them hidden forever.
        if any(not child.display for child in candidates):
            for child in candidates:
                child.display = True
            self._clear_arrangement_cache()

        # Hide from the end — lowest priority, latest in BINDINGS — one at
        # a time, re-measuring after each, until the rest fits.
        for child in reversed(candidates):
            self._clear_arrangement_cache()
            if self.arrange(size).total_region.width <= size.width:
                return
            child.display = False
        self._clear_arrangement_cache()
