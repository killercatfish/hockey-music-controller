"""Find where a song's vibe is high, so a clip starts on the hook, not the intro.

Apple Music subscription tracks are DRM-protected, so the audio itself can't
be analysed. What *is* available is time-synced lyrics: LRCLIB (lrclib.net)
serves them free, with no key, for most mainstream songs. The chorus is the
most-repeated block of lines, and a clip that starts a beat before its first
appearance lands on the part the crowd knows.

Instrumentals and songs with no synced lyrics get no proposal -- whatever clip
they have today stays.

Nothing here writes to the config on its own. `propose` writes a proposal file
to ~/.hockey_music/; `apply` backs the config up and then writes the clips.
"""

import argparse
import json
import re
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from . import paths

LRCLIB = "https://lrclib.net/api"
USER_AGENT = ("hockey-music-controller/3.1 "
              "(https://github.com/killercatfish/hockey-music-controller)")

LYRICS_CACHE_DIR = paths.DATA_DIR / "lyrics_cache"
PROPOSALS_FILE = paths.DATA_DIR / "hype_proposals.json"

LEAD_IN = 1            # seconds of run-up before the first chorus word
MIN_TAIL = 25          # a chorus this close to the end is useless at a whistle
MIN_MASS = 4           # smallest repeated block worth trusting (2 lines x 2 plays)

_TIMESTAMP = re.compile(r"\[(\d+):(\d+(?:\.\d+)?)\]")
_BRACKETS = re.compile(r"\s*[\(\[][^\)\]]*[\)\]]")
_SUFFIX = re.compile(r"\s+-\s+.*$")
_PUNCT = re.compile(r"[^\w\s']")
_STOPWORDS = {"the", "and", "you", "your", "for", "with", "that", "this",
              "feat", "remix", "edit", "mix", "version", "radio"}


# ---------------------------------------------------------------------------
# Lyrics parsing and chorus detection (pure functions; unit-tested)
# ---------------------------------------------------------------------------

def parse_lrc(text):
    """Turn LRC text into a sorted list of (seconds, line) pairs.

    A line may carry several timestamps (a repeated lyric); each becomes its
    own entry. Blank lines and untimed lines are dropped.
    """
    lines = []
    for raw in (text or "").splitlines():
        stamps = _TIMESTAMP.findall(raw)
        if not stamps:
            continue
        body = _TIMESTAMP.sub("", raw).strip()
        if not body:
            continue
        for minutes, seconds in stamps:
            lines.append((int(minutes) * 60 + float(seconds), body))
    lines.sort(key=lambda pair: pair[0])
    return lines


def normalize(line):
    """Lower-case, strip punctuation, collapse spaces -- so 'Thunder!' == 'thunder'."""
    return " ".join(_PUNCT.sub(" ", line.lower()).split())


def clean_title(title):
    """'Cruise (Remix) [feat. Nelly]' -> 'Cruise'; 'Old Town Road - Remix' -> 'Old Town Road'."""
    t = _BRACKETS.sub("", title or "")
    t = _SUFFIX.sub("", t)
    return t.strip() or (title or "").strip()


def title_tokens(title):
    tokens = normalize(clean_title(title)).split()
    return {t for t in tokens if len(t) >= 3 and t not in _STOPWORDS}


@dataclass
class HypePoint:
    start: int            # clip start, whole seconds
    chorus_at: float      # timestamp of the first chorus line
    line: str             # that line, for the human reviewing the proposal
    repeats: int          # how many times the block's lines recur
    block_lines: int
    confidence: str       # "high" or "medium"

    def to_dict(self):
        return asdict(self)


