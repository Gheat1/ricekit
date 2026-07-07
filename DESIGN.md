# the ricekit design philosophy

Everything here was learned building [ltui](https://github.com/Gheat1/ltui).
Follow it and a new TUI feels like part of the same suite on day one.

## 1. speed is the first feature

Never make the user wait for a network you don't control.

- **Cache first**: render the last-known state from disk instantly (~50ms),
  fetch fresh data in a background worker, swap rows in silently. Show a
  small `↻ refreshing` hint in a border subtitle while it happens.
- **Mutations update the cache immediately** — what the user sees is always
  what they did, even if they quit before the refresh lands.
- **Auto-refresh** on a timer (3 min is right); skip while a modal is open
  or a mutation is in flight; always preserve the highlight and open panels.
- All IO in `@work` workers. Exclusive groups for reads that supersede each
  other (opening detail after detail); non-exclusive for mutations.

## 2. shape language

- **Rounded borders** (`border: round $kit-border`) on every panel. Titles
  live *in* the border (`border_title`), counts and status in
  `border_subtitle`. No heavy dividers, no double borders.
- Focus is shown by recoloring the border (`$kit-border-focus`), never by
  reversing video or adding decoration.
- Modals: centered box, `$kit-modal-bg` solid background, `$kit-overlay`
  dim behind, `round $kit-border-focus` border, padding `1 2`.
- Lists get `padding: 0 1` and a 1-cell scrollbar (`scrollbar-size-vertical: 1`).
- Gaps between panels are 1 cell — and that cell is a `Splitter`.

## 3. color is a role system

Two kinds of color, never mixed up:

- **Chrome** (borders, secondary text, hints) uses the shared `palette`
  roles — text/sub/dim/faint/vfaint plus blue/lav/peach/green/red/mauve.
  Chrome restyles with the theme; reference `palette.x` at render time,
  never bake values in at import time.
- **Data** (a ticket's state color, a label, a language color) comes from
  the domain and stays truecolor in every theme. Themes restyle the frame,
  not the facts.

Hierarchy in one line of text: `text` for the subject, `sub` for support,
`dim` for metadata, `faint`/`vfaint` for structure (fills, rules, dots).
One accent per row, maybe two. If everything is colored, nothing is.

## 4. the five themes

`mocha` (catppuccin warmth) · `void` (OLED black) · `onyx` (monochrome
steel) · `clear` (no background — the terminal's transparency/blur shows
through) · `system` (drawn in the terminal's own ANSI palette).

The variable contract is in `themes.py`. Rules that keep it working:

- Every theme defines **every** `kit-*` variable — a missing one crashes
  at stylesheet parse (`UnresolvedVariableError`).
- Scrollbar and selection colors are set explicitly per theme; Textual
  derives both from `primary` otherwise and they collapse into the same
  murky blue.
- `clear`/`system` need `App.ansi_color = True` (KitApp handles it) or
  Textual *emulates* `ansi_default` as solid `#0c0c0c` and you get a fake
  black instead of transparency.
- Alpha can't blend over ansi backgrounds — ansi themes use solid or
  `transparent` overlays, never `black 40%`.
- Theme pickers must **preview live** (restyle on highlight, revert on
  escape, commit on enter) — `ThemeModal` does this.

## 5. motion

One animation: **fade in, ~150ms, out_cubic** (`pop_in`). Modals and
newly-opened panels fade; nothing else moves. Re-selecting content inside
an open panel does not re-animate.

Slides are impossible anyway — `ScalarOffset` isn't animatable in
textual 8.x. Don't fight it.

## 6. icons

- Nerd-font icons for *objects and actions* (`icons.py`), always written
  as `\uXXXX` escapes in source. Raw PUA glyphs break patch tooling and
  don't render for everyone.
- Plain unicode geometry for *state* (`STATE_GLYPHS`: ◌ ○ ◐ ◑ ● ⊘) —
  consistent shapes that need no special font.
- Degrade gracefully: an icon is decoration, never the only signal.

## 7. interaction

- **Vim keys everywhere** (`NavList`, `KitScroll`: j/k/g/G) *and* full
  mouse support: everything clickable, dividers draggable, hint bars with
  `[@click=...]` markup actions.
- Footer shows the ~7 keys that matter; `?` opens the full `HelpModal`.
- First run: onboard in-app (paste a token, validate live, store it with
  `AppDirs.save_secret`), then a one-time welcome card (`welcomed` flag in
  state). Never dump a new user into an empty screen with an error toast.
- Group headers in lists are `disabled=True` options — navigation skips
  them free of charge.
- Persist everything the user shaped: theme, layout widths, toggles, last
  context. `AppDirs.save_state` merges patches so features can't clobber
  each other.

## 8. sharp edges (the appendix that saves you a day each)

| gotcha | rule |
| --- | --- |
| `App.CSS` as f-string | double the braces: `{{ }}` |
| stylesheet parses before themes register | `KitApp.get_css_variables` injects `kit-*` defaults — keep it |
| `widget.size` | is the **content** box; use `outer_size` when measuring bordered widgets |
| empty `Static` | auto-height = 1; splitters/handles need `height: 1fr` |
| dynamic children in a scroll container | the container needs `height: auto` or scrolling stops before the end |
| drag handles | set `ALLOW_SELECT = False` or drags start text selection |
| `_auto_refresh` | reserved attribute on every DOMNode — name your method something else |
| `loading = True` | steals focus to the next focusable when it clears — refocus explicitly |
| fresh `OptionList` | `highlighted` is `None`; set it after populating or Enter does nothing |
| testing mouse features | call nothing directly — drive `pilot._post_mouse_events` so hit-testing runs |
| headless testing | `App.run_test()` + a mocked data layer; screenshot SVGs for visual review |
