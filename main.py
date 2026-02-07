# YOU NEED FFMPEG TO RUN THIS!!!
import pyaudio
import whisper
import threading
import numpy as np
import time
import os
import tkinter as tk
from ollama import chat
from ollama import ChatResponse
from plyer import notification
from pynput import keyboard
from pynput.keyboard import Controller as KeyController, Key
from pydub import AudioSegment
from pydub.playback import play
import subprocess
import json
import wave
from piper import PiperVoice
import sounddevice as sd
from pathlib import Path

# Add ffmpeg bin to PATH
ffmpeg_bin = r"bin path"
os.environ['PATH'] += f";{ffmpeg_bin}"

# Set paths for ffmpeg and ffprobe
AudioSegment.ffmpeg = os.path.join(ffmpeg_bin, "ffmpeg.exe")
AudioSegment.ffprobe = os.path.join(ffmpeg_bin, "ffprobe.exe")

# Change Keybindings as you wish
RECORD='f4'
PASTE='f5'  
INTERRUPT='esc'  # Stop TTS playback

#ai stuff
PROMPT = 'f6'
TTS_MODEL_PATH = r"YOUR PIPER MODEL PATH"
Context = "ALWAYS REFFER TO THIS AS THE CONTEXT FOR THE MESSAGE : You are a helpful assistant that provides concise answers to user questions. If you don't know the answer, say you don't know. Always be concise and to the point. Never give long answers unless very explicitly told. NEVER USE HTML OR ANY OTHER KIND LIKE * OR ** FOR ITALIC OR BOLD TEXT!!! Never give formatting like **bold text** and never use emojis or other complex characters other than letters and basic ones (like . ? ! and). Conversation Context: "
Response = ""
debounce = False

# Overlay settings
OVERLAY_SIZE = 100  # diameter or width/height in pixels
OVERLAY_SHAPE = 'rounded_rect'  # 'circle' or 'rounded_rect'
OVERLAY_ROUNDING = 20 #corner radius, W.I.P if using rounded_rect
OVERLAY_COLOR_FROM = "#00381C"  # starting color 00381C for dark green
OVERLAY_COLOR_TO = "#01E901"  # ending color 01E901 for light green
OVERLAY_MAX_VOLUME = 0.02  # the highest volume to map to the ending color

# Load Whisper model
model = whisper.load_model("small") # if you want english only, add .en at the end so example: "small.en" otherwise leave it as it is,
# The models are : tiny, base, small, medium, large, turbo
# the model tiny is english only, the model turbo is theoretically the fastest, though it takes up the most resources

# Audio settings
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024

# Global variables
recording = False
audio_buffer = []
lock = threading.Lock()
last_transcription = ""  # last transcribed text
is_recording = False
current_volume = 0.0
volume_history = []
tts_playing = False
tts_interrupt = False


def play_mp3(path: str):
    song = AudioSegment.from_mp3(path)
    play(song)



def playtts(target_filename):
    # Play the wav using sounddevice
    with wave.open(target_filename, 'rb') as wf:
        sample_rate = wf.getframerate()
        n_channels = wf.getnchannels()
        n_frames = wf.getnframes()
        audio = wf.readframes(n_frames)
        # Convert byte data to numpy array
        audio_np = np.frombuffer(audio, dtype=np.int16)
        # If stereo, reshape for sounddevice
        if n_channels == 2:
            audio_np = audio_np.reshape(-1, 2)
        # sounddevice expects float32 in [-1, 1]
        audio_np = audio_np.astype(np.float32) / 32768.0
        sd.play(audio_np, sample_rate)
        sd.wait()

def display_text_window(title, text, width=600, height=400):
    """Display text in a simple tkinter window"""
    def show_window():
        root = tk.Tk()
        root.title(title)
        root.geometry(f"{width}x{height}")
        root.attributes("-topmost", True)
        
        # Create text widget with scrollbar
        frame = tk.Frame(root)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_widget = tk.Text(frame, wrap=tk.WORD, yscrollcommand=scrollbar.set, font=("Arial", 11))
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_widget.yview)
        
        text_widget.insert(tk.END, text)
        text_widget.config(state=tk.DISABLED)  # Read-only
        
        # Auto-close after 10 seconds if user doesn't interact
        root.after(10000, root.destroy)
        root.mainloop()
    
    threading.Thread(target=show_window, daemon=True).start()

