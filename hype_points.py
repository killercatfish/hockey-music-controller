#!/usr/bin/env python3
"""Propose and apply clip start points at each song's chorus.

    python3 hype_points.py propose        # look up synced lyrics for the Stoppage pool
    python3 hype_points.py show           # review what would change
    python3 hype_points.py apply          # write it (backs up the config first)
    python3 hype_points.py revert         # put the last backup back

See docs/HYPE_POINTS.md.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hockeymusic.hype import main  # noqa: E402

if __name__ == "__main__":
    main()
