"""Josh's recorded voice: short clips joined into home announcements.

Hume shuts down 2026-11-13, so home calls are built from pieces Josh recorded
himself (docs/RECORDED_VOICE.md). The clips live in paths.VOICE_DIR with a
manifest that maps each spoken line to one or more takes:

    {"clips": {"Patriots GOAL!!": ["A1.wav", "A2.wav", "A3.wav"],
               "Number 7, Alexander Mellen!": ["B3.wav"], ...}}

A line with several takes rotates at random, so six goals don't all open on
the same "GOAL!!". The Hume cache is separate and untouched; Settings picks
which voice home calls use, and anything missing here falls back to Hume.
"""

import hashlib
import json
import random

from . import paths

MANIFEST = "manifest.json"

# Gaps between recorded pieces. Josh's clips are trimmed to the voice, so
# these are the whole pause a listener hears.
PAUSE_SENTENCE = 0.30        # "GOAL!!" | "Scored by",  "Mellen!" | "Assisted by"
PAUSE_COMMA = 0.18
PAUSE_WORD = 0.08            # "Scored by" | "Number 7",  "Brown" | "and"
TAIL = 0.15                  # kept after the last word, before any celebration


def pause_after(text):
    if text.endswith(("!", ".", "?")):
        return PAUSE_SENTENCE
    if text.endswith(","):
        return PAUSE_COMMA
    return PAUSE_WORD


class RecordedVoice:
    def __init__(self, directory=None):
        self.dir = directory or paths.VOICE_DIR
        self.clips = {}
        self.reload()

    def reload(self):
        try:
            data = json.loads((self.dir / MANIFEST).read_text())
            clips = data.get("clips", {})
        except (OSError, ValueError, AttributeError):
            clips = {}
        self.clips = {text: [self.dir / f for f in files]
                      for text, files in clips.items()
                      if any((self.dir / f).exists() for f in files)}

    def __len__(self):
        return len(self.clips)

    def has(self, text):
        return text in self.clips

    def has_all(self, lines):
        return bool(lines) and all(self.has(t) for t in lines)

    def missing(self, lines):
        return [t for t in lines if not self.has(t)]

    def take(self, text):
        files = [f for f in self.clips.get(text, []) if f.exists()]
        return random.choice(files) if files else None

    def assembled(self, lines):
        """One WAV saying `lines` in order, or None if any line isn't recorded.

        Saved under joined/ keyed on the takes chosen, so a repeat call plays
        straight from disk.
        """
        from .announcer import join        # announcer imports this module
        if not self.has_all(lines):
            return None
        try:
            files = [self.take(t) for t in lines]
            if not all(files):
                return None
            key = "|".join(f"{f.name}:{f.stat().st_mtime_ns}" for f in files)
            out = self.dir / "joined" / (hashlib.sha256(key.encode()).hexdigest()[:20] + ".wav")
            if out.exists() and out.stat().st_size > 0:
                return out
            out.parent.mkdir(parents=True, exist_ok=True)
            parts = [(f, pause_after(t)) for f, t in zip(files, lines)]
            parts[-1] = (parts[-1][0], TAIL)
            return join(parts, out)
        except OSError:
            return None
