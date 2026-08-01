"""Persistent settings, with migration from the v1/v2 flat config."""

import json

from . import paths

SCHEMA_VERSION = 3

EVENT_KEYS = [
    ("goal", "Goal Song"),
    ("zamboni", "Zamboni"),
    ("zamboni_2nd", "2nd Zamboni"),
    ("game_start", "Game Start"),
    ("intermission_1st", "1st Intermission"),
    ("intermission_2nd", "2nd Intermission"),
    ("end_of_game", "End of Game"),
    ("power_play", "Power Play"),
    ("penalty_kill", "Penalty Kill"),
]

# Old flat keys -> new event keys. 'goal_song' was the odd one out.
_LEGACY_EVENT_MAP = {
    "goal_song": "goal",
    "zamboni": "zamboni",
    "zamboni_2nd": "zamboni_2nd",
    "game_start": "game_start",
    "intermission_1st": "intermission_1st",
    "intermission_2nd": "intermission_2nd",
    "end_of_game": "end_of_game",
    "power_play": "power_play",
    "penalty_kill": "penalty_kill",
}

DEFAULTS = {
    "version": SCHEMA_VERSION,
    "team_name": "Patriots",
    "roster_file": str(paths.DEFAULT_ROSTER),
    "event_songs": {key: "" for key, _ in EVENT_KEYS},
    "pools": {},
    "active_pool": "",
    "audio": {
        "fade_in": 0.0,
        "fade_out": 1.5,
        "duck_volume": 25,
        "duck_enabled": True,
        "family_safe": False,
    },
    "announcer": {
        "enabled": True,
        "use_cache": True,
        "timeout": 20.0,
        "fallback_voice": "Alex",
        "default_celebration": "woo.m4a",
    },
}


def _deep_merge(base, override):
    """Recursively fill missing keys in `override` from `base`."""
    out = dict(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


class Config:
    """Dict-backed config with dotted-path access."""

    def __init__(self, data=None):
        self.data = _deep_merge(DEFAULTS, data or {})

    # -- persistence ------------------------------------------------------

    @classmethod
    def load(cls):
        raw = {}
        if paths.CONFIG_FILE.exists():
            try:
                raw = json.loads(paths.CONFIG_FILE.read_text())
            except (json.JSONDecodeError, OSError) as e:
                print(f"⚠️  Could not read config ({e}); starting fresh")
                raw = {}
        needs_migration = bool(raw) and raw.get("version", 1) < SCHEMA_VERSION
        if needs_migration:
            backup = paths.CONFIG_FILE.with_suffix(".json.v2bak")
            try:
                backup.write_text(json.dumps(raw, indent=2))
                print(f"📦 Backed up the old config to {backup.name}")
            except OSError:
                pass
            raw = migrate(raw)

        cfg = cls(raw)
        if needs_migration:
            cfg.save()          # persist the upgrade so it only happens once
        return cfg

    def save(self):
        paths.ensure_dirs()
        try:
            tmp = paths.CONFIG_FILE.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(self.data, indent=2))
            tmp.replace(paths.CONFIG_FILE)
        except OSError as e:
            print(f"❌ Error saving config: {e}")

    # -- access -----------------------------------------------------------

    def get(self, dotted, default=None):
        node = self.data
        for part in dotted.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    def set(self, dotted, value):
        parts = dotted.split(".")
        node = self.data
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value

    # -- convenience ------------------------------------------------------

    @property
    def team_name(self):
        return self.get("team_name", "Patriots")

    def event_song(self, key):
        return self.get(f"event_songs.{key}", "")

    def set_event_song(self, key, value):
        self.set(f"event_songs.{key}", value)


def migrate(old):
    """Convert a v1/v2 flat config into the v3 shape.

    v1/v2 stored one playlist under 'playlist' plus a flat 'start_times' map of
    "Track | Artist" -> seconds. Both become the first pool.
    """
    new = dict(DEFAULTS)
    new = _deep_merge(new, {})
    new["version"] = SCHEMA_VERSION

    events = {}
    for legacy, key in _LEGACY_EVENT_MAP.items():
        if old.get(legacy):
            events[key] = old[legacy]
    if events:
        new["event_songs"] = {**new["event_songs"], **events}

    playlist = old.get("playlist", "")
    if playlist:
        clips = {
            track: {"start": int(secs), "end": None}
            for track, secs in (old.get("start_times") or {}).items()
        }
        new["pools"] = {
            "Stoppage": {
                "playlist": playlist,
                "clips": clips,
                "flagged": [],
            }
        }
        new["active_pool"] = "Stoppage"

    print(f"✅ Migrated config to v{SCHEMA_VERSION}"
          f" ({len(new['pools'])} pool, {len(events)} event songs)")
    return new
