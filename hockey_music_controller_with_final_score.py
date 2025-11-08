#!/usr/bin/env python3
"""
Hockey Stoppage Time Music Controller
Control Apple Music for hockey game stoppages with keyboard shortcuts
"""

import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
import random
import base64
import tempfile

# Try to import Hume AI SDK
try:
    from hume import HumeClient
    from hume.tts import PostedUtterance, PostedUtteranceVoiceWithName
    from dotenv import load_dotenv
    load_dotenv()
    HUME_AVAILABLE = True
    HUME_API_KEY = os.getenv('HUME_API_KEY')
    # Hardcoded custom voice ID
    HUME_VOICE_ID = "Hockey Goal Announcer"
except ImportError:
    HUME_AVAILABLE = False
    HUME_API_KEY = None
    HUME_VOICE_ID = None

class AppleMusicController:
    """Interface to control Apple Music via AppleScript"""
    
    @staticmethod
    def run_applescript(script):
        """Execute AppleScript and return output"""
        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip(), result.returncode == 0
        except Exception as e:
            print(f"AppleScript error: {e}")
            return "", False
    
    def get_playlists(self):
        """Get list of all playlists"""
        script = '''
        tell application "Music"
            get name of every playlist
        end tell
        '''
        output, success = self.run_applescript(script)
        if success and output:
            return [p.strip() for p in output.split(',')]
        return []
    
    def get_playlist_tracks(self, playlist_name):
        """Get tracks from a specific playlist"""
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
        output, success = self.run_applescript(script)
        if success and output:
            tracks = output.split('|||')
            return [t.strip() for t in tracks if t.strip()]
        return []
    
    def play_track_from_playlist(self, playlist_name, track_index):
        """Play a specific track by index from playlist (1-indexed)"""
        script = f'''
        tell application "Music"
            play track {track_index} of playlist "{playlist_name}"
        end tell
        '''
        return self.run_applescript(script)[1]
    
    def play_track_by_name(self, track_name):
        """Play a specific track by name"""
        script = f'''
        tell application "Music"
            play track "{track_name}"
        end tell
        '''
        return self.run_applescript(script)[1]
    
    def play_pause(self):
        """Toggle play/pause"""
        script = 'tell application "Music" to playpause'
        return self.run_applescript(script)[1]
    
    def next_track(self):
        """Skip to next track"""
        script = 'tell application "Music" to next track'
        return self.run_applescript(script)[1]
    
    def previous_track(self):
        """Go to previous track"""
        script = 'tell application "Music" to previous track'
        return self.run_applescript(script)[1]
    
    def stop(self):
        """Stop playback"""
        script = 'tell application "Music" to stop'
        return self.run_applescript(script)[1]
    
    def get_current_track(self):
        """Get currently playing track info"""
        script = '''
        tell application "Music"
            if player state is not stopped then
                return name of current track & " - " & artist of current track
            else
                return "No track playing"
            end if
        end tell
        '''
        output, success = self.run_applescript(script)
        return output if success else "Unknown"
    
    def get_current_track_name_only(self):
        """Get just the name of the currently playing track"""
        script = '''
        tell application "Music"
            if player state is not stopped then
                return name of current track
            else
                return ""
            end if
        end tell
        '''
        output, success = self.run_applescript(script)
        return output if success else ""
    
    def is_playing(self):
        """Check if music is currently playing"""
        script = '''
        tell application "Music"
            if player state is playing then
                return "playing"
            else
                return "not playing"
            end if
        end tell
        '''
        output, success = self.run_applescript(script)
        return output == "playing" if success else False
    
    def pause(self):
        """Pause playback"""
        script = 'tell application "Music" to pause'
        return self.run_applescript(script)[1]
    
    def get_track_id_from_playlist(self, playlist_name, track_index):
        """Get the database ID of a track in a playlist"""
        script = f'''
        tell application "Music"
            return database ID of track {track_index} of playlist "{playlist_name}"
        end tell
        '''
        output, success = self.run_applescript(script)
        return output if success else None
    
    def set_current_track_by_id(self, track_id):
        """Set current track by database ID without playing"""
        script = f'''
        tell application "Music"
            set player position to 0
            set current track to (some track whose database ID is {track_id})
        end tell
        '''
        return self.run_applescript(script)[1]
    
    def set_playlist_as_source(self, playlist_name):
        """Set a playlist as the current playback source"""
        script = f'''
        tell application "Music"
            set view of front window to playlist "{playlist_name}"
        end tell
        '''
        return self.run_applescript(script)[1]
    
    @staticmethod
    def generate_goal_announcement(team, scorer, assist1=None, assist2=None, voice="Alex", use_hume=True):
        """Generate and play goal announcement using Hume.ai or macOS text-to-speech"""
        # Build announcement text
        if team.lower() == "home":
            announcement = f"Patriots goal! Scored by number {scorer}"
        else:
            announcement = f"Goal scored by number {scorer}"
        
        # Add assists
        assists = [a for a in [assist1, assist2] if a and a.strip()]
        if len(assists) == 2:
            announcement += f", assisted by {assists[0]} and {assists[1]}"
        elif len(assists) == 1:
            announcement += f", assisted by {assists[0]}"
        else:
            announcement += " unassisted."
        
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



