"""PA announcer: Hume AI voice, disk cache, and non-blocking playback.

Three problems with the original implementation, all fixed here:

1. It blocked the tkinter main loop for up to 5 seconds per announcement, so
   the whole app froze mid-game. Everything now runs on a worker thread.
2. A 5s timeout on rink wifi meant announcements silently got skipped. Cached
   audio plays instantly and offline, the timeout is configurable, and there is
   a real macOS `say` fallback (the old code promised one but just gave up).
3. The music kept blasting over the announcement. Now it ducks and comes back.
"""

import base64
import hashlib
import os
import queue
import socket
import subprocess
import threading
import time

from . import paths

QUOTA_BACKOFF = 10 * 60      # seconds to skip Hume after a 429


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

    def announce(self, text, celebration=None, on_status=None):
        """Queue an announcement. Returns immediately; never blocks the UI.

        `celebration` is an optional sound-clip path played right after.
        `on_status` is called from the worker thread with progress strings --
        wrap it in `root.after` before touching widgets.
        """
        self._ensure_worker()
        self._jobs.put((text, celebration, on_status))

    def _ensure_worker(self):
        if self._worker is None or not self._worker.is_alive():
            self._worker = threading.Thread(target=self._run_jobs, daemon=True)
            self._worker.start()

    def _run_jobs(self):
        while True:
            text, celebration, on_status = self._jobs.get()
            try:
                self._play_one(text, celebration, on_status)
            except Exception as e:                     # keep the worker alive
                print(f"❌ Announcement failed: {e}")
            finally:
                self._jobs.task_done()

    def _play_one(self, text, celebration, on_status):
        def status(msg):
            if on_status:
                on_status(msg)

        cached = self.is_cached(text)
        status("📢 Announcing…" if cached else "📢 Rendering announcement…")

        audio = self.render(text) if self.config.get("announcer.use_cache", True) \
            else self.render(text, force=True)

        ducked = self._duck()
        try:
            if audio:
                subprocess.run(["afplay", str(audio)], check=False)
                status(f"📢 {text}")
            else:
                # Hume unavailable -- the show still goes on.
                voice = self.config.get("announcer.fallback_voice", "Alex")
                subprocess.run(["say", "-v", voice, text], check=False)
                status(f"📢 (macOS voice) {text}")

            if celebration and os.path.exists(celebration):
                subprocess.run(["afplay", str(celebration)], check=False)
        finally:
            self._unduck(ducked)

    def _duck(self):
        if not (self.music and self.config.get("audio.duck_enabled", True)):
            return None
        if not self.music.is_playing():
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
