# CrossFadesConsolider.py
# Scans the current item selection for chains of overlapping (crossfading)
# items on the same track and consolidates each chain into a single item via
# REAPER's built-in glue action. Non-overlapping selected items are left alone.
# The entire operation is wrapped in one undo block.

from reaper_python import *


# Tolerance (in seconds) for treating two nearly-equal timeline positions as
# "just touching" rather than overlapping. 1 microsecond is well below any
# meaningful audio timing and safely above float rounding noise.
OVERLAP_EPSILON = 1e-6

# REAPER native command IDs
CMD_UNSELECT_ALL_ITEMS = 40289  # Item: Unselect all items
CMD_GLUE_IGNORE_TIME_SEL = 41588  # Item: Glue items, ignoring time selection

# Win32 MessageBox type flags / return codes (used by RPR_MB)
MB_YESNOCANCEL = 3
MB_IDCANCEL = 2
MB_IDYES = 6
MB_IDNO = 7


def collect_selected_items_by_track():
    """Return {track: [ {item, pos, end}, ... ]} for the current selection.

    Returns (items_by_track, error_message). If error_message is not None the
    caller should abort and surface it to the user.
    """
    items_by_track = {}
    num_sel_items = RPR_CountSelectedMediaItems(0)

    for i in range(num_sel_items):
        item = RPR_GetSelectedMediaItem(0, i)

        if RPR_GetMediaItemInfo_Value(item, "C_LOCK") > 0:
            return None, (
                "Locked items detected in your selection. "
                "Please unlock them before proceeding."
            )

        track = RPR_GetMediaItemTrack(item)
        pos = RPR_GetMediaItemInfo_Value(item, "D_POSITION")
        length = RPR_GetMediaItemInfo_Value(item, "D_LENGTH")
        items_by_track.setdefault(track, []).append(
            {"item": item, "pos": pos, "end": pos + length}
        )

    return items_by_track, None


def find_overlap_chains(items_by_track):
    """Return a list of chains; each chain is a list of >=2 overlapping items.

    Within a track, items are sorted by start position and grouped greedily:
    an item joins the current chain if it starts before the running maximum
    end of the chain (i.e. it overlaps at least one previously-included item).
    Items that only abut (end == start) are not considered overlapping.
    """
    chains = []
    for track_items in items_by_track.values():
        track_items.sort(key=lambda x: x["pos"])
        current_chain = [track_items[0]]
        chain_end = track_items[0]["end"]

        for entry in track_items[1:]:
            if entry["pos"] < chain_end - OVERLAP_EPSILON:
                current_chain.append(entry)
                if entry["end"] > chain_end:
                    chain_end = entry["end"]
            else:
                if len(current_chain) > 1:
                    chains.append(current_chain)
                current_chain = [entry]
                chain_end = entry["end"]

        if len(current_chain) > 1:
            chains.append(current_chain)

    return chains


def midpoints_for_chain(chain):
    """Return sorted crossfade midpoints between consecutive items in `chain`.

    Midpoints are computed from the items' ORIGINAL positions/lengths, so this
    must be called before the chain is glued.
    """
    points = []
    for i in range(len(chain) - 1):
        overlap_start = chain[i + 1]["pos"]
        overlap_end = chain[i]["end"]
        if overlap_end > overlap_start + OVERLAP_EPSILON:
            points.append((overlap_start + overlap_end) / 2.0)
    points.sort()
    return points


def prompt_split_at_midpoints():
    """Ask whether to cut each consolidated item at the old crossfade midpoints.

    Returns True (yes), False (no), or None (user cancelled).
    """
    result = RPR_MB(
        "Cut each consolidated item at the midpoint of the original "
        "crossfade(s)?\n\n"
        "Yes: split where the crossfades used to be.\n"
        "No: keep each consolidated chain as a single item.",
        "Split at Crossfade Midpoints?",
        MB_YESNOCANCEL,
    )
    if result == MB_IDCANCEL:
        return None
    return result == MB_IDYES


def consolidate_chain(chain, split_points=None):
    """Select items in `chain`, glue them, and optionally split the result.

    `split_points` is an ascending list of absolute timeline positions at
    which to cut the glued item. Splits are applied left-to-right; any
    auto-crossfade that REAPER might add at the split is zeroed so the cut
    is clean.
    """
    RPR_Main_OnCommand(CMD_UNSELECT_ALL_ITEMS, 0)
    for entry in chain:
        RPR_SetMediaItemSelected(entry["item"], True)
    RPR_Main_OnCommand(CMD_GLUE_IGNORE_TIME_SEL, 0)

    if not split_points:
        return

    # After Glue, the resulting item is the only selected item.
    glued = RPR_GetSelectedMediaItem(0, 0)
    if not glued:
        return

    glued_pos = RPR_GetMediaItemInfo_Value(glued, "D_POSITION")
    glued_end = glued_pos + RPR_GetMediaItemInfo_Value(glued, "D_LENGTH")

    current = glued
    cur_start = glued_pos
    cur_end = glued_end
    for m in split_points:
        # Skip split points that don't fall strictly inside the remaining item.
        if not (cur_start + OVERLAP_EPSILON < m < cur_end - OVERLAP_EPSILON):
            continue
        right = RPR_SplitMediaItem(current, m)
        if not RPR_ValidatePtr2(0, right, "MediaItem*"):
            continue
        RPR_SetMediaItemInfo_Value(current, "D_FADEOUTLEN_AUTO", 0)
        RPR_SetMediaItemInfo_Value(right, "D_FADEINLEN_AUTO", 0)
        current = right
        cur_start = m


def main():
    RPR_Undo_BeginBlock2(0)

    if RPR_CountSelectedMediaItems(0) == 0:
        RPR_MB(
            "Please select the items you want to check for crossfades.",
            "No Items Selected",
            0,
        )
        return

    items_by_track, err = collect_selected_items_by_track()
    if err is not None:
        RPR_MB(err, "Cannot Consolidate", 0)
        return

    chains = find_overlap_chains(items_by_track)

    if not chains:
        RPR_MB(
            "No overlapping (crossfading) items were found in the selection.",
            "Nothing to Consolidate",
            0,
        )
        return

    split_choice = prompt_split_at_midpoints()
    if split_choice is None:
        return  # User cancelled; do nothing.

    # Compute midpoints now, using the ORIGINAL item positions, before any glue
    # mutates the timeline.
    chain_splits = [
        midpoints_for_chain(chain) if split_choice else None for chain in chains
    ]

    # Turn off UI refresh while we flip selections and glue multiple chains.
    RPR_PreventUIRefresh(1)
    try:
        num_chains = len(chains)
        num_items = sum(len(c) for c in chains)
        for chain, splits in zip(chains, chain_splits):
            consolidate_chain(chain, splits)
    finally:
        RPR_PreventUIRefresh(-1)

    action_desc = (
        "Consolidate crossfading items, split at midpoints"
        if split_choice
        else "Consolidate crossfading items"
    )
    RPR_Undo_EndBlock2(
        0,
        "{0} ({1} chain(s), {2} item(s))".format(action_desc, num_chains, num_items),
        -1,
    )
    RPR_UpdateTimeline()


if __name__ == "__main__":
    main()