class HockeyMusicGUI:
    """Main GUI for hockey music control"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Hockey Stoppage Music Controller")
        self.root.geometry("800x600")
        
        self.controller = AppleMusicController()
        self.config_file = os.path.expanduser("~/hockey_music_config.json")
        self.config = self.load_config()
        
        self.current_playlist = tk.StringVar(value=self.config.get('playlist', ''))
        self.goal_song = tk.StringVar(value=self.config.get('goal_song', ''))
        self.zamboni_song = tk.StringVar(value=self.config.get('zamboni', ''))
        self.zamboni_2nd_song = tk.StringVar(value=self.config.get('zamboni_2nd', ''))
        self.game_start_song = tk.StringVar(value=self.config.get('game_start', ''))
        self.intermission_1st_song = tk.StringVar(value=self.config.get('intermission_1st', ''))
        self.intermission_2nd_song = tk.StringVar(value=self.config.get('intermission_2nd', ''))
        self.end_of_game_song = tk.StringVar(value=self.config.get('end_of_game', ''))
        self.power_play_song = tk.StringVar(value=self.config.get('power_play', ''))
        self.penalty_kill_song = tk.StringVar(value=self.config.get('penalty_kill', ''))
        self.playlist_tracks = []
        self.shuffled_order = []
        self.current_track_index = 0  # Track current position in shuffled playlist
        
        self.setup_ui()
        self.setup_keyboard_shortcuts()
        
        # Load playlist if configured
        if self.current_playlist.get():
            self.load_playlist()
    
    def load_config(self):
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            'goal_song': '',
            'zamboni': '',
            'zamboni_2nd': '',
            'game_start': '',
            'intermission_1st': '',
            'intermission_2nd': '',
            'end_of_game': '',
            'power_play': '',
            'penalty_kill': ''
        }
    
    def save_config(self):
        """Save configuration to file"""
        self.config['playlist'] = self.current_playlist.get()
        self.config['goal_song'] = self.goal_song.get()
        self.config['zamboni'] = self.zamboni_song.get()
        self.config['zamboni_2nd'] = self.zamboni_2nd_song.get()
        self.config['game_start'] = self.game_start_song.get()
        self.config['intermission_1st'] = self.intermission_1st_song.get()
        self.config['intermission_2nd'] = self.intermission_2nd_song.get()
        self.config['end_of_game'] = self.end_of_game_song.get()
        self.config['power_play'] = self.power_play_song.get()
        self.config['penalty_kill'] = self.penalty_kill_song.get()
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def setup_ui(self):
        """Create the user interface"""
        
        # Main control frame (top)
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(fill=tk.X)
        
        # GOAL button - Large and prominent
        self.goal_button = tk.Button(
            control_frame,
            text="⚽ GOAL! ⚽",
            command=self.play_goal_song,
            font=('Arial', 24, 'bold'),
            bg='#FFD700',
            fg='#000000',
            height=2,
            relief=tk.RAISED,
            bd=5
        )
        self.goal_button.pack(fill=tk.X, pady=(0, 10))
        
        # Special event buttons frame
        special_buttons_frame = ttk.Frame(control_frame)
        special_buttons_frame.pack(fill=tk.X, pady=(0, 10))
        
        btn_style_small = {'font': ('Arial', 10), 'height': 1, 'relief': tk.RAISED, 'bd': 3}
        
        self.zamboni_btn = tk.Button(
            special_buttons_frame,
            text="Zamboni",
            command=self.play_zamboni,
            bg='#87CEEB',
            **btn_style_small
        )
        self.zamboni_btn.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        
        self.zamboni_2nd_btn = tk.Button(
            special_buttons_frame,
            text="2nd Zamboni",
            command=self.play_zamboni_2nd,
            bg='#87CEEB',
            **btn_style_small
        )
        self.zamboni_2nd_btn.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        
        self.game_start_btn = tk.Button(
            special_buttons_frame,
            text="Game Start",
            command=self.play_game_start,
            bg='#FFD700',
            **btn_style_small
        )
        self.game_start_btn.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        
        self.intermission_1st_btn = tk.Button(
            special_buttons_frame,
            text="1st Intermission",
            command=self.play_intermission_1st,
            bg='#98FB98',
            **btn_style_small
        )
        self.intermission_1st_btn.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        
        self.intermission_2nd_btn = tk.Button(
            special_buttons_frame,
            text="2nd Intermission",
            command=self.play_intermission_2nd,
            bg='#98FB98',
            **btn_style_small
        )
        self.intermission_2nd_btn.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        
        self.end_of_game_btn = tk.Button(
            special_buttons_frame,
            text="End of Game",
            command=self.play_end_of_game,
            bg='#FFB6C1',
            **btn_style_small
        )
        self.end_of_game_btn.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        
        # Power Play and Penalty Kill buttons frame
        special_situations_frame = ttk.Frame(control_frame)
        special_situations_frame.pack(fill=tk.X, pady=(5, 10))
        
        btn_style_medium = {'font': ('Arial', 12, 'bold'), 'height': 1, 'relief': tk.RAISED, 'bd': 4}
        
        self.power_play_btn = tk.Button(
            special_situations_frame,
            text="⚡ Power Play",
            command=self.play_power_play,
            bg='#FF6B6B',
            fg='white',
            **btn_style_medium
        )
        self.power_play_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        self.penalty_kill_btn = tk.Button(
            special_situations_frame,
            text="🛡️ Penalty Kill",
            command=self.play_penalty_kill,
            bg='#4ECDC4',
            fg='white',
            **btn_style_medium
        )
        self.penalty_kill_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        # PA Announcement button frame
        pa_frame = ttk.Frame(control_frame)
        pa_frame.pack(fill=tk.X, pady=(5, 10))
        
        self.pa_announce_btn = tk.Button(
            pa_frame,
            text="📢 PA Goal Announcement",
            command=self.open_pa_announcement_window,
            font=('Arial', 12, 'bold'),
            bg='#FFA500',
            fg='white',
            height=1,
            relief=tk.RAISED,
            bd=4
        )
        self.pa_announce_btn.pack(fill=tk.X, padx=5)
        
        # Playback controls
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
        

        playback_frame = ttk.Frame(control_frame)
        playback_frame.pack(fill=tk.X, pady=5)
        
        btn_style = {'font': ('Arial', 14), 'width': 12}
        
        self.play_pause_btn = tk.Button(
            playback_frame,
            text="⏯ Play/Pause",
            command=self.play_pause,
            **btn_style
        )
        self.play_pause_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = tk.Button(
            playback_frame,
            text="⏹ Stop",
            command=self.stop,
            **btn_style
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.next_btn = tk.Button(
            playback_frame,
            text="⏭ Next",
            command=self.next_track,
            **btn_style
        )
        self.next_btn.pack(side=tk.LEFT, padx=5)
        
        # Current track display
        self.current_track_label = ttk.Label(
            control_frame,
            text="No track playing",
            font=('Arial', 12),
            wraplength=700
        )
        self.current_track_label.pack(pady=5)
        
        # Configuration button
        config_button_frame = ttk.Frame(control_frame)
        config_button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(
            config_button_frame,
            text="⚙️ Configure Songs & Playlist",
            command=self.open_config_window
        ).pack(pady=5)
        
        # Playlist management frame
        playlist_frame = ttk.LabelFrame(self.root, text="Playlist Order (Drag to Reorder)", padding="10")
        playlist_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Playlist controls
        playlist_controls = ttk.Frame(playlist_frame)
        playlist_controls.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(playlist_controls, text="Shuffle", command=self.shuffle_playlist).pack(side=tk.LEFT, padx=5)
        ttk.Button(playlist_controls, text="Reset Order", command=self.reset_playlist_order).pack(side=tk.LEFT, padx=5)
        ttk.Button(playlist_controls, text="Play from Top", command=self.play_from_top).pack(side=tk.LEFT, padx=5)
        
        # Listbox with scrollbar
        list_frame = ttk.Frame(playlist_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.playlist_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            font=('Arial', 11),
            selectmode=tk.SINGLE
        )
        self.playlist_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.playlist_listbox.yview)
        
        # Double-click to play
        self.playlist_listbox.bind('<Double-Button-1>', self.play_selected_track)
        
        # Keyboard navigation
        self.playlist_listbox.bind('<Up>', self.on_arrow_up)
        self.playlist_listbox.bind('<Down>', self.on_arrow_down)
        self.playlist_listbox.bind('<Return>', self.on_enter_key)
        self.playlist_listbox.bind('<space>', self.on_listbox_space)
        
        # Drag and drop for reordering
        self.playlist_listbox.bind('<Button-1>', self.on_drag_start)
        self.playlist_listbox.bind('<B1-Motion>', self.on_drag_motion)
        
        # Keyboard shortcuts info
        info_frame = ttk.Frame(self.root)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        shortcuts_text = "Keyboard: SPACE=Play/Pause | G=Goal | N=Next | S=Stop | O=Power Play | P=Penalty Kill"
        ttk.Label(info_frame, text=shortcuts_text, font=('Arial', 9, 'italic')).pack()
        
        # Start updating current track display now that all UI elements exist
        self.update_current_track()
    
    def open_pa_announcement_window(self):
        """Open PA announcement configuration window"""
        pa_window = tk.Toplevel(self.root)
        pa_window.title("PA Goal Announcement")
        pa_window.geometry("450x450")
        pa_window.transient(self.root)
        pa_window.grab_set()
        
        # Main frame with scrollbar support
        main_frame = ttk.Frame(pa_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title with Hume status
        if HUME_AVAILABLE and HUME_API_KEY:
            title_text = "📢 Goal Announcement (Hume.ai Enabled)"
            title_color = 'green'
        else:
            title_text = "📢 Goal Announcement (macOS Voices)"
            title_color = 'orange'
        
        title_label = ttk.Label(
            main_frame,
            text=title_text,
            font=('Arial', 14, 'bold'),
            foreground=title_color
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 15))
        
        # Team selection
        ttk.Label(main_frame, text="Team:", font=('Arial', 11, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=5)
        
        team_var = tk.StringVar(value="home")
        team_frame = ttk.Frame(main_frame)
        team_frame.grid(row=1, column=1, columnspan=2, sticky=tk.W, pady=5)
        home_radio = ttk.Radiobutton(team_frame, text="Home (Patriots)", variable=team_var, value="home")
        home_radio.pack(side=tk.LEFT, padx=5)
        away_radio = ttk.Radiobutton(team_frame, text="Away", variable=team_var, value="away")
        away_radio.pack(side=tk.LEFT, padx=5)
        
        # Scorer input
        ttk.Label(main_frame, text="Goal Scored By #:", font=('Arial', 11)).grid(row=2, column=0, sticky=tk.W, pady=10)
        scorer_entry = ttk.Entry(main_frame, width=15, font=('Arial', 12))
        scorer_entry.grid(row=2, column=1, sticky=tk.W, pady=10)
        scorer_entry.focus()
        
        # Assist 1 input
        ttk.Label(main_frame, text="Assisted By #:", font=('Arial', 11)).grid(row=3, column=0, sticky=tk.W, pady=10)
        assist1_entry = ttk.Entry(main_frame, width=15, font=('Arial', 12))
        assist1_entry.grid(row=3, column=1, sticky=tk.W, pady=10)
        ttk.Label(main_frame, text="(optional)", font=('Arial', 9, 'italic')).grid(row=3, column=2, sticky=tk.W, padx=5)
        
        # Assist 2 input
        ttk.Label(main_frame, text="2nd Assist #:", font=('Arial', 11)).grid(row=4, column=0, sticky=tk.W, pady=10)
        assist2_entry = ttk.Entry(main_frame, width=15, font=('Arial', 12))
        assist2_entry.grid(row=4, column=1, sticky=tk.W, pady=10)
        ttk.Label(main_frame, text="(optional)", font=('Arial', 9, 'italic')).grid(row=4, column=2, sticky=tk.W, padx=5)
        
        # Voice selection (only show if not using Hume)
        if not (HUME_AVAILABLE and HUME_API_KEY):
            ttk.Label(main_frame, text="Voice:", font=('Arial', 11)).grid(row=5, column=0, sticky=tk.W, pady=10)
            voice_var = tk.StringVar(value="Alex")
            voice_combo = ttk.Combobox(main_frame, textvariable=voice_var, width=20, state='readonly')
            # Premium voices (some may need to be downloaded in System Preferences)
            voice_combo['values'] = (
                'Alex',           # US Male - Clear
                'Daniel',         # UK Male - Deep
                'Samantha',       # US Female
                'Karen',          # Australian Female
                'Moira',          # Irish Female
                'Tessa',          # South African Female
                'Rishi',          # Indian Male
                'Veena'           # Indian Female
            )
            voice_combo.grid(row=5, column=1, sticky=tk.W, pady=10)
            ttk.Label(main_frame, text="(Alex recommended)", font=('Arial', 9, 'italic')).grid(row=5, column=2, sticky=tk.W, padx=5)
            
            # Voice download hint
            voice_hint = ttk.Label(
                main_frame, 
                text="💡 Tip: Download 'Enhanced' voices in System Settings → Accessibility → Spoken Content",
                font=('Arial', 8),
                foreground='blue',
                wraplength=380
            )
            voice_hint.grid(row=5, column=0, columnspan=3, sticky=tk.W, pady=(35, 0))
            preview_row = 6
        else:
            # Show Hume.ai info
            voice_var = tk.StringVar(value="Hume")
            hume_info = ttk.Label(
                main_frame,
                text="✅ Using Hume.ai professional voice" + (f"\n(Voice ID: {HUME_VOICE_ID[:20]}...)" if HUME_VOICE_ID else "\n(Auto-selected voice)"),
                font=('Arial', 10),
                foreground='green'
            )
            hume_info.grid(row=5, column=0, columnspan=3, pady=10)
            preview_row = 6
        
        # Preview section
        ttk.Label(main_frame, text="Preview:", font=('Arial', 11, 'bold')).grid(row=preview_row, column=0, columnspan=3, sticky=tk.W, pady=(15, 5))
        
        preview_label = tk.Label(
            main_frame, 
            text="Enter scorer number to preview", 
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
            team = team_var.get()
            scorer = scorer_entry.get().strip()
            assist1 = assist1_entry.get().strip()
            assist2 = assist2_entry.get().strip()
            
            if not scorer:
                preview_label.config(text="Enter scorer number to preview")
                return
            
            if team == "home":
                text = f"Patriots goal scored by number {scorer}!"
                # Add assists with exclamation marks for Patriots
                assists = [a for a in [assist1, assist2] if a]
                if len(assists) == 2:
                    text += f" assisted by number {assists[0]} and number {assists[1]}!"
                elif len(assists) == 1:
                    text += f" assisted by number {assists[0]}!"
                else:
                    text += " unassisted!"
            else:
                text = f"goal scored by number {scorer}"
                # Add assists without exclamation marks for visitors
                assists = [a for a in [assist1, assist2] if a]
                if len(assists) == 2:
                    text += f", assisted by number {assists[0]} and number {assists[1]}"
                elif len(assists) == 1:
                    text += f", assisted by number {assists[0]}"
                else:
                    text += ", unassisted"
            
            preview_label.config(text=text)
        
        # Update preview when inputs change
        scorer_entry.bind('<KeyRelease>', update_preview)
        assist1_entry.bind('<KeyRelease>', update_preview)
        assist2_entry.bind('<KeyRelease>', update_preview)
        team_var.trace('w', update_preview)
        
        # Announce button
        def announce():
            scorer = scorer_entry.get().strip()
            if not scorer:
                messagebox.showwarning("No Scorer", "Please enter the scorer's number!")
                return
            
            team = team_var.get()
            assist1 = assist1_entry.get().strip() or None
            assist2 = assist2_entry.get().strip() or None
            voice = voice_var.get()
            
            # Use Hume.ai if available, otherwise use macOS voice
            use_hume = HUME_AVAILABLE and HUME_API_KEY
            
            # Generate and play announcement
            announcement = self.controller.generate_goal_announcement(
                team, scorer, assist1, assist2, voice, use_hume
            )
            
            # Show what was announced
            tts_method = "Hume.ai" if use_hume else "macOS"
            self.current_track_label.config(text=f"📢 ({tts_method}) {announcement}")
            
            # Close window
            pa_window.destroy()
        
        announce_btn = tk.Button(
            main_frame,
            text="🎤 ANNOUNCE GOAL",
            command=announce,
            font=('Arial', 14, 'bold'),
            bg='#FF6B6B',
            fg='white',
            height=2
        )
        announce_btn.grid(row=preview_row+2, column=0, columnspan=3, sticky=tk.EW, pady=10)
        
        # Bind Enter key to announce
        scorer_entry.bind('<Return>', lambda e: announce())
        assist1_entry.bind('<Return>', lambda e: announce())
        assist2_entry.bind('<Return>', lambda e: announce())
        
        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
        
        # Center window
        pa_window.update_idletasks()
        x = (pa_window.winfo_screenwidth() // 2) - (pa_window.winfo_width() // 2)
        y = (pa_window.winfo_screenheight() // 2) - (pa_window.winfo_height() // 2)
        pa_window.geometry(f"+{x}+{y}")
        
        # Initial preview
        update_preview()

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
    

    def open_config_window(self):
        """Open configuration window as a popup"""
        config_window = tk.Toplevel(self.root)
        config_window.title("Configuration")
        config_window.geometry("650x550")
        config_window.transient(self.root)  # Set to be on top of main window
        config_window.grab_set()  # Make modal
        
        # Main frame with padding
        main_frame = ttk.Frame(config_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text="Configure Special Songs & Playlist",
            font=('Arial', 14, 'bold')
        )
        title_label.pack(pady=(0, 15))
        
        # Configuration frame
        config_frame = ttk.Frame(main_frame)
        config_frame.pack(fill=tk.BOTH, expand=True)
        
        # Goal song setup
        ttk.Label(config_frame, text="Goal Song:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(config_frame, textvariable=self.goal_song, width=35).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(config_frame, text="Set", command=lambda: self.set_special_song('goal_song', self.goal_song)).grid(row=0, column=2, padx=5, pady=5)
        
        # Zamboni song
        ttk.Label(config_frame, text="Zamboni:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(config_frame, textvariable=self.zamboni_song, width=35).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(config_frame, text="Set", command=lambda: self.set_special_song('zamboni', self.zamboni_song)).grid(row=1, column=2, padx=5, pady=5)
        
        # 2nd Zamboni song
        ttk.Label(config_frame, text="2nd Zamboni:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(config_frame, textvariable=self.zamboni_2nd_song, width=35).grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(config_frame, text="Set", command=lambda: self.set_special_song('zamboni_2nd', self.zamboni_2nd_song)).grid(row=2, column=2, padx=5, pady=5)
        
        # Game Start song
        ttk.Label(config_frame, text="Game Start:").grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Entry(config_frame, textvariable=self.game_start_song, width=35).grid(row=3, column=1, padx=5, pady=5)
        ttk.Button(config_frame, text="Set", command=lambda: self.set_special_song('game_start', self.game_start_song)).grid(row=3, column=2, padx=5, pady=5)
        
        # 1st Intermission song
        ttk.Label(config_frame, text="1st Intermission:").grid(row=4, column=0, sticky=tk.W, pady=5)
        ttk.Entry(config_frame, textvariable=self.intermission_1st_song, width=35).grid(row=4, column=1, padx=5, pady=5)
        ttk.Button(config_frame, text="Set", command=lambda: self.set_special_song('intermission_1st', self.intermission_1st_song)).grid(row=4, column=2, padx=5, pady=5)
        
        # 2nd Intermission song
        ttk.Label(config_frame, text="2nd Intermission:").grid(row=5, column=0, sticky=tk.W, pady=5)
        ttk.Entry(config_frame, textvariable=self.intermission_2nd_song, width=35).grid(row=5, column=1, padx=5, pady=5)
        ttk.Button(config_frame, text="Set", command=lambda: self.set_special_song('intermission_2nd', self.intermission_2nd_song)).grid(row=5, column=2, padx=5, pady=5)
        
        # End of Game song
        ttk.Label(config_frame, text="End of Game:").grid(row=6, column=0, sticky=tk.W, pady=5)
        ttk.Entry(config_frame, textvariable=self.end_of_game_song, width=35).grid(row=6, column=1, padx=5, pady=5)
        ttk.Button(config_frame, text="Set", command=lambda: self.set_special_song('end_of_game', self.end_of_game_song)).grid(row=6, column=2, padx=5, pady=5)
        
        # Separator
        ttk.Separator(config_frame, orient='horizontal').grid(row=7, column=0, columnspan=3, sticky='ew', pady=15)
        
        # Power Play song
        ttk.Label(config_frame, text="Power Play:").grid(row=8, column=0, sticky=tk.W, pady=5)
        ttk.Entry(config_frame, textvariable=self.power_play_song, width=35).grid(row=8, column=1, padx=5, pady=5)
        ttk.Button(config_frame, text="Set", command=lambda: self.set_special_song('power_play', self.power_play_song)).grid(row=8, column=2, padx=5, pady=5)
        
        # Penalty Kill song
        ttk.Label(config_frame, text="Penalty Kill:").grid(row=9, column=0, sticky=tk.W, pady=5)
        ttk.Entry(config_frame, textvariable=self.penalty_kill_song, width=35).grid(row=9, column=1, padx=5, pady=5)
        ttk.Button(config_frame, text="Set", command=lambda: self.set_special_song('penalty_kill', self.penalty_kill_song)).grid(row=9, column=2, padx=5, pady=5)
        
        # Separator
        ttk.Separator(config_frame, orient='horizontal').grid(row=10, column=0, columnspan=3, sticky='ew', pady=15)
        
        # Playlist section
        playlist_label = ttk.Label(config_frame, text="Stoppage Playlist", font=('Arial', 11, 'bold'))
        playlist_label.grid(row=11, column=0, columnspan=3, sticky=tk.W, pady=(0, 5))
        
        ttk.Label(config_frame, text="Select Playlist:").grid(row=12, column=0, sticky=tk.W, pady=5)
        self.config_playlist_combo = ttk.Combobox(config_frame, textvariable=self.current_playlist, width=32)
        self.config_playlist_combo.grid(row=12, column=1, padx=5, pady=5)
        ttk.Button(config_frame, text="Refresh", command=self.refresh_playlists_popup).grid(row=12, column=2, padx=5, pady=5)
        
        ttk.Button(
            config_frame,
            text="Load Playlist Tracks",
            command=lambda: [self.load_playlist(), config_window.destroy()]
        ).grid(row=13, column=1, pady=10)
        
        # Close button at bottom
        ttk.Button(
            main_frame,
            text="Close",
            command=config_window.destroy
        ).pack(pady=(10, 0))
        
        # Center the window
        config_window.update_idletasks()
        x = (config_window.winfo_screenwidth() // 2) - (config_window.winfo_width() // 2)
        y = (config_window.winfo_screenheight() // 2) - (config_window.winfo_height() // 2)
        config_window.geometry(f"+{x}+{y}")
    
    def refresh_playlists_popup(self):
        """Refresh playlists in the popup window"""
        playlists = self.controller.get_playlists()
        if playlists:
            self.config_playlist_combo['values'] = playlists
            messagebox.showinfo("Success", f"Loaded {len(playlists)} playlists")
        else:
            messagebox.showerror("Error", "Could not load playlists. Is Music app running?")
    
    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts"""
        self.root.bind('<space>', lambda e: self.play_pause())
        self.root.bind('<g>', lambda e: self.play_goal_song())
        self.root.bind('<G>', lambda e: self.play_goal_song())
        self.root.bind('<n>', lambda e: self.next_track())
        self.root.bind('<N>', lambda e: self.next_track())
        self.root.bind('<s>', lambda e: self.stop())
        self.root.bind('<S>', lambda e: self.stop())
        self.root.bind('<o>', lambda e: self.play_power_play())
        self.root.bind('<O>', lambda e: self.play_power_play())
        self.root.bind('<p>', lambda e: self.play_penalty_kill())
        self.root.bind('<P>', lambda e: self.play_penalty_kill())
    
    def update_current_track(self):
        """Update the current track display - but DON'T change highlight"""
        current = self.controller.get_current_track()
        self.current_track_label.config(text=f"♪ {current}")
        
        # Don't automatically change highlight - user controls it with arrows
        # Just update the display label
        
        self.root.after(1000, self.update_current_track)
    
    def play_goal_song(self):
        """Play the configured goal song"""
        goal_song = self.goal_song.get()
        if not goal_song:
            messagebox.showwarning("No Goal Song", "Please configure a goal song first!")
            return
        
        if self.controller.play_track_by_name(goal_song):
            self.current_track_label.config(text=f"🎉 GOAL! Playing: {goal_song}")
        else:
            messagebox.showerror("Error", f"Could not play goal song: {goal_song}")
    
    def play_zamboni(self):
        """Play the zamboni song"""
        song = self.zamboni_song.get()
        if not song:
            messagebox.showwarning("No Song", "Please configure Zamboni song first!")
            return
        
        if self.controller.play_track_by_name(song):
            self.current_track_label.config(text=f"🧊 Zamboni: {song}")
        else:
            messagebox.showerror("Error", f"Could not play: {song}")
    
    def play_zamboni_2nd(self):
        """Play the 2nd zamboni song"""
        song = self.zamboni_2nd_song.get()
        if not song:
            messagebox.showwarning("No Song", "Please configure 2nd Zamboni song first!")
            return
        
        if self.controller.play_track_by_name(song):
            self.current_track_label.config(text=f"🧊 2nd Zamboni: {song}")
        else:
            messagebox.showerror("Error", f"Could not play: {song}")
    
    def play_game_start(self):
        """Play the game start song"""
        song = self.game_start_song.get()
        if not song:
            messagebox.showwarning("No Song", "Please configure Game Start song first!")
            return
        
        if self.controller.play_track_by_name(song):
            self.current_track_label.config(text=f"🏒 Game Start: {song}")
        else:
            messagebox.showerror("Error", f"Could not play: {song}")
    
    def play_intermission_1st(self):
        """Play the 1st intermission song"""
        song = self.intermission_1st_song.get()
        if not song:
            messagebox.showwarning("No Song", "Please configure 1st Intermission song first!")
            return
        
        if self.controller.play_track_by_name(song):
            self.current_track_label.config(text=f"⏸️ 1st Intermission: {song}")
        else:
            messagebox.showerror("Error", f"Could not play: {song}")
    
    def play_intermission_2nd(self):
        """Play the 2nd intermission song"""
        song = self.intermission_2nd_song.get()
        if not song:
            messagebox.showwarning("No Song", "Please configure 2nd Intermission song first!")
            return
        
        if self.controller.play_track_by_name(song):
            self.current_track_label.config(text=f"⏸️ 2nd Intermission: {song}")
        else:
            messagebox.showerror("Error", f"Could not play: {song}")
    
    def play_end_of_game(self):
        """Play the end of game song"""
        song = self.end_of_game_song.get()
        if not song:
            messagebox.showwarning("No Song", "Please configure End of Game song first!")
            return
        
        if self.controller.play_track_by_name(song):
            self.current_track_label.config(text=f"🏁 End of Game: {song}")
        else:
            messagebox.showerror("Error", f"Could not play: {song}")
    
    def play_power_play(self):
        """Play the Power Play song"""
        song = self.power_play_song.get()
        if not song:
            messagebox.showwarning("No Song", "Please configure Power Play song first!")
            return
        
        if self.controller.play_track_by_name(song):
            self.current_track_label.config(text=f"⚡ Power Play: {song}")
        else:
            messagebox.showerror("Error", f"Could not play: {song}")
    
    def play_penalty_kill(self):
        """Play the Penalty Kill song"""
        song = self.penalty_kill_song.get()
        if not song:
            messagebox.showwarning("No Song", "Please configure Penalty Kill song first!")
            return
        
        if self.controller.play_track_by_name(song):
            self.current_track_label.config(text=f"🛡️ Penalty Kill: {song}")
        else:
            messagebox.showerror("Error", f"Could not play: {song}")
    
    def play_pause(self):
        """Toggle play/pause - if stopped, play current playlist track"""
        # Check current state
        is_currently_playing = self.controller.is_playing()
        
        if is_currently_playing:
            # Just pause
            self.controller.play_pause()
        else:
            # Check if we're stopped vs paused
            current_track = self.controller.get_current_track()
            
            if current_track == "No track playing" and self.shuffled_order and self.current_playlist.get():
                # Completely stopped - restart from current playlist position
                playlist_name = self.current_playlist.get()
                actual_track_idx = self.shuffled_order[self.current_track_index] + 1
                self.controller.play_track_from_playlist(playlist_name, actual_track_idx)
            else:
                # Just paused or has a track - resume
                self.controller.play_pause()
    
    def stop(self):
        """Stop playback"""
        self.controller.stop()
    
    def next_track(self):
        """Move to next track in playlist - stops music and queues next song"""
        if not self.shuffled_order or not self.current_playlist.get():
            messagebox.showwarning("No Playlist", "Please load a playlist first to use Next!")
            return
        
        # Stop playback immediately
        self.controller.stop()
        
        # Move to next track in our shuffled order
        self.current_track_index = (self.current_track_index + 1) % len(self.shuffled_order)
        
        # Manually update the highlight immediately
        self._update_playlist_highlight()
        
        # Get the next track info
        playlist_name = self.current_playlist.get()
        actual_track_idx = self.shuffled_order[self.current_track_index] + 1  # 1-indexed
        
        # Queue the track by playing and immediately stopping
        # Use a delayed call to ensure stop comes after play starts
        def queue_next_track():
            self.controller.play_track_from_playlist(playlist_name, actual_track_idx)
            # Stop it immediately - multiple times to be sure
            self.root.after(5, lambda: self.controller.stop())
            self.root.after(20, lambda: self.controller.stop())
            self.root.after(50, lambda: self.controller.stop())
        
        # Small delay before queuing to ensure stop command completed
        self.root.after(100, queue_next_track)
    
    def _advance_to_next_track(self):
        """Internal method to advance to next track without playing"""
        # Move to next track in our shuffled order
        self.current_track_index = (self.current_track_index + 1) % len(self.shuffled_order)
        
        # Set the next track without playing it
        playlist_name = self.current_playlist.get()
        actual_track_idx = self.shuffled_order[self.current_track_index] + 1  # 1-indexed
        self.controller.set_track_without_playing(playlist_name, actual_track_idx)
    
    def refresh_playlists(self):
        """Refresh the list of available playlists"""
        playlists = self.controller.get_playlists()
        if playlists:
            self.playlist_combo['values'] = playlists
            messagebox.showinfo("Success", f"Loaded {len(playlists)} playlists")
        else:
            messagebox.showerror("Error", "Could not load playlists. Is Music app running?")
    
    def set_special_song(self, song_type, song_var):
        """Open a dialog to select a special song from library"""
        labels = {
            'goal_song': 'Goal Song',
            'zamboni': 'Zamboni Song',
            'zamboni_2nd': '2nd Zamboni Song',
            'game_start': 'Game Start Song',
            'intermission_1st': '1st Intermission Song',
            'intermission_2nd': '2nd Intermission Song',
            'end_of_game': 'End of Game Song',
            'power_play': 'Power Play Song',
            'penalty_kill': 'Penalty Kill Song'
        }
        
        song_name = simpledialog.askstring(
            f"Set {labels.get(song_type, 'Song')}",
            "Enter the exact name of the song from your library:",
            parent=self.root
        )
        if song_name:
            song_var.set(song_name)
            self.save_config()
            messagebox.showinfo("Success", f"{labels.get(song_type, 'Song')} set to: {song_name}")
    
    def load_playlist(self):
        """Load tracks from selected playlist"""
        playlist_name = self.current_playlist.get()
        if not playlist_name:
            messagebox.showwarning("No Playlist", "Please select a playlist first!")
            return
        
        tracks = self.controller.get_playlist_tracks(playlist_name)
        if tracks:
            self.playlist_tracks = tracks
            self.shuffled_order = list(range(len(tracks)))
            self.update_playlist_display()
            self.save_config()
            messagebox.showinfo("Success", f"Loaded {len(tracks)} tracks")
        else:
            messagebox.showerror("Error", f"Could not load tracks from: {playlist_name}")
    
    def update_playlist_display(self):
        """Update the listbox with current track order"""
        self.playlist_listbox.delete(0, tk.END)
        for i, track_idx in enumerate(self.shuffled_order):
            track = self.playlist_tracks[track_idx]
            self.playlist_listbox.insert(tk.END, f"{i+1}. {track}")
    
    def shuffle_playlist(self):
        """Shuffle the playlist order"""
        import random
        random.shuffle(self.shuffled_order)
        self.update_playlist_display()
        
        # Reset to first song and highlight it
        self.current_track_index = 0
        self.playlist_listbox.selection_clear(0, tk.END)
        self.playlist_listbox.selection_set(0)
        self.playlist_listbox.see(0)
        self.playlist_listbox.activate(0)
    
    def reset_playlist_order(self):
        """Reset playlist to original order"""
        self.shuffled_order = list(range(len(self.playlist_tracks)))
        self.update_playlist_display()
    
    def play_from_top(self):
        """Play the first track in the current order"""
        if not self.shuffled_order or not self.current_playlist.get():
            messagebox.showwarning("No Playlist", "Please load a playlist first!")
            return
        
        playlist_name = self.current_playlist.get()
        # Reset to first track
        self.current_track_index = 0
        # Play the first track in shuffled order (convert to 1-indexed)
        first_track_idx = self.shuffled_order[0] + 1
        self.controller.play_track_from_playlist(playlist_name, first_track_idx)
    
    def play_selected_track(self, event):
        """Play the track that was double-clicked"""
        selection = self.playlist_listbox.curselection()
        if not selection or not self.current_playlist.get():
            return
        
        list_idx = selection[0]
        # Update our current position
        self.current_track_index = list_idx
        
        playlist_name = self.current_playlist.get()
        # Convert shuffled index to actual playlist index (1-indexed)
        actual_track_idx = self.shuffled_order[list_idx] + 1
        self.controller.play_track_from_playlist(playlist_name, actual_track_idx)
        
        # Keep highlight on this song
        self.playlist_listbox.selection_clear(0, tk.END)
        self.playlist_listbox.selection_set(list_idx)
    
    def _update_playlist_highlight(self):
        """Manually update the playlist highlight to current track index - only if needed"""
        # Only update if there's no current selection (user hasn't manually selected)
        current_selection = self.playlist_listbox.curselection()
        if not current_selection and self.current_track_index < self.playlist_listbox.size():
            # Clear previous selection
            self.playlist_listbox.selection_clear(0, tk.END)
            # Highlight current track
            self.playlist_listbox.selection_set(self.current_track_index)
    
    def on_arrow_up(self, event):
        """Handle up arrow key in playlist"""
        current_selection = self.playlist_listbox.curselection()
        if current_selection:
            idx = current_selection[0]
            if idx > 0:
                self.playlist_listbox.selection_clear(0, tk.END)
                self.playlist_listbox.selection_set(idx - 1)
                self.playlist_listbox.see(idx - 1)
                self.current_track_index = idx - 1
        return "break"  # Prevent default behavior
    
    def on_arrow_down(self, event):
        """Handle down arrow key in playlist"""
        current_selection = self.playlist_listbox.curselection()
        if current_selection:
            idx = current_selection[0]
            if idx < self.playlist_listbox.size() - 1:
                self.playlist_listbox.selection_clear(0, tk.END)
                self.playlist_listbox.selection_set(idx + 1)
                self.playlist_listbox.see(idx + 1)
                self.current_track_index = idx + 1
        return "break"  # Prevent default behavior
    
    def on_enter_key(self, event):
        """Handle Enter key in playlist - play selected song"""
        self.play_selected_track(event)
        return "break"
    
    def on_listbox_space(self, event):
        """Handle space key in playlist - stop current, play highlighted"""
        # Get the currently highlighted song
        selection = self.playlist_listbox.curselection()
        if not selection:
            return "break"
        
        highlighted_idx = selection[0]
        
        # Check if music is playing
        is_playing = self.controller.is_playing()
        
        if is_playing:
            # Stop the current music
            self.controller.stop()
        else:
            # Not playing - play the highlighted song
            self.current_track_index = highlighted_idx
            playlist_name = self.current_playlist.get()
            if playlist_name and self.shuffled_order:
                actual_track_idx = self.shuffled_order[highlighted_idx] + 1
                self.controller.play_track_from_playlist(playlist_name, actual_track_idx)
        
        return "break"  # Prevent default listbox behavior
    
    def on_drag_start(self, event):
        """Handle start of drag operation"""
        self.drag_start_index = self.playlist_listbox.nearest(event.y)
    
    def on_drag_motion(self, event):
        """Handle drag motion for reordering"""
        current_index = self.playlist_listbox.nearest(event.y)
        if current_index != self.drag_start_index:
            # Swap items
            item = self.shuffled_order.pop(self.drag_start_index)
            self.shuffled_order.insert(current_index, item)
            self.update_playlist_display()
            self.playlist_listbox.selection_set(current_index)
            self.drag_start_index = current_index


def main():
    """Main entry point"""
    root = tk.Tk()
    app = HockeyMusicGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