def interpolate_color(color1, color2, factor):
    # Interpolate between two hex colors
    r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
    r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)
    r = int(r1 + (r2 - r1) * factor)
    g = int(g1 + (g2 - g1) * factor)
    b = int(b1 + (b2 - b1) * factor)
    return f'#{r:02x}{g:02x}{b:02x}'

def create_rounded_rect(canvas, x1, y1, x2, y2, radius, **kwargs):
    # Create a rounded rectangle using polygon with smooth corners
    kwargs['tag'] = 'shape'
    points = [
        x1 + radius, y1,  # top-left start
        x1, y1 + radius,  # top-left end
        x1, y2 - radius,  # bottom-left start
        x1 + radius, y2,  # bottom-left end
        x2 - radius, y2,  # bottom-right start
        x2, y2 - radius,  # bottom-right end
        x2, y1 + radius,  # top-right start
        x2 - radius, y1,  # top-right end
        x1 + radius, y1   # back to start
    ]
    canvas.create_polygon(points, smooth=1, **kwargs)

def create_overlay():
    root = tk.Tk()
    root.attributes("-topmost", True)
    root.attributes("-alpha", 0.8) 
    root.attributes("-transparentcolor", "black")
    root.overrideredirect(True)  # no title bar
    root.withdraw()  # start hidden


    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    size = OVERLAY_SIZE
    x = (screen_width - size) // 2
    y = screen_height - size - 100
    root.geometry(f"{size}x{size}+{x}+{y}")

    canvas = tk.Canvas(root, bg='black', highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)

    # Draw shape with white border
    if OVERLAY_SHAPE == 'circle':
        canvas.create_oval(5, 5, size-5, size-5, fill=OVERLAY_COLOR_FROM, outline='white', width=3, tag='shape')
    else:
        create_rounded_rect(canvas, 5, 5, size-5, size-5, OVERLAY_ROUNDING, fill=OVERLAY_COLOR_FROM, outline='white', width=3)

    def update_color():
        global is_recording, current_volume
        if is_recording:
            # Map volume to color
            vol = min(1.0, current_volume / OVERLAY_MAX_VOLUME)
            color = interpolate_color(OVERLAY_COLOR_FROM, OVERLAY_COLOR_TO, vol)
            canvas.itemconfig('shape', fill=color)
            if not root.winfo_viewable():
                root.deiconify()
        else:
            if root.winfo_viewable():
                root.withdraw()
        root.after(50, update_color)  # update every 50ms for responsive feedback

    update_color()
    root.mainloop()

def record_audio():
    global recording, audio_buffer
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    with lock:
        audio_buffer = []
    print("Recording started...")

    try:
        while recording:
            data = stream.read(CHUNK, exception_on_overflow=False)
            # Calculate volume
            audio_np = np.frombuffer(data, np.int16).astype(np.float32) / 32768.0
            rms = np.sqrt(np.mean(audio_np**2))
            global current_volume, volume_history
            volume_history.append(rms)
            if len(volume_history) > 5:  # smooth over 5 samples
                volume_history.pop(0)
            current_volume = sum(volume_history) / len(volume_history)
            with lock:
                audio_buffer.append(data)
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        print("Recording stopped.")

def transcribe_audio():
    global audio_buffer, last_transcription
    with lock:
        if not audio_buffer:
            print("No audio recorded")
            return
        audio_bytes = b''.join(audio_buffer)
    audio_np = np.frombuffer(audio_bytes, np.int16).astype(np.float32) / 32768.0

    print("Transcribing...")
    result = model.transcribe(audio_np, fp16=False)
    transcription_text = result["text"].strip()
    last_transcription = transcription_text
    print("Transcription:", transcription_text)
    global Context
    Context += " | " + transcription_text
    # Play notification sound
    try:
        play_mp3(r"YOUR NOTIFY SFX PATH HERE!!!")
    except Exception as e:
        print(f"Error playing sound: {e}")

    # When possible send notification
    notification.notify(
        title="Whisper Transcription Complete",
        message=transcription_text,
        timeout=5
    )

