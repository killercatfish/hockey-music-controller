"""Apple Music control via AppleScript, plus volume fading and ducking."""

import subprocess
import threading
import time

# AppleScript error for "no current track" -- a normal stopped state, not a fault.
_NO_TRACK = "(-1728)"

# Separators for bulk reads. Chosen to never appear in a song title or artist.
_FIELD_SEP = "␟"      # ␟ symbol for unit separator
_LIST_SEP = "␞"       # ␞ symbol for record separator


def _escape(s):
    """Escape a Python string for embedding in an AppleScript string literal."""
    return str(s).replace("\\", "\\\\").replace('"', '\\"')


def run_applescript(script, max_retries=3, retry_delay=0.5, silent=False, timeout=30):
    """Execute AppleScript. Returns (stdout, ok)."""
    for attempt in range(max_retries):
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True, text=True, timeout=timeout,
            )
            if result.returncode == 0:
                return result.stdout.strip(), True

            err = result.stderr.strip()
            if _NO_TRACK in err:
                return "", False  # stopped; nothing to retry
            if not silent:
                print(f"⚠️  AppleScript error ({attempt + 1}/{max_retries}): {err}")
        except subprocess.TimeoutExpired:
            if not silent:
                print(f"⏱️  AppleScript timeout ({attempt + 1}/{max_retries})")
        except OSError as e:
            if not silent:
                print(f"❌ AppleScript failed ({attempt + 1}/{max_retries}): {e}")
        if attempt < max_retries - 1:
            time.sleep(retry_delay)
    return "", False


