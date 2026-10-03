# CLAUDE.md — Hockey Music Controller

Orientation for a fresh session in this repo. This is a **personal project**, not
part of HKOS — the lane rules in `~/dev/CLAUDE.md` (hkos-kira vs. josh-roadmap)
do not apply here. Everything lives in this one repo.

---

## What this is

A macOS game-day console for youth hockey. It drives **Apple Music** over
AppleScript and reads **PA announcements** in a custom **Hume AI** voice. Josh
runs it from the box at Patriots games; the audience is players and their
families, so "fun for the kids" is a real design goal, not a nice-to-have.

**Hard constraints:** macOS only (AppleScript + `afplay` + `say`), Python 3.8+,
tkinter, Apple Music must be running. Currently developed on Python 3.14.

---

## Run and test

```bash
bash launch.sh                    # checks deps, opens Music, launches
python3 hockey_music_controller.py

python3 tests/test_core.py        # 39 tests: copy, roster, playlists, migration, clip sharing
python3 tests/test_ui_smoke.py    # 24 tests: builds every window
python3 tests/test_hype.py        # 20 tests: chorus detection, proposal apply, game-deck split

python3 hype_points.py propose|show|apply|revert   # clip starts at the chorus (docs/HYPE_POINTS.md)
python3 game_playlists.py --games 2 [--dry-run]    # one playlist per game (docs/GAME_PLAYLISTS.md)
```

No test file needs Apple Music running or a network connection. **Run all three
before committing** — the UI smoke test is the only thing that catches a typo in
a tkinter callback, since nothing else exercises the dialogs.

---

## Layout

```
hockey_music_controller.py   entry-point shim -> hockeymusic.ui.main_window:main
hype_points.py               CLI shim -> hockeymusic.hype:main
game_playlists.py            CLI shim -> hockeymusic.gameday:main
hockeymusic/
  paths.py            all filesystem locations; nothing resolves off CWD
  config.py           settings dict + v1/v2 -> v3 migration
  music.py            AppleScript, volume, fades, ducking
  roster.py           Player/Roster dataclasses, CSV load/save
  announcements.py    ALL announcement copy
  announcer.py        Hume TTS, disk cache, async playback queue
  playlists.py        Pool/PoolSet, Clip, shuffle, family-safe filter, cross-pool clip lookup
  hype.py             chorus detection from LRCLIB synced lyrics; propose/apply/revert CLI
  gameday.py          deal a pool into N disjoint Apple Music playlists + register pools
  ui/
    main_window.py    HockeyMusicApp — the console
    goal_dialog.py    goal announcement + jersey quick-pick
    dialogs.py        final score, settings, pre-render, clip points
    roster_editor.py  roster table + per-player form
    common.py         modal/center/preview helpers
tests/                FakeMusic-backed, no external deps
docs/                 feature guides (see below)
```

**User data lives outside the repo:**
- `~/hockey_music_config.json` — settings, pools, clip points
- `~/.hockey_music/tts_cache/` — pre-rendered announcement audio (`*.wav`)
- `~/.hockey_music/.env` — Hume key (preferred over a repo `.env`)
- `~/.hockey_music/lyrics_cache/` — LRCLIB responses (misses cached too)
- `~/.hockey_music/hype_proposals.json` — last `hype_points.py propose` run
- `~/hockey_music_config.json.bak-{hype,games}-*` — backups written by `apply` / `game_playlists.py`

`rosters/*.csv` and `sound_clips/*.m4a` are gitignored — Josh's real roster and
clips are local only.

---

## Invariants — break these and the app fails at a game

**1. All announcement copy lives in `announcements.py`.**
The v2 build had the preview pane build its own string. It drifted, so the
preview said one thing and Hume said another. Preview code must call the same
function the announcer calls. `tests/test_ui_smoke.py` asserts this.

**2. Every AppleScript call goes through `AppleMusicController._run` or `_poll`.**
Music.app serialises AppleScript. The once-per-700ms UI poll used to pile up
behind slow calls and time everything out. `_run` waits its turn; `_poll` skips
if busy and returns `(None, False)`. **`get_current_track()` returning `None`
means "unknown, keep the last value"** — it is not an error.

**2b. Seeks are verified, never fire-and-forget.** Right after `play`, Music
rejects `set player position` (error -10006) until the track loads. v3.0 slept
0.4s and hoped; on a miss the retry re-issued `play`, so the song audibly
restarted from 0:00 before jumping. `_seek_verified` retries only the seek and
reads the position back. Keep `play` and the seek as separate calls.
A downloaded track starts instantly, so `_play_then_seek` holds Music's volume
at 0 from `play` until the seek lands (else the first ~0.3s of the intro is
heard, then a jump), and sets `_fading` so a duck in that window can't snapshot 0.

