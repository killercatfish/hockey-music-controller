#!/usr/bin/env python3
"""Headless checks for the non-GUI logic. Run: python3 tests/test_core.py"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hockeymusic import announcements
from hockeymusic.config import Config, migrate
from hockeymusic.playlists import Clip, Pool, PoolSet, format_seconds, parse_time
from hockeymusic.roster import Player, Roster


def demo_roster():
    r = Roster()
    r.players["7"] = Player("7", "Alexander Mellen", "C")
    r.players["10"] = Player("10", "Cale Kulig", "LW", nickname="Cale")
    r.players["5"] = Player("5", "Hugo Brown", "D", goal_song="Thunderstruck")
    return r


class TestAnnouncements(unittest.TestCase):
    def setUp(self):
        self.roster = demo_roster()
        self.roster_away = Roster()
        self.roster_away.players["71"] = Player("71", "Declan Manley")
        self.roster_away.players["22"] = Player("22", "Cedar Keaton")

    def test_scorer_and_assists_use_names(self):
        # The old build read assists out as bare numbers.
        text = announcements.goal("home", "7", ["10", "5"], self.roster)
        self.assertIn("number 7, Alexander Mellen", text)
        self.assertIn("number 10, Cale", text)
        self.assertIn("number 5, Hugo Brown", text)

    def test_nickname_wins(self):
        self.assertEqual(self.roster.display_name("10"), "Cale")

    def test_unknown_number_degrades(self):
        text = announcements.goal("home", "99", [], self.roster)
        self.assertIn("number 99", text)
        self.assertIn("Unassisted", text)

    def test_hash_prefix_tolerated(self):
        self.assertEqual(self.roster.display_name("#7"), "Alexander Mellen")

    def test_away_goal_is_neutral(self):
        text = announcements.goal("away", "12", ["4"], None)
        self.assertTrue(text.startswith("Goal scored by number 12"))
        self.assertNotIn("!", text)


    def test_away_pieces_say_the_same_words_as_the_full_call(self):
        # Invariant 1: pieces may only move commas, never change what's said.
        import re
        words = lambda t: re.sub(r"[,.]", "", t).split()
        for scorer, assists in (("12", []), ("12", ["4"]), ("00", ["7", "99"]),
                                ("#3", ["", "8"])):
            pieces = announcements.away_goal_pieces(scorer, assists)
            self.assertEqual(words(" ".join(pieces)),
                             words(announcements.goal("away", scorer, assists)))

    def test_away_pieces_are_all_in_the_manifest(self):
        manifest = announcements.away_piece_manifest()
        texts = {t for _, t in manifest}
        self.assertEqual(len(texts), len(manifest))
        self.assertEqual(len(manifest), 4 + 2 * 101)
        self.assertEqual(announcements.prerender_manifest(None, scope="away"), manifest)
        for scorer in ("0", "00", "55", "99"):
            for assists in ([], ["1"], ["10", "00"]):
                self.assertLessEqual(
                    set(announcements.away_goal_pieces(scorer, assists)), texts)

    def test_home_pieces_say_the_same_words_as_the_full_call(self):
        # Invariant 1 for the recorded voice: same words as goal("home", ...).
        import re
        words = lambda t: re.sub(r"[^a-z0-9 ]", "", t.lower()).split()
        r = demo_roster()
        for scorer, assists in (("7", []), ("7", ["5"]), ("7", ["5", "10"])):
            pieces = announcements.home_goal_pieces(scorer, assists, r)
            self.assertEqual(words(" ".join(pieces)),
                             words(announcements.goal("home", scorer, assists, r)))
            self.assertLessEqual(set(pieces), set(announcements.home_piece_manifest(r)))

    def test_home_pieces_need_every_number_on_the_roster(self):
        self.assertIsNone(announcements.home_goal_pieces("99", [], demo_roster()))
        self.assertIsNone(announcements.home_goal_pieces("7", ["99"], demo_roster()))

    def test_lineup_line_is_the_recorded_landing_piece(self):
        # The lineup reuses each player's "Number 7, Name!" recording; that only
        # works while the two strings agree (position blank).
        from hockeymusic.roster import Player
        p = Player("7", "Alexander Mellen")
        self.assertEqual(announcements.lineup_player(p),
                         announcements.player_called("7", "Alexander Mellen"))

    def test_away_pieces_refuse_odd_numbers(self):
        self.assertIsNone(announcements.away_goal_pieces("100"))
        self.assertIsNone(announcements.away_goal_pieces("7", ["A"]))

    def test_visiting_goal_uses_their_roster(self):
        text = announcements.visiting_goal("Catamounts", "71", ["22"], self.roster_away)
        self.assertEqual(text, "Catamounts goal, scored by number 71, Declan Manley."
                               " Assisted by number 22, Cedar Keaton.")
        text = announcements.visiting_goal("Catamounts", "99", [], self.roster_away)
        self.assertEqual(text, "Catamounts goal, scored by number 99. Unassisted.")
    def test_team_name_is_configurable(self):
        text = announcements.goal("home", "7", [], self.roster, team_name="Bruins")
        self.assertTrue(text.startswith("Bruins GOAL!!"))

    def test_prerender_scopes_grow(self):
        n = len(self.roster)
        lineup = announcements.prerender_manifest(self.roster, scope="lineup")
        basic = announcements.prerender_manifest(self.roster, scope="basic")
        full = announcements.prerender_manifest(self.roster, scope="full")
        self.assertEqual(len(lineup), n + 1)
        self.assertEqual(len(basic), n + 1 + n)
        self.assertEqual(len(full), n + 1 + n + n * (n - 1))

    def test_prerender_keys_unique(self):
        items = announcements.prerender_manifest(self.roster, scope="full")
        keys = [k for k, _ in items]
        self.assertEqual(len(keys), len(set(keys)))


class TestRosterIO(unittest.TestCase):
    def test_legacy_two_column_csv(self):
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
            f.write("5,Hugo Brown\n7,Alexander Mellen\n")
            path = f.name
        roster = Roster.load(path)
        self.assertEqual(len(roster), 2)
        self.assertEqual(roster.display_name("5"), "Hugo Brown")

    def test_round_trip_keeps_goal_songs(self):
        roster = demo_roster()
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "roster.csv"
            self.assertTrue(roster.save(path))
            reloaded = Roster.load(path)
        self.assertEqual(len(reloaded), 3)
        self.assertEqual(reloaded.get("5").goal_song, "Thunderstruck")
        self.assertEqual(reloaded.get("10").nickname, "Cale")

    def test_sorted_numerically_not_alphabetically(self):
        roster = demo_roster()
        self.assertEqual([p.number for p in roster.sorted_players()], ["5", "7", "10"])


class TestPlaylists(unittest.TestCase):
    def make_pool(self):
        pool = Pool("Stoppage", playlist="Test",
                    tracks=[f"Song {i} | Artist" for i in range(10)])
        pool.reset_order()
        return pool

    def test_time_parsing(self):
        self.assertEqual(parse_time("90"), 90)
        self.assertEqual(parse_time("1:30"), 90)
        self.assertEqual(format_seconds(90), "1:30")
        with self.assertRaises(ValueError):
            parse_time("banana")

    def test_clip_round_trip_and_v2_upgrade(self):
        clip = Clip.from_dict({"start": 15, "end": 45})
        self.assertEqual((clip.start, clip.end), (15, 45))
        legacy = Clip.from_dict(15)          # v2 stored a bare number
        self.assertEqual((legacy.start, legacy.end), (15, None))

    def test_family_safe_excludes_flagged(self):
        pool = self.make_pool()
        pool.toggle_flag("Song 3 | Artist")
        pool.reset_order(family_safe=True)
        self.assertEqual(len(pool.order), 9)
        pool.reset_order(family_safe=False)
        self.assertEqual(len(pool.order), 10)

    def test_shuffle_pushes_recent_tracks_back(self):
        pool = self.make_pool()
        for i in range(4):
            pool.note_played(f"Song {i} | Artist")
        pool.shuffle()
        front = {pool.tracks[i] for i in pool.order[:6]}
        recent = {f"Song {i} | Artist" for i in range(4)}
        self.assertFalse(front & recent, "recently played tracks resurfaced early")

    def test_search_filters(self):
        pool = self.make_pool()
        self.assertEqual(len(pool.matches("Song 3")), 1)
        self.assertEqual(len(pool.matches("")), 10)

    def test_pool_persistence(self):
        pool = self.make_pool()
        pool.set_clip("Song 1 | Artist", 15, 45)
        pool.toggle_flag("Song 2 | Artist")
        restored = Pool.from_dict("Stoppage", pool.to_dict())
        self.assertEqual(restored.clip_for("Song 1 | Artist").end, 45)
        self.assertIn("Song 2 | Artist", restored.flagged)

    def test_poolset_keeps_one_pool(self):
        pools = PoolSet(Config())
        self.assertFalse(pools.remove(pools.active_name))
        pools.add("Warmup")
        self.assertTrue(pools.remove("Warmup"))


class TestConfigMigration(unittest.TestCase):
    def test_v2_config_becomes_a_pool(self):
        old = {
            "playlist": "Stoppage Music",
            "goal_song": "Song 2",
            "power_play": "Thunderstruck",
            "start_times": {"Kernkraft 400 | Zombie Nation": 15},
        }
        new = migrate(old)
        cfg = Config(new)
        self.assertEqual(cfg.event_song("goal"), "Song 2")
        self.assertEqual(cfg.event_song("power_play"), "Thunderstruck")
        self.assertEqual(cfg.get("pools.Stoppage.playlist"), "Stoppage Music")
        clip = cfg.get("pools.Stoppage.clips")["Kernkraft 400 | Zombie Nation"]
        self.assertEqual(clip["start"], 15)
        self.assertEqual(cfg.get("active_pool"), "Stoppage")

    def test_defaults_fill_missing_keys(self):
        cfg = Config({"team_name": "Bruins"})
        self.assertEqual(cfg.team_name, "Bruins")
        self.assertEqual(cfg.get("audio.duck_volume"), 25)
        self.assertTrue(cfg.get("announcer.use_cache"))

    def test_dotted_set_creates_nodes(self):
        cfg = Config()
        cfg.set("audio.fade_out", 2.5)
        self.assertEqual(cfg.get("audio.fade_out"), 2.5)



class TestClipSharing(unittest.TestCase):
    """A clip set in one pool plays in every pool, unless that pool overrides it."""

    def setUp(self):
        self.pools = PoolSet(Config({"pools": {
            "Stoppage": {"playlist": "A", "flagged": [],
                         "clips": {"Song | Band": {"start": 29, "end": None}}},
            "Game 1": {"playlist": "B", "flagged": [], "clips": {}},
            "Warmup": {"playlist": "C", "flagged": [],
                       "clips": {"Song | Band": {"start": 0, "end": 40}}},
        }, "active_pool": "Game 1"}))

    def test_inherits_from_another_pool(self):
        clip = self.pools.clip_for("Song | Band")          # active = Game 1
        self.assertEqual(clip.start, 29)

    def test_own_clip_wins(self):
        clip = self.pools.clip_for("Song | Band", self.pools.pools["Warmup"])
        self.assertEqual((clip.start, clip.end), (0, 40))

    def test_unknown_track_is_none(self):
        self.assertIsNone(self.pools.clip_for("Other | Band"))


class TestAnnouncerQuota(unittest.TestCase):
    """A Hume 429 must not stall a goal call or hammer the API during pre-render."""

    def _announcer(self):
        from hockeymusic import announcer as mod
        a = mod.Announcer(Config({}))
        return a, mod

    def test_quota_error_is_recognised(self):
        _, mod = self._announcer()
        self.assertTrue(mod._is_quota_error(
            "headers: {...}, status_code: 429, body: {'fault': {'faultstring': "
            "'Rate limit quota violation. Quota limit exceeded.'}}"))
        self.assertFalse(mod._is_quota_error("status_code: 500, body: {}"))

    def test_backoff_then_retry(self):
        import time
        a, mod = self._announcer()
        a.quota_exhausted_at = time.time()
        self.assertTrue(a.quota_exhausted)
        a.quota_exhausted_at = time.time() - mod.QUOTA_BACKOFF - 1
        self.assertFalse(a.quota_exhausted)
        self.assertIsNone(a.quota_exhausted_at)

    def test_prerender_stops_after_quota_error(self):
        import time
        a, _ = self._announcer()
        calls = []

        def fake_render(text, force=False):
            calls.append(text)
            a.quota_exhausted_at = time.time()      # what _synthesize does on 429
            return None

        a.render = fake_render
        items = [(f"k{i}", f"line {i}") for i in range(50)]
        rendered, skipped, failed = a.prerender(items)
        self.assertEqual(len(calls), 1)
        self.assertEqual((rendered, skipped, failed), (0, 0, 50))


class TestHumeShutdown(unittest.TestCase):
    """After Hume shuts down (2026-11-13) the cache is the only copy of the voice."""

    def setUp(self):
        from hockeymusic import announcer as mod
        self.mod = mod
        self.tmp = tempfile.TemporaryDirectory()
        self._cache_dir = mod.paths.TTS_CACHE_DIR
        mod.paths.TTS_CACHE_DIR = Path(self.tmp.name)
        self.a = mod.Announcer(Config({}))
        self.line = "Goal scored by number 7"
        self.a.cache_path(self.line).write_bytes(b"audio")

    def tearDown(self):
        self.mod.paths.TTS_CACHE_DIR = self._cache_dir
        self.tmp.cleanup()

    def _patch(self, name, value):
        cls = type(self.a)
        original = cls.__dict__[name]
        setattr(cls, name, property(lambda self: value))
        self.addCleanup(setattr, cls, name, original)

    def _retire(self, retired=True):
        self._patch("hume_retired", retired)

    def test_shutdown_date(self):
        import datetime
        self.assertFalse(self.mod.hume_retired(datetime.date(2026, 11, 12)))
        self.assertTrue(self.mod.hume_retired(datetime.date(2026, 11, 13)))

    def test_clear_cache_refused_after_shutdown(self):
        self._retire()
        self.assertEqual(self.a.clear_cache(), 0)
        self.assertTrue(self.a.is_cached(self.line))
        self.assertFalse(self.a.hume_available)
        self.assertIn("cached lines only", self.a.status_text)

    def test_clear_cache_still_works_before_shutdown(self):
        self._retire(False)
        self.assertEqual(self.a.clear_cache(), 1)

    def test_forced_render_falls_back_to_the_cached_line(self):
        # "Use cached audio" off forces a re-render; with Hume gone (or no
        # wifi) the cached line must still play, not nothing.
        self._retire()
        self.a._synthesize = lambda text: self.fail("called a dead API")
        self.assertEqual(self.a.render(self.line, force=True),
                         self.a.cache_path(self.line))
        self.assertIsNone(self.a.render("never cached", force=True))

    def test_failed_rerender_keeps_the_cached_line(self):
        self._retire(False)
        self._patch("can_render", True)
        self.a._synthesize = lambda text: None
        self.assertEqual(self.a.render(self.line, force=True),
                         self.a.cache_path(self.line))


class TestAnnouncerStopsMusic(unittest.TestCase):
    class Music:
        def __init__(self): self.calls = []; self.playing = True
        def is_playing(self): return self.playing
        def cancel_fades(self): self.calls.append("cancel")
        def stop(self): self.calls.append("stop"); self.playing = False
        def duck(self, level): self.calls.append(("duck", level)); return 100
        def unduck(self, restore_to=None, duration=0.6): self.calls.append("unduck")

    def test_default_stops_the_music_and_never_restores(self):
        from hockeymusic.announcer import Announcer
        m = self.Music(); a = Announcer(Config({}), m)
        prior = a._duck(); a._unduck(prior)
        self.assertEqual(m.calls, ["cancel", "stop"])

    def test_duck_mode_still_works(self):
        from hockeymusic.announcer import Announcer
        m = self.Music()
        a = Announcer(Config({"audio": {"announce_stops_music": False, "duck_volume": 30}}), m)
        prior = a._duck(); a._unduck(prior)
        self.assertEqual(m.calls, [("duck", 30), "unduck"])

    def test_nothing_playing_means_nothing_touched(self):
        from hockeymusic.announcer import Announcer
        m = self.Music(); m.playing = False
        a = Announcer(Config({}), m)
        self.assertIsNone(a._duck()); self.assertEqual(m.calls, [])


class TestStitch(unittest.TestCase):
    """Announcement + celebration become one file with the dead air trimmed."""

    def _wav(self, path, seconds, silent_tail=0.0, rate=44100):
        import math, array, wave
        n = int(seconds * rate); tail = int(silent_tail * rate)
        a = array.array("h", (int(12000 * math.sin(i / 20.0)) for i in range(n - tail)))
        a.extend([0] * tail)
        with wave.open(str(path), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(a.tobytes())
        return path

    def test_tail_is_trimmed_and_clip_appended(self):
        import wave
        from hockeymusic import announcer as mod
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            ann = self._wav(d / "ann.wav", 3.0, silent_tail=1.0)
            woo = self._wav(d / "woo.wav", 1.2)
            out = mod.stitch(ann, woo, d / "combo.wav")
            self.assertIsNotNone(out)
            with wave.open(str(out)) as w:
                dur = w.getnframes() / w.getframerate()
            # 2.0s of voice + 0.15s gap + 1.2s clip, within a few ms
            self.assertAlmostEqual(dur, 2.0 + mod.GAP_AFTER_CALL + 1.2, delta=0.02)

    def test_combined_is_cached_and_survives_missing_clip(self):
        from hockeymusic import announcer as mod
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            mod.COMBO_DIR = d / "combo"
            a = mod.Announcer(Config({}))
            ann = self._wav(d / "ann.wav", 1.0, silent_tail=0.5)
            woo = self._wav(d / "woo.wav", 0.5)
            first = a.combined(ann, woo)
            self.assertIsNotNone(first)
            self.assertEqual(a.combined(ann, woo), first)      # cache hit
            self.assertIsNone(a.combined(ann, d / "nope.m4a"))


    def test_join_trims_both_ends_and_inserts_pauses(self):
        import wave
        from hockeymusic import announcer as mod
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            parts = []
            for i, pause in enumerate((0.18, 0.05, 0.15)):
                wav = d / f"p{i}.wav"
                self._wav(wav, 1.0, silent_tail=0.5)        # 0.5s voice, 0.5s dead air
                self._prepend_silence(wav, 0.6)
                parts.append((wav, pause))
            out = mod.join(parts, d / "joined.wav")
            self.assertIsNotNone(out)
            with wave.open(str(out)) as w:
                dur = w.getnframes() / w.getframerate()
            expected = 3 * (0.5 + 2 * mod.EDGE) + 0.18 + 0.05 + 0.15
            self.assertAlmostEqual(dur, expected, delta=0.03)

    def _prepend_silence(self, path, seconds):
        import wave
        with wave.open(str(path)) as w:
            params, frames = w.getparams(), w.readframes(w.getnframes())
        with wave.open(str(path), "wb") as w:
            w.setparams(params)
            w.writeframes(b"\0\0" * int(seconds * params.framerate) + frames)

    def test_away_call_plays_from_pieces_without_hume(self):
        from hockeymusic import announcer as mod
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            mod.COMBO_DIR = d / "combo"
            a = mod.Announcer(Config({}))
            pieces = announcements.away_goal_pieces("12", ["7"])
            files = {p: self._wav(d / f"{i}.wav", 0.6, silent_tail=0.2)
                     for i, p in enumerate(pieces)}
            a.cache_path = lambda text: files.get(text, d / "missing.wav")
            a.render = lambda text, force=False: self.fail("should not call Hume")
            played = []
            real_run = mod.subprocess.run
            mod.subprocess.run = lambda cmd, **kw: (
                real_run(cmd, **kw) if cmd[0] == "afconvert" else played.append(cmd))
            try:
                a._play_one(announcements.goal("away", "12", ["7"]), None, None, pieces)
            finally:
                mod.subprocess.run = real_run
            self.assertEqual(len(played), 1)
            self.assertEqual(played[0][0], "afplay")
            self.assertTrue(str(played[0][1]).startswith(str(mod.COMBO_DIR)))
            # A missing piece means no joined file -- fall through to Hume.
            self.assertIsNone(a.assembled(pieces[:-1] + ["number 999."]))


class TestRecordedVoice(unittest.TestCase):
    """Home calls joined from Josh's own clips; Hume stays one switch away."""

    def setUp(self):
        import json
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        r = demo_roster()
        self.text = announcements.goal("home", "7", ["5"], r)
        self.lines = announcements.home_goal_pieces("7", ["5"], r)
        clips = {}
        for i, line in enumerate(self.lines):
            TestStitch._wav(None, self.dir / f"{i}.wav", 0.6, silent_tail=0.2)
            clips[line] = [f"{i}.wav"]
        TestStitch._wav(None, self.dir / "alt.wav", 0.5)
        clips[self.lines[0]].append("alt.wav")              # a second GOAL!! take
        (self.dir / "manifest.json").write_text(json.dumps({"clips": clips}))

    def tearDown(self):
        self.tmp.cleanup()

    def _play(self, home_voice, lines):
        from hockeymusic import announcer as mod
        from hockeymusic.voice import RecordedVoice
        a = mod.Announcer(Config({"announcer": {"home_voice": home_voice}}))
        a.voice = RecordedVoice(self.dir)
        hume = []
        a.render = lambda text, force=False: hume.append(text)
        played = []
        real_run = mod.subprocess.run
        mod.subprocess.run = lambda cmd, **kw: (
            real_run(cmd, **kw) if cmd[0] == "afconvert" else played.append(cmd))
        try:
            a._play_one(self.text, None, None, None, lines)
        finally:
            mod.subprocess.run = real_run
        return played, hume

    def test_recorded_voice_plays_without_hume(self):
        played, hume = self._play("recorded", self.lines)
        self.assertEqual(hume, [])
        self.assertEqual(len(played), 1)
        self.assertIn(str(self.dir / "joined"), str(played[0][1]))

    def test_hume_setting_ignores_the_recordings(self):
        _, hume = self._play("hume", self.lines)
        self.assertEqual(hume, [self.text])

    def test_a_missing_recording_falls_back_to_hume(self):
        _, hume = self._play("recorded", self.lines[:-1] + ["Number 99, Nobody!"])
        self.assertEqual(hume, [self.text])

    def test_manifest_and_rotation(self):
        from hockeymusic.voice import RecordedVoice
        v = RecordedVoice(self.dir)
        self.assertEqual(len(v), len(self.lines))
        takes = {v.take(self.lines[0]).name for _ in range(60)}
        self.assertEqual(takes, {"0.wav", "alt.wav"})
        self.assertEqual(len(RecordedVoice(self.dir / "nowhere")), 0)


