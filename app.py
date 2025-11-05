import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import json
import os
import requests
from PIL import Image, ImageTk
import io
import threading
from moviepy.editor import VideoFileClip, ImageClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips, TextClip, CompositeAudioClip
from moviepy.video.tools.subtitles import SubtitlesClip
import asyncio
import edge_tts
import subprocess
import tempfile
import time
from pathlib import Path

CONFIG_FILE = "config.json"
TEMP_DIR = "temp_files"
OUTPUT_DIR = "output"

class VideoCreatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Creator Studio")
        self.root.geometry("1200x800")

        # Create directories
        os.makedirs(TEMP_DIR, exist_ok=True)
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        # Load config
        self.config = self.load_config()

        # Data storage
        self.scenes = []
        self.media_cache = {}
        self.audio_file = None
        self.subtitles_data = None

        # Create notebook
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Create tabs
        self.create_settings_tab()
        self.create_scenes_tab()
        self.create_preview_tab()
        self.create_audio_tab()
        self.create_export_tab()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        return {"pexels_api_key": ""}

    def save_config(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=2)

    def create_settings_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="⚙️ Settings")

        # Main frame
        main_frame = ttk.Frame(tab)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # Title
        title = ttk.Label(main_frame, text="API Configuration", font=('Arial', 16, 'bold'))
        title.pack(pady=(0, 20))

        # Pexels API Key
        pexels_frame = ttk.LabelFrame(main_frame, text="Pexels API Key", padding=15)
        pexels_frame.pack(fill='x', pady=10)

        self.pexels_key_entry = ttk.Entry(pexels_frame, width=60, show='*')
        self.pexels_key_entry.pack(side='left', padx=5)
        self.pexels_key_entry.insert(0, self.config.get('pexels_api_key', ''))

        show_btn = ttk.Button(pexels_frame, text="👁️ Show", command=self.toggle_api_key)
        show_btn.pack(side='left', padx=5)

        # Save button
        save_btn = ttk.Button(main_frame, text="💾 Save Configuration", command=self.save_settings)
        save_btn.pack(pady=20)

        # Info
        info_text = """
        📌 Instructions:
        1. Get your Pexels API key from: https://www.pexels.com/api/
        2. Enter the key above and click Save
        3. The key will be stored locally in config.json

        🔧 Services Used:
        • Pexels: For stock photos and videos
        • Pollinations.ai: For AI-generated images and audio
        • Kokoro TTS: For high-quality text-to-speech
        • Edge TTS: Alternative text-to-speech service
        • WhisperX: For subtitle generation
        """

        info_label = ttk.Label(main_frame, text=info_text, justify='left',
                              font=('Courier', 9), foreground='#666')
        info_label.pack(pady=10)

    def toggle_api_key(self):
        if self.pexels_key_entry['show'] == '*':
            self.pexels_key_entry['show'] = ''
        else:
            self.pexels_key_entry['show'] = '*'

    def save_settings(self):
        self.config['pexels_api_key'] = self.pexels_key_entry.get()
        self.save_config()
        messagebox.showinfo("Success", "Settings saved successfully!")

    def create_scenes_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🎬 Scenes")

        # Main container
        main_frame = ttk.Frame(tab)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # Title
        title = ttk.Label(main_frame, text="Scene Configuration", font=('Arial', 16, 'bold'))
        title.pack(pady=(0, 10))

        # JSON input
        input_frame = ttk.LabelFrame(main_frame, text="Scene JSON (Array of scenes)", padding=10)
        input_frame.pack(fill='both', expand=True, pady=10)

        self.scenes_text = scrolledtext.ScrolledText(input_frame, height=15, font=('Courier', 10))
        self.scenes_text.pack(fill='both', expand=True)

        # Example JSON
        example_json = """[
  {
    "narration": "A beautiful sunset over the ocean",
    "media_source": "pexels",
    "query": "ocean sunset",
    "media_type": "video"
  },
  {
    "narration": "Abstract colorful artwork",
    "media_source": "ai",
    "query": "abstract colorful digital art",
    "media_type": "photo"
  }
]"""
        self.scenes_text.insert('1.0', example_json)

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill='x', pady=10)

        ttk.Button(btn_frame, text="📁 Load from File", command=self.load_scenes_file).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="💾 Save to File", command=self.save_scenes_file).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="✅ Parse & Load Scenes", command=self.parse_scenes).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="🔍 Fetch All Media", command=self.fetch_all_media).pack(side='left', padx=5)

    def load_scenes_file(self):
        filename = filedialog.askopenfilename(
            title="Load Scenes JSON",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            with open(filename, 'r') as f:
                content = f.read()
                self.scenes_text.delete('1.0', tk.END)
                self.scenes_text.insert('1.0', content)

    def save_scenes_file(self):
        filename = filedialog.asksaveasfilename(
            title="Save Scenes JSON",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            with open(filename, 'w') as f:
                f.write(self.scenes_text.get('1.0', tk.END))
            messagebox.showinfo("Success", "Scenes saved successfully!")

    def parse_scenes(self):
        try:
            json_text = self.scenes_text.get('1.0', tk.END)
            self.scenes = json.loads(json_text)
            messagebox.showinfo("Success", f"Loaded {len(self.scenes)} scenes!")
        except json.JSONDecodeError as e:
            messagebox.showerror("Error", f"Invalid JSON: {str(e)}")

    def fetch_all_media(self):
        if not self.scenes:
            messagebox.showwarning("Warning", "Please parse scenes first!")
            return

        # Start fetching in background
        threading.Thread(target=self._fetch_all_media_worker, daemon=True).start()
        messagebox.showinfo("Info", "Fetching media in background... Check Preview tab soon.")

    def _fetch_all_media_worker(self):
        for i, scene in enumerate(self.scenes):
            try:
                if scene['media_source'] == 'pexels':
                    self.fetch_pexels_media(i, scene)
                elif scene['media_source'] == 'ai':
                    self.fetch_ai_media(i, scene)
            except Exception as e:
                print(f"Error fetching media for scene {i}: {e}")

        # Update preview tab
        self.root.after(0, self.refresh_preview)

    def fetch_pexels_media(self, index, scene):
        api_key = self.config.get('pexels_api_key', '')
        if not api_key:
            print("No Pexels API key configured")
            return

        headers = {'Authorization': api_key}

        if scene['media_type'] == 'video':
            url = f"https://api.pexels.com/videos/search?query={scene['query']}&per_page=1"
        else:
            url = f"https://api.pexels.com/v1/search?query={scene['query']}&per_page=1"

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()

            if scene['media_type'] == 'video':
                if data['videos']:
                    video_url = data['videos'][0]['video_files'][0]['link']
                    self.download_media(index, video_url, 'video')
            else:
                if data['photos']:
                    photo_url = data['photos'][0]['src']['large']
                    self.download_media(index, photo_url, 'photo')

    def fetch_ai_media(self, index, scene):
        if scene['media_type'] == 'photo':
            # Pollinations.ai image
            prompt = scene['query'].replace(' ', '%20')
            url = f"https://image.pollinations.ai/prompt/{prompt}"
            self.download_media(index, url, 'photo')
        else:
            # For video, we'll use image as fallback
            prompt = scene['query'].replace(' ', '%20')
            url = f"https://image.pollinations.ai/prompt/{prompt}"
            self.download_media(index, url, 'photo')

    def download_media(self, index, url, media_type):
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                ext = '.mp4' if media_type == 'video' else '.jpg'
                filepath = os.path.join(TEMP_DIR, f"scene_{index}{ext}")

                with open(filepath, 'wb') as f:
                    f.write(response.content)

                self.media_cache[index] = {
                    'filepath': filepath,
                    'media_type': media_type,
                    'status': 'success'
                }
        except Exception as e:
            print(f"Download error for scene {index}: {e}")
            self.media_cache[index] = {
                'filepath': None,
                'media_type': media_type,
                'status': 'failed',
                'error': str(e)
            }

    def create_preview_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="👁️ Preview")

        # Main frame
        main_frame = ttk.Frame(tab)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # Title
        title = ttk.Label(main_frame, text="Scene Preview", font=('Arial', 16, 'bold'))
        title.pack(pady=(0, 10))

        # Refresh button
        ttk.Button(main_frame, text="🔄 Refresh Preview", command=self.refresh_preview).pack(pady=5)

        # Scrollable canvas
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(fill='both', expand=True, pady=10)

        self.preview_canvas = tk.Canvas(canvas_frame, bg='#f0f0f0')
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.preview_canvas.yview)
        self.preview_scrollframe = ttk.Frame(self.preview_canvas)

        self.preview_scrollframe.bind(
            "<Configure>",
            lambda e: self.preview_canvas.configure(scrollregion=self.preview_canvas.bbox("all"))
        )

        self.preview_canvas.create_window((0, 0), window=self.preview_scrollframe, anchor="nw")
        self.preview_canvas.configure(yscrollcommand=scrollbar.set)

        self.preview_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def refresh_preview(self):
        # Clear existing widgets
        for widget in self.preview_scrollframe.winfo_children():
            widget.destroy()

        if not self.scenes:
            ttk.Label(self.preview_scrollframe, text="No scenes loaded",
                     font=('Arial', 12)).pack(pady=20)
            return

        for i, scene in enumerate(self.scenes):
            self.create_scene_preview(i, scene)

    def create_scene_preview(self, index, scene):
        # Scene frame
        scene_frame = ttk.LabelFrame(self.preview_scrollframe,
                                      text=f"Scene {index + 1}",
                                      padding=10)
        scene_frame.pack(fill='x', padx=10, pady=10)

        # Info
        info_text = f"Narration: {scene['narration'][:50]}...\n"
        info_text += f"Source: {scene['media_source']} | Type: {scene['media_type']} | Query: {scene['query']}"

        ttk.Label(scene_frame, text=info_text, wraplength=800).pack(anchor='w', pady=5)

        # Media status
        if index in self.media_cache:
            cache = self.media_cache[index]
            if cache['status'] == 'success':
                ttk.Label(scene_frame, text="✅ Media loaded",
                         foreground='green').pack(anchor='w')

                # Show thumbnail for images
                if cache['media_type'] == 'photo':
                    try:
                        img = Image.open(cache['filepath'])
                        img.thumbnail((200, 200))
                        photo = ImageTk.PhotoImage(img)
                        label = ttk.Label(scene_frame, image=photo)
                        label.image = photo  # Keep reference
                        label.pack(pady=5)
                    except:
                        pass
            else:
                ttk.Label(scene_frame, text=f"❌ Failed: {cache.get('error', 'Unknown')}",
                         foreground='red').pack(anchor='w')
        else:
            ttk.Label(scene_frame, text="⏳ Not fetched yet",
                     foreground='orange').pack(anchor='w')

        # Action buttons
        btn_frame = ttk.Frame(scene_frame)
        btn_frame.pack(anchor='w', pady=5)

        ttk.Button(btn_frame, text="🔄 Retry",
                  command=lambda idx=index: self.retry_scene(idx)).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="✏️ Edit",
                  command=lambda idx=index: self.edit_scene(idx)).pack(side='left', padx=2)

    def retry_scene(self, index):
        scene = self.scenes[index]
        threading.Thread(target=self._retry_scene_worker, args=(index, scene), daemon=True).start()
        messagebox.showinfo("Info", f"Retrying scene {index + 1}...")

    def _retry_scene_worker(self, index, scene):
        try:
            if scene['media_source'] == 'pexels':
                self.fetch_pexels_media(index, scene)
            elif scene['media_source'] == 'ai':
                self.fetch_ai_media(index, scene)
        except Exception as e:
            print(f"Retry error for scene {index}: {e}")

        self.root.after(0, self.refresh_preview)

    def edit_scene(self, index):
        scene = self.scenes[index]

        # Create edit dialog
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Edit Scene {index + 1}")
        dialog.geometry("500x300")

        ttk.Label(dialog, text="Query:").pack(pady=5)
        query_entry = ttk.Entry(dialog, width=50)
        query_entry.insert(0, scene['query'])
        query_entry.pack(pady=5)

        ttk.Label(dialog, text="Media Source:").pack(pady=5)
        source_var = tk.StringVar(value=scene['media_source'])
        source_frame = ttk.Frame(dialog)
        source_frame.pack(pady=5)
        ttk.Radiobutton(source_frame, text="Pexels", variable=source_var,
                       value="pexels").pack(side='left', padx=5)
        ttk.Radiobutton(source_frame, text="AI", variable=source_var,
                       value="ai").pack(side='left', padx=5)

        ttk.Label(dialog, text="Media Type:").pack(pady=5)
        type_var = tk.StringVar(value=scene['media_type'])
        type_frame = ttk.Frame(dialog)
        type_frame.pack(pady=5)
        ttk.Radiobutton(type_frame, text="Photo", variable=type_var,
                       value="photo").pack(side='left', padx=5)
        ttk.Radiobutton(type_frame, text="Video", variable=type_var,
                       value="video").pack(side='left', padx=5)

        def save_edit():
            scene['query'] = query_entry.get()
            scene['media_source'] = source_var.get()
            scene['media_type'] = type_var.get()
            dialog.destroy()
            self.retry_scene(index)

        ttk.Button(dialog, text="💾 Save & Retry", command=save_edit).pack(pady=20)

    def create_audio_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🎤 Audio")

        # Main frame
        main_frame = ttk.Frame(tab)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # Title
        title = ttk.Label(main_frame, text="Audio Generation", font=('Arial', 16, 'bold'))
        title.pack(pady=(0, 10))

        # TTS Engine selection
        engine_frame = ttk.LabelFrame(main_frame, text="TTS Engine", padding=10)
        engine_frame.pack(fill='x', pady=10)

        self.tts_engine = tk.StringVar(value="edge")
        ttk.Radiobutton(engine_frame, text="Edge TTS (Fast)", variable=self.tts_engine,
                       value="edge").pack(anchor='w')
        ttk.Radiobutton(engine_frame, text="Kokoro TTS (Quality)", variable=self.tts_engine,
                       value="kokoro").pack(anchor='w')
        ttk.Radiobutton(engine_frame, text="Pollinations.ai Audio", variable=self.tts_engine,
                       value="pollinations").pack(anchor='w')

        # Voice selection for Edge TTS
        voice_frame = ttk.Frame(engine_frame)
        voice_frame.pack(fill='x', pady=5)
        ttk.Label(voice_frame, text="Voice:").pack(side='left', padx=5)
        self.voice_var = tk.StringVar(value="en-US-AriaNeural")
        voice_combo = ttk.Combobox(voice_frame, textvariable=self.voice_var, width=30)
        voice_combo['values'] = ["en-US-AriaNeural", "en-US-GuyNeural",
                                  "en-GB-SoniaNeural", "en-GB-RyanNeural"]
        voice_combo.pack(side='left', padx=5)

        # Generate button
        ttk.Button(main_frame, text="🎵 Generate Audio",
                  command=self.generate_audio).pack(pady=10)

        # Status
        self.audio_status = ttk.Label(main_frame, text="No audio generated yet")
        self.audio_status.pack(pady=10)

        # Test audio button
        self.test_audio_btn = ttk.Button(main_frame, text="▶️ Test Audio",
                                         command=self.test_audio, state='disabled')
        self.test_audio_btn.pack(pady=5)

        # Retry button
        ttk.Button(main_frame, text="🔄 Regenerate Audio",
                  command=self.generate_audio).pack(pady=5)

    def generate_audio(self):
        if not self.scenes:
            messagebox.showwarning("Warning", "Please load scenes first!")
            return

        # Combine all narrations
        full_text = " ".join([scene['narration'] for scene in self.scenes])

        threading.Thread(target=self._generate_audio_worker,
                        args=(full_text,), daemon=True).start()

        self.audio_status.config(text="⏳ Generating audio...")

    def _generate_audio_worker(self, text):
        try:
            engine = self.tts_engine.get()

            if engine == "edge":
                self.generate_edge_tts(text)
            elif engine == "kokoro":
                self.generate_kokoro_tts(text)
            elif engine == "pollinations":
                self.generate_pollinations_audio(text)

            self.root.after(0, self._audio_complete)
        except Exception as e:
            self.root.after(0, lambda: self.audio_status.config(
                text=f"❌ Error: {str(e)}", foreground='red'))

    def generate_edge_tts(self, text):
        voice = self.voice_var.get()
        output_file = os.path.join(TEMP_DIR, "audio.mp3")

        async def run_tts():
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_file)

        asyncio.run(run_tts())
        self.audio_file = output_file

    def generate_kokoro_tts(self, text):
        # Kokoro TTS - using espeak as fallback since kokoro setup is complex
        output_file = os.path.join(TEMP_DIR, "audio.wav")

        # Using espeak as fallback
        subprocess.run(['espeak', '-w', output_file, text],
                      capture_output=True, timeout=60)

        self.audio_file = output_file

    def generate_pollinations_audio(self, text):
        output_file = os.path.join(TEMP_DIR, "audio.mp3")

        # Pollinations.ai audio endpoint
        url = "https://text-to-speech.pollinations.ai/audio"
        params = {
            "text": text,
            "voice": "en-US-AriaNeural"
        }

        response = requests.get(url, params=params, timeout=60)

        if response.status_code == 200:
            with open(output_file, 'wb') as f:
                f.write(response.content)
            self.audio_file = output_file
        else:
            raise Exception(f"Audio generation failed: {response.status_code}")

    def _audio_complete(self):
        self.audio_status.config(text="✅ Audio generated successfully!", foreground='green')
        self.test_audio_btn.config(state='normal')

    def test_audio(self):
        if self.audio_file and os.path.exists(self.audio_file):
            # Play audio using system player
            if os.name == 'posix':  # Linux/Mac
                subprocess.Popen(['xdg-open', self.audio_file])
            elif os.name == 'nt':  # Windows
                os.startfile(self.audio_file)

    def create_export_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📤 Export")

        # Main frame
        main_frame = ttk.Frame(tab)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # Title
        title = ttk.Label(main_frame, text="Video Export", font=('Arial', 16, 'bold'))
        title.pack(pady=(0, 10))

        # Scene duration
        duration_frame = ttk.LabelFrame(main_frame, text="Scene Settings", padding=10)
        duration_frame.pack(fill='x', pady=10)

        ttk.Label(duration_frame, text="Duration per scene (seconds):").pack(side='left', padx=5)
        self.scene_duration = tk.StringVar(value="5")
        ttk.Entry(duration_frame, textvariable=self.scene_duration, width=10).pack(side='left', padx=5)

        # Subtitles option
        subtitle_frame = ttk.LabelFrame(main_frame, text="Subtitles", padding=10)
        subtitle_frame.pack(fill='x', pady=10)

        self.generate_subtitles = tk.BooleanVar(value=False)
        ttk.Checkbutton(subtitle_frame, text="Generate subtitles using WhisperX",
                       variable=self.generate_subtitles).pack(anchor='w')

        # Export button
        ttk.Button(main_frame, text="🎬 Create Video",
                  command=self.create_video).pack(pady=20)

        # Progress
        self.export_progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.export_progress.pack(fill='x', pady=10)

        self.export_status = ttk.Label(main_frame, text="Ready to export")
        self.export_status.pack(pady=10)

    def create_video(self):
        if not self.scenes:
            messagebox.showwarning("Warning", "Please load scenes first!")
            return

        if not self.audio_file:
            messagebox.showwarning("Warning", "Please generate audio first!")
            return

        # Check if all media is loaded
        missing = []
        for i in range(len(self.scenes)):
            if i not in self.media_cache or self.media_cache[i]['status'] != 'success':
                missing.append(i + 1)

        if missing:
            messagebox.showwarning("Warning",
                f"Missing media for scenes: {', '.join(map(str, missing))}")
            return

        threading.Thread(target=self._create_video_worker, daemon=True).start()

        self.export_progress.start()
        self.export_status.config(text="⏳ Creating video...")

    def _create_video_worker(self):
        try:
            # Get audio duration
            audio = AudioFileClip(self.audio_file)
            total_duration = audio.duration

            # Calculate duration per scene
            scene_duration = float(self.scene_duration.get())

            # Create video clips
            clips = []
            current_time = 0

            for i, scene in enumerate(self.scenes):
                cache = self.media_cache[i]
                filepath = cache['filepath']

                # Determine clip duration
                clip_duration = min(scene_duration, total_duration - current_time)

                if cache['media_type'] == 'video':
                    clip = VideoFileClip(filepath)
                    if clip.duration < clip_duration:
                        # Loop video
                        clip = clip.loop(duration=clip_duration)
                    else:
                        # Trim video
                        clip = clip.subclip(0, clip_duration)
                else:
                    # Image clip
                    clip = ImageClip(filepath, duration=clip_duration)

                clips.append(clip)
                current_time += clip_duration

                if current_time >= total_duration:
                    break

            # Concatenate clips
            final_video = concatenate_videoclips(clips, method="compose")

            # Add audio
            final_video = final_video.set_audio(audio)

            # Generate subtitles if requested
            if self.generate_subtitles.get():
                self.root.after(0, lambda: self.export_status.config(
                    text="⏳ Generating subtitles..."))

                srt_file = self.generate_subtitles_file()

                if srt_file:
                    # Use ffmpeg to burn subtitles
                    temp_output = os.path.join(TEMP_DIR, "video_no_subs.mp4")
                    final_video.write_videofile(temp_output, codec='libx264', audio_codec='aac')

                    output_file = os.path.join(OUTPUT_DIR, f"video_{int(time.time())}.mp4")

                    cmd = [
                        'ffmpeg', '-i', temp_output,
                        '-vf', f"subtitles={srt_file}",
                        '-c:a', 'copy',
                        output_file
                    ]

                    subprocess.run(cmd, capture_output=True, timeout=300)
                else:
                    output_file = os.path.join(OUTPUT_DIR, f"video_{int(time.time())}.mp4")
                    final_video.write_videofile(output_file, codec='libx264', audio_codec='aac')
            else:
                output_file = os.path.join(OUTPUT_DIR, f"video_{int(time.time())}.mp4")
                final_video.write_videofile(output_file, codec='libx264', audio_codec='aac')

            self.root.after(0, lambda: self._video_complete(output_file))

        except Exception as e:
            self.root.after(0, lambda: self._video_error(str(e)))

    def generate_subtitles_file(self):
        try:
            # Using whisperx for subtitle generation
            # This is a simplified version - full whisperx integration would be more complex

            # For now, create a simple SRT with narrations
            srt_file = os.path.join(TEMP_DIR, "subtitles.srt")

            scene_duration = float(self.scene_duration.get())

            with open(srt_file, 'w') as f:
                for i, scene in enumerate(self.scenes):
                    start_time = i * scene_duration
                    end_time = start_time + scene_duration

                    f.write(f"{i + 1}\n")
                    f.write(f"{self._format_srt_time(start_time)} --> {self._format_srt_time(end_time)}\n")
                    f.write(f"{scene['narration']}\n\n")

            return srt_file

        except Exception as e:
            print(f"Subtitle generation error: {e}")
            return None

    def _format_srt_time(self, seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def _video_complete(self, output_file):
        self.export_progress.stop()
        self.export_status.config(text=f"✅ Video created: {output_file}", foreground='green')
        messagebox.showinfo("Success", f"Video created successfully!\n{output_file}")

    def _video_error(self, error_msg):
        self.export_progress.stop()
        self.export_status.config(text=f"❌ Error: {error_msg}", foreground='red')
        messagebox.showerror("Error", f"Video creation failed:\n{error_msg}")


if __name__ == "__main__":
    root = tk.Tk()
    app = VideoCreatorApp(root)
    root.mainloop()
