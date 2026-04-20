# python-rea-scripts

A small collection of Python scripts for REAPER, aimed at speeding up
post-production tasks on dialogue and recorded sessions.

All scripts use ReaScript's Python API (`reaper_python`). They are designed
to be wrapped in a single undo step each and to fail safely when nothing is
selected or when the selection is invalid.

## Installation

1. Make sure Python support is enabled in REAPER: **Preferences → Plug-ins → ReaScript** and point REAPER at your Python install.
2. In REAPER open **Actions → Show action list**.
3. Click **New action → Load ReaScript…** and pick the `.py` file.
4. Optionally assign it a shortcut or add it to a toolbar.

## Scripts

### `CrossFadesConsolider.py`

Finds chains of overlapping (crossfading) items within the current item
selection, on a per-track basis, and consolidates each chain into a single
item via REAPER's built-in **Glue** action. Non-overlapping items in the
selection are left untouched.

On run, you are asked:

> Cut each consolidated item at the midpoint of the original crossfade(s)?

- **Yes** — after gluing, the resulting item is split at each original
  crossfade midpoint. Any auto-crossfade that REAPER would normally create
  at a split is zeroed, so the cut is clean.
- **No** — each chain stays as one glued item.
- **Cancel** — aborts without modifying the project.

Typical use: cleaning up dialogue tracks where overlapping takes have been
manually crossfaded and you want to bake the crossfades into solid clips
(optionally re-splitting at the boundaries so you keep per-line editability).

### `DialogueSpacer.py`

Takes a selection of clips on a single track, asks for a gap in
milliseconds, and:

- Shifts each selected clip to the right by an accumulating gap so existing
  spacing between clips is preserved.
- Applies a 100 ms fade-in and fade-out to each clip to avoid abrupt cuts.
- Shifts any unselected items that sit to the right of the last selected
  clip so their distance to it is preserved.

Typical use: after Dynamic Split has cut a voice-acting session into
tightly-packed individual clips, this gives them natural breathing room in
one pass.

## Conventions

- Every script wraps its work in `RPR_Undo_BeginBlock2` / `RPR_Undo_EndBlock2`,
  so a single Ctrl+Z reverts the whole operation.
- Scripts refuse to run on locked items and surface a clear message instead
  of silently skipping them.
- UI refresh is suspended during batch work where it would otherwise cause
  visible flicker.
