"""PA announcer: Hume AI voice, disk cache, and non-blocking playback.

Three problems with the original implementation, all fixed here:

1. It blocked the tkinter main loop for up to 5 seconds per announcement, so
   the whole app froze mid-game. Everything now runs on a worker thread.
2. A 5s timeout on rink wifi meant announcements silently got skipped. Cached
   audio plays instantly and offline, the timeout is configurable, and there is
   a real macOS `say` fallback (the old code promised one but just gave up).
3. The music kept blasting over the announcement. Now it ducks and comes back.
"""

import array
import base64
import hashlib
import os
import queue
import socket
import subprocess
import threading
import time
import wave
from pathlib import Path

from . import paths
from .voice import RecordedVoice

QUOTA_BACKOFF = 10 * 60      # seconds to skip Hume after a 429

# Stitching: announcement + celebration clip become one file so the "WOO"
# lands right on the end of the call instead of a second afplay later.
COMBO_DIR = paths.TTS_CACHE_DIR / "combo"
GAP_AFTER_CALL = 0.15        # seconds between the last word and the clip
SILENCE = 0.02               # amplitude below this counts as silence (0..1)
_PCM = "LEI16@44100"

# Joining away-goal pieces: Hume pads every line with silence at both ends.
# Trimmed to these, a call joined from pieces keeps a speaker's rhythm.
PAUSE_AFTER_COMMA = 0.18     # "number 12," | "assisted by"
PAUSE_BETWEEN = 0.05         # "Goal scored by" | "number 12,"
EDGE = 0.02                  # silence kept at each trimmed edge


def _decode_pcm(src, dst):
    """Any audio afplay can read -> 16-bit 44.1k stereo WAV. Returns True on success."""
    r = subprocess.run(["afconvert", "-f", "WAVE", "-d", _PCM, "-c", "2",
                        str(src), str(dst)], capture_output=True)
    return r.returncode == 0 and os.path.exists(dst)


def _trim_tail(samples, channels, rate, keep=GAP_AFTER_CALL):
    """Drop trailing silence from an int16 array, keeping `keep` seconds of it."""
    limit = int(SILENCE * 32767)
    last = len(samples) - 1
    while last >= 0 and abs(samples[last]) < limit:
        last -= 1
    end = min(len(samples), last + 1 + int(keep * rate) * channels)
    end -= end % channels
    return samples[:end]


def _trim_head(samples, channels, rate, keep=0.0):
    """Drop leading silence from an int16 array, keeping `keep` seconds of it."""
    limit = int(SILENCE * 32767)
    first = 0
    while first < len(samples) and abs(samples[first]) < limit:
        first += 1
    start = max(0, first - first % channels - int(keep * rate) * channels)
    return samples[start:]


def join(parts, out_path):
    """Write [(audio_path, pause_after), ...] as one WAV, each part trimmed of
    silence at both ends. The last part keeps its pause as a tail. Returns
    out_path or None."""
    temps = []
    try:
        audio, fmt = array.array("h"), None
        for i, (src, pause) in enumerate(parts):
            tmp = out_path.with_suffix(f".{i}.wav")
            temps.append(tmp)
            if not _decode_pcm(src, tmp):
                return None
            with wave.open(str(tmp)) as w:
                this = (w.getframerate(), w.getnchannels(), w.getsampwidth())
                if fmt and this != fmt:
                    return None
                fmt = this
                a = array.array("h"); a.frombytes(w.readframes(w.getnframes()))
            rate, ch = fmt[0], fmt[1]
            # A hair of the silence stays so a soft first or last sound isn't clipped.
            a = _trim_tail(_trim_head(a, ch, rate, EDGE), ch, rate, EDGE)
            audio.extend(a)
            audio.extend([0] * (int(pause * rate) * ch))
        if fmt is None:
            return None
        tmp_out = out_path.with_suffix(".part")
        with wave.open(str(tmp_out), "wb") as w:
            w.setnchannels(fmt[1]); w.setsampwidth(2); w.setframerate(fmt[0])
            w.writeframes(audio.tobytes())
        tmp_out.replace(out_path)
        return out_path
    except (OSError, wave.Error, EOFError):
        return None
    finally:
        for t in temps:
            try:
                t.unlink()
            except OSError:
                pass


