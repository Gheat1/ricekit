"""ricekit — a developer's TUI suite for Textual.

The themes, widgets, modals, icons, and design rules extracted from
building ltui (https://github.com/Gheat1/ltui): everything a fast,
clean, rice-friendly terminal app needs, minus the app.

    from ricekit import KitApp, palette, icons
    from ricekit.widgets import NavList, Splitter, KitScroll, pop_in
    from ricekit.modals import PickerModal, ThemeModal, HelpModal
    from ricekit.storage import AppDirs

See DESIGN.md for the philosophy and the sharp edges.
"""

from __future__ import annotations

__version__ = "0.1.0"

from ricekit import icons
from ricekit.app import KitApp
from ricekit.palette import Palette, palette
from ricekit.storage import AppDirs
from ricekit.themes import KIT_THEMES, KIT_THEME_NAMES

__all__ = [
    "KitApp",
    "Palette",
    "palette",
    "icons",
    "AppDirs",
    "KIT_THEMES",
    "KIT_THEME_NAMES",
    "__version__",
]
