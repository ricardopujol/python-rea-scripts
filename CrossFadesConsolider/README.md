# CrossFadesConsolider

Finds chains of overlapping (crossfading) items within the current item
selection, on a per-track basis, and consolidates each chain into a single
item via REAPER's built-in **Glue** action. Non-overlapping items in the
selection are left untouched.

## Behaviour

On run, you are asked:

> Cut each consolidated item at the midpoint of the original crossfade(s)?

- **Yes** — after gluing, the resulting item is split at each original
  crossfade midpoint. Any auto-crossfade that REAPER would normally create
  at a split is zeroed, so the cut is clean.
- **No** — each chain stays as one glued item.
- **Cancel** — aborts without modifying the project.

## Typical use

Cleaning up dialogue tracks where overlapping takes have been manually
crossfaded and you want to bake the crossfades into solid clips
(optionally re-splitting at the boundaries so you keep per-line
editability).

## Installation

1. Make sure Python support is enabled in REAPER:
   **Preferences → Plug-ins → ReaScript** and point REAPER at your Python install.
2. In REAPER open **Actions → Show action list**.
3. Click **New action → Load ReaScript…** and pick `CrossFadesConsolider.py`.
4. Optionally assign it a shortcut or add it to a toolbar.

## Conventions

- Wrapped in `RPR_Undo_BeginBlock2` / `RPR_Undo_EndBlock2`, so a single
  Ctrl+Z reverts the whole operation.
- Refuses to run on locked items and surfaces a clear message instead of
  silently skipping them.
- UI refresh is suspended during batch work to avoid visible flicker.
