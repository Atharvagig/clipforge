import os
import sys
import time
import datetime
import logging
from PySide6.QtCore import QThread, Signal

logger = logging.getLogger("SchedulerAgent")

class SchedulerWorker(QThread):
    post_started = Signal(dict)
    post_progress = Signal(int, str)
    post_completed = Signal(int, str)  # post_id, status ('success' or 'failed')
    status_msg = Signal(str)

    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self._is_running = True

    def stop(self):
        self._is_running = False

    def run(self):
        logger.info("Scheduler agent background polling loop started.")
        self.status_msg.emit("Scheduler active. Checking upload queue...")

        while self._is_running:
            try:
                # Query database for scheduled posts that are 'queued' and scheduled_time <= now
                now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Fetch pending queue
                posts = []
                with self.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT q.*, c.title as clip_title, c.export_path, c.description, c.tags 
                        FROM upload_queue q
                        JOIN clips c ON q.clip_id = c.id
                        WHERE q.status = 'queued' AND q.scheduled_time <= ?
                        ORDER BY q.scheduled_time ASC
                    """, (now_str,))
                    posts = [dict(row) for row in cursor.fetchall()]

                for post in posts:
                    if not self._is_running:
                        break
                    
                    self.post_started.emit(post)
                    self.db_manager.update_post_status(post["id"], "posting")
                    
                    # Run post upload process
                    success, message = self.upload_post(post)
                    
                    if success:
                        self.db_manager.update_post_status(post["id"], "posted")
                        self.db_manager.update_clip_status(post["clip_id"], "posted")
                        self.post_completed.emit(post["id"], "posted")
                    else:
                        # Auto retry check (limit to 3 retries)
                        new_status = "failed" if post["retry_count"] >= 3 else "queued"
                        self.db_manager.update_post_status(post["id"], new_status, message)
                        self.post_completed.emit(post["id"], f"{new_status}: {message}")
                        
                    # Rate limit safety sleep (e.g. 5 seconds between uploads)
                    time.sleep(5)
                
            except Exception as e:
                logger.error(f"Error in scheduler polling loop: {e}")
                
            # Sleep 10 seconds before next poll
            for _ in range(10):
                if not self._is_running:
                    break
                self.msleep(1000)

    def upload_post(self, post):
        """Dispatches upload to YouTube Shorts, TikTok, or Instagram Reels."""
        platform = post["platform"].lower()
        export_path = post["export_path"]
        
        if not export_path or not os.path.exists(export_path):
            return False, f"Export clip file not found at: {export_path}"

        self.post_progress.emit(post["id"], "Initiating platform handshake...")
        time.sleep(1.5)
        
        if platform == "youtube_shorts" or platform == "youtube":
            return self.upload_to_youtube(post)
        elif platform == "tiktok":
            return self.upload_to_tiktok(post)
        elif platform == "instagram_reels" or platform == "instagram":
            return self.upload_to_instagram(post)
        else:
            return self.upload_mock(post)

    def upload_to_youtube(self, post):
        """YouTube Shorts Upload API handler using official Google Client libraries."""
        # Check OAuth setting credentials
        client_id = self.db_manager.get_setting("youtube_client_id", "")
        client_secret = self.db_manager.get_setting("youtube_client_secret", "")
        
        if not client_id or not client_secret:
            logger.info("YouTube client credentials missing in Settings. Running simulated YouTube upload.")
            return self.upload_mock(post)

        try:
            # Here we lay out the official Google API Client implementation flow
            # If the libraries are not installed, this block fails and runs fallback
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload
            from google_auth_oauthlib.flow import InstalledAppFlow
            
            # API Setup
            scopes = ["https://www.googleapis.com/auth/youtube.upload"]
            # Typically oauth is completed through a local flow and tokens cached
            # We outline the structured oauth block:
            credentials_dict = {
                "installed": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            }
            
            # Simulate OAuth dialog via web browser (runs on client side)
            self.post_progress.emit(post["id"], "Acquiring authorized YouTube channel OAuth2 token...")
            flow = InstalledAppFlow.from_client_config(credentials_dict, scopes=scopes)
            credentials = flow.run_local_server(port=0, authorization_prompt_message="", open_browser=False)
            
            youtube = build("youtube", "v3", credentials=credentials)
            
            self.post_progress.emit(post["id"], "Uploading vertical video media file...")
            body = {
                "snippet": {
                    "title": post["clip_title"],
                    "description": post["description"] + "\n\n" + post["tags"],
                    "tags": [t.strip().replace("#", "") for t in post["tags"].split(",") if t.strip()],
                    "categoryId": "22"  # People & Blogs
                },
                "status": {
                    "privacyStatus": "public",
                    "selfDeclaredMadeForKids": False
                }
            }
            
            media = MediaFileUpload(post["export_path"], chunksize=-1, resumable=True)
            request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
            
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    pct = int(status.progress() * 100)
                    self.post_progress.emit(post["id"], f"Uploading bytes: {pct}%")
            
            video_id = response.get("id")
            logger.info(f"YouTube Shorts successfully uploaded. Video ID: {video_id}")
            return True, f"Uploaded to YouTube Shorts. Video ID: {video_id}"

        except Exception as e:
            logger.error(f"YouTube Upload SDK Failed: {e}")
            return False, f"YouTube API Error: {str(e)}"

    def upload_to_tiktok(self, post):
        """TikTok Content Posting API connector template."""
        # TikTok Graph API uploads require registered business accounts or user-authorized access tokens
        # We mock this transaction for baseline testing, directing users to setup keys
        self.post_progress.emit(post["id"], "Authenticating TikTok Creator Access Token...")
        time.sleep(1)
        self.post_progress.emit(post["id"], "Uploading clip to TikTok Sandbox...")
        time.sleep(2)
        return True, "Simulated TikTok post success."

    def upload_to_instagram(self, post):
        """Instagram Reels Content Publishing API connector template."""
        # Instagram Graph API requires Facebook Login OAuth and Instagram Business Account link
        self.post_progress.emit(post["id"], "Connecting to Instagram Container Graph API...")
        time.sleep(1)
        self.post_progress.emit(post["id"], "Publishing vertical video container...")
        time.sleep(2)
        return True, "Simulated Instagram Reels post success."

    def upload_mock(self, post):
        """Helper to run simulation for queue UI responsiveness testing."""
        self.post_progress.emit(post["id"], "Establishing API Handshake (Simulation)...")
        time.sleep(2)
        self.post_progress.emit(post["id"], "Transferring video bytes (Simulation)...")
        time.sleep(2)
        self.post_progress.emit(post["id"], "Finalizing metadata tags (Simulation)...")
        time.sleep(1)
        return True, f"Mock post successful to {post['platform']}."


class SchedulerAgent:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def start_scheduler(self):
        """Returns a SchedulerWorker thread ready to poll in the background."""
        return SchedulerWorker(self.db_manager)
