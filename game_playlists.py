#!/usr/bin/env python3
"""Split a pool's playlist into one Apple Music playlist per game, no repeats.

    python3 game_playlists.py --games 2 --dry-run   # show the plan
    python3 game_playlists.py --games 2             # create them + add pools

See docs/GAME_PLAYLISTS.md.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hockeymusic.gameday import main  # noqa: E402

if __name__ == "__main__":
    main()
