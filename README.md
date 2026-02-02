# Local-STT
A STT python program that uses openAI Whisper to transcribe text fully locally.

## Documentation
### Setup
Download the file and a sound (built in sound coming in full release), in the main.py edit :

RECORD - Keybind to record
PASTE - Keybind to paste
ffmpeg_bin - Path to ffmpeg, this is optional, but the code didnt work for me when i didnt have this configured

OVERLAY_SIZE - size of the indicator
OVERLAY_SHAPE - shape of the indicator, 'circle' or 'rounded_rect'
OVERLAY_COLOR_FROM - color the indicator starts from
OVERLAY_COLOR_TO = "#01E901"  # ending color
OVERLAY_MAX_VOLUME = 0.02  # the highest volume to map to the ending color

model -if you want english only, add .en at the end so example: "small.en" otherwise leave it as it is,
\n-The models are : tiny, base, small, medium, large, turbo
\n-the model tiny is english only, the model turbo is theoretically the fastest, though it takes up the most resources
\n-personally base works best for english, and small for any language i use
