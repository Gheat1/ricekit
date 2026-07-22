"""Regression tests for KitFooter's zero-horizontal-overflow guarantee.

tuistore shipped a Footer with 12 `show=True` bindings — nowhere near the
DESIGN.md "~7 keys" target — and at 80 columns the stock Textual `Footer`
(a plain `ScrollableContainer` with `scrollbar-size: 0 0`, i.e. an
invisible scrollbar) silently overflowed by 46 columns with no visual sign
anything was missing. tuistore's fix was a hand-tuned `show=False` pass on
five bindings — a static, per-app workaround with nothing stopping the same
mistake next time a binding gets added, in tuistore or any other app on
ricekit. These tests hold KitFooter to the invariant that fix didn't
provide: `max_scroll_x` is 0 no matter how many bindings are marked
`show=True` or how narrow the terminal gets.
"""

from __future__ import annotations

import unittest

from textual.app import App, ComposeResult
from textual.binding import Binding

from ricekit.widgets import KitFooter

WIDTHS = (40, 60, 80, 120)


async def _settle(pilot) -> None:
    """Wait for the footer to reach its steady state after a mount or resize.

    Populating the footer and then checking it for overflow is a chain of
    several `call_after_refresh` hops: the screen's bindings-updated signal
    triggers `bindings_changed`, which schedules a recompose; the recompose
    mounts the real FooterKey children; KitFooter chains its own overflow
    check onto that same refresh. `pilot.pause()` only guarantees draining
    *one* such hop, which is plenty on a fast machine but not reliably
    enough on a loaded CI runner. Pausing a few times drains the whole
    chain deterministically instead of asserting mid-flight.
    """
    for _ in range(5):
        await pilot.pause()


def _visible_flow_keys(footer: KitFooter) -> list:
    """Non-docked children currently displayed (i.e. not trimmed)."""
    return [c for c in footer.children if c.display and c.styles.dock == "none"]


def _hidden_flow_keys(footer: KitFooter) -> list:
    """Non-docked children currently trimmed (hidden, not removed)."""
    return [c for c in footer.children if not c.display and c.styles.dock == "none"]


def _docked_keys(footer: KitFooter) -> list:
    return [c for c in footer.children if c.styles.dock != "none"]


def _visible_key_displays(footer: KitFooter) -> set[str]:
    """Stable identity for a visible flow key: its key display string.

    Not widget identity — a recompose (e.g. from a bindings change) mounts
    brand-new FooterKey instances for the same bindings, so comparing raw
    widgets across two separate settle points would spuriously "differ"
    even when the same keys are showing.
    """
    return {c.key_display for c in _visible_flow_keys(footer)}


def make_app(n: int, show_command_palette: bool = True) -> type[App]:
    """Build a throwaway App class with `n` distinct, always-shown bindings."""

    bindings = [
        Binding(str(i) if i < 10 else chr(ord("a") + i - 10), f"act{i}", f"action {i}", show=True)
        for i in range(n)
    ]

    class FooterHarness(App):
        BINDINGS = bindings

        def compose(self) -> ComposeResult:
            yield KitFooter(show_command_palette=show_command_palette)

    for i in range(n):
        setattr(FooterHarness, f"action_act{i}", lambda self: None)

    return FooterHarness


class SmallBindingSetTest(unittest.IsolatedAsyncioTestCase):
    """A well-under-budget binding set (~6 keys) needs no trimming at all."""

    async def test_fits_without_hiding_anything(self) -> None:
        app_cls = make_app(6)
        app = app_cls()
        async with app.run_test(size=(80, 24)) as pilot:
            await _settle(pilot)
            footer = app.query_one(KitFooter)

            self.assertEqual(footer.max_scroll_x, 0)
            self.assertEqual(len(_hidden_flow_keys(footer)), 0)
            self.assertEqual(len(_visible_flow_keys(footer)), 6)


class ExcessiveBindingSetTest(unittest.IsolatedAsyncioTestCase):
    """Far more bindings than could ever fit — the actual tuistore scenario,
    exaggerated. Zero overflow must hold at every width tested."""

    async def test_never_overflows_across_widths(self) -> None:
        app_cls = make_app(24)
        for width in WIDTHS:
            with self.subTest(width=width):
                app = app_cls()
                async with app.run_test(size=(width, 24)) as pilot:
                    await _settle(pilot)
                    footer = app.query_one(KitFooter)

                    self.assertEqual(
                        footer.max_scroll_x,
                        0,
                        f"footer overflowed at width={width}",
                    )
                    # 24 bindings can't possibly fit even at 120 columns —
                    # something must have been trimmed everywhere.
                    self.assertGreater(len(_hidden_flow_keys(footer)), 0)

    async def test_narrower_width_hides_at_least_as_much(self) -> None:
        app_cls = make_app(24)
        visible_counts = {}
        for width in WIDTHS:
            app = app_cls()
            async with app.run_test(size=(width, 24)) as pilot:
                await _settle(pilot)
                footer = app.query_one(KitFooter)
                visible_counts[width] = len(_visible_flow_keys(footer))

        ordered = sorted(visible_counts)
        for narrower, wider in zip(ordered, ordered[1:]):
            self.assertLessEqual(
                visible_counts[narrower],
                visible_counts[wider],
                f"width={narrower} showed more keys than width={wider}",
            )