class TestNoRobotVoice(unittest.TestCase):
    """A line Hume can't produce is skipped, not read by the macOS voice."""

    def _run(self, fallback_enabled):
        from hockeymusic import announcer as mod
        calls = []
        a = mod.Announcer(Config({"announcer": {"fallback_enabled": fallback_enabled}}))
        a.render = lambda text, force=False: None
        real_run = mod.subprocess.run
        mod.subprocess.run = lambda cmd, **kw: calls.append(cmd[0])
        try:
            status = []
            a._play_one("Patriots GOAL!!", "/nonexistent/woo.m4a", status.append)
        finally:
            mod.subprocess.run = real_run
        return calls, status

    def test_default_skips(self):
        calls, status = self._run(False)
        self.assertEqual(calls, [])
        self.assertTrue(status[-1].startswith("⛔ Not announced"))

    def test_opt_in_uses_say(self):
        calls, _ = self._run(True)
        self.assertEqual(calls, ["say"])


class TestPlayMutedSeek(unittest.TestCase):
    """A clip start plays muted until the seek lands, then restores the volume."""

    def _controller(self, seek_failures=1):
        from hockeymusic import music as mod
        log, state = [], {"fails": seek_failures}

        def fake(script, **_kw):
            s = script.split(" to ", 1)[-1].strip()
            log.append(s)
            if s == "get sound volume":
                return "70", True
            if s.startswith("set player position"):
                if state["fails"]:
                    state["fails"] -= 1
                    return "", False          # -10006: track still loading
                return "", True
            if s == "get player position":
                return "25.0", True
            return "", True

        self._saved = mod.run_applescript
        mod.run_applescript = fake
        self.addCleanup(setattr, mod, "run_applescript", self._saved)
        return mod.AppleMusicController(), log

    def test_mute_play_seek_restore_order(self):
        m, log = self._controller()
        self.assertTrue(m.play_track_from_playlist("Deck", 3, start_time=25))
        self.assertEqual(log[1], "set sound volume to 0")
        self.assertTrue(log[2].startswith("play track 3"))
        self.assertEqual(log.count("play track 3 of playlist \"Deck\""), 1)  # play never re-issued
        self.assertEqual(log[-1], "set sound volume to 70")
        self.assertFalse(m._fading)

    def test_no_start_plays_without_touching_volume(self):
        m, log = self._controller()
        m.play_track_by_name("Song", start_time=None)
        self.assertEqual(log, ['play track "Song"'])

    def test_duck_during_mute_keeps_operator_volume(self):
        m, _ = self._controller()
        m._base_volume = 70
        m._fading = True                     # as during the muted seek
        self.assertEqual(m.remember_base_volume(), 70)


