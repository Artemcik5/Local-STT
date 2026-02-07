# Local-STT
Local-STT is a python project that uses openAI Whisper to transcribe text, which can then be either pasted, or given to an LLM.<br>
Please report any issues you find, I'll be happy to help! (First check the below troubleshooting)<br>
If you find this project interesting then consider giving it a ⭐.

# Documentation
## Setup

### Operating System Compatibility
- Windows 10/11
- macOS 10.15+
- Linux

### Minimum Software Requirements
- Python 3.x+
- FFmpeg
- PortAudio (for audio I/O)
- Libraries used (requirements.txt)

## Installation

### 1. Install Dependencies

#### Windows
```powershell
# Install Python
choco install python --version 3.11

# Install FFmpeg https://ffmpeg.org
choco install ffmpeg

# Install PortAudio (If not already installed)
choco install portaudio
```

#### macOS
```bash
# Install dependencies
brew install python@3.11 ffmpeg portaudio
```

#### Linux (Ubuntu)
```bash
# Update system (if lower command fails)
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install python3.11 python3-pip ffmpeg portaudio19-dev
```

### 2. Clone Repository

```bash
git clone https://github.com/Artemcik5/Local-STT.git
cd Local-STT
```

### 3. Install Python Dependencies

```bash
# Create and activate virtual environment (If needed)
python3.11 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# Install required packages (Required, but can be done manually)
pip install -r requirements.txt
```

## Configuration

### 1. Set FFmpeg Path

```python
# In your script
ffmpeg_bin = r"C:\ffmpeg\bin"  # Windows example
os.environ['PATH'] += f";{ffmpeg_bin}"

# Or set environment variable
# export PATH=$PATH:/path/to/ffmpeg  # Linux/macOS
```

### 2. Configure Key Bindings

```python
# In your script
RECORD='f4'          # Hold to record
PASTE='f5'           # Paste last transcription
INTERRUPT='ctrl+.'   # Interrupt TTS playback
```

### 3. Set Paths

```python
# In your script
TTS_MODEL_PATH = r"C:\models\piper"  # Path to Piper model
```

## Common Issues

### 1. Missing Dependencies

```bash
cd Local-STT
pip install -r requirements.txt
```

### 2. Audio Device Not Found

```bash
# For Windows
pip install pipwin
pipwin install pyaudio
# You can use other ways to install pyaudio if this one doesnt work

# For Linux
sudo apt install portaudio19-dev
```

## Optional Setup

### 1. Adjust Audio Quality

```python
# In your script
FORMAT = pyaudio.paInt24
CHANNELS = 2
RATE = 44100
CHUNK = 2048
```

## Troubleshooting Tips

### 1. Audio Not Working
- Check microphone permissions
- Verify PortAudio installation
- Try different audio devices

### 2. Slow Performance
- Use smaller Whisper model (tiny.en)
- Reduce audio quality settings
- Smaller AI Model (Qwen 0.6b for example (worse accuracy))
- Quantization for AI model

### 3. TTS Not Working
- Ensure Piper model is properly installed
- Check model configuration file
- Verify output directory permissions

## More In-Depth Customization

### AI<br>
<br>
- Editing the Context (default below) can improve on how you want the model to behave, a sidenote that I'd add to this is always try to limit the emojis or other complex symbols it uses,
as they can make piper act weird (Example below)
<details>
            <summary>
                <span>Example scenario</span>
            </summary>
          User : Name a book<br>
          AI : **Book** ....<br>
          Piper TTS : Asterisk asterisk Book asterisk asterisk ....<br><br>
          Example 2
          User : Hi<br>
          AI : 🤗 Hello! ...<br>
          Piper TTS : Happy Face emoji Hello!...
</details>
<details>
            <summary>
                <span>Default system prompt/context</span>
            </summary>
            Context = "ALWAYS REFFER TO THIS AS THE CONTEXT FOR THE MESSAGE : You are a helpful assistant that provides concise answers to user questions. If you don't know the answer, say you don't know. Always be concise and to the point. Never give long answers unless very explicitly told. NEVER USE HTML OR ANY OTHER KIND LIKE * OR ** FOR ITALIC OR BOLD TEXT!!! Never give formatting like **bold text** and never use emojis or other complex characters other than letters and basic ones (like . ? ! and). Conversation Context: "
</details>

### Indicator

```python OVERLAY_SIZE```   diameter or width/height in pixels (number) <br>
```OVERLAY_SHAPE```  'circle' or 'rounded_rect' (string) <br>
```OVERLAY_ROUNDING``` when using rounded_rect, finally working (number) <br>
```OVERLAY_COLOR_FROM```  The color the lowest volume will be (string)<br>
```OVERLAY_COLOR_TO```  The color the highest volume will be (string)<br>
```OVERLAY_MAX_VOLUME```  The max volume for the color (setting this higher will make it so you have to be louder to reach the end color) (number)<br>
## How to Use

1. Set up key bindings in the script
2. Configure paths to your Piper model
3. Run the script:
```bash
python3 ./main.py
```

Press your configured record key to start/stop recording, and use your configured keys for other functions.
