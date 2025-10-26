# Changelog

All notable changes to the Hockey Music Controller project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-10-26

### Added
- Initial release of Hockey Music Controller
- Giant GOAL button with keyboard shortcut (G)
- 6 special event buttons: Zamboni, 2nd Zamboni, Game Start, 1st Intermission, 2nd Intermission, End of Game
- Power Play button (O key)
- Penalty Kill button (P key)
- Playlist management with shuffle and drag-to-reorder
- Keyboard shortcuts for all major functions
- Arrow key navigation in playlist (⬆️⬇️)
- Space key to play/stop highlighted song
- Configuration popup window for all song settings
- Auto-save configuration to JSON file
- AppleScript integration with macOS Music app
- Current track display
- Play/Pause/Stop/Next controls
- Playlist highlighting (manual control)

### Features
- Works with Apple Music subscription
- No external dependencies (Python standard library only)
- Keyboard-first design for quick operation
- Visual playlist management
- Persistent settings between sessions

### Known Issues
- Next button (N) may produce brief audio blip when advancing tracks
- Requires Music app to be running
- Songs must be in user's library (not just catalog)

---

## Version History

### Future Enhancements (Roadmap)
- [ ] Multiple goal songs (home/away teams)
- [ ] Volume control slider
- [ ] Fade in/out effects
- [ ] Timer integration for automatic start/stop
- [ ] Recently played tracking to avoid repeats
- [ ] Game clock integration
- [ ] Import/export configuration presets
- [ ] Dark mode support
- [ ] Customizable button colors
- [ ] Playlist queue preview

---

## Contributing

When contributing, please update this CHANGELOG with your changes under an "Unreleased" section.
