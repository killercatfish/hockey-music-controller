#!/usr/bin/env python3
"""
Simple Roster Integration Patcher
Adds player name lookup to Hockey Music Controller
"""

import os
import shutil
from datetime import datetime

def main():
    print("=" * 70)
    print("Hockey Music Controller - Roster Integration")
    print("=" * 70)
    print()
    
    # Check if file exists
    if not os.path.exists('hockey_music_controller.py'):
        print("❌ Error: hockey_music_controller.py not found")
        print("   Make sure you're in the project directory")
        return
    
    print("✅ Found hockey_music_controller.py")
    print()
    
    # Create backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup = f"hockey_music_controller.py.backup_{timestamp}"
    shutil.copy2('hockey_music_controller.py', backup)
    print(f"✅ Backup created: {backup}")
    print()
    
    # Read file
    with open('hockey_music_controller.py', 'r') as f:
        content = f.read()
    
    # Check if already patched
    if 'def load_roster' in content:
        print("⚠️  Roster integration already installed!")
        print("   No changes needed.")
        return
    
    # Patch 1: Add csv import
    print("📝 Adding csv import...")
    content = content.replace('import socket', 'import socket\nimport csv')
    
    # Patch 2: Add load_roster method
    print("📝 Adding load_roster method...")
    roster_method = '''
    @staticmethod
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
'''
    
    # Find insertion point (after set_playlist_as_source)
    insertion = content.find('def _hume_tts_worker')
    if insertion > 0:
        content = content[:insertion] + roster_method + '\n    ' + content[insertion:]
    
    # Patch 3: Update goal announcement
    print("📝 Updating goal announcements...")
    old_code = '''        # Build announcement text
        if team.lower() == "home":
            announcement = f"Patriots goal! Scored by number {scorer}"
        else:
            announcement = f"Goal scored by number {scorer}"'''
    
    new_code = '''        # Build announcement text
        if team.lower() == "home":
            # Load roster and look up player name
            roster = AppleMusicController.load_roster()
            player_name = roster.get(str(scorer), None)
            
            if player_name:
                announcement = f"Patriots goal! Scored by number {scorer}, {player_name}"
            else:
                announcement = f"Patriots goal! Scored by number {scorer}"
        else:
            announcement = f"Goal scored by number {scorer}"'''
    
    content = content.replace(old_code, new_code)
    
    # Write modified file
    with open('hockey_music_controller.py', 'w') as f:
        f.write(content)
    
    print()
    print("=" * 70)
    print("✅ INSTALLATION COMPLETE!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Create roster directory: mkdir -p rosters")
    print("2. Create roster file: rosters/patriots_roster_2025.csv")
    print("3. Run the controller: python3 hockey_music_controller.py")
    print()
    print("Roster file format:")
    print("  5,Hugo Brown")
    print("  7,Alexander Mellen")
    print("  10,Cale Kulig")
    print()

if __name__ == '__main__':
    main()
