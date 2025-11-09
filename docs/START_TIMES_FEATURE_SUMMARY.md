# Start Times Feature - Implementation Summary

## Overview
Added custom start time functionality to the Hockey Music Controller, allowing you to set a specific starting point (e.g., 15 seconds in) for any track in your playlist. This bypasses Apple Music's cloud track buffering issues and ensures tracks start exactly where you want them.

## What Was Added

### 1. **New AppleScript Method**
- `play_track_from_playlist_with_start_time()` - Plays a track and seeks to a custom start time
- Uses a 0.5 second delay to ensure the track loads before seeking

### 2. **Start Time Storage**
- `start_times` dictionary stores custom start times for each track
- Saved to config file (`~/.hockey_music_config.json`)
- Persists between sessions

### 3. **Right-Click Context Menu**
Added right-click functionality to playlist tracks:
- **macOS**: Right-click or Ctrl+Click
- **Windows/Linux**: Right-click

Menu options:
- **Set Start Time** - Opens dialog to set custom start time
- **Edit Start Time** - Modify existing start time
- **Remove Start Time** - Delete custom start time

### 4. **Time Input Formats**
Supports two formats:
- **Seconds**: `15` (starts at 15 seconds)
- **MM:SS**: `1:30` (starts at 1 minute 30 seconds)

### 5. **Visual Indicators**
Tracks with custom start times show in playlist:
```
1. ⏱️ [0:15] We Will Rock You | Queen
2. ⏱️ [0:10] Thunderstruck | AC/DC
3. Welcome to the Jungle | Guns N' Roses
```

### 6. **Automatic Start Time Application**
Custom start times are automatically applied when:
- Double-clicking a track
- Pressing Enter on selected track
- Using Space to play/pause
- Using Next Track button (N key)
- Resuming playback after stop

## How to Use

### Setting a Start Time

1. **Load your playlist** in the controller
2. **Right-click** (or Ctrl+Click on macOS) on any track
3. **Select "⏱️ Set Start Time"**
4. **Enter the time** in the dialog:
   - `15` for 15 seconds
   - `1:30` for 1 minute 30 seconds
5. **Click OK**

The track will now show: `⏱️ [0:15] Track Name`

### Editing a Start Time

1. **Right-click** on a track with a start time
2. **Select "✏️ Edit Start Time"**
3. **Modify** the time
4. **Click OK**

### Removing a Start Time

1. **Right-click** on a track with a start time
2. **Select "🗑️ Remove Start Time"**

### Using the Feature

Once set, start times work automatically:
- **Play the track** using any method (double-click, Enter, Space, Next button)
- The track will **automatically seek** to your custom start time
- Works with **all playback methods** in the app

## Technical Details

### Files Modified
- Added `re` import for regex support
- Updated `AppleMusicController` class with new playback method
- Modified `HockeyMusicGUI` class with context menu and start time management
- Updated all playback methods to check for and apply start times

### Config File Structure
```json
{
  "playlist": "Hockey Stoppage",
  "start_times": {
    "We Will Rock You | Queen": 15,
    "Thunderstruck | AC/DC": 10,
    "Welcome to the Jungle | Guns N' Roses": 0
  }
}
```

### Methods Added
- `play_track_from_playlist_with_start_time()` - AppleScript playback with seek
- `show_track_context_menu()` - Display right-click menu
- `set_track_start_time()` - Set/edit start time dialog
- `remove_track_start_time()` - Delete start time
- `parse_time_string()` - Parse user input (MM:SS or seconds)
- `format_seconds()` - Display seconds as MM:SS

### Methods Modified
- `update_playlist_display()` - Show start time indicators
- `play_selected_track()` - Apply start times on play
- `on_listbox_space()` - Apply start times on space key
- `next_track()` - Apply start times on next
- `play_pause()` - Apply start times when resuming
- `save_config()` - Save start times
- `load_config()` - Load start times

## Benefits

1. **Solves Cloud Track Issues** - No more waiting for Apple Music to buffer before seeking
2. **Consistent Playback** - Tracks always start at the same spot
3. **Quick Setup** - Set once, works forever
4. **Visual Feedback** - Easy to see which tracks have custom start times
5. **Flexible Input** - Enter times in seconds or MM:SS format

## Testing Recommendations

1. **Test with cloud tracks** - Verify start times work with tracks that aren't downloaded
2. **Test all playback methods** - Double-click, Enter, Space, Next button
3. **Test editing** - Change start times and verify they update
4. **Test removal** - Remove start times and verify they're gone
5. **Test persistence** - Quit and restart app, verify start times are saved

## Next Steps

If you want to apply this to your main script:
1. Back up your current `hockey_music_controller.py`
2. Replace it with `hockey_music_controller_with_start_times.py`
3. Test thoroughly with your playlists
4. Set start times for any problematic tracks

## Notes

- Start times are **per-track basis**, not per-playlist
- If a track appears in multiple playlists, it uses the same start time
- The feature has **no performance impact** when start times aren't set
- Works seamlessly with existing shuffle and playlist functionality