def stitch(announcement, celebration, out_path):
    """Write announcement(trimmed) + celebration as one WAV. Returns out_path or None."""
    tmp_a = out_path.with_suffix(".a.wav")
    tmp_b = out_path.with_suffix(".b.wav")
    try:
        if not (_decode_pcm(announcement, tmp_a) and _decode_pcm(celebration, tmp_b)):
            return None
        with wave.open(str(tmp_a)) as wa, wave.open(str(tmp_b)) as wb:
            if (wa.getframerate(), wa.getnchannels(), wa.getsampwidth()) != \
               (wb.getframerate(), wb.getnchannels(), wb.getsampwidth()):
                return None
            rate, ch = wa.getframerate(), wa.getnchannels()
            a = array.array("h"); a.frombytes(wa.readframes(wa.getnframes()))
            b = wb.readframes(wb.getnframes())
        a = _trim_tail(a, ch, rate)
        tmp_out = out_path.with_suffix(".part")
        with wave.open(str(tmp_out), "wb") as w:
            w.setnchannels(ch); w.setsampwidth(2); w.setframerate(rate)
            w.writeframes(a.tobytes()); w.writeframes(b)
        tmp_out.replace(out_path)
        return out_path
    except (OSError, wave.Error, EOFError):
        return None
    finally:
        for t in (tmp_a, tmp_b):
            try:
                t.unlink()
            except OSError:
                pass


def _is_quota_error(message):
    text = str(message)
    return "429" in text and ("quota" in text.lower() or "rate limit" in text.lower())


def _short_error(message):
    """The SDK's error string is a wall of response headers; keep the tail."""
    text = str(message)
    i = text.find("status_code")
    return text[i:i + 200] if i >= 0 else text[:200]

try:
    from hume import HumeClient
    from hume.tts import PostedUtterance, PostedUtteranceVoiceWithName
    from dotenv import load_dotenv

    # ~/.hockey_music/.env wins, so a shared .app bundle never carries a key.
    for env_file in (paths.DATA_DIR / ".env", paths.PROJECT_ROOT / ".env"):
        if env_file.exists():
            load_dotenv(env_file)
            break
    else:
        load_dotenv()
    HUME_SDK = True
except ImportError:
    HUME_SDK = False

HUME_API_KEY = os.getenv("HUME_API_KEY")
HUME_VOICE_ID = os.getenv("HUME_VOICE_ID") or "Hockey Goal Announcer"


