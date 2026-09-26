"""Final score, settings, and the pre-game voice renderer."""

import threading
import tkinter as tk
from tkinter import ttk, messagebox

from .. import announcements
from ..config import EVENT_KEYS
from ..playlists import format_seconds, parse_time
from .common import modal, center, preview_box


class FinalScoreDialog:
    def __init__(self, app):
        self.app = app
        self.win = modal(app.root, "Final Score", "500x360")

        self.home = tk.StringVar()
        self.visitor = tk.StringVar()
        self.visitor_score = tk.StringVar()

        frame = ttk.Frame(self.win, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frame, text="🏁 Final Score",
                  font=("Arial", 16, "bold")).pack(anchor="w", pady=(0, 12))

        grid = ttk.Frame(frame)
        grid.pack(fill=tk.X)
        rows = [(f"{app.config.team_name} score", self.home, 8),
                ("Visiting team", self.visitor, 22),
                ("Visiting score", self.visitor_score, 8)]
        for row, (label, var, width) in enumerate(rows):
            ttk.Label(grid, text=label).grid(row=row, column=0, sticky=tk.W, pady=8)
            entry = ttk.Entry(grid, textvariable=var, width=width, font=("Arial", 13))
            entry.grid(row=row, column=1, sticky=tk.W, padx=10, pady=8)
            entry.bind("<Return>", lambda e: self.announce())
            if row == 0:
                entry.focus_set()

        ttk.Label(frame, text="The crowd will hear:",
                  font=("Arial", 11, "bold")).pack(anchor="w", pady=(12, 4))
        self.preview = preview_box(frame, width=440)
        self.preview.pack(fill=tk.X)
        for var in (self.home, self.visitor, self.visitor_score):
            var.trace_add("write", lambda *_: self._refresh())
        self._refresh()

        buttons = ttk.Frame(frame)
        buttons.pack(fill=tk.X, pady=(14, 0))
        tk.Button(buttons, text="🎤 ANNOUNCE FINAL SCORE", command=self.announce,
                  font=("Arial", 13, "bold"), bg="#9B59B6", fg="#111111", height=2
                  ).pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(buttons, text="Cancel",
                   command=self.win.destroy).pack(side=tk.LEFT, padx=(8, 0))
        center(self.win)

    def _text(self):
        if not (self.home.get().strip() and self.visitor.get().strip()
                and self.visitor_score.get().strip()):
            return ""
        return announcements.final_score(
            self.home.get().strip(), self.visitor.get().strip(),
            self.visitor_score.get().strip(), self.app.config.team_name)

    def _refresh(self):
        self.preview.config(text=self._text() or "Fill in all three fields")

    def announce(self):
        text = self._text()
        if not text:
            messagebox.showwarning("Incomplete", "Fill in all three fields.",
                                   parent=self.win)
            return
        self.app.announce(text)
        self.win.destroy()