class ResizeRevealTest(unittest.IsolatedAsyncioTestCase):
    """Hiding is not one-way: widening the terminal must bring back keys
    that were trimmed at a narrower size, once they fit again."""

    async def test_widening_reveals_previously_hidden_keys(self) -> None:
        app_cls = make_app(24)
        app = app_cls()
        async with app.run_test(size=(40, 24)) as pilot:
            await _settle(pilot)
            footer = app.query_one(KitFooter)
            self.assertEqual(footer.max_scroll_x, 0)
            narrow_visible = len(_visible_flow_keys(footer))
            narrow_hidden = len(_hidden_flow_keys(footer))
            self.assertGreater(narrow_hidden, 0)

            await pilot.resize_terminal(120, 24)
            await _settle(pilot)

            self.assertEqual(footer.max_scroll_x, 0)
            wide_visible = len(_visible_flow_keys(footer))
            self.assertGreater(wide_visible, narrow_visible)

    async def test_round_trip_narrow_wide_narrow(self) -> None:
        """Shrink, grow, shrink back — the same keys should be hidden as
        the first time at that width, not accumulate stale state."""
        app_cls = make_app(24)
        app = app_cls()
        async with app.run_test(size=(40, 24)) as pilot:
            await _settle(pilot)
            footer = app.query_one(KitFooter)
            first_pass_visible = _visible_key_displays(footer)

            await pilot.resize_terminal(120, 24)
            await _settle(pilot)
            self.assertEqual(footer.max_scroll_x, 0)

            await pilot.resize_terminal(40, 24)
            await _settle(pilot)
            self.assertEqual(footer.max_scroll_x, 0)
            second_pass_visible = _visible_key_displays(footer)

            self.assertEqual(first_pass_visible, second_pass_visible)


class CommandPaletteKeyTest(unittest.IsolatedAsyncioTestCase):
    """The docked command-palette key is a fixed fixture: always present
    when enabled, its width counted against the budget, never itself a
    trim candidate."""

    async def test_command_palette_key_survives_heavy_trimming(self) -> None:
        app_cls = make_app(24, show_command_palette=True)
        app = app_cls()
        async with app.run_test(size=(40, 24)) as pilot:
            await _settle(pilot)
            footer = app.query_one(KitFooter)

            self.assertEqual(footer.max_scroll_x, 0)
            docked = _docked_keys(footer)
            self.assertEqual(len(docked), 1)
            self.assertTrue(docked[0].display)
            self.assertGreater(len(_hidden_flow_keys(footer)), 0)

    async def test_disabled_command_palette_leaves_no_docked_key(self) -> None:
        app_cls = make_app(24, show_command_palette=False)
        app = app_cls()
        async with app.run_test(size=(40, 24)) as pilot:
            await _settle(pilot)
            footer = app.query_one(KitFooter)

            self.assertEqual(footer.max_scroll_x, 0)
            self.assertEqual(len(_docked_keys(footer)), 0)

    async def test_command_palette_width_is_budgeted_not_overlapped(self) -> None:
        """Regression for the actual failure mode: a docked key with real
        width must shrink the flow's usable budget, not be ignored."""
        app_cls = make_app(24, show_command_palette=True)
        app = app_cls()
        async with app.run_test(size=(60, 24)) as pilot:
            await _settle(pilot)
            footer = app.query_one(KitFooter)
            with_palette_visible = len(_visible_flow_keys(footer))

        app_cls_no_palette = make_app(24, show_command_palette=False)
        app2 = app_cls_no_palette()
        async with app2.run_test(size=(60, 24)) as pilot:
            await _settle(pilot)
            footer2 = app2.query_one(KitFooter)
            without_palette_visible = len(_visible_flow_keys(footer2))

        self.assertLessEqual(with_palette_visible, without_palette_visible)


class KitFooterDefaultsTest(unittest.IsolatedAsyncioTestCase):
    """KitFooter matches Footer's constructor but flips the compact default,
    per DESIGN.md's minimalist doctrine."""

    async def test_compact_defaults_true(self) -> None:
        footer = KitFooter()
        self.assertTrue(footer.compact)

    async def test_compact_can_still_be_overridden(self) -> None:
        footer = KitFooter(compact=False)
        self.assertFalse(footer.compact)


if __name__ == "__main__":
    unittest.main()
