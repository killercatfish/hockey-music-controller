# Game Playlists — one deck per game, no repeats

Two games in a day, same rink, some of the same families: they shouldn't hear
the same song twice. `game_playlists.py` deals the master playlist out into one
Apple Music playlist per game, with no overlap, and registers each as a pool.

```bash
python3 game_playlists.py --games 2 --dry-run   # show the plan, create nothing
python3 game_playlists.py --games 2             # create the playlists + pools
```

With the default Stoppage pool of 479 tracks and two games, that's two
playlists of about 240 tracks each — plenty for a game, and still shuffled in
the app.

---

## What it does

1. Reads the source pool's Apple Music playlist (`--source-pool`, default
   Stoppage).
2. Drops flagged tracks and anything Apple Music reports as no longer available.
3. Shuffles and deals into `--games` decks. The shuffle is seeded with today's
   date, so re-running the command gives the same split; pass `--seed` for a
   different one. `--size 150` caps each deck.
4. Creates `<Team> Game 1`, `<Team> Game 2`, … in Apple Music (`--prefix` to
   rename). **It never edits or deletes an existing playlist** — if one of those
   names is taken, it stops and tells you.
5. Backs up the config and adds pools **Game 1**, **Game 2**, … pointing at the
   new playlists.

Clip points carry over automatically. A pool with no clip of its own for a song
plays the clip another pool has, so the hooks set on Stoppage (by hand or by
[hype_points.py](HYPE_POINTS.md)) apply to every game deck. The dry run shows
how many tracks in each deck have one.

---

## On game day

Pick **Game 1** from the Pool menu for the first game and **Game 2** for the
second. Everything else — shuffle, search, next, clips, flags — works the same.

The Stoppage pool is untouched and still there if you'd rather use the full list.

---

## Undo

Delete the playlists in Music, then put the config back:

```bash
python3 hype_points.py revert ~/hockey_music_config.json.bak-games-...
```

Or just delete the pools with the 🗑 button next to the Pool menu.