class SettingsDialog:
    """Event songs plus the audio behaviour that used to be hard-coded."""

    def __init__(self, app):
        self.app = app
        self.win = modal(app.root, "Settings", "700x680")
        self.song_vars = {}
        self._build()
        center(self.win)

    def _build(self):
        notebook = ttk.Notebook(self.win)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        notebook.add(self._songs_tab(notebook), text="Event songs")
        notebook.add(self._audio_tab(notebook), text="Audio")
        notebook.add(self._announcer_tab(notebook), text="Announcer")

        buttons = ttk.Frame(self.win, padding=(10, 0, 10, 10))
        buttons.pack(fill=tk.X)
        tk.Button(buttons, text="💾 Save", command=self._save,
                  font=("Arial", 11, "bold"), bg="#2E86DE", fg="#111111"
                  ).pack(side=tk.RIGHT)
        ttk.Button(buttons, text="Close",
                   command=self.win.destroy).pack(side=tk.RIGHT, padx=8)

    def _songs_tab(self, parent):
        tab = ttk.Frame(parent, padding=14)
        ttk.Label(tab, text="Type the exact track title as it appears in Apple Music, "
                            "or a playlist name to play it all the way through.",
                  font=("Arial", 9, "italic"), foreground="#555"
                  ).grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        for row, (key, label) in enumerate(EVENT_KEYS, start=1):
            var = tk.StringVar(value=self.app.config.event_song(key))
            self.song_vars[key] = var
            ttk.Label(tab, text=f"{label}:").grid(row=row, column=0, sticky=tk.W, pady=5)
            ttk.Entry(tab, textvariable=var, width=44).grid(row=row, column=1,
                                                            padx=8, pady=5)
            ttk.Button(tab, text="▶ Test",
                       command=lambda v=var: self.app.music.play_song_or_playlist(v.get())
                       ).grid(row=row, column=2, padx=4)
        tab.columnconfigure(1, weight=1)

        row = len(EVENT_KEYS) + 1
        ttk.Separator(tab, orient="horizontal").grid(row=row, column=0, columnspan=3,
                                                     sticky="ew", pady=14)
        ttk.Label(tab, text="Team name (used in every announcement):"
                  ).grid(row=row + 1, column=0, sticky=tk.W)
        self.team_var = tk.StringVar(value=self.app.config.team_name)
        ttk.Entry(tab, textvariable=self.team_var, width=24
                  ).grid(row=row + 1, column=1, sticky=tk.W, padx=8)
        return tab

    def _audio_tab(self, parent):
        tab = ttk.Frame(parent, padding=14)
        cfg = self.app.config

        self.fade_out = tk.DoubleVar(value=cfg.get("audio.fade_out", 1.5))
        self.duck_volume = tk.IntVar(value=cfg.get("audio.duck_volume", 25))
        self.duck_enabled = tk.BooleanVar(value=cfg.get("audio.duck_enabled", True))
        self.stop_for_pa = tk.BooleanVar(value=cfg.get("audio.announce_stops_music", True))
        self.family_safe = tk.BooleanVar(value=cfg.get("audio.family_safe", False))

        ttk.Label(tab, text="Stops and skips fade out over:").grid(row=0, column=0,
                                                                   sticky=tk.W, pady=8)
        ttk.Scale(tab, from_=0.0, to=4.0, variable=self.fade_out, length=220
                  ).grid(row=0, column=1, padx=8)
        self.fade_label = ttk.Label(tab, text="")
        self.fade_label.grid(row=0, column=2, sticky=tk.W)
        self.fade_out.trace_add("write", lambda *_: self.fade_label.config(
            text=f"{self.fade_out.get():.1f}s" if self.fade_out.get() else "instant"))
        self.fade_label.config(text=f"{self.fade_out.get():.1f}s")

        ttk.Checkbutton(tab, text="Stop the music when the PA talks (off: duck it instead)",
                        variable=self.stop_for_pa
                        ).grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(8, 0))
        ttk.Checkbutton(tab, text="Duck the music while the PA is talking",
                        variable=self.duck_enabled
                        ).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=8)
        ttk.Label(tab, text="Ducked volume:").grid(row=3, column=0, sticky=tk.W, pady=8)
        ttk.Scale(tab, from_=0, to=80, variable=self.duck_volume, length=220
                  ).grid(row=3, column=1, padx=8)
        self.duck_label = ttk.Label(tab, text=f"{self.duck_volume.get()}%")
        self.duck_label.grid(row=3, column=2, sticky=tk.W)
        self.duck_volume.trace_add("write", lambda *_: self.duck_label.config(
            text=f"{int(self.duck_volume.get())}%"))

        ttk.Separator(tab, orient="horizontal").grid(row=4, column=0, columnspan=3,
                                                     sticky="ew", pady=14)
        ttk.Checkbutton(tab, text="Family-safe mode — keep flagged tracks out of rotation",
                        variable=self.family_safe
                        ).grid(row=5, column=0, columnspan=3, sticky=tk.W)
        ttk.Label(tab, text="Flag a track by right-clicking it in the playlist. "
                            "Flagged tracks stay in the list but are skipped when "
                            "shuffling with this on.",
                  font=("Arial", 9, "italic"), foreground="#555", wraplength=560
                  ).grid(row=6, column=0, columnspan=3, sticky=tk.W, pady=(4, 0))
        return tab

    def _announcer_tab(self, parent):
        tab = ttk.Frame(parent, padding=14)
        cfg = self.app.config
        announcer = self.app.announcer

        ttk.Label(tab, text=announcer.status_text, font=("Arial", 11, "bold"),
                  foreground="green" if announcer.hume_available else "orange"
                  ).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 12))

        self.use_cache = tk.BooleanVar(value=cfg.get("announcer.use_cache", True))
        ttk.Checkbutton(tab, text="Use cached audio when available (instant, works offline)",
                        variable=self.use_cache
                        ).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=4)

        self.timeout = tk.DoubleVar(value=cfg.get("announcer.timeout", 20.0))
        ttk.Label(tab, text="Hume timeout (seconds):").grid(row=2, column=0,
                                                            sticky=tk.W, pady=8)
        ttk.Spinbox(tab, from_=5, to=60, increment=5, textvariable=self.timeout,
                    width=8).grid(row=2, column=1, sticky=tk.W, padx=8)

        self.default_clip = tk.StringVar(
            value=cfg.get("announcer.default_celebration", "woo.m4a"))
        ttk.Label(tab, text="Default celebration clip:").grid(row=3, column=0,
                                                              sticky=tk.W, pady=8)
        ttk.Entry(tab, textvariable=self.default_clip, width=24
                  ).grid(row=3, column=1, sticky=tk.W, padx=8)

        self.fallback_enabled = tk.BooleanVar(
            value=cfg.get("announcer.fallback_enabled", False))
        ttk.Checkbutton(tab, text="If Hume can't render a line, say it in a macOS voice "
                                  "(off: skip the announcement)",
                        variable=self.fallback_enabled
                        ).grid(row=7, column=0, columnspan=2, sticky=tk.W, pady=(14, 0))
        self.fallback_voice = tk.StringVar(
            value=cfg.get("announcer.fallback_voice", "Alex"))
        ttk.Label(tab, text="Fallback macOS voice:").grid(row=4, column=0,
                                                          sticky=tk.W, pady=8)
        ttk.Combobox(tab, textvariable=self.fallback_voice, width=20, state="readonly",
                     values=("Alex", "Daniel", "Samantha", "Karen", "Moira", "Tessa")
                     ).grid(row=4, column=1, sticky=tk.W, padx=8)

        ttk.Separator(tab, orient="horizontal").grid(row=5, column=0, columnspan=2,
                                                     sticky="ew", pady=14)
        count, size = announcer.cache_stats()
        self.cache_label = ttk.Label(
            tab, text=f"Cache: {count} lines, {size / 1_000_000:.1f} MB")
        self.cache_label.grid(row=6, column=0, sticky=tk.W)
        ttk.Button(tab, text="Clear cache", command=self._clear_cache
                   ).grid(row=6, column=1, sticky=tk.W, padx=8)
        return tab

    def _clear_cache(self):
        removed = self.app.announcer.clear_cache()
        self.cache_label.config(text=f"Cache: 0 lines (removed {removed})")

    def _save(self):
        cfg = self.app.config
        for key, var in self.song_vars.items():
            cfg.set_event_song(key, var.get().strip())
        cfg.set("team_name", self.team_var.get().strip() or "Patriots")
        cfg.set("audio.fade_out", round(float(self.fade_out.get()), 2))
        cfg.set("audio.duck_volume", int(self.duck_volume.get()))
        cfg.set("audio.duck_enabled", bool(self.duck_enabled.get()))
        cfg.set("audio.announce_stops_music", bool(self.stop_for_pa.get()))
        cfg.set("audio.family_safe", bool(self.family_safe.get()))
        cfg.set("announcer.use_cache", bool(self.use_cache.get()))
        cfg.set("announcer.timeout", float(self.timeout.get()))
        cfg.set("announcer.default_celebration", self.default_clip.get().strip())
        cfg.set("announcer.fallback_voice", self.fallback_voice.get())
        cfg.set("announcer.fallback_enabled", bool(self.fallback_enabled.get()))
        cfg.save()
        self.app.apply_settings()
        self.win.destroy()