class Announcer:
    """Renders and plays PA announcements without stalling the UI."""

    def __init__(self, config, music=None):
        self.config = config
        self.music = music
        self.voice_id = HUME_VOICE_ID
        self._jobs = queue.Queue()
        self._worker = None
        # After a 429 (account quota exhausted) Hume is skipped for a while, so
        # a goal call falls straight through to the macOS voice instead of
        # waiting on a request that is going to fail anyway.
        self.quota_exhausted_at = None
        self.voice = RecordedVoice()
        paths.ensure_dirs()

    # -- capability -------------------------------------------------------

    @property
    def hume_available(self):
        return bool(HUME_SDK and HUME_API_KEY and self.voice_id)

    @property
    def quota_exhausted(self):
        if self.quota_exhausted_at is None:
            return False
        if time.time() - self.quota_exhausted_at > QUOTA_BACKOFF:
            self.quota_exhausted_at = None      # try again after the backoff
            return False
        return True

    @property
    def can_render(self):
        """True if an uncached line has a real chance of coming out of Hume now."""
        return self.hume_available and not self.quota_exhausted

    @property
    def status_text(self):
        if self.hume_available and self.quota_exhausted:
            return "macOS voice (Hume quota exhausted -- check your Hume plan)"
        if self.hume_available:
            return f"Hume voice: {self.voice_id}"
        if not HUME_SDK:
            return "macOS voice (Hume SDK not installed)"
        if not HUME_API_KEY:
            return "macOS voice (no HUME_API_KEY in .env)"
        return "macOS voice"

    @property
    def use_recorded(self):
        """Home calls in Josh's recorded voice (Settings). Off = Hume, as before."""
        return self.config.get("announcer.home_voice", "hume") == "recorded"

    def recorded_ready(self, lines):
        return bool(lines) and self.use_recorded and self.voice.has_all(lines)

    # -- cache ------------------------------------------------------------

    def cache_path(self, text):
        """Where this exact line, in this exact voice, lives on disk."""
        digest = hashlib.sha256(
            f"{self.voice_id}|{text}".encode("utf-8")).hexdigest()[:20]
        return paths.TTS_CACHE_DIR / f"{digest}.wav"

    def is_cached(self, text):
        p = self.cache_path(text)
        return p.exists() and p.stat().st_size > 0

    def cache_stats(self):
        files = list(paths.TTS_CACHE_DIR.glob("*.wav"))
        return len(files), sum(f.stat().st_size for f in files)

    def clear_cache(self):
        removed = 0
        for f in paths.TTS_CACHE_DIR.glob("*.wav"):
            try:
                f.unlink()
                removed += 1
            except OSError:
                pass
        return removed

    # -- synthesis --------------------------------------------------------

    def render(self, text, force=False):
        """Return a playable audio file for `text`, synthesising if needed.

        Blocking -- call from a worker thread or the prerender dialog, never
        from the tkinter main loop. Returns None if Hume is unreachable.
        """
        path = self.cache_path(text)
        if path.exists() and path.stat().st_size > 0 and not force:
            return path
        if not self.hume_available or self.quota_exhausted:
            return None

        audio = self._synthesize(text)
        if audio is None:
            return None
        try:
            tmp = path.with_suffix(".part")
            tmp.write_bytes(audio)
            tmp.replace(path)
            return path
        except OSError as e:
            print(f"❌ Could not cache announcement: {e}")
            return None

    def _synthesize(self, text):
        """One Hume TTS call. Returns raw audio bytes or None."""
        timeout = float(self.config.get("announcer.timeout", 20.0))
        result = queue.Queue(maxsize=1)

        def work():
            try:
                # Fail fast when the rink wifi is down rather than hanging.
                socket.setdefaulttimeout(3)
                try:
                    socket.getaddrinfo("api.hume.ai", 443)
                except socket.error as e:
                    result.put(("error", f"network unreachable: {e}"))
                    return

                client = HumeClient(api_key=HUME_API_KEY)
                utterance = PostedUtterance(
                    text=text,
                    voice=PostedUtteranceVoiceWithName(
                        name=self.voice_id, provider="CUSTOM_VOICE"),
                )
                res = client.tts.synthesize_json(utterances=[utterance])
                if res and res.generations:
                    result.put(("ok", base64.b64decode(res.generations[0].audio)))
                else:
                    result.put(("error", "no audio generated"))
            except Exception as e:                     # SDK raises many types
                result.put(("error", str(e)))

        t = threading.Thread(target=work, daemon=True)
        t.start()
        t.join(timeout=timeout)
        if t.is_alive():
            print(f"⏱️  Hume timed out after {timeout:.0f}s")
            return None
        try:
            status, payload = result.get_nowait()
        except queue.Empty:
            return None
        if status != "ok":
            if _is_quota_error(payload):
                self.quota_exhausted_at = time.time()
                print("❌ Hume quota exhausted (HTTP 429). Using the macOS voice for "
                      f"uncached lines; will retry Hume in {QUOTA_BACKOFF // 60} min.")
            else:
                print(f"❌ Hume error: {_short_error(payload)}")
            return None
        return payload

    # -- playback ---------------------------------------------------------

    def announce(self, text, celebration=None, on_status=None, pieces=None,
                 recorded=None):
        """Queue an announcement. Returns immediately; never blocks the UI.

        `celebration` is an optional sound-clip path played right after.
        `pieces` are short cached lines that together say `text` (an away
        goal); they're joined and played when `text` itself isn't cached.
        `recorded` are lines in Josh's recorded voice that together say `text`
        (a home call); when they're all recorded and Settings picks that voice,
        they win over Hume.
        `on_status` is called from the worker thread with progress strings --
        wrap it in `root.after` before touching widgets.
        """
        self._ensure_worker()
        self._jobs.put((text, celebration, on_status, pieces, recorded))

    def _ensure_worker(self):
        if self._worker is None or not self._worker.is_alive():
            self._worker = threading.Thread(target=self._run_jobs, daemon=True)
            self._worker.start()

    def _run_jobs(self):
        while True:
            text, celebration, on_status, pieces, recorded = self._jobs.get()
            try:
                self._play_one(text, celebration, on_status, pieces, recorded)
            except Exception as e:                     # keep the worker alive
                print(f"❌ Announcement failed: {e}")
            finally:
                self._jobs.task_done()

    def _play_one(self, text, celebration, on_status, pieces=None, recorded=None):
        def status(msg):
            if on_status:
                on_status(msg)

        if self.recorded_ready(recorded):
            audio = self.voice.assembled(recorded)
            if audio:
                status("🎙 Announcing…")
                self._play(audio, celebration, text, status)
                return

        use_cache = self.config.get("announcer.use_cache", True)
        cached = self.is_cached(text)
        # Order: the whole line cached -> joined from cached pieces -> render
        # the whole line from Hume -> skip.
        audio = None
        if use_cache and not cached and pieces:
            audio = self.assembled(pieces)
        status("📢 Announcing…" if cached or audio else "📢 Rendering announcement…")

        if not audio:
            audio = self.render(text) if use_cache else self.render(text, force=True)

        if not audio and not self.config.get("announcer.fallback_enabled", False):
            # Josh would rather a goal go unannounced than robot-voiced. Leave
            # the music alone too -- nothing is going to play.
            status(f"⛔ Not announced (no Hume audio): {text}")
            return

        self._play(audio, celebration, text, status)

    def _play(self, audio, celebration, text, status):
        """Duck, play `audio` (or the macOS voice if None), then the celebration."""
        ducked = self._duck()
        try:
            if audio:
                combo = self.combined(audio, celebration) if celebration else None
                subprocess.run(["afplay", str(combo or audio)], check=False)
                status(f"📢 {text}")
                if combo:
                    celebration = None          # already played, gap-free
            else:
                voice = self.config.get("announcer.fallback_voice", "Alex")
                subprocess.run(["say", "-v", voice, text], check=False)
                status(f"📢 (macOS voice) {text}")

            if celebration and os.path.exists(celebration):
                subprocess.run(["afplay", str(celebration)], check=False)
        finally:
            self._unduck(ducked)

    def pieces_cached(self, pieces):
        return bool(pieces) and all(self.is_cached(p) for p in pieces)

    def assembled(self, pieces):
        """One file joined from cached pieces, or None if any piece is missing.

        Saved under combo/ keyed on each piece's file and mtime, so the second
        time a call is made it plays straight from disk.
        """
        if not self.pieces_cached(pieces):
            return None
        try:
            files = [self.cache_path(p) for p in pieces]
            key = "pieces|" + "|".join(f"{f.name}:{f.stat().st_mtime_ns}" for f in files)
            out = COMBO_DIR / (hashlib.sha256(key.encode()).hexdigest()[:20] + ".wav")
            if out.exists() and out.stat().st_size > 0:
                return out
            COMBO_DIR.mkdir(parents=True, exist_ok=True)
            parts = [(f, PAUSE_AFTER_COMMA if p.endswith(",") else PAUSE_BETWEEN)
                     for f, p in zip(files, pieces)]
            parts[-1] = (parts[-1][0], GAP_AFTER_CALL)
            return join(parts, out)
        except OSError:
            return None

    def combined(self, audio, celebration):
        """Announcement + celebration as one cached file, or None if stitching fails.

        Hume leaves 0.5-1.2s of silence after the last word, and a second
        afplay costs most of another second to start. One file, trimmed, puts
        the WOO right on the end of the call. Keyed on both files' identity
        and mtime, so a re-rendered take or a swapped clip re-stitches.
        """
        try:
            audio, celebration = Path(audio), Path(celebration)
            if not (audio.exists() and celebration.exists()):
                return None
            key = f"{audio.name}|{audio.stat().st_mtime_ns}|" \
                  f"{celebration.resolve()}|{celebration.stat().st_mtime_ns}"
            out = COMBO_DIR / (hashlib.sha256(key.encode()).hexdigest()[:20] + ".wav")
            if out.exists() and out.stat().st_size > 0:
                return out
            COMBO_DIR.mkdir(parents=True, exist_ok=True)
            return stitch(audio, celebration, out)
        except OSError:
            return None

    def _duck(self):
        if not self.music or not self.music.is_playing():
            return None
        if self.config.get("audio.announce_stops_music", True):
            # A goal call over the goal song is mush. Kill the music outright;
            # the operator cues the next track after the announcement.
            self.music.cancel_fades()
            self.music.stop()
            return None
        if not self.config.get("audio.duck_enabled", True):
            return None
        level = int(self.config.get("audio.duck_volume", 25))
        return self.music.duck(level)

    def _unduck(self, restore_to):
        if restore_to is not None and self.music:
            self.music.unduck(restore_to)

    # -- batch prerender --------------------------------------------------

    def prerender(self, items, progress=None, should_stop=None):
        """Render (key, text) pairs to the cache. Blocking; run in a thread.

        Returns (rendered, skipped, failed).
        """
        rendered = skipped = failed = 0
        total = len(items)
        for i, (_key, text) in enumerate(items, start=1):
            if should_stop and should_stop():
                break
            if self.is_cached(text):
                skipped += 1
            elif self.render(text):
                rendered += 1
            else:
                failed += 1
                if self.quota_exhausted:
                    # Every further line would fail the same way. Count them
                    # and stop instead of hammering the API 250 more times.
                    failed += total - i
                    if progress:
                        progress(total, total, "Hume quota exhausted -- stopped")
                    break
            if progress:
                progress(i, total, text)
        return rendered, skipped, failed
