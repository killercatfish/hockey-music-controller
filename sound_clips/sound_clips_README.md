# Sound Clips

Custom audio files for game events and celebrations.

## Current Files

- `woo.m4a` - Celebration sound that plays after home goal announcements

## How It Works

After a home goal PA announcement, the system automatically plays the celebration sound:

```
1. Goal scored
2. PA announcement: "Patriots GOAL!! Scored by number 7, Alexander Mellen!"
3. Celebration sound: woo.m4a plays
4. Crowd goes wild! 🎉
```

## Adding Your Own Sounds

### Supported Formats
- `.m4a` (recommended)
- `.mp3`
- `.wav`
- `.aiff`

### Adding a New Sound

1. **Place audio file in this directory:**
   ```
   sound_clips/
   ├── woo.m4a              ← Original celebration
   ├── airhorn.m4a          ← Your new sound
   └── goal_horn.m4a        ← Another sound
   ```

2. **Reference it in the code:**
   
   Find this section in `hockey_music_controller.py`:
   ```python
   # Play celebration sound after home goal announcements
   if team.lower() == "home":
       celebration_sound = os.path.expanduser("sound_clips/woo.m4a")
   ```
   
   Change to your file:
   ```python
   celebration_sound = os.path.expanduser("sound_clips/your_file.m4a")
   ```

3. **Test it!**

## Sound Ideas

### Goal Celebrations
- Air horn blasts
- Crowd cheering
- Goal horns
- Team-specific sounds
- Song clips (keep under 5 seconds)

### Other Events
- Zamboni sounds for cleaning
- Whistle for stoppage
- Buzzer for period end
- Organ music clips

## Creating Custom Sounds

### From Spotify/Apple Music

**Warning:** Respect copyright! Use short clips only.

1. Record short section (2-5 seconds)
2. Export as m4a or mp3
3. Test volume levels

### Free Sound Effects

Download from:
- [Freesound.org](https://freesound.org/)
- [Zapsplat.com](https://www.zapsplat.com/)
- [YouTube Audio Library](https://www.youtube.com/audiolibrary)

### Recommended Specs
- **Length:** 1-5 seconds
- **Format:** m4a or mp3
- **Bitrate:** 128-256 kbps
- **Sample Rate:** 44.1 kHz

## Volume Levels

Test your sounds before game time!

```bash
# Play sound at different volumes
afplay -v 0.5 sound_clips/your_file.m4a  # 50% volume
afplay -v 1.0 sound_clips/your_file.m4a  # 100% volume
afplay -v 2.0 sound_clips/your_file.m4a  # 200% volume (careful!)
```

In code:
```python
# Adjust system volume before playing
subprocess.run(['osascript', '-e', 'set volume output volume 50'])
subprocess.run(['afplay', sound_path])
```

## Multiple Sounds

Want different sounds for different situations?

```python
def play_celebration_sound(goal_type):
    """Play appropriate celebration sound"""
    if goal_type == "power_play":
        sound = "sound_clips/power_play_goal.m4a"
    elif goal_type == "short_handed":
        sound = "sound_clips/shorty_goal.m4a"
    else:
        sound = "sound_clips/woo.m4a"
    
    sound_path = os.path.expanduser(sound)
    if os.path.exists(sound_path):
        subprocess.run(['afplay', sound_path])
```

## Troubleshooting

### Sound Not Playing

Check console output:
```
🎉 Playing celebration sound!     ← Working
⚠️  Could not play sound: ...     ← Problem
ℹ️  Celebration sound not found   ← Missing file
```

### Wrong Volume

Adjust macOS system volume or:
- Use quieter source audio
- Edit audio file in Audacity
- Adjust volume in code

### Sound Cuts Off

If music starts before sound finishes:
```python
# Add delay after celebration
subprocess.run(['afplay', celebration_sound])
time.sleep(0.5)  # Wait 0.5 seconds
```

## File Size

Keep sound clips small:
- Under 1 MB each recommended
- 2-5 seconds ideal length
- Compress if needed

```bash
# Check file size
ls -lh sound_clips/

# Example output:
# -rw-r--r--  1 user  staff   127K Nov 23 10:00 woo.m4a  ← Good!
```

## Copyright Notice

**Important:** Only use sounds you have rights to:
- Your own recordings
- Royalty-free sounds
- Licensed content
- Short clips (fair use - check your local laws)

**Never use:**
- Full copyrighted songs
- Professional recordings without permission
- Other teams' proprietary sounds

---

**Tip:** Test all sounds at game-like volume before the actual game!