**3. Bulk-read track properties, never loop in AppleScript.**
`get_playlist_tracks` reads the name and artist columns in one call: ~0.2s on a
479-track playlist versus ~16s for a per-track loop.

**4. Track identity is the string `"Name | Artist"`.**
Clip points and family-safe flags are keyed on it, so any change to that format
orphans every saved clip. Josh has 450+ saved clip points riding on this.
`get_playlist_track_meta` must build the key the same way `get_playlist_tracks` does.

**4b. Clips are shared across pools.** `PoolSet.clip_for(track, pool)` returns
the pool's own clip, else any other pool's. Playback and the list display go
through it, so a new game-day pool inherits every hook point. A pool's own clip
always wins. Don't call `Pool.clip_for` from the UI for playback decisions.

**5. Never block the tkinter main loop.**
Hume synthesis and `afplay` both run on `Announcer`'s worker thread. v2 called
`thread.join(timeout=5.0)` on the main thread and froze the app mid-game.
Status callbacks come back from that worker — marshal them with `root.after`.

**6. Paths resolve off `paths.py`, never the working directory.**
The app gets launched from Finder and from a `.app` bundle, where CWD is not the
project directory.

**7. Secrets never enter the repo.**
`.env` was committed to the public GitHub repo. Local history was purged with
`git filter-repo` on 2026-08-01 but the purge was NOT pushed until 2026-09-26;
the live Hume key and Spotify secret sat public until then. **Key rotation is
still owed** (Hume + Spotify) as of 2026-09-26 -- the audio cache is keyed on
voice + text, so rotating costs no re-render. `.gitignore` does not untrack an
already-committed file. `create_native_app.sh` deliberately does not bundle `.env`.

---

## Things worth knowing

**Song titles must match Apple Music exactly**, punctuation included. There is no
fuzzy matching. Settings has a **▶ Test** button per event song for this reason.

**Config migration:** `Config.load()` writes a `.v2bak` backup, migrates, then
saves. To change the schema, bump `SCHEMA_VERSION` and extend `migrate()`.
Migration is covered in `test_core.py`.

**The TTS cache is keyed on `sha256(voice_id + "|" + text)`.** Change any wording
in `announcements.py` and every cached line for it is invalidated — Josh has to
re-render. Worth mentioning to him before touching announcement copy.

**Testing the UI:** `HockeyMusicApp(root, music=FakeMusic(), autostart=False)`.
The `music` and `autostart` params exist purely so tests can build every window
without Apple Music running and without starting the poll loop. Don't remove them.

---

## Where things stand

**v3.0 (2026-08-01)** restructured the 1,849-line single file into the package
above and shipped three feature bundles Josh picked: Player Spotlight, Playlist
Engine, Announcer Reliability. See the v3.0 commit message for the full list.

**Deliberately not built** — Josh declined this bundle, so don't add it unasked:
*Family Fun & Rituals* — Three Stars of the Game, hat-trick auto-detect,
free-text shout-outs (birthdays, 50/50 winners), soundboard pads, post-game stat
sheet for parents. Still a reasonable backlog if he asks for more fun features.

**v3.1 (2026-09-25)** — the season-opener pass. Hume verified live end-to-end
(one line rendered through `Announcer.render` in ~2.4s; the file is MP3 data
under a `.wav` name, which `afplay` handles). Verified seek. Clips shared across
pools. `hype_points.py` (chorus start points from LRCLIB synced lyrics) and
`game_playlists.py` (disjoint per-game decks). The 458 clip starts that existed
before were bulk genre defaults (5/8/10/12s), not hand-tuned — that's why
`apply` overwrites without a per-track keep list.

**Audio analysis is off the table:** 437 of 479 tracks in the master playlist
are Apple Music subscription tracks (DRM). Only ~41 have local files. Lyrics
are the only per-song timing signal available without a virtual audio device.

**Hume quota (2026-09-26):** the account hit HTTP 429 "Quota limit exceeded"
mid pre-render. The "Everything" scope is ~300 lines; "Lineup + unassisted" is
~35 and had already rendered. `Announcer` now backs off Hume for 10 minutes
after a 429 (uncached lines fall straight to the macOS voice) and pre-render
stops on the first one. Check the plan at platform.hume.ai before a big render.

**The Hume SDK warns on Python 3.14** (`pydantic.v1` compatibility). It's a
warning, not a failure; synthesis works.

---

## Working with Josh

He is the decision-owner. Be direct, flag scope creep by name, and tell the truth
about what was and wasn't verified. He would rather hear "I didn't test that"
than a confident guess. For anything touching saved config, clip points, or the
roster: say what you'll change and how it's reversible before doing it.
