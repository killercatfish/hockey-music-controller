#!/usr/bin/env python3
"""
Diagnostic script to check roster integration
"""

import os
import csv

def check_roster():
    print("=" * 70)
    print("ROSTER INTEGRATION DIAGNOSTIC")
    print("=" * 70)
    print()
    
    # Check 1: Current directory
    print("1️⃣  Current Directory:")
    print(f"   {os.getcwd()}")
    print()
    
    # Check 2: Roster file path
    roster_file = 'rosters/patriots_roster_2025.csv'
    roster_path = os.path.expanduser(roster_file)
    print("2️⃣  Roster File Path:")
    print(f"   Relative: {roster_file}")
    print(f"   Expanded: {roster_path}")
    print()
    
    # Check 3: Does file exist?
    print("3️⃣  File Exists Check:")
    if os.path.exists(roster_path):
        print(f"   ✅ File exists!")
        
        # Get file size
        size = os.path.getsize(roster_path)
        print(f"   📊 File size: {size} bytes")
    else:
        print(f"   ❌ File NOT found!")
        print(f"   💡 Tried to find: {roster_path}")
        
        # Check if rosters directory exists
        roster_dir = 'rosters'
        if os.path.exists(roster_dir):
            print(f"   ℹ️  'rosters/' directory exists")
            print(f"   📁 Contents:")
            for item in os.listdir(roster_dir):
                print(f"      - {item}")
        else:
            print(f"   ❌ 'rosters/' directory doesn't exist!")
        return
    print()
    
    # Check 4: Load and parse roster
    print("4️⃣  Loading Roster:")
    roster = {}
    try:
        with open(roster_path, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2:
                    number = row[0].strip()
                    name = row[1].strip()
                    roster[number] = name
                    print(f"   ✅ #{number}: {name}")
        
        print()
        print(f"   📊 Total players loaded: {len(roster)}")
    except Exception as e:
        print(f"   ❌ Error loading roster: {e}")
        return
    print()
    
    # Check 5: Test lookups
    print("5️⃣  Test Player Lookups:")
    test_numbers = ['7', '10', '5', '99']
    for num in test_numbers:
        if num in roster:
            print(f"   ✅ Player #{num}: {roster[num]}")
        else:
            print(f"   ❌ Player #{num}: NOT FOUND")
    print()
    
    # Check 6: Show first few lines of file
    print("6️⃣  First 5 Lines of Roster File:")
    try:
        with open(roster_path, 'r') as f:
            for i, line in enumerate(f, 1):
                if i <= 5:
                    print(f"   {i}. {line.rstrip()}")
    except Exception as e:
        print(f"   ❌ Error reading file: {e}")
    print()
    
    print("=" * 70)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 70)

if __name__ == '__main__':
    check_roster()