def find_chorus(lines, title="", duration=None):
    """Pick the first strong repeated block of lyrics. Returns HypePoint or None.

    Method: count how often each (normalised) line occurs; group consecutive
    repeated lines into runs; score a run by its total repetition, with a
    bonus when it contains the song title. The best-scoring run wins, but any
    run scoring at least half as much *and appearing earlier* is preferred --
    at a stoppage you want the hook soon, not the biggest chorus at 2:40.
    """
    if len(lines) < 4:
        return None
    norm = [normalize(text) for _, text in lines]
    counts = Counter(norm)
    repeats = [counts[n] if n else 0 for n in norm]
    wanted = title_tokens(title)

    runs = []
    i = 0
    while i < len(lines):
        if repeats[i] < 2:
            i += 1
            continue
        j = i
        while j < len(lines) and repeats[j] >= 2:
            j += 1
        mass = sum(repeats[i:j])
        has_title = bool(wanted) and any(
            wanted <= set(n.split()) for n in norm[i:j])
        score = mass * (1.5 if has_title else 1.0)
        runs.append((score, i, j, mass))
        i = j

    if not runs:
        return None

    def first_occurrence(run):
        """Where this run's *content* first appears in the song.

        The heaviest run is usually the outro, where the chorus repeats four
        times in a row -- but those same lines were first sung at 0:55, and
        that's where the clip should start.
        """
        _, i, j, _ = run
        content = set(norm[i:j])
        for k in range(len(norm)):
            if norm[k] in content and (k + 1 < len(norm) and norm[k + 1] in content
                                       or j - i == 1):
                return k
        return i

    best = max(score for score, *_ in runs)
    candidates = [r for r in runs if r[0] >= 0.5 * best and r[3] >= MIN_MASS]
    if not candidates:
        return None
    chosen = min(candidates, key=first_occurrence)
    i = first_occurrence(chosen)
    j = chosen[2]

    # A chorus that only shows up past the 60% mark is a late chorus; take the
    # earliest repeated block instead so there is something to play.
    if duration and lines[i][0] > 0.6 * duration:
        fallback = [r for r in runs if r[3] >= MIN_MASS]
        if fallback:
            chosen = min(fallback, key=first_occurrence)
            i, j = first_occurrence(chosen), chosen[2]

    chorus_at = lines[i][0]
    if duration and chorus_at > duration - MIN_TAIL:
        return None
    start = max(0, int(chorus_at) - LEAD_IN)
    if start <= 3:
        start = 0
    span = max(j - i, chosen[2] - chosen[1])
    block_repeats = max(repeats[chosen[1]:chosen[2]])
    confidence = "high" if span >= 3 and block_repeats >= 3 else "medium"
    return HypePoint(start=start, chorus_at=round(chorus_at, 2), line=lines[i][1],
                     repeats=block_repeats, block_lines=chosen[2] - chosen[1],
                     confidence=confidence)


# ---------------------------------------------------------------------------
# LRCLIB client with an on-disk cache (so re-runs work offline)
# ---------------------------------------------------------------------------

def _cache_file(name, artist, album, duration):
    import hashlib
    key = f"{name}|{artist}|{album}|{int(duration or 0)}"
    return LYRICS_CACHE_DIR / (hashlib.sha256(key.encode("utf-8")).hexdigest()[:20] + ".json")


def _http_json(path, params, timeout=10):
    url = f"{LRCLIB}/{path}?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.load(resp), None
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None, None
        return None, f"HTTP {e.code}"
    except (urllib.error.URLError, OSError, ValueError) as e:
        return None, str(e)


def _primary_artist(artist):
    return re.split(r"\s*(?:/|,|&|\bfeat\.?\b)\s*", artist or "", maxsplit=1)[0].strip()


def fetch_lyrics(name, artist, album="", duration=None, refresh=False):
    """Return (record, error). `record` is LRCLIB's JSON or None for a miss.

    Tries an exact lookup first, then a looser one without the album, then a
    search on the cleaned title, keeping only a result whose duration is
    within 5 seconds of ours (so a live version doesn't stand in for the
    studio cut). Misses are cached too, so a re-run doesn't re-ask.
    """
    LYRICS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache = _cache_file(name, artist, album, duration)
    if cache.exists() and not refresh:
        try:
            return json.loads(cache.read_text()).get("record"), None
        except (json.JSONDecodeError, OSError):
            pass

    record, err = None, None
    attempts = [
        ("get", {"track_name": name, "artist_name": artist,
                 "album_name": album, "duration": int(duration or 0)}),
        ("get", {"track_name": name, "artist_name": artist}),
        ("get", {"track_name": clean_title(name), "artist_name": _primary_artist(artist)}),
    ]
    for path, params in attempts:
        params = {k: v for k, v in params.items() if v}
        record, err = _http_json(path, params)
        if err:
            return None, err            # network trouble: don't cache, don't guess
        if record and record.get("syncedLyrics"):
            break
        record = None
        time.sleep(0.1)

    if record is None:
        results, err = _http_json("search", {
            "track_name": clean_title(name), "artist_name": _primary_artist(artist)})
        if err:
            return None, err
        for r in results or []:
            if not r.get("syncedLyrics"):
                continue
            if duration and abs(float(r.get("duration") or 0) - duration) > 5:
                continue
            record = r
            break

    try:
        cache.write_text(json.dumps({"record": record}))
    except OSError:
        pass
    return record, None


