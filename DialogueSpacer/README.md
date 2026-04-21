# DialogueSpacer

Takes a selection of clips on a single track, asks for a gap in
milliseconds, and:

- Shifts each selected clip to the right by an accumulating gap so existing
  spacing between clips is preserved.
- Applies a 100 ms fade-in and fade-out to each clip to avoid abrupt cuts.
- Shifts any unselected items that sit to the right of the last selected
  clip so their distance to it is preserved.

## Typical use

After Dynamic Split has cut a voice-acting session into tightly-packed
individual clips, this gives them natural breathing room in one pass.

## Installation

1. Make sure Python support is enabled in REAPER:
   **Preferences → Plug-ins → ReaScript** and point REAPER at your Python install.
2. In REAPER open **Actions → Show action list**.
3. Click **New action → Load ReaScript…** and pick `DialogueSpacer.py`.
4. Optionally assign it a shortcut or add it to a toolbar.

## Conventions

- Wrapped in `RPR_Undo_BeginBlock2` / `RPR_Undo_EndBlock2`, so a single
  Ctrl+Z reverts the whole operation.
- Refuses to run on locked items and surfaces a clear message instead of
  silently skipping them.
- UI refresh is suspended during batch work to avoid visible flicker.
