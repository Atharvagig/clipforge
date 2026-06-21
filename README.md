Here is an SEO-optimized repository description and README introduction designed to rank highly for searches related to AI video editors, video clipping, and automation:

***

# ClipForgeAI: Local AI Multi-Agent Video Clipper & Highlight Detector

**ClipForgeAI** is a production-grade, local AI multi-agent desktop application that automatically transforms long-form videos and YouTube URLs into viral, short-form clips (9:16) tailored for TikTok, YouTube Shorts, and Instagram Reels. Built using **PySide6**, **OpenCV**, **FFmpeg**, **faster-whisper (CUDA)**, and **Google Gemini 1.5/3.5 Flash**, it runs fully locally on consumer GPUs (optimized for 6GB VRAM cards like the RTX 3050).

---

### 🚀 Key Features & Multi-Agent Architecture
* **Highlight Detection**: Semantic timeline scanning via Gemini Flash to target funny, educational, or motivational moments with virality scores.
* **GPU-Accelerated Transcription**: Word-level timestamps using `faster-whisper` quantized models with SQLite caching.
* **Auto-Crop & Face Tracking**: Keeps the speaker centered in a 9:16 vertical view using Haar Cascade face-tracking filters.
* **High-Contrast Captions**: Synchronized, styled caption overlays (outline-stroke rendering) matching word timelines.
* **Silence Removal**: Trims speech gaps using timeline heuristics for fast-paced pacing.
* **Copywriting Engine**: Auto-generates social media hooks, SEO descriptions, titles, and hashtags.
* **Posting Scheduler**: Background publishing queue supporting rate limits and official social media APIs.
* **Advisor Analytics**: Aggregates metric cards (views, likes, retention) and yields growth strategies.

---

### 🛠️ Tech Stack & Keywords
* **Core**: Python 3.12, PySide6 (GUI)
* **ML/AI**: faster-whisper, PyTorch (CUDA), Google Gemini API
* **Video/Audio**: OpenCV, FFmpeg, yt-dlp
* **Database**: SQLite3 (thread-safe connection pool)
* **Keywords**: *AI video editor, video clipper, highlight detector, auto crop, face tracking, automated captions, vertical shorts generator, youtube upload api, tiktok poster, creator tools.*
