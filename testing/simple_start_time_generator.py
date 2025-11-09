#!/usr/bin/env python3
"""
Simple Start Time Generator - No API Required
Apply smart defaults to all tracks in your playlist
"""

import json
import os
import subprocess

def get_apple_music_tracks(playlist_name):
    """Get tracks from Apple Music playlist"""
    script = f'''
    tell application "Music"
        set trackList to {{}}
        repeat with t in (every track of playlist "{playlist_name}")
            set end of trackList to (name of t & " | " & artist of t)
        end repeat
        set AppleScript's text item delimiters to "|||"
        return trackList as text
    end tell
    '''
    
    result = subprocess.run(
        ['osascript', '-e', script],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode == 0 and result.stdout:
        tracks = result.stdout.strip().split('|||')
        return [t.strip() for t in tracks if t.strip()]
    return []

def smart_default_start_time(track_name, track_artist):
    """
    Apply smart default start times based on simple rules
    
    Returns start time in seconds
    """
    track_lower = track_name.lower()
    artist_lower = track_artist.lower()
    
    # Known artists/songs with long intros
    long_intro_artists = [
        'ac/dc', 'guns n\' roses', 'queen', 'led zeppelin',
        'the white stripes', 'metallica', 'iron maiden'
    ]
    
    long_intro_keywords = [
        'thunderstruck', 'welcome to the jungle', 'we will rock you',
        'seven nation army', 'enter sandman', 'crazy train'
    ]
    
    short_intro_keywords = [
        'remix', 'radio edit', 'edit', 'horn', 'charge'
    ]
    
    # Check for known long intros
    for artist in long_intro_artists:
        if artist in artist_lower:
            return 10  # Skip 10 seconds for classic rock
    
    for keyword in long_intro_keywords:
        if keyword in track_lower:
            return 12  # Skip 12 seconds for specific songs
    
    # Check for short/no intros
    for keyword in short_intro_keywords:
        if keyword in track_lower:
            return 3  # Minimal skip for remixes/edits
    
    # Default: moderate skip
    return 8

def generate_start_times_simple(playlist_name, min_skip=3, default_skip=8, max_skip=30):
    """
    Generate start times using simple rules
    
    Args:
        playlist_name: Apple Music playlist name
        min_skip: Minimum seconds to skip
        default_skip: Default skip for most tracks
        max_skip: Maximum skip time
    """
    print("🎵 Simple Start Time Generator")
    print("=" * 60)
    print(f"📋 Loading playlist: {playlist_name}")
    
    # Get tracks from Apple Music
    tracks = get_apple_music_tracks(playlist_name)
    
    if not tracks:
        print("❌ Could not load playlist. Is Music app running?")
        return {}
    
    print(f"✓ Found {len(tracks)} tracks")
    print("\n🔍 Applying smart defaults...")
    print("=" * 60)
    
    start_times = {}
    
    for i, track in enumerate(tracks, 1):
        # Parse track name and artist
        if ' | ' in track:
            name, artist = track.split(' | ', 1)
        else:
            name = track
            artist = ''
        
        # Calculate start time
        start_time = smart_default_start_time(name, artist)
        
        # Apply min/max constraints
        start_time = max(min_skip, min(start_time, max_skip))
        
        # Store it
        start_times[track] = start_time
        
        # Show progress
        if start_time > min_skip:
            print(f"[{i}/{len(tracks)}] {name} → Start at {start_time}s")
    
    print("\n" + "=" * 60)
    print(f"✓ Generated {len(start_times)} start times")
    
    return start_times

def interactive_mode():
    """Interactive mode to customize start times"""
    print("🎵 Simple Start Time Generator - No Spotify API Required!")
    print("=" * 60)
    print("\nThis script applies smart default start times based on:")
    print("  • Artist (classic rock = longer skips)")
    print("  • Song title keywords (known intros)")
    print("  • Track type (remixes = shorter skips)")
    print()
    
    # Get playlist name
    playlist_name = input("Enter Apple Music playlist name: ").strip()
    if not playlist_name:
        print("❌ Playlist name required!")
        return
    
    print("\n⚙️  Configuration:")
    print("Choose a mode:")
    print("1. Conservative (3-8 seconds) - Minimal skips")
    print("2. Moderate (5-12 seconds) - Balanced [DEFAULT]")
    print("3. Aggressive (8-20 seconds) - Skip long intros")
    print("4. Custom")
    
    mode = input("\nMode [2]: ").strip() or "2"
    
    if mode == "1":
        min_skip, default_skip, max_skip = 3, 6, 10
    elif mode == "3":
        min_skip, default_skip, max_skip = 8, 15, 25
    elif mode == "4":
        min_skip = int(input("Minimum skip [3]: ").strip() or "3")
        default_skip = int(input("Default skip [8]: ").strip() or "8")
        max_skip = int(input("Maximum skip [30]: ").strip() or "30")
    else:  # mode == "2" or default
        min_skip, default_skip, max_skip = 5, 10, 15
    
    print(f"\n📊 Using: min={min_skip}s, default={default_skip}s, max={max_skip}s")
    
    # Generate start times
    start_times = generate_start_times_simple(
        playlist_name,
        min_skip=min_skip,
        default_skip=default_skip,
        max_skip=max_skip
    )
    
    if not start_times:
        return
    
    # Preview
    print("\n📊 Preview (first 10 tracks with custom start times):")
    print("=" * 60)
    shown = 0
    for track, start_time in start_times.items():
        if start_time > min_skip:
            name = track.split(' | ')[0] if ' | ' in track else track
            minutes = start_time // 60
            seconds = start_time % 60
            print(f"{shown + 1}. {name} → {minutes}:{seconds:02d}")
            shown += 1
            if shown >= 10:
                break
    
    # Save
    print("\n" + "=" * 60)
    print("💾 Save to Hockey Music Controller config?")
    save = input("Save? [y/n]: ").strip().lower()
    
    if save == 'y' or save == 'yes':
        config_path = os.path.expanduser('~/hockey_music_config.json')
        
        # Load existing config
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            config = {}
        
        # Update start_times
        if 'start_times' not in config:
            config['start_times'] = {}
        
        config['start_times'].update(start_times)
        
        # Save
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✓ Saved {len(start_times)} start times to {config_path}")
        print("\n✨ All done! Restart Hockey Music Controller to load the new start times.")
    else:
        print("Cancelled - no changes made")

if __name__ == '__main__':
    interactive_mode()
