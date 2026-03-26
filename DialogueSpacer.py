# DialogueSpacer.py
# Selects clips on a single track, asks for a gap in milliseconds, then:
#   - Shifts each clip right by an accumulating gap (preserving existing spacing)
#   - Extends each clip 100 ms on both sides to expose natural ambience/breath
#   - Adjusts the take source offset so the audio content does not drift
#   - Applies 100 ms fade-in and fade-out to each clip
# The entire operation is wrapped in one undo block

from reaper_python import *


def main():
    RPR_Undo_BeginBlock2(0)

    # --- Guard: nothing selected ---
    num_sel_items = RPR_CountSelectedMediaItems(0)
    if num_sel_items == 0:
        RPR_MB(
            "Please select the clip or clips that need to be spaced out.",
            "No Items Selected",
            0,
        )
        return

    # --- Collect selected items and enforce single-track selection ---
    first_track = None
    items = []

    for i in range(num_sel_items):
        item = RPR_GetSelectedMediaItem(0, i)

        # Enforce that every selected clip lives on the same track
        track = RPR_GetMediaItemTrack(item)
        if first_track is None:
            first_track = track
        elif track != first_track:
            RPR_MB("Can Only Select Clips on the same Track", "Error", 0)
            return

        # Guard: warn if any selected item is locked
        is_locked = RPR_GetMediaItemInfo_Value(item, "C_LOCK")
        if is_locked > 0:
            RPR_MB(
                "Locked items detected in your selection. Please unlock them before proceeding.",
                "Locked Items Warning",
                0,
            )
            return

        # Store the item's original position and length using strict boundaries
        pos = RPR_GetMediaItemInfo_Value(item, "D_POSITION")
        length = RPR_GetMediaItemInfo_Value(item, "D_LENGTH")
        items.append({"pos": pos, "length": length, "item": item})

    # --- Ask the user for the extra gap time in milliseconds ---
    res, title, num, caps, vals, max_len = RPR_GetUserInputs(
        "Add Silence Gap", 1, "Gap Time (ms):", "500", 512
    )
    if not res:
        return  # User cancelled the dialog

    try:
        gap_ms = float(vals)
    except ValueError:
        RPR_MB("Please enter a valid numeric value for the gap time.", "Invalid Input", 0)
        return

    # Convert the user-supplied gap from milliseconds to seconds
    gap_sec = gap_ms / 1000.0

    # Sort items chronologically so we always process left-to-right
    items.sort(key=lambda x: x["pos"])

    # 100 ms pad applied to both sides of every clip for breath/ambience and fades
    pad_sec = 0.1

    # --- Process each clip ---
    for index, p_item in enumerate(items):

        # Shift this clip right by index * gap so the gap accumulates progressively:
        # clip 0 moves 0x gap (anchor), clip 1 moves 1x gap, clip 2 moves 2x gap, etc.
        shifted_pos = p_item["pos"] + (index * gap_sec)

        # Extend the clip 100 ms to the left and 100 ms to the right
        final_pos = shifted_pos - pad_sec
        final_length = p_item["length"] + (2 * pad_sec)

        RPR_SetMediaItemInfo_Value(p_item["item"], "D_POSITION", final_pos)
        RPR_SetMediaItemInfo_Value(p_item["item"], "D_LENGTH", final_length)

        # Compensate the take source offset so the underlying audio does not drift
        # when we extend the left edge of the item boundary
        take = RPR_GetActiveTake(p_item["item"])
        if take:
            start_offs = RPR_GetMediaItemTakeInfo_Value(take, "D_STARTOFFS")
            RPR_SetMediaItemTakeInfo_Value(take, "D_STARTOFFS", start_offs - pad_sec)

        # Apply exact 100 ms fade-in and fade-out for smooth transitions
        RPR_SetMediaItemInfo_Value(p_item["item"], "D_FADEINLEN", pad_sec)
        RPR_SetMediaItemInfo_Value(p_item["item"], "D_FADEOUTLEN", pad_sec)

    RPR_Undo_EndBlock2(0, "Space selected dialogue items", -1)
    RPR_UpdateTimeline()


if __name__ == "__main__":
    main()
