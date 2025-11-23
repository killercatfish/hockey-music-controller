#!/usr/bin/env python3
"""
Test goal announcement with roster integration
"""

import os
import csv

def load_roster(roster_file='rosters/patriots_roster_2025.csv'):
    """Load player roster from CSV file"""
    roster = {}
    roster_path = os.path.expanduser(roster_file)
    
    if not os.path.exists(roster_path):
        print(f"⚠️  Roster file not found: {roster_path}")
        return roster
    
    try:
        with open(roster_path, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2:
                    number = row[0].strip()
                    name = row[1].strip()
                    roster[number] = name
        print(f"✅ Loaded {len(roster)} players from roster")
    except Exception as e:
        print(f"❌ Error loading roster: {e}")
    
    return roster

def test_announcement(scorer, assist1=None, assist2=None):
    """Test what announcement would be generated"""
    
    print("\n" + "=" * 70)
    print(f"TESTING GOAL ANNOUNCEMENT FOR PLAYER #{scorer}")
    print("=" * 70)
    print()
    
    # Load roster
    print("Loading roster...")
    roster = load_roster()
    print()
    
    # Look up player
    print(f"Looking up player #{scorer}...")
    player_name = roster.get(str(scorer), None)
    
    if player_name:
        print(f"✅ Found: {player_name}")
    else:
        print(f"❌ NOT FOUND in roster")
    print()
    
    # Build announcement
    print("Building announcement text...")
    if player_name:
        announcement = f"Patriots GOAL!! Scored by number {scorer}, {player_name}!"
    else:
        announcement = f"Patriots GOAL!! Scored by number {scorer}!"
    
    # Add assists
    assists = [a for a in [assist1, assist2] if a and a.strip()]
    if len(assists) == 2:
        announcement += f" Assisted by {assists[0]} and {assists[1]}!"
    elif len(assists) == 1:
        announcement += f" Assisted by {assists[0]}!"
    else:
        announcement += " Unassisted!"
    
    print()
    print("📢 ANNOUNCEMENT TEXT:")
    print("   " + announcement)
    print()
    print("=" * 70)

if __name__ == '__main__':
    print("\n🏒 GOAL ANNOUNCEMENT TEST\n")
    
    # Test with player 7 (should be Alexander Mellen)
    test_announcement('7', '10', '5')
    
    # Test with player 99 (should NOT be in roster)
    test_announcement('99')
    
    # Test with player 10 (should be Cale Kulig)
    test_announcement('10')
