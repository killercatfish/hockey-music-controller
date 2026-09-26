# Hype Points — start every song on the hook

A stoppage is twenty seconds long. If the song starts on its intro, the whistle
blows before the crowd hears the part they know. Hype points move each track's
[clip start](CLIP_POINTS.md) to a beat before its first chorus.

Setting 450 of these by hand is a season's work. `hype_points.py` does it from
**time-synced lyrics**.

---

## Why lyrics, not audio

Almost every track in an Apple Music subscription playlist is DRM-protected, so
the audio can't be read from disk. Time-synced lyrics can — [LRCLIB](https://lrclib.net)
serves them free, with no account, for most mainstream songs.

The chorus is the most-repeated block of lines. The tool finds the first strong
repeated block and starts the clip one second before it. Instrumentals and
songs with no synced lyrics are left exactly as they are.

---

## Running it

Do this at home, with Music open. It's three commands and nothing touches your
config until the third.

```bash
python3 hype_points.py propose        # reads the pool's playlist, looks up lyrics
python3 hype_points.py show           # review: proposed start, old start, chorus line
python3 hype_points.py apply          # backs up the config, then writes the clips
```

`propose` prints one line per track as it goes:

```
   2/479  ⏱  0:23  high    We Will Rock You | Queen
   3/479     --     instrumental  Eruption | Van Halen
```

Lyrics are cached in `~/.hockey_music/lyrics_cache/`, so a re-run is instant
and offline. `--refresh` ignores the cache. `--pool NAME` targets a pool other
than Stoppage.

`show` sorts by proposed start so the oddities stand out. `apply` overwrites
the start of every track that has a proposal (end points are kept). If you've
hand-set a clip you want to keep, either delete its entry from
`~/.hockey_music/hype_proposals.json` before applying, or re-set it in the app
afterwards — the right-click clip dialog works exactly as before.

`apply` writes a backup first:

```
Backed up config to ~/hockey_music_config.json.bak-hype-20260926-081500
Updated 388 clip start points in pool “Stoppage”.
```

**Undo** at any time:

```bash
python3 hype_points.py revert                     # latest backup
python3 hype_points.py revert ~/hockey_music_config.json.bak-hype-...
```

---

## What it decides, and how well

| Confidence | Means |
|---|---|
| `high` | A block of 3+ lines that recurs 3+ times — a textbook chorus |
| `medium` | A shorter or less-repeated block — usually right, worth a listen |

Where a song has both an early hook and a bigger chorus later, the earlier one
wins as long as it is at least half as strong. At a whistle you want the hook
now, not the biggest chorus at 2:40.

It will not propose a start within the last 25 seconds of a track, and a hook
that starts in the first three seconds plays from the top.

Known gaps:

- **Famous instrumental intros** (Seven Nation Army, Enter Sandman, Eye of the
  Tiger). The lyric-based start is still fine, but if the riff *is* the moment,
  set it by hand afterwards — the app's clip dialog still works exactly as before.
- **Chants and ad-libs** ("Ah-ah-ah") count as lyrics. Usually that's the hype.
- **Remixes** sometimes match the original's lyrics, whose timings are off. The
  lookup only accepts a match within 5 seconds of the track's duration, which
  catches most of these; the rest come back as "no synced lyrics".

---

## Clips are shared across pools

As of v3.1 a clip set in one pool plays in every pool that doesn't set its own.
Build a second game-day playlist from the same songs and it starts them at the
same hooks — see [GAME_PLAYLISTS.md](GAME_PLAYLISTS.md).
