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

if __name__ == "__main__":
    unittest.main(verbosity=2)


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
