#!/usr/bin/env python3
"""Hockey Music Controller.

The app now lives in the `hockeymusic` package; this stays as the familiar
entry point so `launch.sh`, the .app bundle, and muscle memory keep working.
"""

from hockeymusic.ui.main_window import main

if __name__ == "__main__":
    main()
