"""Playlist pools: clip in/out points, no-repeat shuffle, family-safe filtering.

A "pool" is one Apple Music playlist plus the game-day metadata layered on top
of it. Having several -- Warmup, Stoppage, Intermission, Power Play -- means you
switch context with one click instead of reloading a playlist mid-period.
"""

import random
from collections import deque
from dataclasses import dataclass


@dataclass
class Clip:
    """In and out points for a track, in seconds."""
    start: int = 0
    end: int = None

    @property
    def is_set(self):
        return bool(self.start) or self.end is not None

    def to_dict(self):
        return {"start": self.start, "end": self.end}

    @classmethod
    def from_dict(cls, d):
        if isinstance(d, (int, float)):       # v2 stored a bare start time
            return cls(start=int(d))
        return cls(start=int(d.get("start") or 0),
                   end=None if d.get("end") is None else int(d["end"]))


def format_seconds(seconds):
    seconds = int(seconds or 0)
    return f"{seconds // 60}:{seconds % 60:02d}"


def parse_time(text):
    """Parse '90', '1:30' or '1:30.5' into whole seconds."""
    text = (text or "").strip()
    if not text:
        raise ValueError("Enter a time as seconds or MM:SS")
    try:
        if ":" in text:
            minutes, _, secs = text.partition(":")
            return int(minutes) * 60 + int(float(secs))
        return int(float(text))
    except ValueError:
        raise ValueError("Invalid time. Use seconds (90) or MM:SS (1:30).")


class Pool:
    """One playlist plus its clips, flags, and play order."""

    HISTORY_LEN = 12

    def __init__(self, name, playlist="", tracks=None, clips=None, flagged=None):
        self.name = name
        self.playlist = playlist
        self.tracks = list(tracks or [])
        self.clips = dict(clips or {})            # track string -> Clip
        self.flagged = set(flagged or ())         # tracks kept out of rotation
        self.order = list(range(len(self.tracks)))
        self.history = deque(maxlen=self.HISTORY_LEN)

    # -- tracks -----------------------------------------------------------

    def load_tracks(self, controller):
        """Pull the track list from Apple Music. Returns the count."""
        tracks = controller.get_playlist_tracks(self.playlist)
        if tracks:
            self.tracks = tracks
            self.reset_order()
        return len(tracks)

    def track_at(self, position):
        """Track string at a position in the current order, or None."""
        if 0 <= position < len(self.order):
            return self.tracks[self.order[position]]
        return None

    def music_index(self, position):
        """1-indexed position in the underlying Apple Music playlist."""
        return self.order[position] + 1

    def clip_for(self, track):
        return self.clips.get(track)

    def set_clip(self, track, start=0, end=None):
        if not start and end is None:
            self.clips.pop(track, None)
        else:
            self.clips[track] = Clip(start=int(start or 0),
                                     end=None if end is None else int(end))

    def toggle_flag(self, track):
        """Flag/unflag a track as not family-friendly."""
        if track in self.flagged:
            self.flagged.discard(track)
            return False
        self.flagged.add(track)
        return True

    # -- ordering ---------------------------------------------------------

    def reset_order(self, family_safe=False):
        self.order = [i for i, t in enumerate(self.tracks)
                      if not (family_safe and t in self.flagged)]

    def shuffle(self, family_safe=False):
        """Shuffle, pushing anything played recently toward the back.

        A plain `random.shuffle` happily plays the same song twice in a period.
        This keeps the last dozen tracks out of the front of the deck.
        """
        self.reset_order(family_safe=family_safe)
        random.shuffle(self.order)
        if not self.history:
            return
        recent = set(self.history)
        fresh = [i for i in self.order if self.tracks[i] not in recent]
        stale = [i for i in self.order if self.tracks[i] in recent]
        self.order = fresh + stale

    def note_played(self, track):
        if track:
            self.history.append(track)

    def matches(self, query):
        """Indices into `order` whose track matches a search string."""
        q = (query or "").strip().lower()
        if not q:
            return list(range(len(self.order)))
        return [pos for pos in range(len(self.order))
                if q in self.tracks[self.order[pos]].lower()]

    # -- persistence ------------------------------------------------------

    def to_dict(self):
        return {
            "playlist": self.playlist,
            "clips": {t: c.to_dict() for t, c in self.clips.items()},
            "flagged": sorted(self.flagged),
        }

    @classmethod
    def from_dict(cls, name, d):
        clips = {t: Clip.from_dict(v) for t, v in (d.get("clips") or {}).items()}
        return cls(name=name, playlist=d.get("playlist", ""),
                   clips=clips, flagged=d.get("flagged") or [])


class PoolSet:
    """All configured pools, and which one is live."""

    DEFAULT_NAMES = ["Stoppage", "Warmup", "Intermission", "Power Play"]

    def __init__(self, config):
        self.config = config
        self.pools = {name: Pool.from_dict(name, d)
                      for name, d in (config.get("pools") or {}).items()}
        if not self.pools:
            self.pools["Stoppage"] = Pool("Stoppage")
        active = config.get("active_pool") or next(iter(self.pools))
        self.active_name = active if active in self.pools else next(iter(self.pools))

    @property
    def active(self):
        return self.pools[self.active_name]

    @property
    def names(self):
        return list(self.pools)

    def activate(self, name):
        if name in self.pools:
            self.active_name = name
        return self.active

    def clip_for(self, track, pool=None):
        """The clip to play for a track: the pool's own, else any other pool's.

        Clips are set once per song, not once per pool -- a second game-day
        playlist built from the same songs should start them at the same hook
        without redoing 450 clip points. The pool's own clip still wins, so a
        Warmup pool can deliberately start a song from the top.
        """
        pool = pool or self.active
        clip = pool.clip_for(track)
        if clip:
            return clip
        for other in self.pools.values():
            if other is not pool:
                clip = other.clip_for(track)
                if clip:
                    return clip
        return None

    def add(self, name, playlist=""):
        name = name.strip()
        if not name or name in self.pools:
            return None
        self.pools[name] = Pool(name, playlist=playlist)
        return self.pools[name]

    def remove(self, name):
        if len(self.pools) <= 1 or name not in self.pools:
            return False
        del self.pools[name]
        if self.active_name == name:
            self.active_name = next(iter(self.pools))
        return True

    def save_into_config(self):
        self.config.set("pools", {n: p.to_dict() for n, p in self.pools.items()})
        self.config.set("active_pool", self.active_name)
