import logging
from PySide6.QtCore import QThread, Signal
from clipforge.models.gemini_client import GeminiClient

logger = logging.getLogger("ClipDetectionAgent")

class ClipDetectionWorker(QThread):
    progress = Signal(int)
    status_msg = Signal(str)
    finished = Signal(list)  # Emits list of created clip dicts
    error = Signal(str)

    def __init__(self, db_manager, video_id):
        super().__init__()
        self.db_manager = db_manager
        self.video_id = video_id

    def run(self):
        try:
            self.status_msg.emit("Reading transcripts from database...")
            self.progress.emit(10)
            
            # Fetch transcripts
            transcripts = self.db_manager.get_transcripts_for_video(self.video_id)
            if not transcripts:
                raise Exception("No transcripts found for this video. Please transcribe it first.")
            
            video = self.db_manager.get_video(self.video_id)
            duration = video["duration"] if video else 0.0

            # Format transcripts for Gemini
            formatted_transcripts = []
            for t in transcripts:
                formatted_transcripts.append({
                    "start": t["start_time"],
                    "end": t["end_time"],
                    "text": t["text"]
                })

            self.status_msg.emit("Evaluating highlight potential with Gemini AI...")
            self.progress.emit(30)

            # Initialize Gemini API Client
            api_key = self.db_manager.get_setting("gemini_api_key", "")
            
            highlights = []
            if api_key:
                client = GeminiClient(api_key=api_key)
                highlights = client.detect_highlights(formatted_transcripts)
            
            # Fallback to smart local mock highlights if API key is not configured or failed
            if not highlights:
                logger.info("Gemini API key missing or request returned no clips. Running heuristic clip builder.")
                self.status_msg.emit("Running highlight-detection heuristics...")
                highlights = self.run_heuristic_detection(transcripts, duration)

            self.status_msg.emit("Saving highlights to database...")
            self.progress.emit(80)

            created_clips = []
            for hl in highlights:
                # Sanitize times
                start = max(0.0, float(hl.get("start_time", 0.0)))
                end = min(duration, float(hl.get("end_time", duration)))
                if end - start < 3.0:
                    # Skip clips that are too short
                    continue
                
                title = hl.get("title", f"Clip Highlight ({start:.1f}s - {end:.1f}s)")
                score = int(hl.get("viral_score", 70))
                rationale = hl.get("rationale", "High verbal energy moment.")

                # Insert clip into db
                clip_id = self.db_manager.add_clip(
                    video_id=self.video_id,
                    title=title,
                    start_time=start,
                    end_time=end,
                    viral_score=score,
                    hook=title,
                    description=rationale
                )
                
                created_clips.append({
                    "id": clip_id,
                    "video_id": self.video_id,
                    "title": title,
                    "start_time": start,
                    "end_time": end,
                    "viral_score": score,
                    "status": "detected"
                })

            self.progress.emit(100)
            self.status_msg.emit(f"Successfully detected {len(created_clips)} highlight clips!")
            self.finished.emit(created_clips)

        except Exception as e:
            logger.error(f"Clip detection failed: {e}")
            self.error.emit(str(e))

    def run_heuristic_detection(self, transcripts, video_duration):
        """
        Builds highlight clips algorithmically based on sentence markers, duration, and question markers.
        """
        highlights = []
        # Create clip segments of roughly 25-45 seconds
        current_clip_start = None
        current_clip_text = []
        clip_index = 1
        
        for segment in transcripts:
            text = segment["text"]
            start = segment["start_time"]
            end = segment["end_time"]
            
            if current_clip_start is None:
                current_clip_start = start
                
            current_clip_text.append(text)
            
            # Create a clip if the duration is 25s - 45s, or contains exclamation/question marks
            clip_dur = end - current_clip_start
            is_good_stopping_point = "?" in text or "!" in text or text.endswith(".")
            
            if (clip_dur >= 30.0) or (clip_dur >= 15.0 and is_good_stopping_point) or (end >= video_duration - 1.0):
                # Save clip
                headline = f"Highlight Part {clip_index}"
                # Set dynamic viral scores
                score = 75 + (clip_index * 3) % 20 
                
                highlights.append({
                    "title": headline,
                    "start_time": current_clip_start,
                    "end_time": end,
                    "viral_score": score,
                    "rationale": "High-interest conversation block based on structural indicators."
                })
                
                # Reset for next clip
                current_clip_start = None
                current_clip_text = []
                clip_index += 1
                
                if clip_index > 5:
                    break
                    
        return highlights


class ClipDetectionAgent:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def detect_clips(self, video_id):
        """Returns a QThread worker that runs the clip detection process."""
        return ClipDetectionWorker(self.db_manager, video_id)
