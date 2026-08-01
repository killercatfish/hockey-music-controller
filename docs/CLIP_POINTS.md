# Clip Points

Play just the good part of a track. Set a **start**, an **end**, or both.

Replaces the v2 "start times" feature — your old start times were migrated
automatically and are now clips with no end point.

---

## Setting a clip

1. **Right-click** a track in the playlist (Ctrl+Click also works on macOS).
2. Choose **⏱️ Set clip points**.
3. Enter a start, an end, or both:
   - `15` — 15 seconds
   - `1:30` — one minute thirty

**Use current position** grabs wherever playback is right now — the fastest way
to find an out point is to let the song play and click the button when it stops
being good.

Leave **Stop at** blank to play through to the end of the track.

Tracks with clips show their window in the list:

```
  1. ⏱0:15–1:20  Thunderstruck | AC/DC
  2. ⏱0:08       Whatever It Takes | Imagine Dragons
  3.             Welcome to the Jungle | Guns N' Roses
```

---

## What clips do

**Start point** — seeks there as soon as the track loads. Good for long intros,
and it works around Apple Music cloud tracks that won't seek reliably on their own.

**End point** — the app watches playback and fades out as it reaches the out
point, so the music lands on the beat instead of getting chopped off. The fade
length is **Settings → Audio → Stops and skips fade out over**.

Clips apply everywhere a track plays: double-click, Enter, Space, and the
queued-up track from **N**.

---

## Editing and clearing

Right-click a track that already has a clip:
- **✏️ Edit clip points**
- **🗑️ Clear clip points**

Clips are saved to `~/hockey_music_config.json` per pool and persist between
sessions.

---

## Notes

- Clips belong to a **pool**, not to the whole app. The same song can start at
  0:15 in your Stoppage pool and 0:00 in Warmup.
- Clips are keyed to the track's `Name | Artist` string. Rename a track in Apple
  Music and its clip stops matching.
- An end point must be later than the start point.
- Setting both fields to blank/zero removes the clip.

---

## Suggested workflow

Do this once at the start of a season, not at the rink:

1. Load your stoppage playlist.
2. Play through it, and whenever a track has dead air at the front, right-click →
   **Use current position** for the start.
3. For tracks you only want a short burst of, set an end point 20–30 seconds in.

You only pay this cost once — the clips persist.
