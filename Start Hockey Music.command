#!/bin/bash
# Double-click me in Finder to start the Hockey Music Controller.
# (If macOS says it can't be opened: right-click -> Open, just the first time.)

cd "$(dirname "$0")"

if ! /usr/bin/xcode-select -p >/dev/null 2>&1 && ! command -v python3 >/dev/null 2>&1; then
    echo "macOS needs to install its command line tools (one time, a few minutes)."
    echo "Click Install in the window that pops up, then double-click this file again."
    xcode-select --install
    exit 0
fi

if ! python3 -c "import tkinter" 2>/dev/null; then
    echo "Python is here but its window toolkit (tkinter) is missing."
    echo "Install Python from https://www.python.org/downloads/ and try again."
    open "https://www.python.org/downloads/"
    exit 1
fi

open -a Music
sleep 2
echo "Starting Hockey Music Controller... (leave this window open while the app runs)"
python3 hockey_music_controller.py