class PrerenderDialog:
    """Render announcements to disk before game day.

    Rink wifi is the enemy: a cached line plays in milliseconds with no network
    at all, and costs nothing on the second use.
    """

    def __init__(self, app):
        self.app = app
        self.win = modal(app.root, "Pre-render Announcements", "620x420")
        self.scope = tk.StringVar(value="basic")
        self._stop = False
        self._running = False
        self._build()
        self._refresh()
        center(self.win)

    def _build(self):
        frame = ttk.Frame(self.win, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frame, text="🎙 Pre-render the announcer",
                  font=("Arial", 15, "bold")).pack(anchor="w")
        ttk.Label(frame,
                  text="Do this at home on good wifi. Cached lines play instantly at "
                       "the rink even with no internet, and never cost another API call.",
                  font=("Arial", 9, "italic"), foreground="#555", wraplength=560
                  ).pack(anchor="w", pady=(4, 12))

        for value, label in (("lineup", "Starting lineup only"),
                             ("basic", "Lineup + every unassisted goal call"),
                             ("full", "Everything, including each single-assist call")):
            ttk.Radiobutton(frame, text=label, variable=self.scope, value=value,
                            command=self._refresh).pack(anchor="w", pady=2)

        self.summary = ttk.Label(frame, text="", font=("Arial", 11, "bold"))
        self.summary.pack(anchor="w", pady=(12, 6))

        self.progress = ttk.Progressbar(frame, mode="determinate", length=560)
        self.progress.pack(fill=tk.X, pady=4)
        self.status = ttk.Label(frame, text="", font=("Arial", 9), wraplength=560,
                                foreground="#555")
        self.status.pack(anchor="w")

        buttons = ttk.Frame(frame)
        buttons.pack(fill=tk.X, pady=(14, 0))
        self.run_button = tk.Button(buttons, text="⚡ Render", command=self._start,
                                    font=("Arial", 12, "bold"),
                                    bg="#27AE60", fg="#111111")
        self.run_button.pack(side=tk.LEFT)
        ttk.Button(buttons, text="Close", command=self._close).pack(side=tk.RIGHT)

    def _manifest(self):
        return announcements.prerender_manifest(
            self.app.roster, self.app.config.team_name, self.scope.get())

    def _refresh(self):
        items = self._manifest()
        missing = [i for i in items if not self.app.announcer.is_cached(i[1])]
        self.summary.config(
            text=f"{len(items)} lines — {len(items) - len(missing)} already cached, "
                 f"{len(missing)} to render")
        self.progress["maximum"] = max(1, len(missing))
        self.progress["value"] = 0

    def _start(self):
        if self._running:
            self._stop = True
            return
        if not self.app.announcer.hume_available:
            messagebox.showwarning(
                "Hume unavailable",
                "Rendering needs a working HUME_API_KEY in .env.", parent=self.win)
            return

        self._running = True
        self._stop = False
        self.run_button.config(text="■ Stop", bg="#C0392B")
        items = self._manifest()

        def progress(done, total, text):
            self.win.after(0, lambda: self._on_progress(done, total, text))

        def work():
            result = self.app.announcer.prerender(
                items, progress=progress, should_stop=lambda: self._stop)
            self.win.after(0, lambda: self._finish(result))

        threading.Thread(target=work, daemon=True).start()

    def _on_progress(self, done, total, text):
        if not self.win.winfo_exists():
            return
        self.progress["maximum"] = total
        self.progress["value"] = done
        self.status.config(text=f"{done}/{total}  {text[:90]}")

    def _finish(self, result):
        rendered, skipped, failed = result
        self._running = False
        if not self.win.winfo_exists():
            return
        self.run_button.config(text="⚡ Render", bg="#27AE60")
        self.status.config(
            text=f"Done — {rendered} rendered, {skipped} already cached, {failed} failed."
                 + (" Check your connection and retry the failures." if failed else ""))
        self._refresh()

    def _close(self):
        self._stop = True
        self.win.destroy()


