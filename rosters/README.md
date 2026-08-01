# Rosters

Player rosters live here as CSV. `rosters/*.csv` is **gitignored** — real names
stay off GitHub.

Edit them in the app: **👥 Roster**. Saving from there writes the format below.

---

## Format

```csv
number,name,position,nickname,goal_song,goal_song_start,celebration_clip
7,Alexander Mellen,C,,Thunderstruck,10,
10,Cale Kulig,LW,Cale,,0,
88,Jake O'Neil,D,,Enter Sandman,32,airhorn.m4a
```

| Column | Meaning |
|---|---|
| `number` | Jersey number. The lookup key — must be unique. |
| `name` | Full name, used on the PA unless `nickname` is set. |
| `position` | `C` / `LW` / `RW` / `D` / `G`. Announced in the starting lineup. |
| `nickname` | **PA name.** Overrides `name` in announcements — the name the kid actually goes by. |
| `goal_song` | Exact Apple Music track title. Plays instead of the team goal song when they score. Blank = team horn. |
| `goal_song_start` | Seconds into that track to start. `0` = beginning. |
| `celebration_clip` | Filename in `sound_clips/`. Blank = the default clip from Settings. |

Only `number` and `name` are required.

---

## Legacy files

The original two-column format still loads:

```csv
5,Hugo Brown
7,Alexander Mellen
```

No header, no extra columns. Open it in the roster editor and save — it upgrades
in place, keeping every player.

---

## Switching rosters

**👥 Roster → Open CSV…** picks a different file and remembers it in
`~/hockey_music_config.json`. Handy for multiple teams or seasons:

```
rosters/
├── patriots_roster_2025.csv
├── patriots_roster_2026.csv
└── squirts_b.csv
```

---

## Notes

- `goal_song` must match the Apple Music title **exactly**, punctuation included.
  There is no fuzzy matching.
- A number not on the roster still announces fine — it just says "number 99"
  with no name, rather than failing.
- Changing a name or nickname invalidates that player's cached announcements.
  Re-run **🎙 Pre-render voice** afterwards.
