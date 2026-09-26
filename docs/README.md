# Documentation

| Guide | What it covers |
|---|---|
| [HUME_VOICE_SETUP.md](HUME_VOICE_SETUP.md) | Creating the custom voice, storing the API key, and **pre-rendering announcements** so they work without rink wifi |
| [CLIP_POINTS.md](CLIP_POINTS.md) | Setting start and end points so a track plays only its good part |
| [HYPE_POINTS.md](HYPE_POINTS.md) | `hype_points.py` — set every clip start at the chorus automatically, from synced lyrics |
| [GAME_PLAYLISTS.md](GAME_PLAYLISTS.md) | `game_playlists.py` — one Apple Music playlist per game, no repeats, clips carried over |
| [SPOTIFY_TO_APPLE_MUSIC.md](SPOTIFY_TO_APPLE_MUSIC.md) | Moving an existing Spotify playlist into Apple Music |

Also useful:

- [../README.md](../README.md) — features and game-day flow
- [../CLAUDE.md](../CLAUDE.md) — architecture, invariants, and gotchas for
  anyone (or any agent) changing the code
- [../rosters/README.md](../rosters/README.md) — roster CSV format, including
  per-player goal songs
- [../sound_clips/sound_clips_README.md](../sound_clips/sound_clips_README.md) —
  celebration clips

## Removed in v3

`QUICK_START_START_TIMES.md` and `START_TIMES_FEATURE_SUMMARY.md` described the
v2 start-times feature. It grew end points and moved into pools, so both were
replaced by [CLIP_POINTS.md](CLIP_POINTS.md). Existing start times migrate
automatically.
