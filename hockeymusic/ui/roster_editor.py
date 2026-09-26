"""Roster editor -- names, nicknames, and each player's own goal song."""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from ..roster import Player
from ..playlists import format_seconds, parse_time
from .. import paths
from .common import modal, center

COLUMNS = [
    ("number", "#", 50),
    ("name", "Name", 190),
    ("position", "Pos", 60),
    ("nickname", "PA name", 140),
    ("goal_song", "Goal song", 230),
    ("celebration_clip", "Clip", 110),
]


class RosterEditor:
    """Give every kid their own goal song and their own name on the PA."""

    def __init__(self, app):
        self.app = app
        self.win = modal(app.root, "Roster", "940x560")
        self._build()
        self._reload()
        center(self.win)

    def _build(self):
        frame = ttk.Frame(self.win, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(frame)
        header.pack(fill=tk.X)
        ttk.Label(header, text="👥 Roster", font=("Arial", 15, "bold")).pack(side=tk.LEFT)
        self.count_label = ttk.Label(header, text="", font=("Arial", 10, "italic"))
        self.count_label.pack(side=tk.LEFT, padx=10)
        ttk.Button(header, text="Open CSV…", command=self._open_csv).pack(side=tk.RIGHT)

        ttk.Label(
            frame,
            text="“PA name” overrides the announced name (a nickname the kid loves). "
                 "“Goal song” plays instead of the team goal song when they score.",
            font=("Arial", 9, "italic"), foreground="#555", wraplength=880,
        ).pack(anchor="w", pady=(4, 8))

        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        self.tree = ttk.Treeview(tree_frame, columns=[c[0] for c in COLUMNS],
                                 show="headings", selectmode="browse")
        for key, title, width in COLUMNS:
            self.tree.heading(key, text=title)
            self.tree.column(key, width=width, anchor=tk.W)
        scroll = ttk.Scrollbar(tree_frame, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<Double-Button-1>", lambda e: self._edit())

        buttons = ttk.Frame(frame)
        buttons.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(buttons, text="➕ Add player", command=self._add).pack(side=tk.LEFT)
        ttk.Button(buttons, text="✏️ Edit", command=self._edit).pack(side=tk.LEFT, padx=6)
        ttk.Button(buttons, text="🗑️ Remove", command=self._remove).pack(side=tk.LEFT)
        ttk.Button(buttons, text="Close", command=self.win.destroy).pack(side=tk.RIGHT)
        tk.Button(buttons, text="💾 Save roster", command=self._save,
                  font=("Arial", 11, "bold"), bg="#2E86DE", fg="#111111"
                  ).pack(side=tk.RIGHT, padx=8)

    # -- data -------------------------------------------------------------

    @property
    def roster(self):
        return self.app.roster

    def _reload(self):
        self.tree.delete(*self.tree.get_children())
        for p in self.roster.sorted_players():
            self.tree.insert("", tk.END, iid=p.number, values=(
                p.number, p.name, p.position, p.nickname,
                self._song_cell(p), p.celebration_clip,
            ))
        self.count_label.config(text=f"{len(self.roster)} players")

    @staticmethod
    def _song_cell(player):
        if not player.goal_song:
            return ""
        if player.goal_song_start:
            return f"{player.goal_song}  @{format_seconds(player.goal_song_start)}"
        return player.goal_song

    def _selected(self):
        sel = self.tree.selection()
        return self.roster.get(sel[0]) if sel else None

    # -- actions ----------------------------------------------------------

    def _open_csv(self):
        path = filedialog.askopenfilename(
            parent=self.win, title="Open roster CSV",
            initialdir=str(paths.ROSTER_DIR), filetypes=[("CSV", "*.csv")])
        if path:
            self.app.load_roster(path)
            self._reload()

    def _add(self):
        PlayerForm(self, None)

    def _edit(self):
        player = self._selected()
        if player:
            PlayerForm(self, player)
        else:
            messagebox.showinfo("No selection", "Pick a player first.", parent=self.win)

    def _remove(self):
        player = self._selected()
        if not player:
            return
        if messagebox.askyesno("Remove player",
                               f"Remove #{player.number} {player.name}?",
                               parent=self.win):
            self.roster.players.pop(player.number, None)
            self._reload()

    def _save(self):
        if self.roster.save():
            self.app.config.set("roster_file", str(self.roster.source))
            self.app.config.save()
            self.app.refresh_after_roster_change()
            messagebox.showinfo("Saved", f"Saved {len(self.roster)} players.",
                                parent=self.win)
        else:
            messagebox.showerror("Save failed", "Could not write the roster file.",
                                 parent=self.win)


class PlayerForm:
    """Add or edit one player."""

    def __init__(self, editor, player):
        self.editor = editor
        self.original = player
        self.win = modal(editor.win, "Player", "520x400")

        self.fields = {
            "number": tk.StringVar(value=player.number if player else ""),
            "name": tk.StringVar(value=player.name if player else ""),
            "position": tk.StringVar(value=player.position if player else ""),
            "nickname": tk.StringVar(value=player.nickname if player else ""),
            "goal_song": tk.StringVar(value=player.goal_song if player else ""),
            "goal_song_start": tk.StringVar(
                value=format_seconds(player.goal_song_start) if player else "0:00"),
            "celebration_clip": tk.StringVar(
                value=player.celebration_clip if player else ""),
        }
        self._build()
        center(self.win)

    def _build(self):
        frame = ttk.Frame(self.win, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        rows = [
            ("Jersey number", "number", 10),
            ("Full name", "name", 34),
            ("Position (C/LW/RW/D/G)", "position", 10),
            ("PA name (optional)", "nickname", 34),
            ("Goal song (exact Apple Music title)", "goal_song", 34),
            ("Start song at (MM:SS)", "goal_song_start", 10),
            ("Celebration clip (file in sound_clips/)", "celebration_clip", 34),
        ]
        for row, (label, key, width) in enumerate(rows):
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky=tk.W, pady=6)
            entry = ttk.Entry(frame, textvariable=self.fields[key], width=width)
            entry.grid(row=row, column=1, sticky=tk.W, padx=8, pady=6)
            if row == 0:
                entry.focus_set()
        frame.columnconfigure(1, weight=1)

        clips = sorted(p.name for p in paths.SOUND_DIR.glob("*")
                       if p.suffix.lower() in {".m4a", ".mp3", ".wav", ".aiff"})
        ttk.Label(frame, text=f"Available clips: {', '.join(clips) or 'none yet'}",
                  font=("Arial", 9, "italic"), foreground="#555", wraplength=460
                  ).grid(row=len(rows), column=0, columnspan=2, sticky=tk.W, pady=(4, 10))

        buttons = ttk.Frame(frame)
        buttons.grid(row=len(rows) + 1, column=0, columnspan=2, sticky=tk.EW)
        tk.Button(buttons, text="Save", command=self._save, font=("Arial", 11, "bold"),
                  bg="#2E86DE", fg="#111111").pack(side=tk.RIGHT)
        ttk.Button(buttons, text="Cancel",
                   command=self.win.destroy).pack(side=tk.RIGHT, padx=8)

    def _save(self):
        number = self.fields["number"].get().strip().lstrip("#")
        name = self.fields["name"].get().strip()
        if not number or not name:
            messagebox.showwarning("Missing", "Number and name are required.",
                                   parent=self.win)
            return
        try:
            start = parse_time(self.fields["goal_song_start"].get() or "0")
        except ValueError as e:
            messagebox.showerror("Invalid time", str(e), parent=self.win)
            return

        roster = self.editor.roster
        if self.original and self.original.number != number:
            roster.players.pop(self.original.number, None)

        roster.players[number] = Player(
            number=number,
            name=name,
            position=self.fields["position"].get().strip().upper(),
            nickname=self.fields["nickname"].get().strip(),
            goal_song=self.fields["goal_song"].get().strip(),
            goal_song_start=start,
            celebration_clip=self.fields["celebration_clip"].get().strip(),
        )
        self.editor._reload()
        self.win.destroy()
