"""Player roster: numbers, names, and each player's own goal song."""

import csv
from dataclasses import dataclass, field, asdict
from pathlib import Path

from . import paths

FIELDS = ["number", "name", "position", "nickname",
          "goal_song", "goal_song_start", "celebration_clip"]


@dataclass
class Player:
    number: str
    name: str
    position: str = ""
    nickname: str = ""
    goal_song: str = ""          # Apple Music track name; blank = team goal song
    goal_song_start: int = 0     # seconds into that track
    celebration_clip: str = ""   # file in sound_clips/; blank = default

    @property
    def display_name(self):
        """What the PA announcer says. Nickname wins when set."""
        return self.nickname or self.name

    @property
    def label(self):
        """What the operator sees in a list."""
        bits = f"#{self.number}  {self.name}"
        if self.position:
            bits += f"  ({self.position})"
        if self.goal_song:
            bits += "  🎵"
        return bits


@dataclass
class Roster:
    players: dict = field(default_factory=dict)   # number -> Player
    source: object = None                         # Path it was loaded from

    # -- lookup -----------------------------------------------------------

    def get(self, number):
        return self.players.get(str(number).strip().lstrip("#"))

    def display_name(self, number):
        """Name for the PA, or None when the number isn't on the roster."""
        p = self.get(number)
        return p.display_name if p else None

    def sorted_players(self):
        def key(p):
            try:
                return (0, int(p.number))
            except ValueError:
                return (1, 0)
        return sorted(self.players.values(), key=key)

    def __len__(self):
        return len(self.players)

    # -- persistence ------------------------------------------------------

    @classmethod
    def load(cls, path=None):
        """Read a roster CSV.

        Handles both the modern header format and the original two-column
        `number,name` files with no header.
        """
        path = paths.DEFAULT_ROSTER if path is None else Path(path).expanduser()
        roster = cls(source=path)

        if not path.exists():
            print(f"⚠️  Roster file not found: {path}")
            return roster

        try:
            with open(path, newline="", encoding="utf-8") as f:
                sample = f.read(256)
                f.seek(0)
                has_header = sample.lower().lstrip().startswith("number,")
                if has_header:
                    for row in csv.DictReader(f):
                        p = _player_from_row(row)
                        if p:
                            roster.players[p.number] = p
                else:
                    for row in csv.reader(f):
                        if len(row) >= 2 and row[0].strip():
                            num = row[0].strip()
                            roster.players[num] = Player(number=num, name=row[1].strip())
            print(f"✅ Loaded {len(roster)} players from {path.name}")
        except (OSError, csv.Error) as e:
            print(f"❌ Error loading roster: {e}")

        return roster

    def save(self, path=None):
        path = path or self.source or paths.DEFAULT_ROSTER
        path = Path(path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=FIELDS)
                writer.writeheader()
                for p in self.sorted_players():
                    writer.writerow(asdict(p))
            self.source = path
            print(f"✅ Saved {len(self)} players to {path.name}")
            return True
        except OSError as e:
            print(f"❌ Error saving roster: {e}")
            return False


def _player_from_row(row):
    number = (row.get("number") or "").strip()
    if not number:
        return None
    try:
        start = int(float(row.get("goal_song_start") or 0))
    except ValueError:
        start = 0
    return Player(
        number=number,
        name=(row.get("name") or "").strip(),
        position=(row.get("position") or "").strip(),
        nickname=(row.get("nickname") or "").strip(),
        goal_song=(row.get("goal_song") or "").strip(),
        goal_song_start=start,
        celebration_clip=(row.get("celebration_clip") or "").strip(),
    )