class AppleMusicController:
    """Everything the app does to the Music app."""

    def __init__(self):
        # Music's own volume is shared by fades and ducking, so serialise access
        # and remember what the operator actually set it to.
        self._vol_lock = threading.RLock()
        self._base_volume = None
        self._fade_generation = 0
        # Music.app serialises AppleScript. Without this, the once-a-second UI
        # poll piles up behind a slow call (reading a 500-track playlist) and
        # everything times out.
        self._script_lock = threading.Lock()

    def _run(self, script, **kwargs):
        """Run a command, waiting for any in-flight script to finish."""
        with self._script_lock:
            return run_applescript(script, **kwargs)

    def _poll(self, script):
        """Read state for the UI. Returns (None, False) if Music is busy.

        Skipping a poll is always better than queueing one -- the next tick is
        700ms away, and a queued poll would delay the operator's next cue.
        """
        if not self._script_lock.acquire(blocking=False):
            return None, False
        try:
            return run_applescript(script, max_retries=1, silent=True)
        finally:
            self._script_lock.release()

    # -- library ----------------------------------------------------------

    def get_playlists(self):
        """User-created playlists only -- skips Library, Music Videos, and the
        auto-generated genre lists that just clutter the picker."""
        out, ok = self._run(
            'tell application "Music" to get name of every user playlist')
        return [p.strip() for p in out.split(",")] if ok and out else []

    def get_playlist_tracks(self, playlist_name):
        """Return ["Track | Artist", ...] for a playlist.

        Fetches the name and artist columns in bulk. Looping track-by-track in
        AppleScript costs ~16s on a 500-track playlist; this is ~0.1s.
        """
        name = _escape(playlist_name)
        script = f'''
        tell application "Music"
            set theNames to name of every track of playlist "{name}"
            set theArtists to artist of every track of playlist "{name}"
            set AppleScript's text item delimiters to "{_FIELD_SEP}"
            return (theNames as text) & "{_LIST_SEP}" & (theArtists as text)
        end tell
        '''
        out, ok = self._run(script)
        if ok and out and _LIST_SEP in out:
            names, _, artists = out.partition(_LIST_SEP)
            names = names.split(_FIELD_SEP)
            artists = artists.split(_FIELD_SEP)
            if len(names) == len(artists):
                return [f"{n.strip()} | {a.strip()}" for n, a in zip(names, artists)
                        if n.strip()]
        return self._get_playlist_tracks_slow(playlist_name)

    def get_playlist_track_meta(self, playlist_name):
        """Return [{"track", "name", "artist", "album", "duration", "cloud"}, ...].

        Same bulk-read trick as `get_playlist_tracks`, and the same "Name |
        Artist" key -- so a row here lines up with the pool's clips. Used by the
        hype-point lookup and the game-playlist generator, not by the UI.
        """
        name = _escape(playlist_name)
        script = f'''
        tell application "Music"
            set pl to playlist "{name}"
            set AppleScript's text item delimiters to "{_FIELD_SEP}"
            return ((name of every track of pl) as text) & "{_LIST_SEP}" & ¬
                ((artist of every track of pl) as text) & "{_LIST_SEP}" & ¬
                ((album of every track of pl) as text) & "{_LIST_SEP}" & ¬
                ((duration of every track of pl) as text) & "{_LIST_SEP}" & ¬
                ((cloud status of every track of pl) as text)
        end tell
        '''
        out, ok = self._run(script)
        if not (ok and out):
            return []
        columns = [c.split(_FIELD_SEP) for c in out.split(_LIST_SEP)]
        if len(columns) != 5 or len({len(c) for c in columns}) != 1:
            return []
        rows = []
        for n, a, album, dur, cloud in zip(*columns):
            if not n.strip():
                continue
            try:
                duration = float(dur)
            except ValueError:
                duration = None
            rows.append({"track": f"{n.strip()} | {a.strip()}", "name": n.strip(),
                         "artist": a.strip(), "album": album.strip(),
                         "duration": duration, "cloud": cloud.strip()})
        return rows

    def playlist_exists(self, playlist_name):
        out, ok = self._run(
            f'tell application "Music" to return exists user playlist "{_escape(playlist_name)}"')
        return ok and out == "true"

    def create_playlist_from(self, source_playlist, new_name, track_indices, chunk=40):
        """Make a new user playlist holding the given (1-indexed) tracks of another.

        Refuses to touch an existing playlist of that name. Copies in chunks so
        no single AppleScript call runs long enough to time out.
        """
        if self.playlist_exists(new_name):
            print(f"❌ Playlist “{new_name}” already exists; not touching it")
            return False
        src, dst = _escape(source_playlist), _escape(new_name)
        _, ok = self._run(
            f'tell application "Music" to make new user playlist with properties {{name:"{dst}"}}')
        if not ok:
            return False
        for i in range(0, len(track_indices), chunk):
            indices = ", ".join(str(int(x)) for x in track_indices[i:i + chunk])
            script = f'''
            tell application "Music"
                repeat with i in {{{indices}}}
                    duplicate track i of playlist "{src}" to playlist "{dst}"
                end repeat
            end tell
            '''
            _, ok = self._run(script, max_retries=1, timeout=120)
            if not ok:
                print(f"❌ Copying tracks into “{new_name}” failed partway")
                return False
        return True

    def _get_playlist_tracks_slow(self, playlist_name):
        """Per-track fallback for the rare playlist the bulk read chokes on."""
        script = f'''
        tell application "Music"
            set trackList to {{}}
            repeat with t in (every track of playlist "{_escape(playlist_name)}")
                set end of trackList to (name of t & " | " & artist of t)
            end repeat
            set AppleScript's text item delimiters to "{_FIELD_SEP}"
            return trackList as text
        end tell
        '''
        out, ok = self._run(script)
        if not (ok and out):
            return []
        return [t.strip() for t in out.split(_FIELD_SEP) if t.strip()]

    # -- playback ---------------------------------------------------------

    def play_track_from_playlist(self, playlist_name, track_index, start_time=None):
        """Play track `track_index` (1-indexed) of a playlist, optionally seeking."""
        ok = self._run(f'tell application "Music" to play track {int(track_index)} '
                       f'of playlist "{_escape(playlist_name)}"')[1]
        if not ok:
            print(f"❌ Could not play track {track_index} of '{playlist_name}'")
        elif start_time:
            self._seek_verified(start_time)
        return ok

    def play_track_by_name(self, track_name, start_time=None):
        ok = self._run(f'tell application "Music" to play track "{_escape(track_name)}"')[1]
        if ok and start_time:
            self._seek_verified(start_time)
        return ok

    def play_playlist(self, playlist_name):
        """Play a whole user playlist from its first track (Zamboni set etc)."""
        return self._run(f'tell application "Music" to play user playlist '
                         f'"{_escape(playlist_name)}"')[1]

    def play_song_or_playlist(self, name):
        """An event song may name a track OR a playlist. A playlist plays through
        from the top; a track plays alone. Used by the event buttons and the
        Settings ▶ Test button so both agree."""
        if self.playlist_exists(name):
            return self.play_playlist(name)
        return self.play_track_by_name(name)

    def _seek_verified(self, seconds, attempts=8, settle=0.25):
        """Seek to `seconds` once the player is ready, and confirm it took.

        Right after `play`, Music refuses `set player position` (error -10006)
        until the track is loaded. The old code slept a fixed 0.4s and hoped;
        when that missed, the retry re-issued `play` and the song restarted
        from 0:00 before jumping -- an audible blip at the rink. Now the seek
        is retried on its own, and the position is read back to prove it.
        """
        target = int(seconds)
        for _ in range(attempts):
            _, ok = self._run(f'tell application "Music" to set player position to {target}',
                              max_retries=1, silent=True)
            if ok:
                out, ok = self._run('tell application "Music" to get player position',
                                    max_retries=1, silent=True)
                try:
                    if ok and abs(float(out) - target) <= 3:
                        return True
                except ValueError:
                    pass
            time.sleep(settle)
        print(f"⚠️  Could not seek to {target}s; playing from wherever Music started")
        return False

    def play_pause(self):
        return self._run('tell application "Music" to playpause')[1]

    def pause(self):
        return self._run('tell application "Music" to pause')[1]

    def stop(self):
        return self._run('tell application "Music" to stop')[1]

    def next_track(self):
        return self._run('tell application "Music" to next track')[1]

    # -- state ------------------------------------------------------------

    def get_current_track(self):
        script = '''
        tell application "Music"
            if player state is not stopped then
                return name of current track & " - " & artist of current track
            else
                return "No track playing"
            end if
        end tell
        '''
        out, ok = self._poll(script)
        return out if ok else None      # None = unknown, keep the last value

    def is_playing(self):
        out, ok = self._poll(
            'tell application "Music" to if player state is playing '
            'then return "yes" else return "no"')
        return ok and out == "yes"

    def get_player_position(self):
        """Seconds into the current track, or None when stopped."""
        out, ok = self._poll('tell application "Music" to get player position')
        if not (ok and out):
            return None
        try:
            return float(out)
        except ValueError:
            return None

    # -- volume, fading, ducking -----------------------------------------

    def get_volume(self):
        out, ok = self._poll('tell application "Music" to get sound volume')
        try:
            return int(float(out)) if ok and out else None
        except ValueError:
            return None

    def set_volume(self, value):
        value = max(0, min(100, int(value)))
        return run_applescript(
            f'tell application "Music" to set sound volume to {value}',
            max_retries=1, silent=True)[1]  # fades call this in a tight loop

    @property
    def base_volume(self):
        """The volume to return to after a fade or duck (defaults to current)."""
        with self._vol_lock:
            if self._base_volume is None:
                self._base_volume = self.get_volume() or 100
            return self._base_volume

    def remember_base_volume(self):
        """Snapshot the operator's current volume as the level to restore to."""
        with self._vol_lock:
            current = self.get_volume()
            if current is not None:
                self._base_volume = current
            return self._base_volume

    def cancel_fades(self):
        """Invalidate any in-flight fade so it stops stepping."""
        with self._vol_lock:
            self._fade_generation += 1

    def fade(self, target, duration, steps=12, then=None):
        """Ramp Music's volume to `target` over `duration` seconds, off-thread.

        `then` runs on the worker thread once the ramp completes; it is skipped
        if a newer fade superseded this one.
        """
        with self._vol_lock:
            self._fade_generation += 1
            generation = self._fade_generation
            start = self.get_volume()
        if start is None:
            start = self.base_volume

        def worker():
            delay = max(0.0, duration / max(1, steps))
            for i in range(1, steps + 1):
                with self._vol_lock:
                    if generation != self._fade_generation:
                        return  # superseded
                self.set_volume(start + (target - start) * i / steps)
                if delay:
                    time.sleep(delay)
            if then:
                then()

        threading.Thread(target=worker, daemon=True).start()

    def fade_out_and_stop(self, duration=1.5):
        """Fade the music down, stop, and restore the volume for the next cue."""
        base = self.remember_base_volume()

        def finish():
            self.stop()
            self.set_volume(base)

        if duration <= 0:
            finish()
        else:
            self.fade(0, duration, then=finish)

    def duck(self, to_volume):
        """Drop volume quickly for a PA announcement. Returns the prior volume."""
        base = self.remember_base_volume()
        self.cancel_fades()
        self.set_volume(to_volume)
        return base

    def unduck(self, restore_to=None, duration=0.6):
        """Bring the music back up after an announcement."""
        target = self.base_volume if restore_to is None else restore_to
        self.fade(target, duration, steps=6)
