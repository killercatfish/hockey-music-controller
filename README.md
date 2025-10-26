# Hockey Stoppage Music Controller

A Python GUI application for controlling Apple Music during hockey games. Designed for game operations personnel who need quick, reliable music control during stoppages, goals, and special situations.

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![Platform](https://img.shields.io/badge/platform-macOS-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green)

## Features

### 🎯 Special Event Buttons
- **⚽ GOAL Button** - Instant goal celebration song (Keyboard: `G`)
- **Zamboni** - Ice resurfacing music
- **2nd Zamboni** - Second period zamboni
- **Game Start** - Opening faceoff song
- **1st Intermission** - First break music
- **2nd Intermission** - Second break music
- **End of Game** - Victory/closing song
- **⚡ Power Play** - Power play situation (Keyboard: `O`)
- **🛡️ Penalty Kill** - Penalty kill situation (Keyboard: `P`)

### 🎵 Playlist Management
- Load playlists from Apple Music
- Visual shuffle and drag-to-reorder
- Arrow key navigation (⬆️⬇️)
- Double-click or Enter to play
- Space to play/stop highlighted song
- Playlist stays visible while music plays

### ⌨️ Keyboard Shortcuts
Perfect for split-second control:
- `SPACE` - Play/Pause main controls
- `G` - Play goal song
- `O` - Power play music
- `P` - Penalty kill music
- `N` - Next track (queues next song)
- `S` - Stop all playback
- `⬆️⬇️` - Navigate playlist
- `Enter` - Play highlighted song
- `Space` (in playlist) - Play/Stop highlighted

### 💾 Auto-Save Configuration
- All song assignments saved automatically
- Playlist order remembered
- Settings persist between sessions

## Screenshots

### Main Interface
![Main Interface](docs/screenshot_main.png)

### Configuration Window
![Configuration](docs/screenshot_config.png)

## Requirements

- **macOS** (10.14 or later)
- **Python 3.8+** (pre-installed on macOS)
- **Apple Music app**
- **Apple Music subscription** (or music in your library)

## Installation

### Quick Start

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/hockey-music-controller.git
cd hockey-music-controller
```

2. **Run the application**
```bash
python3 hockey_music_controller.py
```

That's it! No dependencies to install - uses only Python standard library.

### Alternative: Download Release

Download the latest release from the [Releases page](https://github.com/yourusername/hockey-music-controller/releases) and run:

```bash
python3 hockey_music_controller.py
```

## Quick Setup Guide

### First Launch

1. **Open Music app** (must be running)
2. **Launch the controller**
   ```bash
   python3 hockey_music_controller.py
   ```

3. **Configure your songs**
   - Click "⚙️ Configure Songs & Playlist"
   - Set your goal song
   - Set special event songs (zamboni, intermissions, etc.)
   - Select your stoppage playlist
   - Click "Load Playlist Tracks"

4. **Test it!**
   - Click the GOAL button to test
   - Use arrow keys to navigate playlist
   - Press Space to play/stop

### Configuration Tips

**Finding Exact Song Names:**
1. Open Music app
2. Right-click song → Get Info
3. Copy the exact "Name" field
4. Paste into configuration

**Songs Must Be in Your Library:**
- Songs must be added to your library (click "+" in Apple Music)
- Downloaded songs work best (more reliable)

## Usage During Games

### Pre-Game Setup
1. Open Music app
2. Launch Hockey Music Controller
3. Test goal song (click GOAL button)
4. Shuffle stoppage playlist
5. Position window for easy access

### During Stoppages
1. Press `Space` or click Play/Pause
2. Music plays through your playlist
3. Press `N` to skip songs
4. Press `Space` or `S` when play resumes

### For Goals
- Press `G` or click GOAL button
- Goal song plays immediately
- Crowd celebrates! 🎉

### Special Situations
- **Power Play:** Press `O` or click Power Play button
- **Penalty Kill:** Press `P` or click Penalty Kill button
- **Zamboni Time:** Click Zamboni buttons
- **Intermissions:** Click intermission buttons

### Playlist Navigation
- Use `⬆️⬇️` arrows to browse
- Highlight the song you want next
- Press `Space` (in playlist) to play it

## How It Works

### AppleScript Integration
This app uses **AppleScript** to control the macOS Music app:

**Advantages:**
- ✅ Works with Apple Music subscription
- ✅ No need for local audio files
- ✅ Native macOS integration
- ✅ Access to your entire library

**Requirements:**
- Music app must be running
- Songs must be in your library

### Architecture
```
┌─────────────────────────┐
│   Python GUI (Tkinter)  │
│  - Buttons & Controls   │
│  - Playlist Display     │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  AppleScript Commands   │
│  - Play/Pause/Stop      │
│  - Track Selection      │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│     Music.app (macOS)   │
│  - Apple Music Library  │
│  - Playback Engine      │
└─────────────────────────┘
```

## Configuration File

Settings stored in: `~/hockey_music_config.json`

Example:
```json
{
  "goal_song": "Chelsea Dagger",
  "zamboni": "Ice Ice Baby",
  "power_play": "Thunderstruck",
  "penalty_kill": "Eye of the Tiger",
  "playlist": "Hockey Stoppages"
}
```

## Troubleshooting

### "Could not play goal song"
- ✅ Check song name is exactly right (capitals, punctuation)
- ✅ Ensure song is in your library (not just Apple Music catalog)
- ✅ Verify Music app is running

### "Could not load playlists"
- ✅ Open Music app first
- ✅ Wait for it to fully load
- ✅ Try clicking "Load Playlists" again

### Keyboard shortcuts don't work
- ✅ Click inside the app window
- ✅ Make sure no text fields are selected

### Music won't play
- ✅ Check Music app volume
- ✅ Verify songs are downloaded/available
- ✅ Restart Music app

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed solutions.

## Development

### Project Structure
```
hockey-music-controller/
├── hockey_music_controller.py  # Main application
├── README.md                    # This file
├── TROUBLESHOOTING.md          # Detailed troubleshooting
├── LICENSE                      # MIT License
└── requirements.txt            # Empty (no external deps)
```

### No External Dependencies
Uses only Python standard library:
- `tkinter` - GUI framework
- `subprocess` - AppleScript execution
- `json` - Configuration storage
- `os` - File operations

### Contributing
Contributions welcome! Please feel free to submit a Pull Request.

## Use Cases

Perfect for:
- 🏒 Hockey game operations
- ⚽ Other sports events
- 🎭 Theater productions
- 🎪 Events requiring timed music cues
- 📻 Live broadcasts
- 🎉 Any situation needing quick music control

## Roadmap

- [ ] Multiple goal songs (home/away)
- [ ] Volume control slider
- [ ] Fade in/out effects
- [ ] Timer integration
- [ ] Recently played tracking
- [ ] Game clock integration
- [ ] Import/export configuration

## Credits

Created for hockey game operations where quick, reliable music control is essential during stoppages and goal celebrations.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- 📖 [Documentation](https://github.com/yourusername/hockey-music-controller/wiki)
- 🐛 [Report Issues](https://github.com/yourusername/hockey-music-controller/issues)
- 💬 [Discussions](https://github.com/yourusername/hockey-music-controller/discussions)

## Acknowledgments

Built with Python and AppleScript for seamless macOS Music app integration.

---

**Enjoy your games! 🏒 🎵**
