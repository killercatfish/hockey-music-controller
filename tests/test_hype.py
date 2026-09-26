#!/usr/bin/env python3
"""Chorus detection and proposal application. Run: python3 tests/test_hype.py

No network: LRCLIB is never called here. The lyrics fixtures are shaped like
real LRCLIB responses so the parser sees the formats it meets in the wild.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hockeymusic import hype
from hockeymusic.config import Config
from hockeymusic.gameday import deal


def lrc(*pairs):
    """Build LRC text from (seconds, line) pairs."""
    return "\n".join(f"[{int(s) // 60:02d}:{s % 60:05.2f}]{text}" for s, text in pairs)


VERSE_CHORUS = lrc(
    (10, "Walking down the empty street"), (14, "Nothing left for me to say"),
    (18, "Every light is turning red"), (22, "I keep going anyway"),
    (30, "Light it up, light it up"), (33, "We are never going down"),
    (36, "Light it up, light it up"), (39, "Louder than the whole town"),
    (50, "Second verse is something new"), (54, "Different words in every line"),
    (58, "Nothing here repeats at all"), (62, "So the verse should never win"),
    (70, "Light it up, light it up"), (73, "We are never going down"),
    (76, "Light it up, light it up"), (79, "Louder than the whole town"),
    (110, "Light it up, light it up"), (113, "We are never going down"),
    (116, "Light it up, light it up"), (119, "Louder than the whole town"),
)


class TestParseLrc(unittest.TestCase):
    def test_parses_and_sorts(self):
        lines = hype.parse_lrc("[00:12.50] second\n[00:05.00]first\n\n[00:20.00]\n")
        self.assertEqual(lines, [(5.0, "first"), (12.5, "second")])

    def test_multiple_stamps_on_one_line(self):
        lines = hype.parse_lrc("[00:10.00][00:40.00]Hey!")
        self.assertEqual([s for s, _ in lines], [10.0, 40.0])

    def test_no_space_after_stamp(self):
        # LRCLIB serves both "[mm:ss.xx] text" and "[mm:ss.xx]text".
        self.assertEqual(hype.parse_lrc("[01:02.03]Whatever It Takes"),
                         [(62.03, "Whatever It Takes")])


class TestFindChorus(unittest.TestCase):
    def test_lands_a_beat_before_the_first_chorus(self):
        point = hype.find_chorus(hype.parse_lrc(VERSE_CHORUS), title="Light It Up",
                                 duration=180)
        self.assertIsNotNone(point)
        self.assertEqual(point.chorus_at, 30.0)
        self.assertEqual(point.start, 29)           # LEAD_IN of one second
        self.assertEqual(point.confidence, "high")
        self.assertEqual(point.line, "Light it up, light it up")

    def test_no_repeats_means_no_proposal(self):
        text = lrc((5, "one"), (10, "two"), (15, "three"), (20, "four"), (25, "five"))
        self.assertIsNone(hype.find_chorus(hype.parse_lrc(text)))

    def test_too_short_means_no_proposal(self):
        self.assertIsNone(hype.find_chorus(hype.parse_lrc(lrc((1, "a"), (2, "a")))))

    def test_chorus_too_close_to_the_end_is_rejected(self):
        text = lrc((5, "v1"), (10, "v2"), (15, "v3"), (20, "v4"),
                   (170, "hook"), (172, "hook"), (174, "hook"), (176, "hook"))
        self.assertIsNone(hype.find_chorus(hype.parse_lrc(text), duration=180))
        self.assertIsNotNone(hype.find_chorus(hype.parse_lrc(text), duration=400))

    def test_immediate_repeats_count(self):
        # Thunderstruck: the same chant line over and over is the hook.
        text = lrc((5, "Ah ah ah"), (12, "Ooh"), (20, "Nope"), (25, "Verse"),
                   (29, "Thunder (ah-ah)"), (32, "Thunder (ah-ah)"),
                   (36, "Thunder (ah-ah)"), (39, "Thunder (ah-ah)"),
                   (50, "Thunder"), (54, "Thunder"), (57, "Thunder"))
        point = hype.find_chorus(hype.parse_lrc(text), title="Thunderstruck")
        self.assertEqual(point.chorus_at, 29.0)

    def test_earlier_run_wins_when_close_in_strength(self):
        # A pre-chorus at 0:30 repeated 3x vs a chorus at 2:00 repeated 4x:
        # the earlier one is what you want at a whistle.
        early = [(30 + i * 3, "pre chorus line one" if i % 2 == 0 else "pre chorus line two")
                 for i in range(6)]
        late = [(120 + i * 3, "big chorus line one" if i % 2 == 0 else "big chorus line two")
                for i in range(8)]
        verses = [(5, "a"), (10, "b"), (60, "c"), (65, "d")]
        text = lrc(*sorted(verses + early + late))
        point = hype.find_chorus(hype.parse_lrc(text))
        self.assertEqual(point.chorus_at, 30.0)

    def test_outro_repeats_do_not_drag_the_start_late(self):
        # Livin' On a Prayer: chorus once at 0:55, once at 2:00, then four times
        # in a row at 3:20. The heaviest run is the outro; the start is 0:55.
        chorus = ["Whoa, we're half way there", "Whoa, livin' on a prayer"]
        pairs = [(5, "v1"), (10, "v2"), (15, "v3"), (20, "v4"),
                 (55, chorus[0]), (58, chorus[1]),
                 (90, "v5"), (95, "v6"), (100, "v7"),
                 (120, chorus[0]), (123, chorus[1])]
        pairs += [(200 + k * 3, chorus[k % 2]) for k in range(8)]
        point = hype.find_chorus(hype.parse_lrc(lrc(*pairs)), title="Livin' On a Prayer",
                                 duration=250)
        self.assertEqual(point.chorus_at, 55.0)
        self.assertEqual(point.start, 54)

    def test_late_chorus_falls_back_to_an_earlier_hook(self):
        pairs = [(5, "v1"), (10, "v2"), (30, "oh oh"), (33, "oh oh"), (36, "oh oh"),
                 (60, "v3"), (65, "v4")]
        pairs += [(180 + k * 3, "big chorus " + str(k % 3)) for k in range(12)]
        point = hype.find_chorus(hype.parse_lrc(lrc(*pairs)), duration=240)
        self.assertEqual(point.chorus_at, 30.0)

    def test_punctuation_and_case_do_not_split_a_line(self):
        text = lrc((5, "x"), (10, "y"), (15, "z"), (20, "w"),
                   (40, "Welcome to my house!"), (43, "welcome to my house"),
                   (46, "Welcome To My House."), (49, "Baby take control"),
                   (80, "Welcome to my house"), (83, "Baby take control"))
        point = hype.find_chorus(hype.parse_lrc(text), title="My House")
        self.assertEqual(point.chorus_at, 40.0)

    def test_very_early_hook_starts_from_the_top(self):
        text = lrc((2, "hook"), (4, "hook"), (6, "hook"), (8, "hook"), (30, "verse"))
        self.assertEqual(hype.find_chorus(hype.parse_lrc(text)).start, 0)


class TestTitleHelpers(unittest.TestCase):
    def test_clean_title(self):
        self.assertEqual(hype.clean_title("Cruise (Remix) [feat. Nelly]"), "Cruise")
        self.assertEqual(hype.clean_title("Old Town Road (feat. Billy Ray Cyrus) - Remix"),
                         "Old Town Road")
        self.assertEqual(hype.clean_title("Thunderstruck"), "Thunderstruck")

    def test_primary_artist(self):
        self.assertEqual(hype._primary_artist("Lil Nas X/Billy Ray Cyrus"), "Lil Nas X")
        self.assertEqual(hype._primary_artist("R3HAB, A Touch of Class & DVLM"), "R3HAB")
        self.assertEqual(hype._primary_artist("AC/DC"), "AC")  # known wart; exact lookup runs first

    def test_title_tokens_drop_noise(self):
        self.assertEqual(hype.title_tokens("Levels (Radio Edit)"), {"levels"})


class TestApplyProposals(unittest.TestCase):
    def setUp(self):
        self.config = Config({"pools": {"Stoppage": {
            "playlist": "P", "flagged": [],
            "clips": {"A | X": {"start": 8, "end": None},
                      "B | X": {"start": 8, "end": 45},
                      "C | X": {"start": 30, "end": None},
                      "D | X": {"start": 8, "end": None}},
        }}})

    def test_writes_starts_and_keeps_end_points(self):
        changed = hype.apply_proposals(self.config, "Stoppage", {
            "A | X": {"start": 29}, "B | X": {"start": 61},
            "C | X": {"start": 30},              # unchanged
            "D | X": {"start": 0},               # chorus from the top: clip removed
            "E | X": {"start": 12},              # not clipped before
        })
        clips = self.config.get("pools.Stoppage.clips")
        self.assertEqual(changed, 4)
        self.assertEqual(clips["A | X"], {"start": 29, "end": None})
        self.assertEqual(clips["B | X"], {"start": 61, "end": 45})
        self.assertEqual(clips["C | X"], {"start": 30, "end": None})
        self.assertNotIn("D | X", clips)
        self.assertEqual(clips["E | X"], {"start": 12, "end": None})

    def test_unknown_pool_raises(self):
        with self.assertRaises(KeyError):
            hype.apply_proposals(self.config, "Nope", {})


class TestDeal(unittest.TestCase):
    def setUp(self):
        self.meta = [{"track": f"T{i} | A", "cloud": "subscription"} for i in range(10)]
        self.meta[3]["cloud"] = "no longer available"

    def test_disjoint_and_complete(self):
        decks = deal(self.meta, 2, flagged={"T5 | A"}, seed=1)
        flat = sorted(i for d in decks for i in d)
        self.assertEqual(flat, [1, 2, 3, 5, 7, 8, 9, 10])   # 4 unavailable, 6 flagged
        self.assertEqual(len(decks[0]) + len(decks[1]), 8)
        self.assertFalse(set(decks[0]) & set(decks[1]))

    def test_seed_repeats_and_size_caps(self):
        self.assertEqual(deal(self.meta, 2, seed="x"), deal(self.meta, 2, seed="x"))
        decks = deal(self.meta, 3, size=2, seed="x")
        self.assertEqual([len(d) for d in decks], [2, 2, 2])


if __name__ == "__main__":
    unittest.main(verbosity=1)
