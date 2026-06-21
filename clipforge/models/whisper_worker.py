import os
import sys
import time
import logging
from PySide6.QtCore import QThread, Signal
from clipforge.config.config import WHISPER_CACHE_DIR

logger = logging.getLogger("WhisperWorker")

class WhisperWorker(QThread):
    progress = Signal(int)       # Percentage progress (0-100)
    status_msg = Signal(str)     # Current operation message
    segment_ready = Signal(dict) # Segment dictionary ready
    finished = Signal(list)      # All segments list
    error = Signal(str)          # Error details

    def __init__(self, audio_path, model_size="base", device="cuda", compute_type="float16"):
        super().__init__()
        self.audio_path = audio_path
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._is_running = True

    def stop(self):
        self._is_running = False

    def run(self):
        try:
            self.status_msg.emit("Initializing Whisper...")
            self.progress.emit(5)
            
            # Dynamic lazy loading of faster-whisper
            try:
                from faster_whisper import WhisperModel
                import torch
            except ImportError:
                logger.warning("faster-whisper or torch not installed. Falling back to Mock Simulation Mode.")
                self.run_mock_whisper()
                return

            # Check CUDA availability and fallback to CPU if needed
            selected_device = self.device
            selected_compute = self.compute_type
            
            if selected_device == "cuda":
                if not torch.cuda.is_available():
                    logger.warning("CUDA is not available on PyTorch. Falling back to CPU.")
                    selected_device = "cpu"
                    selected_compute = "int8"
                else:
                    # Limit VRAM: empty cache before starting
                    torch.cuda.empty_cache()

            self.status_msg.emit(f"Loading Whisper model '{self.model_size}' on {selected_device.upper()}...")
            self.progress.emit(15)

            # Initialize Whisper Model
            try:
                model = WhisperModel(
                    self.model_size,
                    device=selected_device,
                    compute_type=selected_compute,
                    download_root=WHISPER_CACHE_DIR
                )
            except Exception as model_err:
                logger.warning(f"Failed to load Whisper on {selected_device}: {model_err}. Falling back to CPU.")
                model = WhisperModel(
                    self.model_size,
                    device="cpu",
                    compute_type="int8",
                    download_root=WHISPER_CACHE_DIR
                )

            self.status_msg.emit("Transcribing audio segments...")
            self.progress.emit(30)

            # Run transcription with word timestamps enabled
            segments, info = model.transcribe(
                self.audio_path,
                beam_size=5,
                word_timestamps=True
            )
            
            duration = info.duration
            transcribed_segments = []
            
            for segment in segments:
                if not self._is_running:
                    self.status_msg.emit("Transcription cancelled.")
                    return

                # Build segment data
                words_list = []
                if segment.words:
                    for w in segment.words:
                        words_list.append({
                            "word": w.word,
                            "start": w.start,
                            "end": w.end
                        })
                
                segment_dict = {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip(),
                    "speaker": "Speaker 1",
                    "words": words_list
                }
                
                transcribed_segments.append(segment_dict)
                self.segment_ready.emit(segment_dict)
                
                # Calculate progress percentage
                if duration > 0:
                    pct = int(30 + (segment.end / duration) * 65)
                    pct = min(95, pct)
                    self.progress.emit(pct)
                    self.status_msg.emit(f"Transcribed {segment.end:.1f}s / {duration:.1f}s")
            
            # Clear CUDA memory cache when done
            if selected_device == "cuda":
                del model
                torch.cuda.empty_cache()

            self.progress.emit(100)
            self.status_msg.emit("Transcription complete!")
            self.finished.emit(transcribed_segments)

        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")
            self.error.emit(str(e))

    def run_mock_whisper(self):
        """Simulates transcription if faster-whisper is not installed."""
        self.status_msg.emit("Simulating transcription...")
        time.sleep(1)
        
        mock_data = [
            ("Welcome to ClipForgeAI, the automatic video clipper.", 0.0, 4.2),
            ("In this video, I will show you how to generate viral clips from long videos.", 4.5, 9.8),
            ("This runs fully locally using optimized models on your RTX GPU.", 10.2, 14.5),
            ("You can also integrate Gemini API for smart copy generation and high viral scores.", 15.0, 20.2),
            ("Let's look at the performance statistics on our Dashboard.", 21.0, 25.5),
            ("Don't forget to configure your API keys in the Settings tab.", 26.0, 30.0)
        ]

        total_steps = len(mock_data)
        transcribed_segments = []

        for i, (text, start, end) in enumerate(mock_data):
            if not self._is_running:
                return
            
            # Simulate word-level timestamps
            words = []
            split_words = text.split()
            word_duration = (end - start) / len(split_words)
            for j, w in enumerate(split_words):
                w_start = start + j * word_duration
                w_end = w_start + word_duration
                words.append({
                    "word": w,
                    "start": round(w_start, 2),
                    "end": round(w_end, 2)
                })

            segment_dict = {
                "start": start,
                "end": end,
                "text": text,
                "speaker": "Speaker 1",
                "words": words
            }
            
            time.sleep(0.5)  # Simulate progress delay
            transcribed_segments.append(segment_dict)
            self.segment_ready.emit(segment_dict)
            
            pct = int(10 + ((i + 1) / total_steps) * 85)
            self.progress.emit(pct)
            self.status_msg.emit(f"Transcribed {end:.1f}s / {mock_data[-1][2]:.1f}s")
            
        self.progress.emit(100)
        self.status_msg.emit("Transcription complete (Simulation)!")
        self.finished.emit(transcribed_segments)
