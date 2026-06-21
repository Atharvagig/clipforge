import logging
from PySide6.QtCore import QThread, Signal
from clipforge.models.gemini_client import GeminiClient

logger = logging.getLogger("CaptionAgent")

class CaptionWorker(QThread):
    progress = Signal(int)
    status_msg = Signal(str)
    finished = Signal(dict)  # Emits dictionary of copywriting metadata
    error = Signal(str)

    def __init__(self, db_manager, clip_id):
        super().__init__()
        self.db_manager = db_manager
        self.clip_id = clip_id

    def run(self):
        try:
            self.status_msg.emit("Fetching clip details...")
            self.progress.emit(10)
            
            clip = self.db_manager.get_clip(self.clip_id)
            if not clip:
                raise Exception(f"Clip with ID {self.clip_id} not found.")

            # Load the corresponding transcript slice to provide context to Gemini
            video_id = clip["video_id"]
            start_time = clip["start_time"]
            end_time = clip["end_time"]
            
            transcripts = self.db_manager.get_transcripts_for_video(video_id)
            clip_text_list = []
            for t in transcripts:
                if t["start_time"] >= start_time and t["end_time"] <= end_time:
                    clip_text_list.append(t["text"])
                    
            clip_transcript = " ".join(clip_text_list)
            if not clip_transcript:
                clip_transcript = clip["title"]

            self.status_msg.emit("Generating hook, title, and hashtags via Gemini AI...")
            self.progress.emit(40)

            # API check
            api_key = self.db_manager.get_setting("gemini_api_key", "")
            
            copy_results = None
            if api_key:
                client = GeminiClient(api_key=api_key)
                copy_results = client.generate_marketing_copy(clip["title"], clip_transcript)
            
            # Local Template Fallback if API key is not configured or fails
            if not copy_results:
                logger.info("Gemini API key missing or request failed. Generating template-based social copy.")
                self.status_msg.emit("Generating template copywriting...")
                copy_results = self.generate_local_fallback_copy(clip["title"], clip_transcript)

            self.status_msg.emit("Saving copy to SQLite...")
            self.progress.emit(80)

            # Save in database
            self.db_manager.update_clip_metadata(
                clip_id=self.clip_id,
                title=copy_results["title"],
                hook=copy_results["hook"],
                caption=copy_results["hook"],  # Use hook as active overlay caption
                description=copy_results["description"],
                tags=copy_results["hashtags"]
            )

            self.progress.emit(100)
            self.status_msg.emit("Copywriting assets generated successfully!")
            self.finished.emit(copy_results)

        except Exception as e:
            logger.error(f"Copy generation failed: {e}")
            self.error.emit(str(e))

    def generate_local_fallback_copy(self, original_title, transcript_snippet):
        """Generates engaging social copy using heuristics and transcript content."""
        words = transcript_snippet.split()
        first_few = " ".join(words[:6]) if len(words) >= 6 else transcript_snippet
        
        hook = f"🚀 \"{first_few}...\""
        title = f"{original_title} #Shorts"
        description = (
            f"Here is an interesting segment: \"{transcript_snippet[:150]}...\"\n\n"
            f"Watch the full clip to learn more! Made with ClipForgeAI."
        )
        
        # Pull key nouns/topics or use default tags
        hashtags = "#viral, #shorts, #trending, #clipforge, #creators, #ai"
        
        return {
            "hook": hook,
            "title": title,
            "description": description,
            "hashtags": hashtags
        }


class CaptionAgent:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def generate_copy(self, clip_id):
        """Returns a CaptionWorker QThread ready to run."""
        return CaptionWorker(self.db_manager, clip_id)