def play_tts(text):
    global tts_playing, tts_interrupt
    tts_playing = True
    amy_voice = PiperVoice.load("YOUR PATH AGAIN", config_path="YOURPATHAGAIN.json")
    first_voice_file = "piper_output.wav"
    BASE_DIR = Path(__file__).resolve().parent
    OUT_WAV = BASE_DIR / "piper_output.wav"
    with wave.open(str(OUT_WAV), "wb") as wav_file:
        amy_voice.synthesize_wav(text, wav_file)
    playtts(str(BASE_DIR / "piper_output.wav"))

def start_push_to_talk(record_key=RECORD, paste_key=PASTE, prompt_key=PROMPT):
    global recording

    # Map string keys to Key objects
    try:
        record_key_obj = keyboard.Key[record_key.lower()]
        paste_key_obj = keyboard.Key[paste_key.lower()]
        prompt_key_obj = keyboard.Key[prompt_key.lower()]
    except KeyError:
        print(f"Invalid key: {record_key} or {paste_key}")
        return

    def on_record_press(e):
        global recording, is_recording
        if not recording:
            recording = True
            is_recording = True
            threading.Thread(target=record_audio, daemon=True).start()

    def on_record_release(e):
        global recording, is_recording
        if recording:
            recording = False
            is_recording = False
            threading.Thread(target=transcribe_audio, daemon=True).start()

    def on_paste_press(e):
        # Paste with a little delay
        time.sleep(0.05)
        kbd = KeyController()
        kbd.type(last_transcription)
        print("Pasted transcription from clipboard")

    def on_prompt_press(e):
        global debounce, tts_playing, tts_interrupt
        # Prompt with a little delay
        if not debounce:
            debounce = True
            time.sleep(0.05)
            response: ChatResponse = chat(model='qwen3:1.7b', messages=[
                {
                    'role': 'user',
                    'content': last_transcription + Context,
                },
            ])
            response_text = response.message.content
            time.sleep(0.05)
            print("Context sent to AI:", Context)
            print("AI Response:", response_text)
            
            # Display response in text window
            display_text_window("AI Response", response_text)
            
            # Start TTS in a separate thread
            tts_interrupt = False
            threading.Thread(target=play_tts, args=(response_text,), daemon=True).start()

            debounce = False
    
    def on_interrupt_press(e):
        global tts_interrupt
        tts_interrupt = True
        sd.stop()
        print("Playback interrupted (interrupt key pressed)")
         

    # Map interrupt key
    try:
        interrupt_key_obj = keyboard.Key[INTERRUPT.lower()]
    except KeyError:
        print(f"Invalid interrupt key: {INTERRUPT}")
        interrupt_key_obj = None
    
    # Start overlay thread
    threading.Thread(target=create_overlay, daemon=True).start()
    
    with keyboard.Listener(
        on_press=lambda e: on_record_press(e) if e == record_key_obj else (on_paste_press(e) if e == paste_key_obj else (on_prompt_press(e) if e == prompt_key_obj else (on_interrupt_press(e) if interrupt_key_obj and e == interrupt_key_obj else None))),
        on_release=lambda e: on_record_release(e) if e == record_key_obj else None) as listener:

        print(f"Push-to-talk active. Hold '{record_key}' to record. Press '{paste_key}' to paste last transcription. Press '{prompt_key}' for AI response. Press '{INTERRUPT}' to interrupt TTS. Ctrl+C to exit.")
        while True:
            time.sleep(0.1)

if __name__ == "__main__":

    start_push_to_talk(record_key=RECORD, paste_key=PASTE, prompt_key=PROMPT)

