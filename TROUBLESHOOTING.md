# Troubleshooting Guide - Hockey Music Controller

## Quick Diagnostics

### Is Everything Working?
Run through this checklist:
- [ ] Music app is open and responsive
- [ ] You can manually play songs in Music app
- [ ] Python script launches without errors
- [ ] Goal song name is spelled EXACTLY as in Music app
- [ ] Playlist name is spelled EXACTLY as in Music app
- [ ] Songs are in your library (not just Apple Music catalog)

## Common Issues & Solutions

### 1. "Could not play goal song: [song name]"

**Symptoms:**
- Error message when clicking GOAL button
- Nothing plays when pressing 'G'

**Causes & Solutions:**

**A. Song name doesn't match exactly**
```
Problem: You typed "chelsea dagger" but it's actually "Chelsea Dagger"
Solution: 
1. Open Music app
2. Find the song
3. Right-click → Get Info → Details tab
4. Copy the EXACT name from "Song Name" field
5. Paste into Hockey Music Controller
```

**B. Song not in library**
```
Problem: Song is in Apple Music but not added to YOUR library
Solution:
1. Search for the song in Music app
2. Click the "+" button or "Add to Library"
3. Wait a few seconds for it to sync
4. Try again in Hockey Music Controller
```

**C. Special characters in song name**
```
Problem: Song has quotes, apostrophes, or special characters
Examples: "Don't Stop Believin'" or "Song (Live Version)"
Solution: Type them exactly as shown, including all punctuation
```

---

### 2. "Could not load playlists"

**Symptoms:**
- Error when clicking "Load Playlists"
- Dropdown remains empty

**Solutions:**

**A. Music app isn't fully loaded**
```
1. Close Music app completely (Cmd+Q)
2. Wait 5 seconds
3. Open Music app
4. Wait for it to fully load (see your library)
5. Try "Load Playlists" again
```

**B. AppleScript permission issue**
```
macOS Catalina and later may need permission:
1. Open System Settings/Preferences
2. Go to Security & Privacy → Privacy
3. Click "Automation"
4. Look for "Python" or "Terminal"
5. Ensure "Music" is checked
6. Restart the app
```

**C. No playlists exist**
```
If you have no playlists:
1. Open Music app
2. File → New → Playlist
3. Name it (e.g., "Hockey Stoppages")
4. Add songs to it
5. Try loading again
```

---

### 3. Playlist Loads But Won't Play

**Symptoms:**
- Tracks appear in list
- Clicking or pressing keys does nothing
- No sound

**Solutions:**

**A. Track indexing issue**
```
Problem: Playlist was modified in Music app
Solution:
1. Click "Load Playlist Tracks" again to refresh
2. Try "Play from Top"
```

**B. Music app volume is muted**
```
Check:
1. Music app's own volume slider
2. Mac system volume
3. Output device (check Sound settings)
```

**C. Songs not available offline**
```
For Apple Music subscribers:
1. Some songs might not be downloaded
2. Check your internet connection
3. In Music app, click the cloud download icon
4. Wait for songs to download
```

---

### 4. Keyboard Shortcuts Not Working

**Symptoms:**
- Pressing G, N, S, or SPACE does nothing
- Buttons work but keys don't

**Solutions:**

**A. Window not focused**
```
Solution: Click anywhere inside the Hockey Music Controller window
```

**B. Text field is selected**
```
Problem: Cursor is blinking in Goal Song or Playlist field
Solution: Click outside the text field (on the window background)
```

**C. Another app is capturing keys**
```
Check if other apps are using these shortcuts:
1. Close other music apps
2. Disable gaming overlays
3. Check System Settings → Keyboard → Shortcuts
```

---

### 5. Application Won't Start

**Symptoms:**
- Double-clicking does nothing
- Error in Terminal

**Solutions:**

**A. Python not found**
```bash
# Check Python version
python3 --version

# Should show: Python 3.x.x
# If not, reinstall Python from python.org
```

**B. Permission denied**
```bash
# Make executable
chmod +x hockey_music_controller.py

# Run with Python explicitly
python3 hockey_music_controller.py
```

**C. Tkinter not available**
```bash
# Test if tkinter is available
python3 -c "import tkinter; print('OK')"

# If error, reinstall Python from python.org
# (Not homebrew - use official installer)
```

---

### 6. Drag-and-Drop Not Working

**Symptoms:**
- Can't reorder songs by dragging
- Songs jump back to original position

**Solutions:**

**A. Single-click and drag**
```
Technique:
1. Click on a song (don't double-click)
2. Hold mouse button down
3. Drag up or down
4. Release
```

**B. List is locked**
```
Try:
1. Click "Reset Order"
2. Try dragging again
3. If still stuck, reload the playlist
```

---

### 7. "No track playing" Shows Continuously

**Symptoms:**
- Status always says "No track playing"
- But music IS playing in Music app

**Solutions:**

