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

# The custom announcer voice needs two small Python packages. Install them the
# first time only (needs internet); the app runs fine without them.
if ! python3 -c "import hume, dotenv" >/dev/null 2>&1; then
    echo "First run: installing the announcer voice packages (one time, ~1 minute)..."
    python3 -m pip install --user --quiet --disable-pip-version-check hume python-dotenv \
        || echo "Couldn't install them (no internet?). The app still works; announcements use the Mac voice."
fi

open -a Music
sleep 2
echo "Starting Hockey Music Controller... (leave this window open while the app runs)"
python3 hockey_music_controller.py
