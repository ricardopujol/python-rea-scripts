import sys
from reaper_python import *

def msg(m):
    RPR_ShowConsoleMsg(str(m) + "\n")

def main():
    RPR_Undo_BeginBlock2(0)
    
    # 5. Check if no items selected
    num_sel_items = RPR_CountSelectedMediaItems(0)
    if num_sel_items == 0:
        RPR_MB("Please select the clip or clips that need to be spaced out.", "No Items Selected", 0)
        return

    track_set = set()
    items = []
    
    # Iterate through selected items
    for i in range(num_sel_items):
        item = RPR_GetSelectedMediaItem(0, i)
        
        # 2. Get track info correctly to ensure same track
        track = RPR_GetMediaItemTrack(item)
        track_set.add(track)
        
        # 4. Check lock status and display warning
        is_locked = RPR_GetMediaItemInfo_Value(item, "C_LOCK")
        if is_locked > 0:
            RPR_MB("Locked items detected in your selection. Please unlock them before proceeding.", "Locked Items Warning", 0)
            return
            
        # Get start position and strict length
        pos = RPR_GetMediaItemInfo_Value(item, "D_POSITION")
        length = RPR_GetMediaItemInfo_Value(item, "D_LENGTH")
        
        items.append({"pos": pos, "length": length, "item": item})

    # 2. Prevent multiple track selections
    if len(track_set) > 1:
        RPR_MB("Can Only Select Clips on the same Track", "Error", 0)
        return

    # 1. Ask for 'Gap Time' in milliseconds
    res, title, num, caps, vals, max_len = RPR_GetUserInputs("Add Silence Gap", 1, "Gap Time (ms):", "500", 512)
    if not res:
        return # User cancelled the prompt
        
    try:
        gap_ms = float(vals)
        if gap_ms < 0:
            RPR_MB("Please enter a positive number for the gap time.", "Invalid Input", 0)
            return
    except ValueError:
        RPR_MB("Please enter a valid numeric value for the gap time.", "Invalid Input", 0)
        return
        
    # Convert ms to seconds
    gap_sec = gap_ms / 1000.0

    # Sort items chronologically by their current start position
    items.sort(key=lambda x: x["pos"])
    
    # Process if there's more than one item to space
    if len(items) > 1:
        # 3. Calculate from the strict end boundary of the very first item
        prev_end = items[0]["pos"] + items[0]["length"]
        
        for p_item in items[1:]:
            # New position = EXACT previous item end position + gap time
            new_pos = prev_end + gap_sec
            
            # Move the item
            RPR_SetMediaItemInfo_Value(p_item["item"], "D_POSITION", new_pos)
            
            # Recalculate prev_end for the next iteration (using its strict end boundary)
            prev_end = new_pos + p_item["length"]

    RPR_Undo_EndBlock2(0, "Space selected dialogue items", -1)
    RPR_UpdateTimeline()

if __name__ == "__main__":
    main()