**A. Music app stuck**
```
1. Stop all playback in Music app
2. Close Music app (Cmd+Q)
3. Reopen Music app
4. Restart Hockey Music Controller
```

**B. Status update timing**
```
The status updates every 1 second
Wait 1-2 seconds to see if it updates
```

---

### 8. Shuffle Produces Same Order

**Symptoms:**
- Clicking Shuffle multiple times gives same order
- Order doesn't seem random

**Solutions:**

This is normal! Python's random.shuffle() can produce similar results.

**To get different orders:**
1. Click Shuffle multiple times
2. Manually drag a few songs between shuffles
3. Or just manually arrange the order you want

---

### 9. Goal Song Plays Wrong Track

**Symptoms:**
- GOAL button plays a different song than configured
- Song name is correct but wrong song plays

**Solutions:**

**A. Multiple songs with same name**
```
Problem: Two songs named "Jump"
Solution:
1. Rename one in Music app (add artist name)
2. Example: "Jump (Van Halen)" vs "Jump (Other Artist)"
3. Update goal song name in controller
```

**B. Song in multiple locations**
```
Music might have duplicates:
1. Search for the song in Music app
2. Check if it appears multiple times
3. Delete duplicates
4. Keep only one version
```

---

### 10. Config File Issues

**Symptoms:**
- Settings don't save between sessions
- Error about config file

**Solutions:**

**A. Permission issue**
```bash
# Check if file exists and is writable
ls -la ~/hockey_music_config.json

# If permission denied:
chmod 644 ~/hockey_music_config.json
```

**B. Corrupted config**
```bash
# Delete and start fresh
rm ~/hockey_music_config.json

# Restart app, it will create a new one
```

**C. Manual config edit**
```bash
# Edit config file directly
nano ~/hockey_music_config.json

# Format must be:
{
  "playlist": "Your Playlist Name",
  "goal_song": "Your Goal Song"
}

# Save: Ctrl+O, Enter, Ctrl+X
```

---

## Advanced Troubleshooting

### Testing AppleScript Directly

Open Terminal and test commands:

```bash
# Test if Music app responds
osascript -e 'tell application "Music" to get name of every playlist'

# Test playing a song
osascript -e 'tell application "Music" to play track "Song Name"'

# Test getting current track
osascript -e 'tell application "Music" to get name of current track'
```

If these commands fail, the issue is with Music app or AppleScript permissions, not the Python app.

### Checking System Requirements

```bash
# Check macOS version (should be 10.14+)
sw_vers

# Check Python version (should be 3.6+)
python3 --version

# Check if Music app is installed
ls /System/Applications/Music.app
```

### Running in Debug Mode

Modify the script to see detailed errors:

```python
# In hockey_music_controller.py
# Change run_applescript method to print errors:

def run_applescript(self, script):
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            print(f"Error: {result.stderr}")  # ADD THIS LINE
        return result.stdout.strip(), result.returncode == 0
    except Exception as e:
        print(f"Exception: {e}")  # ADD THIS LINE
        return "", False
```

Then run from Terminal to see error messages.

---

## Getting Additional Help

### Before Asking for Help

Collect this information:
1. macOS version: `sw_vers`
2. Python version: `python3 --version`
3. Error message (if any)
4. What you were trying to do
5. Whether Music app plays songs manually

### Things to Try First

1. **Restart everything**
   - Close Music app
   - Close Hockey Music Controller
   - Wait 10 seconds
   - Open Music app first
   - Then open controller

2. **Test in Music app first**
   - Can you play songs manually?
   - Does the playlist exist?
   - Are songs available/downloaded?

3. **Simplify**
   - Try a different goal song
   - Try a different playlist
   - Test with a simple playlist (3-4 songs)

4. **Check permissions**
   - System Settings → Security & Privacy
   - Look for any blocked permissions
   - Grant access to Music app

---

## Prevention Tips

### Before Every Game

1. Open Music app first
2. Verify internet connection (for Apple Music)
3. Test goal song with GOAL button
4. Do a quick test of playlist playback
5. Check system volume

### Regular Maintenance

1. Keep macOS updated
2. Keep Music library organized
3. Remove duplicate songs
4. Periodically refresh playlists
5. Test after Music app updates

### Best Practices

1. Use simple song names when possible
2. Keep playlists under 100 songs (faster loading)
3. Download songs for offline use
4. Create backup playlists
5. Test new songs before game day

---

## Still Having Issues?

If none of these solutions work:

1. **Create a minimal test case**
   - New playlist with 3 songs
   - Simple song name for goal
   - Test if that works

2. **Check system logs**
   - Console app → search for "Music"
   - Look for error messages

3. **Try system reset**
   - Restart your Mac
   - Reset Music app: Hold Option while opening Music app
   - Try controller again

Remember: The app uses AppleScript to control Music app, so anything that breaks Music app will break the controller. Always test Music app first!
