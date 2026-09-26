"""The game-day console."""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from .. import announcements, paths
from ..announcer import Announcer
from ..config import Config, EVENT_KEYS
from ..music import AppleMusicController
from ..playlists import PoolSet, format_seconds
from ..roster import Roster
from . import common
from .dialogs import ClipDialog, FinalScoreDialog, PrerenderDialog, SettingsDialog
from .goal_dialog import GoalDialog
from .roster_editor import RosterEditor

TICK_MS = 700


class HockeyMusicApp:
    def __init__(self, root, music=None, autostart=True):
        """`music` and `autostart` exist so tests can build the whole UI
        without Apple Music running and without a polling loop."""
        self.root = root
        self.root.title("Hockey Music Controller")
        self.root.geometry("980x780")
        self.root.minsize(860, 640)

        paths.ensure_dirs()
        self.config = Config.load()
        self.music = music or AppleMusicController()
        self.announcer = Announcer(self.config, self.music)
        self.roster = Roster.load(self.config.get("roster_file"))
        self.pools = PoolSet(self.config)

        self.position = 0            # index into the active pool's order
        self.visible = []            # listbox row -> position in order
        self.active_clip = None      # (track, Clip) currently playing
        self._drag_from = None

        self.status_var = tk.StringVar(value="Ready")
        self.now_playing_var = tk.StringVar(value="No track playing")
        self.up_next_var = tk.StringVar(value="")
        self.search_var = tk.StringVar()
        self.pool_var = tk.StringVar(value=self.pools.active_name)
        self.volume_var = tk.IntVar(value=100)

        self._build()
        self._bind_shortcuts()

        if autostart:
            if self.pool.playlist:
                self.load_pool_tracks(quiet=True)
            self._sync_volume()
            self._tick()

    # -- convenience ------------------------------------------------------

    @property
    def pool(self):
        return self.pools.active

    @property
    def family_safe(self):
        return bool(self.config.get("audio.family_safe", False))

    @property
    def fade_out(self):
        return float(self.config.get("audio.fade_out", 1.5))

    # =====================================================================
    # Layout
    # =====================================================================

    def _build(self):
        top = ttk.Frame(self.root, padding=(10, 10, 10, 0))
        top.pack(fill=tk.X)

        tk.Button(top, text="🥅  GOAL!  🏒", command=self.play_goal_song,
                  font=("Arial", 26, "bold"), bg="#FFD700", fg="#000000",
                  height=2, relief=tk.RAISED, bd=5).pack(fill=tk.X)

        self._build_event_buttons(top)
        self._build_pa_buttons(top)
        self._build_transport(top)
        self._build_playlist()
        self._build_footer()

    def _build_event_buttons(self, parent):
        colours = {
            "zamboni": "#87CEEB", "zamboni_2nd": "#87CEEB",
            "game_start": "#FFD700", "intermission_1st": "#98FB98",
            "intermission_2nd": "#98FB98", "end_of_game": "#FFB6C1",
        }
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=(8, 4))
        for key, label in EVENT_KEYS:
            if key in ("goal", "power_play", "penalty_kill"):
                continue
            tk.Button(row, text=label, font=("Arial", 10),
                      bg=colours.get(key, "#DDDDDD"), relief=tk.RAISED, bd=3,
                      command=lambda k=key, l=label: self.play_event(k, l)
                      ).pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)

        situations = ttk.Frame(parent)
        situations.pack(fill=tk.X, pady=4)
        tk.Button(situations, text="⚡ Power Play", bg="#FF6B6B", fg="#111111",
                  font=("Arial", 12, "bold"), relief=tk.RAISED, bd=4,
                  command=lambda: self.play_event("power_play", "Power Play")
                  ).pack(side=tk.LEFT, padx=4, expand=True, fill=tk.X)
        tk.Button(situations, text="🛡️ Penalty Kill", bg="#4ECDC4", fg="#111111",
                  font=("Arial", 12, "bold"), relief=tk.RAISED, bd=4,
                  command=lambda: self.play_event("penalty_kill", "Penalty Kill")
                  ).pack(side=tk.LEFT, padx=4, expand=True, fill=tk.X)

    def _build_pa_buttons(self, parent):
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=4)
        specs = [
            ("📢 Goal Announcement", "#FFA500", lambda: GoalDialog(self)),
            ("🎙 Starting Lineup", "#16A085", self.announce_lineup),
            ("🏁 Final Score", "#9B59B6", lambda: FinalScoreDialog(self)),
        ]
        for label, colour, command in specs:
            tk.Button(row, text=label, command=command, bg=colour, fg="#111111",
                      font=("Arial", 12, "bold"), relief=tk.RAISED, bd=4
                      ).pack(side=tk.LEFT, padx=4, expand=True, fill=tk.X)

    def _build_transport(self, parent):
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=(8, 4))
        for label, command in (("⏯ Play/Pause", self.play_pause),
                               ("⏹ Stop", self.stop),
                               ("⏭ Next", self.next_track)):
            tk.Button(row, text=label, command=command,
                      font=("Arial", 13), width=12).pack(side=tk.LEFT, padx=4)

        ttk.Label(row, text="Volume").pack(side=tk.LEFT, padx=(20, 4))
        ttk.Scale(row, from_=0, to=100, variable=self.volume_var, length=170,
                  command=self._on_volume).pack(side=tk.LEFT)

        info = ttk.Frame(parent)
        info.pack(fill=tk.X, pady=(6, 0))
        ttk.Label(info, textvariable=self.now_playing_var, font=("Arial", 13, "bold"),
                  wraplength=920).pack(anchor="w")
        ttk.Label(info, textvariable=self.up_next_var, font=("Arial", 10),
                  foreground="#555", wraplength=920).pack(anchor="w")

    def _build_playlist(self):
        frame = ttk.LabelFrame(self.root, text="Playlist", padding=8)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        pool_row = ttk.Frame(frame)
        pool_row.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(pool_row, text="Pool:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        self.pool_combo = ttk.Combobox(pool_row, textvariable=self.pool_var, width=18,
                                       state="readonly", values=self.pools.names)
        self.pool_combo.pack(side=tk.LEFT, padx=6)
        self.pool_combo.bind("<<ComboboxSelected>>", lambda e: self.switch_pool())
        ttk.Button(pool_row, text="＋ New", command=self.new_pool).pack(side=tk.LEFT)
        ttk.Button(pool_row, text="🗑", width=3,
                   command=self.delete_pool).pack(side=tk.LEFT, padx=(4, 12))

        ttk.Label(pool_row, text="Apple Music playlist:").pack(side=tk.LEFT)
        self.playlist_combo = ttk.Combobox(pool_row, width=26, state="readonly")
        self.playlist_combo.pack(side=tk.LEFT, padx=6)
        self.playlist_combo.bind("<<ComboboxSelected>>", lambda e: self.assign_playlist())
        ttk.Button(pool_row, text="⟳", width=3,
                   command=self.refresh_playlists).pack(side=tk.LEFT)

        tools = ttk.Frame(frame)
        tools.pack(fill=tk.X, pady=(0, 6))
        ttk.Button(tools, text="🔀 Shuffle", command=self.shuffle).pack(side=tk.LEFT)
        ttk.Button(tools, text="↺ Reset order",
                   command=self.reset_order).pack(side=tk.LEFT, padx=4)
        ttk.Button(tools, text="⏏ Play from top",
                   command=self.play_from_top).pack(side=tk.LEFT)
        ttk.Label(tools, text="Search:").pack(side=tk.LEFT, padx=(16, 4))
        search = ttk.Entry(tools, textvariable=self.search_var, width=24)
        search.pack(side=tk.LEFT)
        self.search_var.trace_add("write", lambda *_: self.refresh_playlist_view())
        ttk.Button(tools, text="✕", width=3,
                   command=lambda: self.search_var.set("")).pack(side=tk.LEFT, padx=2)
        self.track_count = ttk.Label(tools, text="", font=("Arial", 9, "italic"),
                                     foreground="#555")
        self.track_count.pack(side=tk.RIGHT)

        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        scroll = ttk.Scrollbar(list_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox = tk.Listbox(list_frame, yscrollcommand=scroll.set,
                                  font=("Menlo", 12), selectmode=tk.SINGLE,
                                  activestyle="none")
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.config(command=self.listbox.yview)

        self.listbox.bind("<Double-Button-1>", lambda e: self.play_selected())
        self.listbox.bind("<Return>", lambda e: self.play_selected())
        self.listbox.bind("<Button-2>", self._context_menu)
        self.listbox.bind("<Control-Button-1>", self._context_menu)
        self.listbox.bind("<Button-3>", self._context_menu)
        self.listbox.bind("<ButtonPress-1>", self._drag_start)
        self.listbox.bind("<B1-Motion>", self._drag_motion)
        self.listbox.bind("<ButtonRelease-1>", lambda e: setattr(self, "_drag_from", None))

    def _build_footer(self):
        footer = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        footer.pack(fill=tk.X)

        buttons = ttk.Frame(footer)
        buttons.pack(fill=tk.X, pady=(0, 6))
        for label, command in (("⚙️ Settings", lambda: SettingsDialog(self)),
                               ("👥 Roster", lambda: RosterEditor(self)),
                               ("🎙 Pre-render voice", lambda: PrerenderDialog(self))):
            ttk.Button(buttons, text=label, command=command).pack(side=tk.LEFT, padx=4)

        ttk.Label(footer, textvariable=self.status_var, font=("Arial", 10),
                  foreground="#0a6", wraplength=920).pack(anchor="w")
        ttk.Label(footer, font=("Arial", 9, "italic"), foreground="#555",
                  text="SPACE Play/Pause · G Goal · N Next · S Stop · "
                       "O Power play · P Penalty kill · A Announce goal · L Lineup"
                  ).pack(anchor="w")

    def _bind_shortcuts(self):
        actions = {
            "space": self.play_pause,
            "g": self.play_goal_song,
            "n": self.next_track,
            "s": self.stop,
            "o": lambda: self.play_event("power_play", "Power Play"),
            "p": lambda: self.play_event("penalty_kill", "Penalty Kill"),
            "a": lambda: GoalDialog(self),
            "l": self.announce_lineup,
        }
        for key, action in actions.items():
            for variant in ({key} if key == "space" else {key, key.upper()}):
                self.root.bind(f"<{variant}>", self._shortcut(action))

    def _shortcut(self, action):
        """Wrap an action so it never fires while the operator is typing."""
        def handler(event):
            if common.is_typing(event.widget):
                return None
            action()
            return "break"
        return handler

    # =====================================================================
    # Pools and the playlist view
    # =====================================================================

    def refresh_playlists(self):
        playlists = self.music.get_playlists()
        if not playlists:
            messagebox.showerror("Error", "Could not read playlists. Is Music running?")
            return
        self.playlist_combo["values"] = playlists
        self.status_var.set(f"Found {len(playlists)} Apple Music playlists")

    def assign_playlist(self):
        self.pool.playlist = self.playlist_combo.get()
        self.load_pool_tracks()

    def load_pool_tracks(self, quiet=False):
        if not self.pool.playlist:
            if not quiet:
                messagebox.showwarning("No playlist",
                                       "Pick an Apple Music playlist for this pool.")
            return
        count = self.pool.load_tracks(self.music)
        if count:
            self.position = 0
            self.pool.reset_order(family_safe=self.family_safe)
            self.refresh_playlist_view()
            self.save_pools()
            self.status_var.set(f"Loaded {count} tracks into “{self.pool.name}”")
        elif not quiet:
            messagebox.showerror("Error",
                                 f"No tracks found in “{self.pool.playlist}”.")

    def switch_pool(self):
        self.pools.activate(self.pool_var.get())
        self.position = 0
        self.playlist_combo.set(self.pool.playlist)
        if self.pool.playlist and not self.pool.tracks:
            self.load_pool_tracks(quiet=True)
        else:
            self.refresh_playlist_view()
        self.save_pools()
        self.status_var.set(f"Pool: {self.pool.name}")

    def new_pool(self):
        name = simpledialog.askstring("New pool", "Name this pool "
                                      "(Warmup, Intermission, Power Play…):",
                                      parent=self.root)
        if not name:
            return
        if not self.pools.add(name):
            messagebox.showwarning("Already exists", f"“{name}” already exists.")
            return
        self.pool_combo["values"] = self.pools.names
        self.pool_var.set(name)
        self.switch_pool()

    def delete_pool(self):
        name = self.pools.active_name
        if not messagebox.askyesno("Delete pool", f"Delete the “{name}” pool?"):
            return
        if not self.pools.remove(name):
            messagebox.showwarning("Cannot delete", "Keep at least one pool.")
            return
        self.pool_combo["values"] = self.pools.names
        self.pool_var.set(self.pools.active_name)
        self.switch_pool()

    def save_pools(self):
        self.pools.save_into_config()
        self.config.save()

    def refresh_playlist_view(self):
        self.listbox.delete(0, tk.END)
        self.visible = self.pool.matches(self.search_var.get())
        for pos in self.visible:
            self.listbox.insert(tk.END, self._row_text(pos))
        self._highlight()
        shown, total = len(self.visible), len(self.pool.order)
        flagged = len(self.pool.flagged)
        summary = f"{shown} of {total} shown"
        if flagged:
            summary += f" · {flagged} flagged"
        if self.family_safe:
            summary += " · family-safe on"
        self.track_count.config(text=summary)
        self._update_up_next()

    def _row_text(self, pos):
        track = self.pool.track_at(pos)
        marks = []
        clip = self.pools.clip_for(track, self.pool)
        if clip and clip.is_set:
            window = format_seconds(clip.start)
            if clip.end is not None:
                window += f"–{format_seconds(clip.end)}"
            marks.append(f"⏱{window}")
        if track in self.pool.flagged:
            marks.append("🚫")
        prefix = f"{pos + 1:>3}. "
        suffix = ("  " + " ".join(marks)) if marks else ""
        return f"{prefix}{track}{suffix}"

    def _highlight(self):
        self.listbox.selection_clear(0, tk.END)
        if self.position in self.visible:
            row = self.visible.index(self.position)
            self.listbox.selection_set(row)
            self.listbox.see(row)

    def _update_up_next(self):
        track = self.pool.track_at(self.position)
        self.up_next_var.set(f"⏭ Up next:  {track}" if track else "")

    # -- reordering and the context menu ----------------------------------

    def _drag_start(self, event):
        self._drag_from = self.listbox.nearest(event.y)

    def _drag_motion(self, event):
        if self._drag_from is None or self.search_var.get().strip():
            return  # reordering a filtered view would be misleading
        to_row = self.listbox.nearest(event.y)
        if to_row == self._drag_from or to_row < 0 or to_row >= len(self.visible):
            return
        moved = self.pool.order.pop(self.visible[self._drag_from])
        self.pool.order.insert(self.visible[to_row], moved)
        self._drag_from = to_row
        self.refresh_playlist_view()
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(to_row)

    def _context_menu(self, event):
        row = self.listbox.nearest(event.y)
        if row < 0 or row >= len(self.visible):
            return
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(row)
        pos = self.visible[row]
        track = self.pool.track_at(pos)

        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="▶ Play now", command=lambda: self.play_at(pos))
        menu.add_command(label="⏭ Queue as next", command=lambda: self.queue_at(pos))
        menu.add_separator()
        clip = self.pools.clip_for(track, self.pool)
        label = "✏️ Edit clip points" if clip and clip.is_set else "⏱️ Set clip points"
        menu.add_command(label=label, command=lambda: ClipDialog(self, self.pool, track))
        if self.pool.clip_for(track):
            menu.add_command(label="🗑️ Clear clip points",
                             command=lambda: self._clear_clip(track))
        menu.add_separator()
        flagged = track in self.pool.flagged
        menu.add_command(
            label="✅ Unflag (family-safe)" if flagged else "🚫 Flag as not family-safe",
            command=lambda: self._toggle_flag(track))
        menu.tk_popup(event.x_root, event.y_root)

    def _clear_clip(self, track):
        self.pool.set_clip(track, 0, None)
        self.save_pools()
        self.refresh_playlist_view()

    def _toggle_flag(self, track):
        flagged = self.pool.toggle_flag(track)
        self.save_pools()
        self.refresh_playlist_view()
        self.status_var.set(f"{'Flagged' if flagged else 'Unflagged'}: {track}")

    # =====================================================================
    # Playback
    # =====================================================================

    def _on_volume(self, _value=None):
        self.music.set_volume(self.volume_var.get())
        self.music.remember_base_volume()

    def _sync_volume(self):
        current = self.music.get_volume()
        if current is not None:
            self.volume_var.set(current)
            self.music.remember_base_volume()

    def play_at(self, pos):
        """Play the track at `pos` in the current order, honouring its clip."""
        if not self.pool.tracks or not self.pool.playlist:
            messagebox.showwarning("No playlist", "Load a playlist for this pool first.")
            return
        pos = max(0, min(pos, len(self.pool.order) - 1))
        self.position = pos
        track = self.pool.track_at(pos)
        clip = self.pools.clip_for(track, self.pool)

        self.music.cancel_fades()
        self.music.set_volume(self.music.base_volume)
        self.music.play_track_from_playlist(
            self.pool.playlist, self.pool.music_index(pos),
            start_time=clip.start if clip else None)

        self.active_clip = (track, clip) if clip and clip.end is not None else None
        self.pool.note_played(track)
        self._highlight()
        self._update_up_next()

    def queue_at(self, pos):
        """Point at a track without playing it -- ready for the next whistle."""
        self.position = max(0, min(pos, len(self.pool.order) - 1))
        self._highlight()
        self._update_up_next()

    def play_selected(self):
        selection = self.listbox.curselection()
        if selection and selection[0] < len(self.visible):
            self.play_at(self.visible[selection[0]])

    def play_from_top(self):
        self.play_at(0)

    def play_pause(self):
        if self.music.is_playing():
            self._fade_and(self.music.pause)
            self.status_var.set("Paused")
        else:
            current = self.music.get_current_track()
            if current in (None, "No track playing"):
                # Fully stopped (or Music was busy) -- start the queued track.
                self.play_at(self.position)
            else:
                self.music.set_volume(self.music.base_volume)
                self.music.play_pause()

    def stop(self):
        """Hard stop, no fade -- when the whistle goes, the music goes."""
        self.active_clip = None
        base = self.music.remember_base_volume()
        self.music.cancel_fades()
        self.music.stop()
        self.music.set_volume(base)
        self.status_var.set("Stopped")

    def _fade_and(self, action):
        """Fade the music down, then run `action`, then restore the volume."""
        base = self.music.remember_base_volume()
        duration = self.fade_out
        if duration <= 0:
            action()
            self.music.set_volume(base)
            return

        def finish():
            action()
            self.music.set_volume(base)

        self.music.fade(0, duration, then=finish)

    def next_track(self):
        """Fade out and line up the next track for the next stoppage."""
        if not self.pool.order:
            messagebox.showwarning("No playlist", "Load a playlist for this pool first.")
            return
        self.active_clip = None
        self._fade_and(self.music.stop)
        self.position = (self.position + 1) % len(self.pool.order)
        self._highlight()
        self._update_up_next()
        self.status_var.set(f"Queued: {self.pool.track_at(self.position)}")

    def shuffle(self):
        if not self.pool.tracks:
            return
        self.pool.shuffle(family_safe=self.family_safe)
        self.position = 0
        self.refresh_playlist_view()
        self.status_var.set(f"Shuffled {len(self.pool.order)} tracks"
                            + (" (family-safe)" if self.family_safe else ""))

    def reset_order(self):
        self.pool.reset_order(family_safe=self.family_safe)
        self.position = 0
        self.refresh_playlist_view()

    # -- one-off songs ----------------------------------------------------

    def play_event(self, key, label):
        song = self.config.event_song(key)
        if not song:
            messagebox.showwarning("Not configured",
                                   f"Set a song for “{label}” in Settings.")
            return
        self.active_clip = None
        self.music.cancel_fades()
        self.music.set_volume(self.music.base_volume)
        if self.music.play_track_by_name(song):
            self.status_var.set(f"{label}: {song}")
        else:
            messagebox.showerror("Error", f"Could not play “{song}”. "
                                          "Check the exact title in Apple Music.")

    def play_goal_song(self, player=None):
        """Play the scorer's own goal song, falling back to the team's."""
        song = player.goal_song if player and player.goal_song else \
            self.config.event_song("goal")
        if not song:
            messagebox.showwarning("No goal song", "Set a goal song in Settings.")
            return
        start = player.goal_song_start if player and player.goal_song else 0

        self.active_clip = None
        self.music.cancel_fades()
        self.music.set_volume(self.music.base_volume)
        if self.music.play_track_by_name(song, start_time=start or None):
            who = f"{player.display_name}'s song" if player and player.goal_song \
                else "goal song"
            self.status_var.set(f"🎉 GOAL! Playing {who}: {song}")
        else:
            messagebox.showerror("Error", f"Could not play “{song}”.")

    # =====================================================================
    # Announcements
    # =====================================================================

    def announce(self, text, celebration=None):
        """Queue a PA announcement. Returns immediately."""
        self.announcer.announce(text, celebration=celebration,
                                on_status=self._status_from_thread)

    def _status_from_thread(self, message):
        self.root.after(0, lambda: self.status_var.set(message))

    def announce_lineup(self):
        if not len(self.roster):
            messagebox.showwarning("No roster", "Load a roster first.")
            return
        items = announcements.lineup_sequence(self.roster, self.config.team_name)
        uncached = sum(1 for _, text in items if not self.announcer.is_cached(text))
        if uncached and not messagebox.askyesno(
                "Announce lineup",
                f"{len(items)} lines, {uncached} not yet cached.\n\n"
                "Uncached lines render from Hume one at a time, which is slow on "
                "rink wifi. Pre-render them for instant playback.\n\nAnnounce anyway?"):
            return
        for _key, text in items:
            self.announce(text)
        self.status_var.set(f"🎙 Announcing lineup ({len(items)} lines)…")

    # =====================================================================
    # Housekeeping
    # =====================================================================

    def load_roster(self, path):
        self.roster = Roster.load(path)
        self.config.set("roster_file", str(path))
        self.config.save()

    def refresh_after_roster_change(self):
        self.status_var.set(f"Roster: {len(self.roster)} players")

    def apply_settings(self):
        """Re-read settings that change how the list is filtered or displayed."""
        self.pool.reset_order(family_safe=self.family_safe)
        self.position = 0
        self.refresh_playlist_view()
        self.status_var.set("Settings saved")

    def _tick(self):
        """Poll Apple Music: update the display and honour clip stop points."""
        current = self.music.get_current_track()
        if current is not None:      # None means Music was busy; keep the last value
            self.now_playing_var.set(f"♪  {current}")
        self._check_clip_end()
        self.root.after(TICK_MS, self._tick)

    def _check_clip_end(self):
        if not self.active_clip:
            return
        _track, clip = self.active_clip
        position = self.music.get_player_position()
        if position is None:
            return
        # Start the fade early so the music lands on the out point, not past it.
        if position >= max(0, clip.end - self.fade_out):
            self.active_clip = None
            self._fade_and(self.music.stop)
            self.status_var.set("Clip finished")


def main():
    root = tk.Tk()
    HockeyMusicApp(root)
    root.mainloop()
