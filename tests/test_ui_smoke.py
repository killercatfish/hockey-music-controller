#!/usr/bin/env python3
"""Build every window against a fake Apple Music, so a typo in the UI shows up
here rather than at the rink. Run: python3 tests/test_ui_smoke.py
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import tkinter as tk

from hockeymusic import paths


class FakeMusic:
    """Stands in for Apple Music -- no AppleScript, no Music.app required."""

    def __init__(self):
        self.tracks = [f"Song {i} | Artist {i % 4}" for i in range(24)]
        self.played = []
        self.volume = 80
        self.playing = False

    def get_playlists(self):
        return ["Stoppage Music", "Warmups"]

    def get_playlist_tracks(self, _name):
        return list(self.tracks)

    def get_playlist_track_meta(self, _name):
        return [{"track": t, "duration": 200.0 + i} for i, t in enumerate(self.tracks)]

    def play_track_from_playlist(self, name, index, start_time=None):
        self.played.append((name, index, start_time))
        self.playing = True
        return True

    def play_track_by_name(self, name, start_time=None):
        self.played.append((name, start_time))
        self.playing = True
        return True

    def play_pause(self):
        self.playing = not self.playing
        return True

    def pause(self):
        self.playing = False
        return True

    def stop(self):
        self.playing = False
        return True

    def get_current_track(self):
        return "Song 0 | Artist 0" if self.playing else "No track playing"

    def is_playing(self):
        return self.playing

    def get_player_position(self):
        return 12.0

    def get_volume(self):
        return self.volume

    def set_volume(self, value):
        self.volume = int(value)
        return True

    @property
    def base_volume(self):
        return self.volume

    def remember_base_volume(self):
        return self.volume

    def cancel_fades(self):
        pass

    def fade(self, target, duration, steps=12, then=None):
        self.volume = int(target)
        if then:
            then()

    def duck(self, to_volume):
        return self.volume

    def unduck(self, restore_to=None, duration=0.6):
        pass


class UITestCase(unittest.TestCase):
    """Base that swaps in a temp config dir and a fake Music app."""

    @classmethod
    def setUpClass(cls):
        try:
            cls.root = tk.Tk()
        except tk.TclError as e:
            raise unittest.SkipTest(f"no display available: {e}")
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def setUp(self):
        from hockeymusic.ui import main_window

        self.tmp = tempfile.TemporaryDirectory()
        tmp_path = Path(self.tmp.name)
        self._saved = (paths.CONFIG_FILE, paths.DATA_DIR, paths.TTS_CACHE_DIR)
        paths.CONFIG_FILE = tmp_path / "config.json"
        paths.DATA_DIR = tmp_path / "data"
        paths.TTS_CACHE_DIR = tmp_path / "data" / "tts"

        # No Apple Music, no polling loop -- the fake stands in for both.
        self.app = main_window.HockeyMusicApp(
            tk.Toplevel(self.root), music=FakeMusic(), autostart=False)
        # Never let a test hit the network or play audio.
        self.announced = []
        self.app.announce = lambda text, celebration=None: self.announced.append(text)
        self.app.pool.playlist = "Stoppage Music"
        self.app.load_pool_tracks(quiet=True)

    def tearDown(self):
        self.app.root.destroy()
        paths.CONFIG_FILE, paths.DATA_DIR, paths.TTS_CACHE_DIR = self._saved
        self.tmp.cleanup()

    def pump(self):
        self.root.update_idletasks()


class TestMainWindow(UITestCase):
    def test_playlist_renders(self):
        self.pump()
        self.assertEqual(self.app.listbox.size(), 24)

    def test_space_plays_then_stops_and_queues_next(self):
        app, music = self.app, self.app.music
        app.position = 3
        app.space_key()
        self.assertTrue(music.playing)
        self.assertEqual(music.played[-1][1], app.pool.music_index(3))
        app.space_key()
        self.assertFalse(music.playing)
        self.assertEqual(app.position, 4)
        app.space_key()
        self.assertEqual(music.played[-1][1], app.pool.music_index(4))

    def test_arrows_move_the_queue_and_enter_plays_it(self):
        app = self.app
        app.position = 0
        app.move_queue(-1)
        self.assertEqual(app.position, 0)          # clamped at the top
        app.move_queue(1)
        app.move_queue(1)
        self.assertEqual(app.position, 2)
        self.assertEqual(app.listbox.curselection(), (2,))
        app.play_queued()
        self.assertEqual(app.music.played[-1][1], app.pool.music_index(2))
        # With a search filter, arrows walk the visible rows only.
        app.search_var.set("Song 2")
        self.pump()
        app.move_queue(1)
        self.assertEqual(app.pool.track_at(app.position), "Song 20 | Artist 0")

    def test_rows_show_track_length(self):
        self.pump()
        self.assertIn("(3:20)", self.app.listbox.get(0))

    def test_playlist_picker_shows_pool_playlists_then_expands(self):
        app = self.app
        app.refresh_playlists()
        self.assertEqual(list(app.playlist_combo["values"]),
                         ["Stoppage Music", app.SHOW_ALL_PLAYLISTS])
        # Picking the sentinel expands to everything and leaves the pool alone.
        app.playlist_combo.set(app.SHOW_ALL_PLAYLISTS)
        app.assign_playlist()
        self.assertEqual(list(app.playlist_combo["values"]), ["Stoppage Music", "Warmups"])
        self.assertEqual(app.playlist_combo.get(), "Stoppage Music")
        self.assertEqual(app.pool.playlist, "Stoppage Music")
        # Re-pointing the pool keeps the old playlist in the short list.
        app.playlist_combo.set("Warmups")
        app.assign_playlist()
        self.assertEqual(app.pool.playlist, "Warmups")
        self.assertEqual(list(app.playlist_combo["values"]),
                         ["Stoppage Music", "Warmups", app.SHOW_ALL_PLAYLISTS])
        self.assertEqual(app.config.get("known_playlists"), ["Stoppage Music", "Warmups"])
        # A remembered playlist Music no longer has is not listed.
        app.config.set("known_playlists", ["Gone"])
        app.pool.playlist = "Gone"
        app.refresh_playlists()
        self.assertEqual(list(app.playlist_combo["values"]), ["Stoppage Music", "Warmups"])

    def test_search_filters_the_view(self):
        self.app.search_var.set("Song 1")
        self.pump()
        # "Song 1", and "Song 10".."Song 19"
        self.assertEqual(self.app.listbox.size(), 11)
        self.app.search_var.set("")
        self.pump()
        self.assertEqual(self.app.listbox.size(), 24)

    def test_clip_start_is_passed_to_playback(self):
        track = self.app.pool.track_at(0)
        self.app.pool.set_clip(track, 15, 45)
        self.app.play_at(0)
        self.assertEqual(self.app.music.played[-1][2], 15)
        # An end point arms the clip watcher.
        self.assertIsNotNone(self.app.active_clip)

    def test_clip_without_end_does_not_arm_the_watcher(self):
        track = self.app.pool.track_at(0)
        self.app.pool.set_clip(track, 15, None)
        self.app.play_at(0)
        self.assertIsNone(self.app.active_clip)

    def test_clip_end_stops_playback(self):
        track = self.app.pool.track_at(0)
        self.app.pool.set_clip(track, 0, 12)      # fake position is 12.0
        self.app.play_at(0)
        self.app.music.playing = True
        self.app._check_clip_end()
        self.assertFalse(self.app.music.playing)
        self.assertIsNone(self.app.active_clip)

    def test_next_queues_without_playing(self):
        self.app.play_at(0)
        before = len(self.app.music.played)
        self.app.next_track()
        self.assertEqual(self.app.position, 1)
        self.assertEqual(len(self.app.music.played), before,
                         "Next should queue, not start playback")

    def test_next_wraps_at_the_end(self):
        self.app.position = len(self.app.pool.order) - 1
        self.app.next_track()
        self.assertEqual(self.app.position, 0)

    def test_player_goal_song_beats_team_goal_song(self):
        from hockeymusic.roster import Player
        self.app.config.set_event_song("goal", "Team Horn")
        player = Player("7", "Alexander Mellen", goal_song="Thunderstruck",
                        goal_song_start=10)
        self.app.play_goal_song(player)
        self.assertEqual(self.app.music.played[-1], ("Thunderstruck", 10))
        self.app.play_goal_song(None)
        self.assertEqual(self.app.music.played[-1], ("Team Horn", None))

    def test_family_safe_shuffle_drops_flagged(self):
        self.app.pool.toggle_flag(self.app.pool.tracks[0])
        self.app.config.set("audio.family_safe", True)
        self.app.shuffle()
        self.pump()
        self.assertEqual(len(self.app.pool.order), 23)

    def test_shortcuts_ignore_typing(self):
        entry = tk.Entry(self.app.root)
        fired = []
        handler = self.app._shortcut(lambda: fired.append(1))

        class Event:
            widget = entry
        self.assertIsNone(handler(Event()))
        self.assertEqual(fired, [])

        Event.widget = self.app.listbox
        self.assertEqual(handler(Event()), "break")
        self.assertEqual(fired, [1])

    def test_pools_round_trip_through_config(self):
        self.app.pools.add("Warmup", playlist="Warmups")
        self.app.save_pools()
        self.assertIn("Warmup", self.app.config.get("pools"))


class TestDialogs(UITestCase):
    def test_goal_dialog_preview_matches_what_is_announced(self):
        from hockeymusic import announcements
        from hockeymusic.roster import Player
        from hockeymusic.ui.goal_dialog import GoalDialog

        self.app.roster.players["7"] = Player("7", "Alexander Mellen")
        self.app.roster.players["10"] = Player("10", "Cale Kulig")

        dialog = GoalDialog(self.app)
        dialog.scorer.set("7")
        dialog.assist1.set("10")
        self.pump()

        shown = dialog.preview.cget("text")
        expected = announcements.goal("home", "7", ["10", ""], self.app.roster,
                                      self.app.config.team_name)
        self.assertEqual(shown, expected)
        self.assertIn("Alexander Mellen", shown)
        self.assertIn("Cale Kulig", shown)
        dialog.win.destroy()

    def test_goal_dialog_quick_pick_advances_fields(self):
        from hockeymusic.roster import Player
        from hockeymusic.ui.goal_dialog import GoalDialog

        self.app.roster.players["7"] = Player("7", "Alexander Mellen")
        dialog = GoalDialog(self.app)
        dialog._quick_pick("7")
        self.assertEqual(dialog.scorer.get(), "7")
        self.assertEqual(dialog.target.get(), "assist1")
        dialog._quick_pick("10")
        self.assertEqual(dialog.assist1.get(), "10")
        dialog.win.destroy()

    def test_every_dialog_builds(self):
        from hockeymusic.ui.dialogs import (ClipDialog, FinalScoreDialog,
                                            PrerenderDialog, SettingsDialog)
        from hockeymusic.ui.roster_editor import RosterEditor

        for factory in (
            lambda: FinalScoreDialog(self.app),
            lambda: SettingsDialog(self.app),
            lambda: PrerenderDialog(self.app),
            lambda: RosterEditor(self.app),
            lambda: ClipDialog(self.app, self.app.pool, self.app.pool.track_at(0)),
        ):
            dialog = factory()
            self.pump()
            dialog.win.destroy()

    def test_settings_save_round_trips(self):
        from hockeymusic.ui.dialogs import SettingsDialog

        dialog = SettingsDialog(self.app)
        dialog.song_vars["goal"].set("Boston Bruins Goal Sound")
        dialog.team_var.set("Bruins")
        dialog.duck_volume.set(15)
        dialog._save()
        self.assertEqual(self.app.config.event_song("goal"), "Boston Bruins Goal Sound")
        self.assertEqual(self.app.config.team_name, "Bruins")
        self.assertEqual(self.app.config.get("audio.duck_volume"), 15)

    def test_roster_editor_saves_a_goal_song(self):
        from hockeymusic.ui.roster_editor import RosterEditor, PlayerForm

        editor = RosterEditor(self.app)
        form = PlayerForm(editor, None)
        form.fields["number"].set("88")
        form.fields["name"].set("Jake O'Neil")
        form.fields["goal_song"].set("Thunderstruck")
        form.fields["goal_song_start"].set("0:10")
        form._save()

        player = self.app.roster.get("88")
        self.assertEqual(player.name, "Jake O'Neil")
        self.assertEqual(player.goal_song, "Thunderstruck")
        self.assertEqual(player.goal_song_start, 10)
        editor.win.destroy()


if __name__ == "__main__":
    unittest.main(verbosity=2)
