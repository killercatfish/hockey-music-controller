# Hockey Stoppage Music Controller - Quick Start Guide

## Overview
This application controls Apple Music during hockey game stoppages. It features a large GOAL button, playlist shuffling, and keyboard shortcuts for quick operation.

## Prerequisites
- **Mac** with macOS (tested on macOS 10.14+)
- **Apple Music** app installed and running
- **Apple Music subscription** with songs added to your library
- **Python 3** (pre-installed on Mac)

## Installation

### Step 1: Download the Application
Save the `hockey_music_controller.py` file to your Mac (e.g., in your Documents folder or Desktop).

### Step 2: Make it Executable
Open Terminal and run:
```bash
chmod +x ~/Desktop/hockey_music_controller.py
```
(Adjust the path if you saved it elsewhere)

### Step 3: First Run
Run the application:
```bash
python3 ~/Desktop/hockey_music_controller.py
```

## Initial Setup

### 1. Set Your Goal Song
This is the song that plays when you press the GOAL button.

**Steps:**
1. Open the Music app
2. Find the exact name of your goal song (e.g., "Chelsea Dagger" or "Rock and Roll Part 2")
3. In the Hockey Music Controller, click **"Set from Library"** next to "Goal Song"
4. Type the EXACT song name (must match exactly)
5. Click OK

**Pro Tip:** If the song name is tricky, you can:
- Right-click the song in Music app → Get Info → copy the exact name
- Or just type carefully!

### 2. Load Your Stoppage Playlist

**Steps:**
1. In the Music app, create a playlist with all your stoppage-time music (if you haven't already)
2. Name it something like "Hockey Stoppages"
3. In the Hockey Music Controller:
   - Click **"Load Playlists"** button
   - Select your playlist from the dropdown
   - Click **"Load Playlist Tracks"**
4. Your songs will appear in the list below!

### 3. Shuffle the Playlist (Optional)
- Click **"Shuffle"** to randomize the order
- Drag and drop songs to manually reorder them
- Click **"Reset Order"** to return to original order

## During the Game - Quick Reference

### Large Buttons (Mouse Control)
- **⚽ GOAL! ⚽** (Yellow button) - Plays your goal song instantly
- **⏯ Play/Pause** - Start/stop music
- **⏹ Stop** - Completely stop playback
- **⏭ Next** - Skip to next song

### Keyboard Shortcuts (Hands-Free!)
Perfect for when you're running the scoreboard:
- **SPACEBAR** - Play/Pause
- **G** - Play GOAL song
- **N** - Next song
- **S** - Stop

### Playing Your Playlist
1. **Shuffle it** (or reorder manually by dragging)
2. Click **"Play from Top"** - starts playing from the first song in your custom order
3. Music app will continue through the list in that order
4. Use **Next** button or **N** key to skip songs

### Double-Click to Play
Double-click any song in the list to jump directly to it!

## Tips for Game Day

### Before the Game:
1. Open Music app (must be running)
2. Launch Hockey Music Controller
3. Verify your goal song works (click the GOAL button)
4. Shuffle your stoppage playlist
5. Position the window where you can see it

### During Stoppages:
- Click **Play/Pause** or press **SPACEBAR** to start music
- Press **G** immediately when a goal is scored
- Use **N** to skip songs you don't want
- Press **SPACEBAR** or click **Stop** when play resumes

### Window Management:
- Keep the window on top of other applications
- On macOS: You can set it to "Always on Top" by:
  - Opening Mission Control
  - Dragging to its own desktop space
  - OR use a third-party app like "Afloat" for always-on-top

## Troubleshooting

### "Could not play goal song"
- Make sure the song name is EXACTLY as it appears in Music app
- Check that the song is in your library (not just in the catalog)
- Ensure Music app is running

### "Could not load playlists"
- Open the Music app
- Make sure it's fully loaded (not just starting up)
- Try clicking "Load Playlists" again

### Playlist doesn't load
- Verify the playlist exists in Music app
- Check that the playlist has songs in it
- Make sure the songs are actually downloaded/available

### Music won't play
- Check Music app volume
- Verify your Mac's audio output is working
- Make sure Music app isn't in an error state

### Keyboard shortcuts don't work
- Click inside the Hockey Music Controller window to focus it
- Don't have text fields selected when pressing shortcuts

## Advanced Features

### Saving Your Setup
Your configuration automatically saves:
- Goal song choice
- Selected playlist
- Last shuffled order

It remembers everything when you close and reopen!

### Creating Multiple Playlists
Create different playlists for different situations:
- "Hockey Stoppages - Rock"
- "Hockey Stoppages - Mixed"
- "Hockey Stoppages - Clean" (family-friendly)

Switch between them using the dropdown!

### Manual Playlist Ordering
Instead of shuffling randomly:
1. Load your playlist
2. Drag songs up/down to create your perfect order
3. Save by just leaving it (it remembers)

## Technical Notes

### Configuration File Location
Settings are saved to: `~/hockey_music_config.json`

You can edit this file manually if needed.

### AppleScript Backend
This app uses AppleScript to control Music app, which means:
- ✅ Works with Apple Music subscription
- ✅ No need for local files
- ✅ Full access to your library
- ⚠️ Music app must be running
- ⚠️ Only songs in YOUR library (not entire Apple Music catalog)

### Adding Songs to Library
To use songs with this app, they must be in your library:
1. Find song in Apple Music
2. Click the "+" or "Add" button
3. It's now in your library and accessible to this app!

## Quick Start Checklist

- [ ] Music app is open
- [ ] Python script is running
- [ ] Goal song is configured and tested
- [ ] Stoppage playlist is loaded
- [ ] Playlist is shuffled (if desired)
- [ ] Volume is set appropriately
- [ ] Window is positioned for easy access
- [ ] You know the keyboard shortcuts (SPACE, G, N, S)

## Getting Help

### Common Questions

**Q: Can I use this without an Apple Music subscription?**
A: Yes! As long as you have music in your Music library (purchased, imported, or from Apple Music).

**Q: Will this work with Spotify?**
A: No, this is specifically for Apple Music. A Spotify version would require different code.

**Q: Can I automate starting at faceoffs?**
A: Not directly, but the keyboard shortcuts make it very fast to start music.

**Q: Does the goal song interrupt the current song?**
A: Yes! Pressing the GOAL button immediately switches to your goal song.

---

## Support
This is a custom script. For issues:
1. Check that Music app is running and responsive
2. Verify song/playlist names are exact matches
3. Restart both the script and Music app if needed

Enjoy your games! 🏒🎵