# ---------------------------------------------------------------------------
# Proposals
# ---------------------------------------------------------------------------

def propose_for_track(meta, refresh=False):
    """meta: {"track", "name", "artist", "album", "duration"}.

    Returns (HypePoint or None, reason). `reason` explains a miss.
    """
    record, err = fetch_lyrics(meta["name"], meta["artist"], meta.get("album", ""),
                               meta.get("duration"), refresh=refresh)
    if err:
        return None, f"lookup failed: {err}"
    if record is None:
        return None, "no synced lyrics"
    if record.get("instrumental"):
        return None, "instrumental"
    lines = parse_lrc(record.get("syncedLyrics") or "")
    point = find_chorus(lines, title=meta["name"], duration=meta.get("duration"))
    if point is None:
        return None, "no repeated chorus found"
    return point, "ok"


def build_proposals(track_meta, current_clips, progress=None, refresh=False):
    """Run every track through the lookup. Returns the proposal document."""
    proposals, misses = {}, {}
    for i, meta in enumerate(track_meta, start=1):
        point, reason = propose_for_track(meta, refresh=refresh)
        prev = current_clips.get(meta["track"])
        if point:
            entry = point.to_dict()
            entry["previous"] = prev.start if prev else None
            proposals[meta["track"]] = entry
        else:
            misses[meta["track"]] = reason
        if progress:
            progress(i, len(track_meta), meta["track"], point, reason)
    return {"generated": datetime.now().isoformat(timespec="seconds"),
            "proposals": proposals, "misses": misses}


def apply_proposals(config, pool_name, proposals):
    """Write proposed starts into a pool's clips, keeping any end points.

    Pure config mutation -- the caller backs up and saves. Returns the number
    of clips changed.
    """
    pools = config.get("pools") or {}
    pool = pools.get(pool_name)
    if pool is None:
        raise KeyError(f"No pool named {pool_name!r}")
    clips = pool.setdefault("clips", {})
    changed = 0
    for track, entry in proposals.items():
        start = int(entry["start"])
        existing = clips.get(track)
        if isinstance(existing, dict):
            end = existing.get("end")
            if existing.get("start") == start:
                continue
        else:
            end = None
        if start == 0 and end is None:
            if existing is not None:
                clips.pop(track)
                changed += 1
            continue
        clips[track] = {"start": start, "end": end}
        changed += 1
    config.set("pools", pools)
    return changed


def backup_config(tag="hype"):
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = paths.CONFIG_FILE.with_name(f"{paths.CONFIG_FILE.name}.bak-{tag}-{stamp}")
    shutil.copy2(paths.CONFIG_FILE, backup)
    return backup


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _fmt(seconds):
    seconds = int(seconds or 0)
    return f"{seconds // 60}:{seconds % 60:02d}"


def _load_proposals(path):
    path = Path(path)
    if not path.exists():
        sys.exit(f"No proposal file at {path}. Run: python3 hype_points.py propose")
    return json.loads(path.read_text())


