"""Filesystem locations.

Everything resolves off the package location, never the current working
directory -- the app has to work when launched from Finder, a .app bundle, or
any terminal.
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

ROSTER_DIR = PROJECT_ROOT / "rosters"
SOUND_DIR = PROJECT_ROOT / "sound_clips"

DEFAULT_ROSTER = ROSTER_DIR / "patriots_roster_2025.csv"

# User data lives outside the repo so it survives a git pull.
DATA_DIR = Path.home() / ".hockey_music"
TTS_CACHE_DIR = DATA_DIR / "tts_cache"

# Kept at the legacy location so existing setups keep their songs.
CONFIG_FILE = Path.home() / "hockey_music_config.json"


def ensure_dirs():
    """Create the writable directories the app needs."""
    for d in (DATA_DIR, TTS_CACHE_DIR, ROSTER_DIR, SOUND_DIR):
        d.mkdir(parents=True, exist_ok=True)


def sound_clip(name):
    """Resolve a celebration clip name to a path, or None if missing.

    Accepts a bare filename (looked up in sound_clips/) or an absolute path.
    """
    if not name:
        return None
    p = Path(name).expanduser()
    if not p.is_absolute():
        p = SOUND_DIR / p
    return p if p.exists() else None
