# Talking Human AI

Generates AI talking human videos using:
- **Wav2Lip** — fast lip sync on an existing video
- **LivePortrait** — realistic face animation from a single image

## Folder Structure

```
talking_human_ai/
├── input/
│   ├── face.jpg       ← source face image (for LivePortrait)
│   ├── video.mp4      ← source video with face (for Wav2Lip)
│   └── audio.wav      ← speech audio
├── output/            ← generated videos saved here
├── models/            ← model weights go here
├── wav2lip/           ← Wav2Lip repo cloned here
├── liveportrait/      ← LivePortrait repo cloned here
└── main.py
```

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Clone Wav2Lip
```bash
git clone https://github.com/Rudrabha/Wav2Lip wav2lip
```

### 3. Download Wav2Lip model
Download `wav2lip.pth` from:
https://github.com/Rudrabha/Wav2Lip#getting-the-weights

Place it at: `models/wav2lip.pth`

### 4. Clone LivePortrait
```bash
git clone https://github.com/KwaiVGI/LivePortrait liveportrait
```
Follow LivePortrait's own setup instructions for its model weights.

### 5. Add your input files
- `input/video.mp4` — a video with a clear face (for Wav2Lip)
- `input/face.jpg`  — a single face photo (for LivePortrait)
- `input/audio.wav` — speech audio (16kHz mono recommended)

## Run

Edit `main.py` and set the mode:

```python
mode = "fast"   # Wav2Lip lip sync
mode = "real"   # LivePortrait face animation
```

Then run:
```bash
python main.py
```

Output saved to `output/`.
