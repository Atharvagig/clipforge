# ClipForgeAI - Local AI Multi-Agent Video Clipper

ClipForgeAI is a production-grade local AI multi-agent desktop application built with PySide6. It automatically transforms long-form videos (local files or YouTube URLs) into short clips formatted for vertical 9:16 viewing (TikToks, Shorts, Reels) with OpenCV face-tracking, silence compression, and synchronized captions overlays.

---

## Key Features
- **IngestionAgent**: Paste YouTube URLs or select local files. Extracts mono audio tracks losslessly using FFmpeg.
- **TranscriptAgent**: GPU-accelerated word-level Whisper transcription with persistent SQLite caching.
- **ClipDetectionAgent**: Calls Google Gemini Flash to dynamically scan transcripts, scoring segments for engagement and virality.
- **EditingAgent**: Automated face detection using Haar Cascades, smoothing vertical centering, 9:16 aspect cropping, and outline caption overlays.
- **CaptionAgent**: Marketing copywriter drafting titles, hooks, and hashtags via Gemini.
- **SchedulerAgent**: Polls SQLite queue and publishes posts cleanly to social network endpoints using official APIs.
- **AnalyticsAgent**: Aggregates creator metrics (views, Likes, Watch time) and delivers advice using Gemini.

---

## Getting Started

### Prerequisites
1. **Python 3.10+** (Recommended: Python 3.12).
2. **FFmpeg** (Ensure `ffmpeg` is registered in your system `Path`).
3. **NVIDIA CUDA Toolkit & cuDNN** (For local GPU-accelerated transcription).

### Installation
Open terminal inside the directory and run:
```powershell
pip install PySide6 opencv-python numpy yt-dlp google-genai google-api-python-client google-auth-oauthlib faster-whisper torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### Launch
Double-click `run_app.bat` or run:
```powershell
python -m clipforge.main
```

---

## Project Structure
```
clipforge-github/
├── clipforge/
│   ├── agents/          # Multi-agent controller scripts
│   ├── ui/              # Glassmorphic PySide6 tab widgets
│   ├── database/        # SQLite migration managers
│   ├── models/          # Whisper workers and Gemini API client wrappers
│   ├── config/          # Subdirectories and settings defaults
│   ├── tests/           # Database automated unittests
│   └── main.py          # Application entry point
├── run_app.bat          # App launcher script for Windows
├── .gitignore           # Git ignore targets
└── README.md            # Project presentation
```
