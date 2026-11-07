# Phase 0 spike: rink audio on the iPhone

One web page, three music sources, three tests each. It answers the go/no-go
question in `docs/CROSS_PLATFORM_PLAN.md`: can a web app do the game-day basics
on a phone? It is throwaway code and not part of the Mac app.

| Test | What it checks | Why it matters |
|---|---|---|
| **Play at clip** | Starts the song and jumps to the clip point; reads the position back | The console's core move. Listen for the intro leaking before the jump. |
| **Fade out 3s** | Sets volume 0.5 and reads it back, then fades | iOS Safari usually locks web-page volume. If this FAILs, no fades. |
| **Duck + announce** | Lowers music, plays the announcement, brings music back | The goal call. Falls back to pause if volume is locked. |

Sources: **own file** (needs nothing), **YouTube** (needs nothing; ads show
unless you're signed into YouTube Premium in Safari), **Apple Music** (needs a
developer token, below).

## 1. Put the page online (once, ~2 minutes)

MusicKit needs HTTPS, so the page runs from GitHub Pages:

1. github.com/killercatfish/hockey-music-controller → **Settings → Pages**
2. Source: **Deploy from a branch**. Branch: `claude/beautiful-cerf-jlgfi4`, folder **/docs** → Save
3. After a minute or two it's at
   **https://killercatfish.github.io/hockey-music-controller/spike/**

The repo is public, so the page is too. It holds no secrets. To undo: set
Pages back to **None**.

## 2. Apple Music token (only for the Apple Music test)

Needs the **Apple Developer Program** ($99/yr), which the iPhone app would need
anyway. Skip this and run the own-file and YouTube tests first if you haven't
joined yet.

1. developer.apple.com → Certificates, Identifiers & Profiles → **Identifiers → +
   → Media IDs**. Register one, e.g. `media.com.killercatfish.rinkaudio`.
2. **Keys → +**: name it, tick **Media Services (MusicKit, ShazamKit, Apple Music
   Feed)**, configure it with that Media ID, then Continue → Register →
   **Download** the `AuthKey_XXXXXXXXXX.p8` file. You can download it **only
   once**; keep it out of the repo.
3. Note the **Key ID** (on the key page) and **Team ID** (top-right, Membership).
4. On the Mac:
   ```bash
   pip3 install pyjwt cryptography
   python3 docs/spike/make_musickit_token.py --key ~/Downloads/AuthKey_XXXX.p8 \
       --key-id XXXXXXXXXX --team-id YYYYYYYYYY
   ```
5. AirDrop or Notes the printed token to the phone and paste it into the page's
   token box. It's saved in that Safari only, locked to the Pages site, and
   expires in 30 days.

## 3. Run it on the iPhone

- Ringer switch **on** (silent mode can mute web audio), Bluetooth to the PA if
  that's how you'd run a game.
- Optional: put a cached Hume line in Files and pick it as the announcement file.
  Lines are in `~/.hockey_music/tts_cache/`. Otherwise the iPhone's own voice reads it.
- Do each source: Play at clip → Duck + announce → Fade out.
- Also try once after **Share → Add to Home Screen**, opened from the icon. It
  behaves a bit differently.
- Also try with the screen **locked** mid-song: does the music keep going?
- Tap **Copy results** and send them back with what you heard ("intro leaked",
  "fade was a hard cut", etc.).

## What the results mean

- **All PASS on Apple Music:** web app is a go for iPhone.
- **Play PASS, fade/duck FAIL:** expected iOS behaviour. Options: pause instead
  of duck in the web app, or build a native iOS shell that ducks with
  `AVAudioSession` (still no smooth music fade). Decision for Josh.
- **Play FAIL on Apple Music:** web MusicKit isn't good enough on iPhone; the
  iPhone version would need native code.
