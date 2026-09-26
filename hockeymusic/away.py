"""Visiting-team goal calls from a photographed game sheet.

The console only carries the home roster. Before a game, Josh photographs the
visitors' lineup, the names get typed into a CSV, and this CLI announces their
goals by name -- rendered through Hume, never the macOS voice. If Hume can't
render a line, the call is skipped and says so.

Runs beside the live app (it only touches the TTS cache and pauses Music), so
nothing here needs the console restarted.

    python3 away_goal.py set rosters/away_catamounts.csv Catamounts
    python3 away_goal.py prerender          # render every player's call now
    python3 away_goal.py 71                 # goal by #71, unassisted
    python3 away_goal.py 71 22 9            # with assists
    python3 away_goal.py list
"""

import json
import subprocess
import sys
import time

from . import announcements, paths
from .announcer import Announcer
from .roster import Roster

STATE_FILE = paths.DATA_DIR / "away_team.json"


class _NoConfig:
    """Announcer only reads a few optional settings; defaults are fine here,
    and this keeps the CLI from loading (and re-saving) the live config file
    while the console is running."""

    def get(self, _dotted, default=None):
        return default


def load_state():
    try:
        return json.loads(STATE_FILE.read_text())
    except (OSError, ValueError):
        return None


def save_state(roster_path, team):
    paths.ensure_dirs()
    STATE_FILE.write_text(json.dumps({"roster": str(roster_path), "team": team}))


def current():
    state = load_state()
    if not state:
        sys.exit("No visiting team set. Run: away_goal.py set <roster.csv> <Team>")
    return Roster.load(state["roster"]), state["team"]


def pause_music():
    subprocess.run(["osascript", "-e", 'tell application "Music" to pause'],
                   capture_output=True, timeout=5)


def render_once(announcer, text, retry_after=20.0):
    """Hume only. One retry after a short pause covers the plan's burst 429s."""
    path = announcer.render(text)
    if path:
        return path
    if not announcer.hume_available:
        return None
    time.sleep(retry_after)
    announcer.quota_exhausted_at = None     # the 10-min backoff is for the live app
    return announcer.render(text)


def cmd_prerender(roster, team):
    announcer = Announcer(_NoConfig())
    if not announcer.hume_available:
        sys.exit("Hume is not configured (no HUME_API_KEY).")
    ok, failed = 0, []
    for p in roster.sorted_players():
        text = announcements.visiting_goal(team, p.number, roster=roster)
        if announcer.is_cached(text):
            ok += 1
            continue
        if render_once(announcer, text):
            ok += 1
            print(f"  ✅ #{p.number} {p.display_name}")
        else:
            failed.append(p.number)
            print(f"  ❌ #{p.number} {p.display_name}")
        time.sleep(2.0)
    print(f"{ok} ready, {len(failed)} failed" + (f": {' '.join(failed)}" if failed else ""))
    return 1 if failed else 0


def cmd_goal(roster, team, scorer, assists):
    text = announcements.visiting_goal(team, scorer, assists, roster)
    print(f"📣 {text}")
    announcer = Announcer(_NoConfig())
    path = render_once(announcer, text)
    if not path:
        print("⏭  SKIPPED -- Hume could not render this line (no macOS voice fallback).")
        return 2
    pause_music()
    subprocess.run(["afplay", str(path)])
    return 0


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd = argv[0]
    if cmd == "set":
        if len(argv) < 3:
            sys.exit("usage: away_goal.py set <roster.csv> <Team name>")
        roster = Roster.load(argv[1])
        if not len(roster):
            sys.exit("That roster is empty or missing.")
        save_state(argv[1], " ".join(argv[2:]))
        print(f"Visiting team: {' '.join(argv[2:])} ({len(roster)} players)")
        return 0
    roster, team = current()
    if cmd == "list":
        print(f"{team}:")
        for p in roster.sorted_players():
            print(f"  {p.number:>3}  {p.display_name}")
        return 0
    if cmd == "prerender":
        return cmd_prerender(roster, team)
    return cmd_goal(roster, team, cmd, argv[1:])


if __name__ == "__main__":
    sys.exit(main())
