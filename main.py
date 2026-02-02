# YOU NEED FFMPEG TO RUN THIS
import pyaudio
import whisper
import threading
import numpy as np
import time
import os
import tkinter as tk
from plyer import notification
from pynput import keyboard
from pynput.keyboard import Controller as KeyController, Key
from pydub import AudioSegment
from pydub.playback import play

# Add ffmpeg bin to PATH
ffmpeg_bin = r"FFMPEG PATH"
os.environ['PATH'] += f";{ffmpeg_bin}"

# Set paths for ffmpeg and ffprobe
AudioSegment.ffmpeg = os.path.join(ffmpeg_bin, "ffmpeg.exe")
AudioSegment.ffprobe = os.path.join(ffmpeg_bin, "ffprobe.exe")

# Change Keybindings as you wish
RECORD='f4'
PASTE='f5'

# Overlay settings
OVERLAY_SIZE = 100  # diameter or width/height in pixels
OVERLAY_SHAPE = 'rounded_rect'  # 'circle' or 'rounded_rect'
OVERLAY_COLOR_FROM = "#00381C"  # starting color
OVERLAY_COLOR_TO = "#01E901"  # ending color
OVERLAY_MAX_VOLUME = 0.02  # the highest volume to map to the ending color

# Load Whisper model
model = whisper.load_model("small")

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
    root.attributes("-alpha", 0.8)  # semi-transparent
    root.attributes("-transparentcolor", "black")  # make black areas transparent
    root.overrideredirect(True)  # no title bar
    root.withdraw()  # start hidden

    # Position in lower center
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

    # Play notification sound
    try:
        song = AudioSegment.from_mp3(r"YOUR FINISHED TRANSCRIPTION SOUND PATH HERE")
        play(song)
    except Exception as e:
        print(f"Error playing sound: {e}")

    # When possible send notification
    notification.notify(
        title="Whisper Transcription Complete",
        message=transcription_text,
        timeout=5
    )

def start_push_to_talk(record_key='f4', paste_key='f5'):
    global recording

    # Map string keys to Key objects
    try:
        record_key_obj = keyboard.Key[record_key.lower()]
        paste_key_obj = keyboard.Key[paste_key.lower()]
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
    
    # Start overlay thread
    threading.Thread(target=create_overlay, daemon=True).start()
    
    with keyboard.Listener(
        on_press=lambda e: on_record_press(e) if e == record_key_obj else (on_paste_press(e) if e == paste_key_obj else None),
        on_release=lambda e: on_record_release(e) if e == record_key_obj else None) as listener:

        print(f"Push-to-talk active. Hold '{record_key}' to record. Press '{paste_key}' to paste last transcription. Ctrl+C to exit.")
        while True:
            time.sleep(0.1)

if __name__ == "__main__":
  
    start_push_to_talk(record_key=RECORD, paste_key=PASTE)
