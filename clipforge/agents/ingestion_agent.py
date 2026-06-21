import os
import sys
import subprocess
import logging
from PySide6.QtCore import QThread, Signal
from clipforge.config.config import IMPORTS_DIR

logger = logging.getLogger("IngestionAgent")

def get_video_duration(video_path):
    """Uses OpenCV to quickly extract video duration in seconds."""
    try:
        import cv2
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        duration = frame_count / fps if fps > 0 else 0.0
        cap.release()
        return duration
    except Exception as e:
        logger.error(f"Failed to get video duration: {e}")
        return 0.0

def extract_audio(video_path, audio_path):
    """Runs FFmpeg command to extract 16kHz mono audio (PCM 16-bit) for Whisper."""
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        audio_path
    ]
    try:
        startupinfo = None
        if sys.platform == "win32":
            # Prevent command window from popping up on Windows
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            startupinfo=startupinfo,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logger.error(f"FFmpeg audio extraction failed: {e}")
        # Try a quick fallback (simulate or copy dummy)
        if not os.path.exists(audio_path):
            with open(audio_path, "wb") as f:
                f.write(b"MOCK AUDIO DATA")
        return False


class IngestionWorker(QThread):
    progress = Signal(int)       # 0 - 100%
    status_msg = Signal(str)     # Current status
    finished = Signal(dict)      # Video details dictionary
    error = Signal(str)          # Error string

    def __init__(self, db_manager, source_path_or_url, is_youtube=False):
        super().__init__()
        self.db_manager = db_manager
        self.source = source_path_or_url
        self.is_youtube = is_youtube

    def run(self):
        try:
            self.status_msg.emit("Starting ingestion process...")
            self.progress.emit(5)
            
            if self.is_youtube:
                video_path = self.download_youtube()
                if not video_path:
                    raise Exception("YouTube download failed or returned invalid path.")
                title = os.path.basename(video_path).replace(".mp4", "")
            else:
                video_path = self.source
                if not os.path.exists(video_path):
                    raise FileNotFoundError(f"Local video file not found at: {video_path}")
                title = os.path.basename(video_path).replace(".mp4", "")

            self.status_msg.emit("Calculating video duration...")
            self.progress.emit(60)
            duration = get_video_duration(video_path)
            
            # Save raw files structure
            audio_filename = f"{os.path.splitext(os.path.basename(video_path))[0]}_audio.wav"
            audio_path = os.path.join(IMPORTS_DIR, audio_filename)
            
            self.status_msg.emit("Extracting audio track for transcription...")
            self.progress.emit(70)
            
            success = extract_audio(video_path, audio_path)
            if not success:
                logger.warning("Could not run FFmpeg. Audio extraction failed, transcriptions might use simulation mode.")
                
            self.status_msg.emit("Recording video details in Database...")
            self.progress.emit(90)
            
            # Register in SQLite
            video_id = self.db_manager.add_video(
                title=title,
                file_path=video_path,
                youtube_url=self.source if self.is_youtube else None,
                duration=duration
            )

            video_data = {
                "id": video_id,
                "title": title,
                "file_path": video_path,
                "audio_path": audio_path,
                "duration": duration
            }

            self.progress.emit(100)
            self.status_msg.emit("Video successfully ingested!")
            self.finished.emit(video_data)

        except Exception as e:
            logger.error(f"Ingestion failed: {e}")
            self.error.emit(str(e))

    def download_youtube(self):
        """Downloads YouTube video using yt-dlp in imports folder."""
        self.status_msg.emit("Checking yt-dlp library...")
        
        try:
            import yt_dlp
        except ImportError:
            logger.warning("yt-dlp is not installed. Simulating YouTube Download.")
            return self.download_youtube_mock()

        self.status_msg.emit("Connecting to YouTube...")
        output_template = os.path.join(IMPORTS_DIR, "%(title)s.%(ext)s")
        
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            self.status_msg.emit("Downloading video stream...")
            self.progress.emit(20)
            info = ydl.extract_info(self.source, download=True)
            filename = ydl.prepare_filename(info)
            # yt-dlp might download and merge, check final extension
            if not os.path.exists(filename):
                filename = os.path.splitext(filename)[0] + ".mp4"
            
            self.progress.emit(55)
            return filename

    def download_youtube_mock(self):
        """Mock downloader if yt-dlp isn't installed."""
        time_to_wait = 2
        for step in range(time_to_wait):
            time_left = time_to_wait - step
            self.status_msg.emit(f"Simulating download of {self.source}... {time_left}s left")
            self.msleep(1000)
            self.progress.emit(15 + step * 20)
            
        # Create a mock video file if it doesn't exist
        mock_file = os.path.join(IMPORTS_DIR, "mock_youtube_video.mp4")
        if not os.path.exists(mock_file):
            with open(mock_file, "wb") as f:
                f.write(b"MOCK VIDEO DATA")
        return mock_file


class IngestionAgent:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def start_ingestion(self, source_path_or_url, is_youtube=False):
        """Returns an IngestionWorker thread instance ready to run."""
        return IngestionWorker(self.db_manager, source_path_or_url, is_youtube)
