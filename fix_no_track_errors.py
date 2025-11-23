#!/usr/bin/env python3
"""
Silence "No Track Playing" Errors
Patches hockey_music_controller.py to stop spamming error messages
"""

import os
import shutil
from datetime import datetime

def main():
    print("=" * 70)
    print("Hockey Music Controller - Silence 'No Track' Errors")
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
    if "Check if this is the \"no track playing\" error" in content:
        print("⚠️  Error silencing already installed!")
        print("   No changes needed.")
        return
    
    # Patch: Update run_applescript method
    print("📝 Updating run_applescript method...")
    
    old_code = '''    @staticmethod
    def run_applescript(script, max_retries=3, retry_delay=0.5):
        """Execute AppleScript with retry logic"""
        for attempt in range(max_retries):
            try:
                result = subprocess.run(
                    ['osascript', '-e', script],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    return result.stdout.strip(), True
                else:
                    error_msg = result.stderr.strip()
                    print(f"⚠️  AppleScript error (attempt {attempt + 1}/{max_retries}): {error_msg}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
            except subprocess.TimeoutExpired:
                print(f"⏱️  AppleScript timeout (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
            except Exception as e:
                print(f"❌ AppleScript error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
        
        print("💥 All retry attempts failed!")
        return "", False'''
    
    new_code = '''    @staticmethod
    def run_applescript(script, max_retries=3, retry_delay=0.5, silent_on_error=False):
        """Execute AppleScript with retry logic"""
        for attempt in range(max_retries):
            try:
                result = subprocess.run(
                    ['osascript', '-e', script],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    return result.stdout.strip(), True
                else:
                    error_msg = result.stderr.strip()
                    
                    # Check if this is the "no track playing" error (-1728)
                    # This is a NORMAL state, not an actual error!
                    if '(-1728)' in error_msg:
                        # Silently return on first attempt for -1728 errors
                        return "", False
                    
                    # For other errors, print messages unless silent mode
                    if not silent_on_error:
                        print(f"⚠️  AppleScript error (attempt {attempt + 1}/{max_retries}): {error_msg}")
                    
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
            except subprocess.TimeoutExpired:
                if not silent_on_error:
                    print(f"⏱️  AppleScript timeout (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
            except Exception as e:
                if not silent_on_error:
                    print(f"❌ AppleScript error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
        
        if not silent_on_error:
            print("💥 All retry attempts failed!")
        return "", False'''
    
    if old_code in content:
        content = content.replace(old_code, new_code)
        print("✅ Patched run_applescript method")
    else:
        print("⚠️  Warning: Could not find exact match for run_applescript")
        print("   Your code may have been customized")
        print("   Please apply the fix manually")
        return
    
    # Write modified file
    with open('hockey_music_controller.py', 'w') as f:
        f.write(content)
    
    print()
    print("=" * 70)
    print("✅ PATCH COMPLETE!")
    print("=" * 70)
    print()
    print("What changed:")
    print("• Added 'silent_on_error' parameter to run_applescript()")
    print("• Special handling for error -1728 (no track playing)")
    print("• Returns immediately without retries or spam")
    print()
    print("Test it:")
    print("  python3 hockey_music_controller.py")
    print()
    print("Expected: Clean status messages, no error spam!")
    print()

if __name__ == '__main__':
    main()