class TestHumeEnvFile(unittest.TestCase):
    """Settings writes Hume credentials to ~/.hockey_music/.env, merging."""

    def setUp(self):
        from hockeymusic import paths
        self.tmp = tempfile.TemporaryDirectory()
        self._saved = paths.DATA_DIR
        paths.DATA_DIR = Path(self.tmp.name) / "data"

    def tearDown(self):
        from hockeymusic import paths
        paths.DATA_DIR = self._saved
        self.tmp.cleanup()

    def test_round_trip_and_merge(self):
        from hockeymusic.ui.dialogs import _read_env_file, _write_env_file, _env_path
        self.assertEqual(_read_env_file(), {})
        self.assertTrue(_write_env_file({"HUME_API_KEY": "abc", "HUME_VOICE_ID": "Rink Voice"}))
        self.assertEqual(_read_env_file(), {"HUME_API_KEY": "abc", "HUME_VOICE_ID": "Rink Voice"})
        # Another line survives, a blank value removes a key, no-op returns False.
        with open(_env_path(), "a") as f:
            f.write("SPOTIFY_SECRET='keep me'\n")
        self.assertFalse(_write_env_file({"HUME_API_KEY": "abc", "HUME_VOICE_ID": "Rink Voice"}))
        self.assertTrue(_write_env_file({"HUME_API_KEY": "abc", "HUME_VOICE_ID": ""}))
        self.assertEqual(_read_env_file(), {"HUME_API_KEY": "abc", "SPOTIFY_SECRET": "keep me"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
