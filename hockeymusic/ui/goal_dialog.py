"""Goal announcement dialog with roster quick-pick and per-player goal songs."""

import tkinter as tk
from tkinter import ttk, messagebox

from .. import announcements, paths
from .common import modal, center, preview_box


class GoalDialog:
    """Announce a goal: pick the scorer, pick assists, hear their song."""

    def __init__(self, app):
        self.app = app
        self.roster = app.roster
        self.win = modal(app.root, "Goal Announcement", "640x680")

        self.team = tk.StringVar(value="home")
        self.scorer = tk.StringVar()
        self.assist1 = tk.StringVar()
        self.assist2 = tk.StringVar()
        self.play_song = tk.BooleanVar(value=True)
        # Which field the roster quick-pick buttons fill next.
        self.target = tk.StringVar(value="scorer")

        self._build()
        for var in (self.team, self.scorer, self.assist1, self.assist2):
            var.trace_add("write", lambda *_: self._refresh())
        self._refresh()
        center(self.win)

    # -- layout -----------------------------------------------------------

    def _build(self):
        frame = ttk.Frame(self.win, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="📢 Goal Announcement",
                  font=("Arial", 16, "bold")).pack(anchor="w")
        ttk.Label(frame, text=self.app.announcer.status_text,
                  font=("Arial", 9, "italic"),
                  foreground="green" if self.app.announcer.hume_available else "orange"
                  ).pack(anchor="w", pady=(0, 10))

        team_row = ttk.Frame(frame)
        team_row.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(team_row, text="Team:", font=("Arial", 11, "bold")).pack(side=tk.LEFT)
        ttk.Radiobutton(team_row, text=f"Home ({self.app.config.team_name})",
                        variable=self.team, value="home").pack(side=tk.LEFT, padx=8)
        ttk.Radiobutton(team_row, text="Away", variable=self.team,
                        value="away").pack(side=tk.LEFT)

        # Number entries, each with the resolved player name beside it.
        self.name_labels = {}
        grid = ttk.Frame(frame)
        grid.pack(fill=tk.X, pady=4)
        rows = [("Goal by #", "scorer", self.scorer),
                ("Assist #", "assist1", self.assist1),
                ("2nd assist #", "assist2", self.assist2)]
        for row, (label, key, var) in enumerate(rows):
            ttk.Radiobutton(grid, text=label, variable=self.target,
                            value=key).grid(row=row, column=0, sticky=tk.W, pady=4)
            entry = ttk.Entry(grid, textvariable=var, width=8, font=("Arial", 14))
            entry.grid(row=row, column=1, padx=8, pady=4)
            entry.bind("<Return>", lambda e: self.announce())
            if key == "scorer":
                entry.focus_set()
            name = ttk.Label(grid, text="", font=("Arial", 12, "bold"),
                             foreground="#0a6")
            name.grid(row=row, column=2, sticky=tk.W)
            self.name_labels[key] = name
        grid.columnconfigure(2, weight=1)

        self._build_quick_pick(frame)

        ttk.Checkbutton(frame, text="Play the scorer's goal song first",
                        variable=self.play_song).pack(anchor="w", pady=(8, 4))
        self.song_label = ttk.Label(frame, text="", font=("Arial", 9, "italic"),
                                    foreground="#555")
        self.song_label.pack(anchor="w")

        ttk.Label(frame, text="The crowd will hear:",
                  font=("Arial", 11, "bold")).pack(anchor="w", pady=(12, 4))
        self.preview = preview_box(frame, width=580)
        self.preview.pack(fill=tk.X)
        self.cache_label = ttk.Label(frame, text="", font=("Arial", 9, "italic"))
        self.cache_label.pack(anchor="w", pady=(4, 0))

        buttons = ttk.Frame(frame)
        buttons.pack(fill=tk.X, pady=(14, 0))
        tk.Button(buttons, text="🎤 ANNOUNCE GOAL", command=self.announce,
                  font=("Arial", 15, "bold"), bg="#FF6B6B", fg="white",
                  height=2).pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(buttons, text="Cancel",
                   command=self.win.destroy).pack(side=tk.LEFT, padx=(8, 0))

    def _build_quick_pick(self, parent):
        """A grid of jersey numbers -- faster and less error-prone than typing."""
        if not len(self.roster):
            return
        box = ttk.LabelFrame(parent, text="Tap a number (fills the selected field)",
                             padding=6)
        box.pack(fill=tk.X, pady=(10, 0))
        columns = 9
        for i, player in enumerate(self.roster.sorted_players()):
            btn = tk.Button(
                box, text=player.number, width=4,
                font=("Arial", 12, "bold"),
                command=lambda n=player.number: self._quick_pick(n),
            )
            btn.grid(row=i // columns, column=i % columns, padx=2, pady=2)
            _tooltip(btn, player.label)

    def _quick_pick(self, number):
        var = {"scorer": self.scorer, "assist1": self.assist1,
               "assist2": self.assist2}[self.target.get()]
        var.set(number)
        # Advance the target so tapping scorer → assist → assist just works.
        nxt = {"scorer": "assist1", "assist1": "assist2", "assist2": "assist2"}
        self.target.set(nxt[self.target.get()])

    # -- state ------------------------------------------------------------

    def _refresh(self, *_):
        home = self.team.get() == "home"
        for key, var in (("scorer", self.scorer), ("assist1", self.assist1),
                         ("assist2", self.assist2)):
            number = var.get().strip()
            if not number:
                self.name_labels[key].config(text="")
                continue
            name = self.roster.display_name(number) if home else None
            if home and not name:
                self.name_labels[key].config(text="not on roster", foreground="#c60")
            else:
                self.name_labels[key].config(text=name or "", foreground="#0a6")

        text = self._text()
        self.preview.config(text=text or "Enter the scorer's number")

        if text:
            cached = self.app.announcer.is_cached(text)
            self.cache_label.config(
                text="⚡ Cached — plays instantly, no wifi needed" if cached
                else "☁️ Not cached — will render from Hume (needs wifi)",
                foreground="#0a6" if cached else "#c60")
        else:
            self.cache_label.config(text="")

        player = self.roster.get(self.scorer.get()) if home else None
        if player and player.goal_song:
            self.song_label.config(text=f"🎵 {player.display_name}'s song: {player.goal_song}")
        elif home:
            team_song = self.app.config.event_song("goal") or "(none configured)"
            self.song_label.config(text=f"🎵 Team goal song: {team_song}")
        else:
            self.song_label.config(text="")

    def _text(self):
        scorer = self.scorer.get().strip()
        if not scorer:
            return ""
        assists = [self.assist1.get().strip(), self.assist2.get().strip()]
        return announcements.goal(
            self.team.get(), scorer, assists,
            self.roster if self.team.get() == "home" else None,
            self.app.config.team_name,
        )

    # -- action -----------------------------------------------------------

    def announce(self):
        scorer = self.scorer.get().strip()
        if not scorer:
            messagebox.showwarning("No scorer", "Enter the scorer's number.",
                                   parent=self.win)
            return

        home = self.team.get() == "home"
        player = self.roster.get(scorer) if home else None

        if home and self.play_song.get():
            self.app.play_goal_song(player)

        celebration = None
        if home:
            clip = (player.celebration_clip if player and player.celebration_clip
                    else self.app.config.get("announcer.default_celebration"))
            found = paths.sound_clip(clip)
            celebration = str(found) if found else None

        self.app.announce(self._text(), celebration=celebration)
        self.win.destroy()


def _tooltip(widget, text):
    """Minimal hover tooltip -- enough to show who wears the number."""
    tip = {"win": None}

    def show(_event):
        if tip["win"]:
            return
        win = tk.Toplevel(widget)
        win.wm_overrideredirect(True)
        x = widget.winfo_rootx()
        y = widget.winfo_rooty() + widget.winfo_height() + 2
        win.wm_geometry(f"+{x}+{y}")
        tk.Label(win, text=text, background="#ffffe0", relief=tk.SOLID,
                 borderwidth=1, font=("Arial", 10)).pack()
        tip["win"] = win

    def hide(_event):
        if tip["win"]:
            tip["win"].destroy()
            tip["win"] = None

    widget.bind("<Enter>", show)
    widget.bind("<Leave>", hide)
