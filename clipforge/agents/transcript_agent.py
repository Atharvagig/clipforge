import os
import logging
from PySide6.QtCore import QObject, Signal
from clipforge.models.whisper_worker import WhisperWorker
from clipforge.config.config import IMPORTS_DIR

logger = logging.getLogger("TranscriptAgent")

class TranscriptAgent(QObject):
    progress = Signal(int)
    status_msg = Signal(str)
    segment_ready = Signal(dict)
    finished = Signal(list)
    error = Signal(str)

    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.worker = None

    def transcribe_video(self, video_id):
        """
        Transcribes the audio for a given video_id.
        First checks if transcripts are already cached in the database.
        """
        # 1. Check database cache
        cached = self.db_manager.get_transcripts_for_video(video_id)
        if cached:
            logger.info(f"Using cached transcript for video_id={video_id}")
            self.status_msg.emit("Loading transcript from cache...")
            self.progress.emit(100)
            self.finished.emit(cached)
            return

        # 2. Get video info
        video = self.db_manager.get_video(video_id)
        if not video:
            self.error.emit(f"Video with ID {video_id} not found in database.")
            return

        video_path = video["file_path"]
        
        # Audio file path mapping
        audio_filename = f"{os.path.splitext(os.path.basename(video_path))[0]}_audio.wav"
        audio_path = os.path.join(IMPORTS_DIR, audio_filename)
        
        # Fallback if audio file is deleted but video exists
        if not os.path.exists(audio_path):
            # Try to extract audio again
            from clipforge.agents.ingestion_agent import extract_audio
            self.status_msg.emit("Audio file missing. Extracting audio...")
            success = extract_audio(video_path, audio_path)
            if not success:
                logger.warning("Could not re-extract audio. Transcription might fail or run in simulated mode.")

        # 3. Retrieve settings
        model_size = self.db_manager.get_setting("whisper_model", "base")
        device = self.db_manager.get_setting("whisper_device", "cuda")
        compute_type = self.db_manager.get_setting("whisper_compute_type", "float16")

        logger.info(f"Starting Whisper transcription for video {video_id} using {model_size} model on {device}")
        
        # 4. Create and start the worker thread
        self.worker = WhisperWorker(audio_path, model_size, device, compute_type)
        
        # Connect signals
        self.worker.progress.connect(self.progress.emit)
        self.worker.status_msg.connect(self.status_msg.emit)
        self.worker.segment_ready.connect(self._on_segment_ready)
        self.worker.finished.connect(lambda segments: self._on_transcription_finished(video_id, segments))
        self.worker.error.connect(self.error.emit)
        
        self.worker.start()

    def _on_segment_ready(self, segment_dict):
        """Passes segment data to the UI in real-time."""
        self.segment_ready.emit(segment_dict)

    def _on_transcription_finished(self, video_id, segments):
        """Saves transcribed segments into SQLite and emits finished signal."""
        # Clean existing just in case
        self.db_manager.clear_transcripts_for_video(video_id)
        
        # Save to DB
        for seg in segments:
            self.db_manager.add_transcript_segment(
                video_id=video_id,
                start_time=seg["start"],
                end_time=seg["end"],
                text=seg["text"],
                speaker=seg.get("speaker", "Speaker 1"),
                words=seg.get("words", [])
            )
            
        # Update video status
        self.db_manager.update_video_status(video_id, "transcribed")
        
        logger.info(f"Saved {len(segments)} segments to SQLite database for video_id={video_id}")
        self.finished.emit(segments)
