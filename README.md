# 🏒 Hockey Music Controller

A professional music and PA announcement controller for hockey games, featuring Apple Music integration and Hume AI voice announcements.

![Version](https://img.shields.io/badge/version-2.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![Platform](https://img.shields.io/badge/platform-macOS-lightgrey)

![Player](https://github.com/killercatfish/hockey-music-controller/assets/player.jpg)

## ✨ Features

### Music Control
- 🎵 **Stoppage Music Playlist** - Shuffle and queue tracks for stoppages
- ⚽ **Goal Song** - Instant goal celebration music
- 🧊 **Zamboni Music** - Two separate zamboni cleaning songs
- 🏒 **Game Events** - Game start, intermissions, end of game music
- ⚡ **Special Situations** - Power play and penalty kill music
- ⏯️ **Full Playback Control** - Play/pause, stop, next track
- 🎹 **Keyboard Shortcuts** - Quick access to all functions

### PA Announcements (Hume AI)
- 📢 **Goal Announcements** - Professional PA announcements for goals with scorer and assists
- 🏁 **Final Score** - End-of-game score announcements
- 🎤 **Custom Voice** - Uses your Hume AI custom voice for authentic arena sound
- 🔊 **Fallback Support** - Falls back to macOS voices if Hume unavailable

### Interface
- 🎨 **Color-Coded Buttons** - Easy visual identification of functions
- 📝 **Live Preview** - See announcements before playing them
- ⌨️ **Keyboard Shortcuts** - SPACE, G, N, S, O, P for quick control
- 🖱️ **Drag & Drop** - Reorder playlist tracks easily

## 🚀 Quick Start

### Prerequisites
- macOS (10.14 or later)
- Python 3.8 or later
- Apple Music app
- Hume AI account (optional, for professional voice)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/killercatfish/hockey-music-controller.git
   cd hockey-music-controller
   ```

2. **Set up Hume AI (Optional)**
   
   Create a `.env` file:
   ```bash
   HUME_API_KEY=your_api_key_here
   HUME_VOICE_ID=your_custom_voice_name
   ```
   
   Install Hume dependencies:
   ```bash
   pip install hume python-dotenv
   ```

3. **Launch the application**
   ```bash
   # Using the launch script (recommended)
   bash launch.sh
   
   # Or directly with Python
   python3 hockey_music_controller.py
   ```

## 📖 Usage Guide

### First-Time Setup

1. **Open Apple Music** - Make sure Music app is running
2. **Configure Special Songs** - Click "⚙️ Configure Songs & Playlist"
3. **Set Goal Song** - Enter the exact song name from your library
4. **Set Event Songs** - Configure zamboni, intermission, etc.
5. **Load Stoppage Playlist** - Select a playlist for general stoppage music

### During a Game

**Goal Scored:**
1. Click "⚽ GOAL!" to play goal song
2. Click "📢 PA Goal Announcement" to announce scorer
3. Enter team (Home/Away), scorer number, and assists
4. Click "🎤 ANNOUNCE GOAL"

**Stoppage Play:**
- Press **SPACE** or click "⏯ Play/Pause" to start music
- Press **N** or click "⏭ Next" to queue next song (without playing)
- Press **S** or click "⏹ Stop" to stop music

**Special Events:**
- Click event buttons for zamboni, intermissions, etc.
- Press **O** for Power Play music
- Press **P** for Penalty Kill music

**End of Game:**
1. Click "🏁 Final Score Announcement"
2. Enter Patriots score, visiting team, and visiting score
3. Click "🎤 ANNOUNCE FINAL SCORE"

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| **SPACE** | Play/Pause |
| **G** | Play Goal Song |
| **N** | Next Track (queue without playing) |
| **S** | Stop |
| **O** | Power Play |
| **P** | Penalty Kill |

## 🔧 Configuration

### Music Setup

The controller saves your configuration to `~/hockey_music_config.json`

Songs are referenced by their exact name in Apple Music. For best results:
- Use the full song name as it appears in Music
- Songs must be in your Music library
- Playlists must be created in Music first

### Hume AI Voice Setup

1. Create a Hume AI account at [hume.ai](https://www.hume.ai)
2. Create a custom voice (record samples of PA announcements)
3. Get your API key from the Hume dashboard
4. Add to `.env` file:
   ```
   HUME_API_KEY=your_api_key
   HUME_VOICE_ID=Hockey Goal Announcer
   ```

Without Hume AI, the controller will use macOS text-to-speech (Alex voice).

## 📁 Project Structure

```
hockey-music-controller/
├── hockey_music_controller.py          # Main application
├── launch.sh                           # Launch script
├── requirements.txt                    # Python dependencies info
├── LICENSE                            # MIT License
├── README.md                          # This file
├── .gitignore                         # Git ignore rules
├── .env.example                       # Example environment file
├── docs/
│   ├── HUME_VOICE_SETUP.md           # Hume AI setup guide
│   ├── FINAL_SCORE_FEATURE_GUIDE.md  # Final score feature docs
│   └── FINAL_SCORE_QUICK_START.md    # Quick start for final score
└── add_final_score_feature_v2.py     # Enhancement patch script
```

## 🎯 Adding the Final Score Feature

If you're using an older version without the Final Score feature, you can add it:

```bash
python3 add_final_score_feature_v2.py hockey_music_controller.py
```

This creates `hockey_music_controller_with_final_score.py` with the feature added.

See `docs/FINAL_SCORE_FEATURE_GUIDE.md` for detailed instructions.

## 🐛 Troubleshooting

### Music App Issues
- **Error loading playlists**: Make sure Music app is running and authorized
- **Songs won't play**: Verify song names exactly match what's in Music
- **Playlist not loading**: Check playlist exists and has tracks

### Hume AI Issues
- **"Voice not found"**: Check `HUME_VOICE_ID` matches your voice name in Hume dashboard
- **No API key error**: Verify `.env` file is in the same directory as the script
- **Falls back to macOS voice**: Check Hume packages installed: `pip install hume python-dotenv`

### Python/tkinter Issues
- **"No module named '_tkinter'"**: Reinstall Python from [python.org](https://www.python.org/downloads/)
- **Python not found**: Use Python 3 from python.org, not Homebrew

See `requirements.txt` for detailed troubleshooting steps.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Hume AI for the professional voice synthesis API
- Apple Music for the music playback platform
- The hockey community for inspiration

## 📧 Contact

Project Link: [https://github.com/killercatfish/hockey-music-controller](https://github.com/killercatfish/hockey-music-controller)

---

**Made with ❤️ for hockey game operations**
