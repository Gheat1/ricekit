"""Curated nerd-font icons, written as \\uXXXX escapes so source stays ASCII-safe.

Never string-match raw private-use-area glyphs in tooling: PUA bytes do not
round-trip reliably through editors and patch scripts. Escapes always do.
"""

from __future__ import annotations

from rich.text import Text


# people & actions
USER = "\uf007"
USERS = "\uf0c0"
CHECK = "\uf00c"
CHECK_CIRCLE = "\uf058"
CROSS_CIRCLE = "\uf057"
PLUS = "\uf067"
PENCIL = "\uf040"
TRASH = "\uf1f8"

# state & alerts
WARN = "\uf071"
BAN = "\uf05e"
MINUS_CIRCLE = "\uf056"  # blocked
EXCLAIM_CIRCLE = "\uf06a"  # blocking
INFO_CIRCLE = "\uf05a"

# objects
TAG = "\uf02b"
COMMENT = "\uf075"
CLOCK = "\uf017"
CALENDAR = "\uf073"
BRANCH = "\uf126"
LINK = "\uf0c1"
EXTERNAL = "\uf08e"
LIST = "\uf03a"
STAR = "\uf005"
KEYBOARD = "\uf11c"
GEAR = "\uf013"
PLUG = "\uf1e6"
PAINTBRUSH = "\uf1fc"
SEARCH = "\uf002"
FILTER = "\uf0b0"
REFRESH = "\uf021"
LEVEL_UP = "\uf148"  # parent / up the tree
SITEMAP = "\uf0e8"  # children / sub-items

# workflow-state circles (plain unicode: consistent geometry, no font needed)
STATE_GLYPHS = {
    "triage": "\u25ce",     # circled ring
    "backlog": "\u25cc",    # dotted circle
    "unstarted": "\u25cb",  # empty circle
    "started": "\u25d0",    # half circle
    "review": "\u25d1",     # other half
    "completed": "\u25cf",  # full circle
    "canceled": "\u2298",   # slashed circle
}

BULLET = "\u25cf"
DOT_SEP = " \u00b7 "


def bars(lit: int, on: str, off: str, total: int = 3) -> Text:
    """Mini bar gauge — e.g. priority levels, capacity, progress."""
    chars = "\u2582\u2584\u2586\u2587\u2588"[:total]
    t = Text()
    for i, ch in enumerate(chars):
        t.append(ch, style=on if i < lit else off)
    return t
