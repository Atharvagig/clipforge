import os
import sys

# Base Directory Setup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

# App Sub-directories
DB_DIR = os.path.join(BASE_DIR, "database")
EXPORTS_DIR = os.path.join(PROJECT_ROOT, "exports")
IMPORTS_DIR = os.path.join(PROJECT_ROOT, "imports")
MODELS_DIR = os.path.join(BASE_DIR, "models")
WHISPER_CACHE_DIR = os.path.join(MODELS_DIR, "whisper_cache")

# Database Path
DB_PATH = os.path.join(DB_DIR, "clipforge.db")

# Create directories if they do not exist
for folder in [DB_DIR, EXPORTS_DIR, IMPORTS_DIR, MODELS_DIR, WHISPER_CACHE_DIR]:
    os.makedirs(folder, exist_ok=True)

# Default Settings
DEFAULT_SETTINGS = {
    "gemini_api_key": "",
    "whisper_model": "base",  # base, small, tiny
    "whisper_device": "cuda",  # cuda, cpu
    "whisper_compute_type": "float16",  # float16, int8
    "max_vram_gb": "5.0",
    "face_tracking_enabled": "True",
    "silence_removal_enabled": "True",
    "silence_threshold_db": "-35",
    "silence_min_duration_sec": "1.0",
    "caption_font": "Arial Black",
    "caption_font_size": "24",
    "caption_color": "#FFFF00",  # Yellow hook color
    "caption_stroke_color": "#000000",
    "caption_stroke_width": "3",
    "youtube_client_id": "",
    "youtube_client_secret": "",
}