def cmd_propose(args):
    from .config import Config
    from .music import AppleMusicController
    from .playlists import PoolSet

    config = Config.load()
    pools = PoolSet(config)
    if args.pool not in pools.pools:
        sys.exit(f"No pool named {args.pool!r}. Pools: {', '.join(pools.names)}")
    pool = pools.pools[args.pool]
    if not pool.playlist:
        sys.exit(f"Pool {args.pool!r} has no Apple Music playlist assigned.")

    print(f"Reading “{pool.playlist}” from Apple Music…")
    meta = AppleMusicController().get_playlist_track_meta(pool.playlist)
    if not meta:
        sys.exit("Could not read the playlist. Is Music running?")
    print(f"{len(meta)} tracks. Looking up synced lyrics"
          f" (cached in {LYRICS_CACHE_DIR})…")

    def progress(i, total, track, point, reason):
        mark = f"⏱ {_fmt(point.start):>5}  {point.confidence:6}" if point else f"   --     {reason}"
        print(f"  {i:>3}/{total}  {mark}  {track[:70]}")

    doc = build_proposals(meta, pool.clips, progress=progress, refresh=args.refresh)
    doc["pool"] = args.pool
    doc["playlist"] = pool.playlist
    PROPOSALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROPOSALS_FILE.write_text(json.dumps(doc, indent=2))

    n, m = len(doc["proposals"]), len(doc["misses"])
    reasons = Counter(doc["misses"].values())
    print(f"\n{n} proposed, {m} unchanged ({', '.join(f'{v} {k}' for k, v in reasons.items())})")
    print(f"Wrote {PROPOSALS_FILE}")
    print("Review with:  python3 hype_points.py show\n"
          "Apply with:   python3 hype_points.py apply   (backs up the config first)")


def cmd_show(args):
    doc = _load_proposals(args.file)
    items = sorted(doc["proposals"].items(), key=lambda kv: kv[1]["start"])
    print(f"Pool “{doc.get('pool')}” · playlist “{doc.get('playlist')}”"
          f" · generated {doc.get('generated')}\n")
    print(f"{'start':>6} {'was':>5}  {'conf':6}  track  ·  first chorus line")
    for track, e in items:
        was = _fmt(e["previous"]) if e.get("previous") is not None else "-"
        print(f"{_fmt(e['start']):>6} {was:>5}  {e['confidence']:6}  {track[:56]}"
              f"  ·  “{e['line'][:48]}”")
    if args.misses:
        print("\nUnchanged:")
        for track, reason in sorted(doc["misses"].items(), key=lambda kv: kv[1]):
            print(f"  {reason:26} {track}")
    print(f"\n{len(items)} proposals, {len(doc['misses'])} unchanged")


def cmd_apply(args):
    from .config import Config
    doc = _load_proposals(args.file)
    pool_name = args.pool or doc.get("pool")
    config = Config.load()
    if not (config.get("pools") or {}).get(pool_name):
        sys.exit(f"No pool named {pool_name!r} in the config.")
    backup = backup_config()
    changed = apply_proposals(config, pool_name, doc["proposals"])
    config.save()
    print(f"Backed up config to {backup}")
    print(f"Updated {changed} clip start points in pool “{pool_name}”.")
    print(f"Revert with:  python3 hype_points.py revert \"{backup}\"")


def cmd_revert(args):
    backups = sorted(paths.CONFIG_FILE.parent.glob(paths.CONFIG_FILE.name + ".bak-*"))
    backup = Path(args.backup) if args.backup else (backups[-1] if backups else None)
    if not backup or not backup.exists():
        sys.exit("No backup found." if not backup else f"No such file: {backup}")
    shutil.copy2(backup, paths.CONFIG_FILE)
    print(f"Restored {paths.CONFIG_FILE} from {backup.name}")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="hype_points.py",
        description="Propose clip start points at each song's chorus, from synced lyrics.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("propose", help="look up every track in a pool (network)")
    p.add_argument("--pool", default="Stoppage")
    p.add_argument("--refresh", action="store_true", help="ignore the lyrics cache")
    p.set_defaults(func=cmd_propose)

    p = sub.add_parser("show", help="print the proposal file")
    p.add_argument("--file", default=str(PROPOSALS_FILE))
    p.add_argument("--misses", action="store_true", help="also list tracks left unchanged")
    p.set_defaults(func=cmd_show)

    p = sub.add_parser("apply", help="write proposals into the config (after a backup)")
    p.add_argument("--file", default=str(PROPOSALS_FILE))
    p.add_argument("--pool", default=None, help="defaults to the pool in the proposal file")
    p.set_defaults(func=cmd_apply)

    p = sub.add_parser("revert", help="restore the config from a backup (latest by default)")
    p.add_argument("backup", nargs="?")
    p.set_defaults(func=cmd_revert)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
