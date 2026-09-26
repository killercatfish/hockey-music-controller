"""Small shared UI helpers."""

import tkinter as tk
from tkinter import ttk


def center(window):
    """Centre a window on screen once its size is known."""
    window.update_idletasks()
    x = (window.winfo_screenwidth() // 2) - (window.winfo_width() // 2)
    y = (window.winfo_screenheight() // 2) - (window.winfo_height() // 2)
    window.geometry(f"+{max(0, x)}+{max(0, y)}")


def modal(parent, title, size=None):
    """Create a modal Toplevel owned by `parent`."""
    win = tk.Toplevel(parent)
    win.title(title)
    if size:
        win.geometry(size)
    win.transient(parent)
    win.grab_set()
    return win


def preview_box(parent, text="", width=420):
    """The sunken grey panel used to show announcement text before it plays."""
    return tk.Label(
        parent, text=text, wraplength=width, font=("Arial", 11),
        justify=tk.LEFT, bg="#f4f4f4", fg="#222222",
        padx=10, pady=10, relief=tk.SUNKEN, anchor="w",
    )


def section(parent, title):
    frame = ttk.LabelFrame(parent, text=title, padding=8)
    return frame


def is_typing(widget):
    """True when keyboard focus is in a text field.

    Guards the single-letter game shortcuts so typing a jersey number or a
    song title doesn't fire the goal horn.
    """
    if isinstance(widget, ttk.Combobox):
        # A read-only picker (pool, playlist) takes no typed text, but it keeps
        # keyboard focus after a pick -- that swallowed Space at the rink.
        try:
            return "readonly" not in str(widget.cget("state"))
        except tk.TclError:
            return True
    return isinstance(widget, (tk.Entry, ttk.Entry, tk.Text, tk.Spinbox))
