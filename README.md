# python-rea-scripts

A small collection of Python scripts for REAPER, aimed at speeding up
post-production tasks on dialogue and recorded sessions.

All scripts use ReaScript's Python API (`reaper_python`). They are designed
to be wrapped in a single undo step each and to fail safely when nothing is
selected or when the selection is invalid.

## Scripts

Each script lives in its own folder with its own README:

- **[CrossFadesConsolider/](./CrossFadesConsolider)** — glue overlapping
  item chains into single clips (optionally re-split at original crossfade
  midpoints).
- **[DialogueSpacer/](./DialogueSpacer)** — space a selection of clips by
  a user-chosen gap while preserving relative spacing and fades.

## Installation (common)

1. Make sure Python support is enabled in REAPER:
   **Preferences → Plug-ins → ReaScript** and point REAPER at your Python install.
2. In REAPER open **Actions → Show action list**.
3. Click **New action → Load ReaScript…** and pick the `.py` file inside
   the script's folder.
4. Optionally assign it a shortcut or add it to a toolbar.

## Conventions

- Every script wraps its work in `RPR_Undo_BeginBlock2` / `RPR_Undo_EndBlock2`,
  so a single Ctrl+Z reverts the whole operation.
- Scripts refuse to run on locked items and surface a clear message instead
  of silently skipping them.
- UI refresh is suspended during batch work where it would otherwise cause
  visible flicker.
