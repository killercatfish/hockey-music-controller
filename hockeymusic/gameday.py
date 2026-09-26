"""Build one Apple Music playlist per game from a master pool, with no overlap.

Two games in a day means the same families hear the same songs twice unless
the decks are different. This deals the master playlist out into N disjoint
game playlists inside Apple Music, then registers each as a pool. Clips
carry over automatically: a pool with no clip of its own for a song plays the
clip another pool has (see PoolSet.clip_for), so the hook points set on the
master pool apply to every game deck.

The generator never deletes or edits an existing playlist. Registering the
pools is the only config write, and it backs the config up first.
"""

import argparse
import random
import sys
from datetime import date

from .hype import backup_config

UNAVAILABLE = {"no longer available", "not uploaded", "error"}


def deal(track_meta, games, flagged=(), size=None, seed=None):
    """Split tracks into `games` disjoint decks of 1-indexed playlist positions.

    Drops flagged tracks and anything Apple Music can't play any more. With
    `size`, each deck is capped at that many tracks; otherwise the whole
    playlist is dealt out evenly.
    """
    flagged = set(flagged)
    eligible = [i + 1 for i, m in enumerate(track_meta)
                if m["track"] not in flagged and m.get("cloud", "") not in UNAVAILABLE]
    rng = random.Random(seed)
    rng.shuffle(eligible)
    if size:
        eligible = eligible[:size * games]
    decks = [sorted(eligible[g::games]) for g in range(games)]
    return decks


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="game_playlists.py",
        description="Deal a pool's playlist into disjoint per-game Apple Music playlists.")
    parser.add_argument("--source-pool", default="Stoppage")
    parser.add_argument("--games", type=int, default=2)
    parser.add_argument("--prefix", default=None,
                        help='playlist name prefix (default "<Team> Game")')
    parser.add_argument("--size", type=int, default=None,
                        help="cap each game playlist at this many tracks")
    parser.add_argument("--seed", default=None,
                        help="shuffle seed (default: today's date, so a re-run repeats)")
    parser.add_argument("--dry-run", action="store_true", help="print the plan only")
    args = parser.parse_args(argv)

    from .config import Config
    from .music import AppleMusicController
    from .playlists import PoolSet

    config = Config.load()
    pools = PoolSet(config)
    if args.source_pool not in pools.pools:
        sys.exit(f"No pool named {args.source_pool!r}. Pools: {', '.join(pools.names)}")
    source = pools.pools[args.source_pool]
    if not source.playlist:
        sys.exit(f"Pool {args.source_pool!r} has no Apple Music playlist assigned.")

    music = AppleMusicController()
    meta = music.get_playlist_track_meta(source.playlist)
    if not meta:
        sys.exit("Could not read the playlist. Is Music running?")

    prefix = args.prefix or f"{config.team_name} Game"
    seed = args.seed or date.today().isoformat()
    decks = deal(meta, args.games, flagged=source.flagged, size=args.size, seed=seed)
    names = [f"{prefix} {g + 1}" for g in range(args.games)]

    skipped = len(meta) - sum(len(d) for d in decks)
    print(f"Source: “{source.playlist}” ({len(meta)} tracks, {skipped} left out)")
    for name, deck in zip(names, decks):
        clipped = sum(1 for i in deck if pools.clip_for(meta[i - 1]["track"], source))
        print(f"  {name}: {len(deck)} tracks ({clipped} with clip points)")
        for i in deck[:5]:
            print(f"      {meta[i - 1]['track']}")
        if len(deck) > 5:
            print("      …")

    existing = [n for n in names if music.playlist_exists(n)]
    if existing:
        sys.exit(f"\nAlready in Apple Music: {', '.join(existing)}. "
                 "Delete them in Music or pick another --prefix.")
    if args.dry_run:
        print("\nDry run: nothing created.")
        return

    for name, deck in zip(names, decks):
        print(f"\nCreating “{name}” in Apple Music…")
        if not music.create_playlist_from(source.playlist, name, deck):
            sys.exit("Stopped. Check Music and delete any half-made playlist.")
        print(f"  ✅ {len(deck)} tracks")

    backup = backup_config(tag="games")
    for name in names:
        pool = pools.add(name.replace(prefix, "Game").strip(), playlist=name)
        if pool is None:                       # pool name already taken
            pool = pools.pools[name.replace(prefix, "Game").strip()]
            pool.playlist = name
        pool.flagged = set(source.flagged)
    pools.save_into_config()
    config.save()
    print(f"\nBacked up config to {backup}")
    print(f"Added pools: {', '.join(n.replace(prefix, 'Game').strip() for n in names)}."
          " Pick one from the Pool menu in the app.")
    print(f"Undo: delete the playlists in Music, then  python3 hype_points.py revert \"{backup}\"")


if __name__ == "__main__":
    main()
