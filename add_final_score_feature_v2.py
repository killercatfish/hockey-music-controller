#!/usr/bin/env python3
"""
Automated Patch Script: Add Final Score Feature to Hockey Music Controller (FIXED)
Run this script to automatically add the Final Score announcement feature.

Usage:
    python3 add_final_score_feature_v2.py hockey_music_controller.py

This will create a new file: hockey_music_controller_with_final_score.py
"""

import sys
import os

def read_file(filepath):
    """Read the source file"""
    with open(filepath, 'r') as f:
        return f.read()

def find_insertion_point(content, marker):
    """Find where to insert code"""
    pos = content.find(marker)
    if pos == -1:
        return None
    return pos

def patch_file(input_file):
    """Patch the hockey music controller file with Final Score feature"""
    print(f"Reading {input_file}...")
    
    try:
        content = read_file(input_file)
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found!")
        return False
    
    # Check if already patched
    if 'generate_final_score_announcement' in content:
        print("✓ File appears to already have the Final Score feature!")
        print("  No changes needed.")
        return True
    
    print("Applying patches...")
    
    # STEP 1: Add the generate_final_score_announcement method
    # Find the end of generate_goal_announcement method
    marker1 = "        return announcement\n\n\nclass HockeyMusicGUI:"
    pos1 = content.find(marker1)
    
    if pos1 == -1:
        print("Error: Could not find insertion point for final score method!")
        return False
    
    final_score_method = '''
    @staticmethod
    def generate_final_score_announcement(home_score, visiting_team, visiting_score, voice="Alex", use_hume=True):
        """Generate and play final score announcement using Hume.ai or macOS text-to-speech"""
        # Build announcement text
        announcement = f"Final score: Patriots {home_score}, {visiting_team} {visiting_score}"
        
        # Try Hume.ai first if available and enabled
        if use_hume and HUME_AVAILABLE and HUME_API_KEY:
            try:
                client = HumeClient(api_key=HUME_API_KEY)
                
                # Use custom voice if specified, otherwise use a default Hume voice 
                if HUME_VOICE_ID:
                    # For custom voices, specify provider='CUSTOM_VOICE'
                    print(f"Attempting Hume TTS with custom voice: {HUME_VOICE_ID}")
                    utterance = PostedUtterance(
                        text=announcement,
                        voice=PostedUtteranceVoiceWithName(
                            name=HUME_VOICE_ID,
                            provider='CUSTOM_VOICE'
                        )
                    )
                else:
                    # Use Hume's default voice library
                    print("Attempting Hume TTS with default voice: Ava Song")
                    utterance = PostedUtterance(
                        text=announcement,
                        voice=PostedUtteranceVoiceWithName(
                            name='Ava Song',
                            provider='HUME_AI'
                        )
                    )
                
                # Synthesize speech
                result = client.tts.synthesize_json(utterances=[utterance])
                
                # Decode base64 audio and play it
                if result and result.generations and len(result.generations) > 0:
                    audio_base64 = result.generations[0].audio
                    audio_bytes = base64.b64decode(audio_base64)
                    
                    # Write to temporary file and play
                    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
                        temp_audio.write(audio_bytes)
                        temp_audio_path = temp_audio.name
                    
                    # Play audio using afplay (macOS)
                    subprocess.run(['afplay', temp_audio_path])
                    
                    # Clean up temp file
                    try:
                        os.unlink(temp_audio_path)
                    except:
                        pass
                    
                    print("✓ Hume TTS successful!")
                    return announcement
            except Exception as e:
                print(f"Hume.ai TTS error: {e}")
                
                # If custom voice failed, try default Ava Song as fallback
                if HUME_VOICE_ID:
                    try:
                        print("Trying fallback to Ava Song...")
                        client = HumeClient(api_key=HUME_API_KEY)
                        utterance = PostedUtterance(
                            text=announcement,
                            voice=PostedUtteranceVoiceWithName(
                                name='Ava Song',
                                provider='HUME_AI'
                            )
                        )
                        result = client.tts.synthesize_json(utterances=[utterance])
                        
                        if result and result.generations and len(result.generations) > 0:
                            audio_base64 = result.generations[0].audio
                            audio_bytes = base64.b64decode(audio_base64)
                            
                            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
                                temp_audio.write(audio_bytes)
                                temp_audio_path = temp_audio.name
                            
                            subprocess.run(['afplay', temp_audio_path])
                            
                            try:
                                os.unlink(temp_audio_path)
                            except:
                                pass
                            
                            print("✓ Fallback to Ava Song successful!")
                            return announcement
                    except Exception as e2:
                        print(f"Ava Song fallback also failed: {e2}")
                
                print("Falling back to macOS voice...")
        
        # Fallback to macOS 'say' command
        # Use a deeper voice for PA effect
        subprocess.run(['say', '-v', voice, '-r', '180', announcement])
        
        return announcement

'''
    
    content = content[:pos1] + "        return announcement\n" + final_score_method + "\n\nclass HockeyMusicGUI:" + content[pos1+len(marker1):]
    
    # STEP 2: Add the Final Score button
    marker2 = "        self.pa_announce_btn.pack(fill=tk.X, padx=5)\n        \n        # Playback controls"
    pos2 = content.find(marker2)
    
    if pos2 == -1:
        print("Error: Could not find insertion point for final score button!")
        return False
    
    final_score_button = '''
        # Final Score button frame
        final_score_frame = ttk.Frame(control_frame)
        final_score_frame.pack(fill=tk.X, pady=(5, 10))
        
        self.final_score_btn = tk.Button(
            final_score_frame,
            text="🏁 Final Score Announcement",
            command=self.open_final_score_window,
            font=('Arial', 12, 'bold'),
            bg='#9B59B6',
            fg='white',
            height=1,
            relief=tk.RAISED,
            bd=4
        )
        self.final_score_btn.pack(fill=tk.X, padx=5)
        
'''
    
    content = content[:pos2+len(marker2)] + final_score_button + content[pos2+len(marker2):]
    
    # STEP 3: Add the open_final_score_window method
    marker3 = "        # Initial preview\n        update_preview()\n    \n    def open_config_window(self):"
    pos3 = content.find(marker3)
    
    if pos3 == -1:
        print("Error: Could not find insertion point for final score window method!")
        return False
    
    # Split the method into parts to avoid f-string issues
    final_score_window_method = '''
    def open_final_score_window(self):
        """Open Final Score announcement configuration window"""
        fs_window = tk.Toplevel(self.root)
        fs_window.title("Final Score Announcement")
        fs_window.geometry("450x400")
        fs_window.transient(self.root)
        fs_window.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(fs_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title with Hume status
        if HUME_AVAILABLE and HUME_API_KEY:
            title_text = "🏁 Final Score Announcement (Hume.ai Enabled)"
            title_color = 'green'
        else:
            title_text = "🏁 Final Score Announcement (macOS Voices)"
            title_color = 'orange'
        
        title_label = ttk.Label(
            main_frame,
            text=title_text,
            font=('Arial', 14, 'bold'),
            foreground=title_color
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 15))
        
        # Patriots Score input
        ttk.Label(main_frame, text="Patriots Score:", font=('Arial', 11, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=10)
        patriots_score_entry = ttk.Entry(main_frame, width=10, font=('Arial', 12))
        patriots_score_entry.grid(row=1, column=1, sticky=tk.W, pady=10)
        patriots_score_entry.focus()
        
        # Visiting Team Name input
        ttk.Label(main_frame, text="Visiting Team:", font=('Arial', 11)).grid(row=2, column=0, sticky=tk.W, pady=10)
        visiting_team_entry = ttk.Entry(main_frame, width=20, font=('Arial', 12))
        visiting_team_entry.grid(row=2, column=1, sticky=tk.W, pady=10)
        
        # Visiting Team Score input
        ttk.Label(main_frame, text="Visiting Score:", font=('Arial', 11)).grid(row=3, column=0, sticky=tk.W, pady=10)
        visiting_score_entry = ttk.Entry(main_frame, width=10, font=('Arial', 12))
        visiting_score_entry.grid(row=3, column=1, sticky=tk.W, pady=10)
        
        # Voice selection (only show if not using Hume)
        if not (HUME_AVAILABLE and HUME_API_KEY):
            ttk.Label(main_frame, text="Voice:", font=('Arial', 11)).grid(row=4, column=0, sticky=tk.W, pady=10)
            voice_var = tk.StringVar(value="Alex")
            voice_combo = ttk.Combobox(main_frame, textvariable=voice_var, width=20, state='readonly')
            voice_combo['values'] = ('Alex', 'Daniel', 'Samantha', 'Karen', 'Moira', 'Tessa', 'Rishi', 'Veena')
            voice_combo.grid(row=4, column=1, sticky=tk.W, pady=10)
            preview_row = 5
        else:
            # Show Hume.ai info
            voice_var = tk.StringVar(value="Hume")
            voice_info_text = "✅ Using Hume.ai professional voice"
            if HUME_VOICE_ID:
                voice_info_text += f" (Voice: {HUME_VOICE_ID[:20]}...)"
            hume_info = ttk.Label(
                main_frame,
                text=voice_info_text,
                font=('Arial', 10),
                foreground='green'
            )
            hume_info.grid(row=4, column=0, columnspan=3, pady=10)
            preview_row = 5
        
        # Preview section
        ttk.Label(main_frame, text="Preview:", font=('Arial', 11, 'bold')).grid(row=preview_row, column=0, columnspan=3, sticky=tk.W, pady=(15, 5))
        
        preview_label = tk.Label(
            main_frame, 
            text="Enter scores to preview", 
            wraplength=380, 
            font=('Arial', 10),
            justify=tk.LEFT,
            bg='#f0f0f0',
            fg='#333333',
            padx=10,
            pady=10,
            relief=tk.SUNKEN
        )
        preview_label.grid(row=preview_row+1, column=0, columnspan=3, sticky=tk.EW, pady=(0, 15))
        
        def update_preview(*args):
            """Update the preview text"""
            home_score = patriots_score_entry.get().strip()
            visiting_team = visiting_team_entry.get().strip()
            visiting_score = visiting_score_entry.get().strip()
            
            if not home_score or not visiting_team or not visiting_score:
                preview_label.config(text="Enter all fields to preview")
                return
            
            text = f"Final score: Patriots {home_score}, {visiting_team} {visiting_score}"
            preview_label.config(text=text)
        
        # Update preview when inputs change
        patriots_score_entry.bind('<KeyRelease>', update_preview)
        visiting_team_entry.bind('<KeyRelease>', update_preview)
        visiting_score_entry.bind('<KeyRelease>', update_preview)
        
        # Announce button
        def announce():
            home_score = patriots_score_entry.get().strip()
            visiting_team = visiting_team_entry.get().strip()
            visiting_score = visiting_score_entry.get().strip()
            
            if not home_score or not visiting_team or not visiting_score:
                messagebox.showwarning("Incomplete", "Please enter all fields!")
                return
            
            voice = voice_var.get()
            
            # Use Hume.ai if available, otherwise use macOS voice
            use_hume = HUME_AVAILABLE and HUME_API_KEY
            
            # Generate and play announcement
            announcement = self.controller.generate_final_score_announcement(
                home_score, visiting_team, visiting_score, voice, use_hume
            )
            
            # Show what was announced
            tts_method = "Hume.ai" if use_hume else "macOS"
            self.current_track_label.config(text=f"🏁 ({tts_method}) {announcement}")
            
            # Close window
            fs_window.destroy()
        
        announce_btn = tk.Button(
            main_frame,
            text="🎤 ANNOUNCE FINAL SCORE",
            command=announce,
            font=('Arial', 14, 'bold'),
            bg='#9B59B6',
            fg='white',
            height=2
        )
        announce_btn.grid(row=preview_row+2, column=0, columnspan=3, sticky=tk.EW, pady=10)
        
        # Bind Enter key to announce
        patriots_score_entry.bind('<Return>', lambda e: announce())
        visiting_team_entry.bind('<Return>', lambda e: announce())
        visiting_score_entry.bind('<Return>', lambda e: announce())
        
        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
        
        # Center window
        fs_window.update_idletasks()
        x = (fs_window.winfo_screenwidth() // 2) - (fs_window.winfo_width() // 2)
        y = (fs_window.winfo_screenheight() // 2) - (fs_window.winfo_height() // 2)
        fs_window.geometry(f"+{x}+{y}")
        
        # Initial preview
        update_preview()
    
'''
    
    content = content[:pos3] + "        # Initial preview\n        update_preview()\n" + final_score_window_method + "\n    def open_config_window(self):" + content[pos3+len(marker3):]
    
    # Write the enhanced version
    output_file = input_file.replace('.py', '_with_final_score.py')
    if output_file == input_file:
        output_file = 'hockey_music_controller_patched.py'
    
    with open(output_file, 'w') as f:
        f.write(content)
    
    print(f"✓ Successfully created {output_file}")
    print("\nChanges made:")
    print("  1. Added generate_final_score_announcement() method")
    print("  2. Added Final Score button to UI (purple, below PA Announcement)")
    print("  3. Added open_final_score_window() method for the popup")
    print("\nYou can now run the enhanced version:")
    print(f"  python3 {output_file}")
    
    return True


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 add_final_score_feature_v2.py hockey_music_controller.py")
        print("\nThis will create a new file with the Final Score feature added.")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found!")
        sys.exit(1)
    
    success = patch_file(input_file)
    sys.exit(0 if success else 1)
