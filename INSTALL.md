# 🏒 Hockey Music Controller - Complete Installation Package

## What You've Downloaded

This package contains everything you need to control Apple Music during hockey games:

1. **hockey_music_controller.py** - The main application
2. **launch.sh** - Easy launcher script (recommended)
3. **QUICKSTART.md** - Quick start guide (read this first!)
4. **README.md** - Complete documentation
5. **TROUBLESHOOTING.md** - Solutions to common problems
6. **INSTALL.md** - This file

## 🚀 Quick Installation (2 Minutes)

### Step 1: Download & Extract
You've already done this! All files should be in one folder.

### Step 2: Easy Launch Method

**Option A: Using the Launcher (Easiest)**
1. Open Terminal (press Cmd+Space, type "Terminal", press Enter)
2. Type `cd ` (with a space after cd)
3. Drag the folder containing these files into Terminal
4. Press Enter
5. Type: `./launch.sh`
6. Press Enter

The launcher will:
- Check if Python is installed
- Check if Music app is running
- Offer to open Music app for you
- Launch the controller

**Option B: Direct Launch**
1. Open Terminal
2. Navigate to the folder with these files
3. Run: `python3 hockey_music_controller.py`

### Step 3: First-Time Setup (in the app)

1. **Set Your Goal Song**
   - Click "Set from Library"
   - Type the EXACT name of your goal song
   - Click OK

2. **Load Your Playlist**
   - Click "Load Playlists"
   - Select your stoppage playlist from dropdown
   - Click "Load Playlist Tracks"

3. **Test It!**
   - Click the big yellow GOAL button
   - Your goal song should play!

## 📋 System Requirements

- ✅ Mac computer (any recent macOS)
- ✅ Apple Music app installed
- ✅ Apple Music subscription (or music in your library)
- ✅ Python 3 (already on your Mac!)

## 🎯 Key Features At-A-Glance

### Giant GOAL Button
- Instantly plays your celebration song
- Press 'G' on keyboard for hands-free operation

### Playlist Control
- Load your stoppage-time playlist
- Shuffle with one click
- Drag songs to reorder manually
- Double-click any song to play it

### Keyboard Shortcuts (No Mouse Needed!)
- **SPACE** - Play/Pause
- **G** - GOAL!
- **N** - Next track
- **S** - Stop

### Visual Playlist Management
- See all your songs
- Shuffle and reorder
- Play from top of your custom order
- Drag and drop to rearrange

## 📖 Documentation Files Explained

### QUICKSTART.md
**Read this first!** Quick guide to get started, including:
- Initial setup instructions
- How to configure goal song and playlist
- Game day usage tips
- Keyboard shortcuts reference

### README.md
Complete technical documentation:
- All features explained in detail
- How the app works (AppleScript)
- Advanced customization options
- Code structure (if you want to modify it)

### TROUBLESHOOTING.md
Solutions to common problems:
- "Could not play goal song" fixes
- Playlist loading issues
- Keyboard shortcuts not working
- Permission problems
- And much more!

## 🎮 Quick Game Day Checklist

Before the game starts:

- [ ] Open Music app
- [ ] Run launch.sh (or python3 hockey_music_controller.py)
- [ ] Test GOAL button
- [ ] Load/shuffle your stoppage playlist
- [ ] Position window where you can see it
- [ ] Verify volume is good
- [ ] Test keyboard shortcuts

During stoppages:
- Press SPACE to start music
- Press G when goals are scored
- Press N to skip songs
- Press SPACE or S when play resumes

## ⚙️ Configuration

The app saves your settings automatically to:
```
~/hockey_music_config.json
```

This remembers:
- Your goal song
- Your selected playlist
- Your last playlist order

You can edit this file manually if needed.

## 🔧 Troubleshooting Quick Fixes

### App won't start
```bash
# Make sure it's executable
chmod +x hockey_music_controller.py

# Run with python directly
python3 hockey_music_controller.py
```

### Goal song won't play
- Check song name is EXACTLY right (including capital letters)
- Make sure song is in your library (click + in Apple Music)
- Ensure Music app is running

### Playlist won't load
- Music app must be running first
- Wait a few seconds after opening Music app
- Click "Load Playlists" again

### Keyboard shortcuts don't work
- Click inside the app window
- Make sure no text fields are selected
- Close other music apps that might capture keys

## 📁 File Locations

After installation, you'll have:

```
Your_Download_Folder/
├── hockey_music_controller.py  (main app)
├── launch.sh                    (easy launcher)
├── QUICKSTART.md               (quick guide)
├── README.md                   (full docs)
├── TROUBLESHOOTING.md          (help)
└── INSTALL.md                  (this file)

~/hockey_music_config.json      (created on first run)
```

## 🎵 Adding Music to Your Library

For songs to work with this app, they must be in YOUR library:

1. Search for song in Apple Music
2. Click the **+** button or **Add to Library**
3. Wait for it to sync
4. Now it's available to the controller!

## 🏆 Pro Tips

1. **Create a dedicated stoppage playlist** in Music app
2. **Download songs for offline use** (for reliable playback)
3. **Keep the window visible** during games
4. **Use keyboard shortcuts** when you're busy with other tasks
5. **Test everything before the game starts**
6. **Have a backup plan** (know how to control Music app manually)

## 🔄 Updating the App

To update (if a new version is released):
1. Download the new hockey_music_controller.py
2. Replace the old file
3. Your config file will remain (settings preserved)

## ❓ Getting Help

1. Check **TROUBLESHOOTING.md** first
2. Make sure Music app works manually
3. Verify Python and Music app are updated
4. Try restarting both apps
5. Check System Settings for permissions

## 🎊 You're Ready!

That's it! You now have a professional hockey music control system.

**Next Steps:**
1. Read QUICKSTART.md for detailed setup
2. Configure your goal song
3. Load your stoppage playlist
4. Test during practice or a scrimmage
5. Use confidently on game day!

## 💡 Usage Example - Typical Game

**Period Break:**
1. Press SPACE to start stoppage playlist
2. Music plays in your shuffled order
3. Press N to skip songs if needed
4. Press SPACE when period starts

**Goal is Scored:**
1. Press G (or click GOAL button)
2. Goal song plays immediately
3. Crowd celebrates!
4. Press SPACE to resume stoppage playlist

**Quick Stoppage:**
1. Press SPACE
2. Let one song play
3. Press SPACE to pause
4. Resume when needed

**Multiple Quick Stops:**
- Keep pressing SPACE to toggle
- Music picks up right where it left off
- Press N to advance if same song is getting old

## 🚀 Launch Shortcuts for Future Use

Create a desktop shortcut or alias:

```bash
# Option 1: Create an alias in Terminal
alias hockey='cd /path/to/folder && python3 hockey_music_controller.py'

# Option 2: Create a desktop launcher
# (Save this as Hockey.command on your desktop)
#!/bin/bash
cd /path/to/your/folder
python3 hockey_music_controller.py
```

Then double-click to launch!

---

## 📞 Support

This is a custom application. For technical issues:
- Review TROUBLESHOOTING.md
- Check that Music app works normally
- Verify all requirements are met
- Test with simple songs/playlists first

For Apple Music issues:
- Contact Apple Support
- Check Apple Music subscription status

---

**Enjoy your games! 🏒 🎵 ⚽**

*Built for hockey operations personnel who need fast, reliable music control*
