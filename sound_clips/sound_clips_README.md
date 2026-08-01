# Sound Clips

Short celebration sounds that fire right after a home goal announcement.

Drop audio files in this directory and reference them **by filename** — no code
changes needed. (In v2 you had to edit `hockey_music_controller.py`; that is no
longer true.)

---

## How a goal plays out

```
1. Goal scored
2. The scorer's goal song starts       ← per player, or the team horn
3. Music ducks, PA announces over it   ← "Patriots GOAL!! Scored by
                                          number 7, Alexander Mellen!"
4. Celebration clip fires              ← woo.m4a, or that player's own clip
5. Music comes back up
```

---

## Assigning a clip

**Per player** — **👥 Roster** → select a player → **Celebration clip**. Enter
the filename, e.g. `airhorn.m4a`. The form lists what's available in this folder.

**Default for everyone else** — **⚙️ Settings → Announcer → Default celebration
clip**. Ships as `woo.m4a`.

An absolute path works too. A missing file is skipped silently rather than
breaking the announcement.

---

## Formats and specs

Supported: `.m4a` (recommended), `.mp3`, `.wav`, `.aiff`

| | |
|---|---|
| Length | 1–5 seconds |
| Bitrate | 128–256 kbps |
| Sample rate | 44.1 kHz |
| File size | under 1 MB |

Keep them short. The clip plays *after* the announcement, so a long one delays
the music coming back up.

---

## Testing levels

Test at game volume before game day — the box PA is much louder than your laptop.

```bash
afplay -v 0.5 sound_clips/your_file.m4a   # 50%
afplay -v 1.0 sound_clips/your_file.m4a   # 100%
afplay -v 2.0 sound_clips/your_file.m4a   # 200% — careful
```

If a clip is too hot relative to the others, normalise it in Audacity rather
than riding the system volume.

---

## Ideas

- Air horn / goal horn
- Crowd roar
- A short signature sound per player — kids love having their own
- Organ sting

---

## Copyright

Only use audio you have rights to: your own recordings, royalty-free sources
([Freesound](https://freesound.org/), [Zapsplat](https://www.zapsplat.com/),
[YouTube Audio Library](https://www.youtube.com/audiolibrary)), or licensed
content. Don't use full copyrighted songs or another team's proprietary sounds.

---

## Notes

- `sound_clips/*.m4a` is gitignored — your clips stay local. `woo.m4a` predates
  that rule and is still tracked.
- Console output tells you what happened: a missing file logs a notice and the
  announcement continues normally.
