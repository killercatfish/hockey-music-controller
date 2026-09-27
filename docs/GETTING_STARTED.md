# Getting started (no terminal needed)

For a parent running the box on their own Mac. The shareable, illustrated
version of this lives at the private guide page Josh sends; this is the copy
that travels with the code.

**You need:** a Mac with the Music app, about 15 minutes, and wifi the first time.

1. **Download the folder.** On the GitHub page click the green **Code** button,
   then **Download ZIP**. Safari unzips it into Downloads as
   `hockey-music-controller-main`. Drag it into Documents. Don't rename anything.
2. **Make a playlist in Music** for stoppage music. Add any one-off songs
   (goal, Zamboni, intermission) to your library and note their exact titles.
3. **Double-click `Start Hockey Music.command`.** A text window opens; leave it
   open. The console appears a few seconds later. First-time prompts:
   - *"cannot be opened because Apple could not verify it"* → right-click the
     file → **Open** → **Open**. If there is no Open choice: System Settings →
     Privacy & Security → scroll down → **Open Anyway**.
   - *"python3 requires the command line developer tools"* → **Install**, wait
     a few minutes, then double-click the file again. Once only.
   - *"Terminal wants access to control Music"* → **Allow**. (Undo a wrong
     click at System Settings → Privacy & Security → Automation → Terminal.)
4. **Pick your playlist.** In the Playlist section click **⟳** next to *Apple
   Music playlist* and choose it. **Show all playlists…** lists everything.
5. **Settings (⚙️).** *Event songs*: exact titles, **▶ Test** each; team name.
   *Announcer*: turn on **If Hume can't render a line, say it in a macOS
   voice**, or goal calls stay silent. The custom Hume voice is optional; see
   [HUME_VOICE_SETUP.md](HUME_VOICE_SETUP.md).
6. **Roster (👥).** Jersey number and name per player; the rest is optional.
7. **Game day.** Start the console before warmups (it opens Music). Click a
   song to line it up. **Space** plays it, or if music is playing, fades out,
   stops and lines up the next one. **↑/↓** move the line-up, **Enter** plays,
   **G** goal song, **A** announce a goal, **S** hard stop, **O/P** power play
   and penalty kill, **L** starting lineup.

## Optional: the real announcer voice (Hume AI)

Out of the box, goal calls use a built-in Mac voice. The arena-announcer voice
comes from Hume AI, a paid text-to-speech service (a few dollars a month covers
a season). Setup is all clicking:

1. Sign up at [platform.hume.ai](https://platform.hume.ai). Pick a plan.
2. In Hume, open **Text to Speech**, describe the voice you want (for example
   "energetic arena hockey PA announcer") and **save it** with a name like
   `Rink Announcer`. That name is what the app asks for.
3. In Hume, open **API keys** and copy your key.
4. In the app: **⚙️ Settings → Announcer**, paste the key and type the voice
   name into the *Hume AI* fields. **Save**, then quit and relaunch. The
   Announcer tab turns green when Hume is connected.
5. Click **🎤 Pre-render voice** at the bottom of the window and render the
   lineup and goal calls at home, on wifi. They are saved to disk and play
   instantly at the rink with no internet.

While you're setting it up, leave the *say it in a macOS voice* box checked so
nothing goes silent. Once Hume works, untick it if you'd rather skip a call
than hear the robot voice.

Settings, roster and clip points are stored in your home folder, so updating
is just downloading the ZIP again and swapping the folder.