class ClipDialog:
    """Set the in and out points for one track."""

    def __init__(self, app, pool, track):
        self.app = app
        self.pool = pool
        self.track = track
        clip = app.pools.clip_for(track, pool)   # inherits another pool's clip
        self.win = modal(app.root, "Clip", "460x300")

        self.start = tk.StringVar(value=format_seconds(clip.start if clip else 0))
        self.end = tk.StringVar(
            value=format_seconds(clip.end) if clip and clip.end is not None else "")

        frame = ttk.Frame(self.win, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frame, text="⏱️ Clip points", font=("Arial", 14, "bold")).pack(anchor="w")
        ttk.Label(frame, text=track, wraplength=400, font=("Arial", 10),
                  foreground="#555").pack(anchor="w", pady=(4, 12))

        grid = ttk.Frame(frame)
        grid.pack(fill=tk.X)
        ttk.Label(grid, text="Start at:").grid(row=0, column=0, sticky=tk.W, pady=6)
        start_entry = ttk.Entry(grid, textvariable=self.start, width=10,
                                font=("Arial", 13))
        start_entry.grid(row=0, column=1, padx=8)
        start_entry.focus_set()
        ttk.Button(grid, text="Use current position",
                   command=lambda: self._grab(self.start)).grid(row=0, column=2)

        ttk.Label(grid, text="Stop at:").grid(row=1, column=0, sticky=tk.W, pady=6)
        ttk.Entry(grid, textvariable=self.end, width=10,
                  font=("Arial", 13)).grid(row=1, column=1, padx=8)
        ttk.Button(grid, text="Use current position",
                   command=lambda: self._grab(self.end)).grid(row=1, column=2)

        ttk.Label(frame, text="Leave “stop at” blank to play to the end of the track. "
                              "The stop fades out rather than cutting off.",
                  font=("Arial", 9, "italic"), foreground="#555", wraplength=400
                  ).pack(anchor="w", pady=(10, 0))

        buttons = ttk.Frame(frame)
        buttons.pack(fill=tk.X, pady=(16, 0))
        tk.Button(buttons, text="Save", command=self._save, font=("Arial", 11, "bold"),
                  bg="#2E86DE", fg="#111111").pack(side=tk.RIGHT)
        ttk.Button(buttons, text="Cancel", command=self.win.destroy).pack(side=tk.RIGHT,
                                                                          padx=8)
        ttk.Button(buttons, text="Clear clip", command=self._clear).pack(side=tk.LEFT)
        center(self.win)

    def _grab(self, var):
        position = self.app.music.get_player_position()
        if position is None:
            messagebox.showinfo("Not playing", "Start the track first.", parent=self.win)
            return
        var.set(format_seconds(int(position)))

    def _clear(self):
        self.pool.set_clip(self.track, 0, None)
        self.app.save_pools()
        self.app.refresh_playlist_view()
        self.win.destroy()

    def _save(self):
        try:
            start = parse_time(self.start.get() or "0")
            end = parse_time(self.end.get()) if self.end.get().strip() else None
        except ValueError as e:
            messagebox.showerror("Invalid time", str(e), parent=self.win)
            return
        if end is not None and end <= start:
            messagebox.showerror("Invalid range", "Stop time must be after start time.",
                                 parent=self.win)
            return
        self.pool.set_clip(self.track, start, end)
        self.app.save_pools()
        self.app.refresh_playlist_view()
        self.win.destroy()
