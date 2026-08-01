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


if __name__ == "__main__":
    unittest.main(verbosity=2)
