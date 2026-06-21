import os
import sys
import json
import subprocess
import logging
from PySide6.QtCore import QThread, Signal
from clipforge.config.config import EXPORTS_DIR

logger = logging.getLogger("EditingAgent")

class EditingWorker(QThread):
    progress = Signal(int)
    status_msg = Signal(str)
    finished = Signal(str)  # Emits output clip file path
    error = Signal(str)

    def __init__(self, db_manager, clip_id):
        super().__init__()
        self.db_manager = db_manager
        self.clip_id = clip_id
        self._is_running = True

    def stop(self):
        self._is_running = False

    def run(self):
        try:
            self.status_msg.emit("Reading clip info from database...")
            self.progress.emit(5)
            
            # Retrieve clip info
            clip = self.db_manager.get_clip(self.clip_id)
            if not clip:
                raise Exception(f"Clip with ID {self.clip_id} not found.")

            video = self.db_manager.get_video(clip["video_id"])
            if not video:
                raise Exception("Parent video record not found.")

            input_path = video["file_path"]
            start_time = clip["start_time"]
            end_time = clip["end_time"]
            
            # Fetch transcripts and word level timestamps
            transcripts = self.db_manager.get_transcripts_for_video(video["id"])
            
            # Settings
            face_tracking = self.db_manager.get_setting("face_tracking_enabled", "True") == "True"
            silence_removal = self.db_manager.get_setting("silence_removal_enabled", "True") == "True"
            
            output_filename = f"clip_{self.clip_id}_{int(start_time)}_{int(end_time)}.mp4"
            output_path = os.path.join(EXPORTS_DIR, output_filename)
            
            # Temporary paths
            temp_dir = os.path.join(EXPORTS_DIR, "temp")
            os.makedirs(temp_dir, exist_ok=True)
            temp_visual = os.path.join(temp_dir, f"visual_{self.clip_id}.mp4")
            temp_audio = os.path.join(temp_dir, f"audio_{self.clip_id}.wav")

            # Dynamic imports
            try:
                import cv2
                import numpy as np
            except ImportError:
                raise ImportError("OpenCV (cv2) or NumPy is not installed. Please install them to render videos.")

            self.status_msg.emit("Initializing OpenCV capture and Haar cascades...")
            self.progress.emit(10)

            # Load Face Cascade
            face_cascade = None
            if face_tracking:
                cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                if os.path.exists(cascade_path):
                    face_cascade = cv2.CascadeClassifier(cascade_path)
                else:
                    logger.warning("Haar cascade XML file not found. Face tracking disabled.")
                    face_tracking = False

            # Open Capture
            cap = cv2.VideoCapture(input_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            if not fps or fps <= 0:
                fps = 30.0

            start_frame = int(start_time * fps)
            end_frame = int(end_time * fps)
            target_frames_count = end_frame - start_frame

            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

            # Define 9:16 layout sizes
            # Let's say we output 720x1280 (HD vertical) or crop source height to matching width
            # Target height is source height, crop width is height * 9 / 16
            crop_height = height
            crop_width = int(crop_height * 9 / 16)
            if crop_width > width:
                crop_width = width
                crop_height = int(crop_width * 16 / 9)

            # Center coordinates
            default_center_x = width // 2
            last_center_x = default_center_x
            
            # Smooth tracking using rolling history
            center_history = [default_center_x] * 10

            # Output video writer (we write silent video first)
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(temp_visual, fourcc, fps, (crop_width, crop_height))

            self.status_msg.emit("Rendering cropped frames and captions...")
            
            frame_idx = 0
            
            # Extract word segments relevant to this clip
            clip_words = []
            for t in transcripts:
                if t["words"]:
                    for w in t["words"]:
                        w_start = w["start"]
                        w_end = w["end"]
                        # Adjust timestamps relative to clip start
                        if w_start >= start_time and w_end <= end_time:
                            clip_words.append({
                                "word": w["word"],
                                "start": w_start - start_time,
                                "end": w_end - start_time
                            })

            while cap.isOpened() and frame_idx < target_frames_count:
                if not self._is_running:
                    cap.release()
                    writer.release()
                    return

                ret, frame = cap.read()
                if not ret:
                    break

                current_time_sec = frame_idx / fps

                # --- 1. Face Detection / Auto Crop ---
                target_x = default_center_x
                if face_tracking and face_cascade and (frame_idx % 5 == 0):
                    # Shrink frame to speed up face detection
                    small_gray = cv2.cvtColor(cv2.resize(frame, (width // 2, height // 2)), cv2.COLOR_BGR2GRAY)
                    faces = face_cascade.detectMultiScale(small_gray, scaleFactor=1.2, minNeighbors=4, minSize=(40, 40))
                    
                    if len(faces) > 0:
                        # Take largest face
                        faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
                        fx, fy, fw, fh = faces[0]
                        # Scale back coordinates
                        target_x = (fx + fw // 2) * 2
                
                # Apply moving average smooth
                if face_tracking:
                    center_history.append(target_x)
                    center_history.pop(0)
                    smoothed_center_x = int(sum(center_history) / len(center_history))
                else:
                    smoothed_center_x = default_center_x

                # Keep crop within bounds
                left = smoothed_center_x - crop_width // 2
                if left < 0:
                    left = 0
                elif left + crop_width > width:
                    left = width - crop_width

                cropped_frame = frame[0:crop_height, left:left + crop_width]

                # --- 2. Caption Overlay ---
                active_words = [w["word"] for w in clip_words if w["start"] <= current_time_sec <= w["end"]]
                if active_words:
                    caption_text = " ".join(active_words).upper()
                    
                    # Compute text size to center it
                    font = cv2.FONT_HERSHEY_DUPLEX
                    font_scale = 1.3
                    thickness = 3
                    text_size = cv2.getTextSize(caption_text, font, font_scale, thickness)[0]
                    
                    text_x = (crop_width - text_size[0]) // 2
                    # Position in bottom 30% of screen
                    text_y = int(crop_height * 0.75)
                    
                    # Draw thick black outline
                    cv2.putText(cropped_frame, caption_text, (text_x, text_y), font, font_scale, (0, 0, 0), thickness + 4, cv2.LINE_AA)
                    # Draw bright yellow text inside outline
                    cv2.putText(cropped_frame, caption_text, (text_x, text_y), font, font_scale, (0, 255, 255), thickness, cv2.LINE_AA)

                writer.write(cropped_frame)
                frame_idx += 1
                
                if frame_idx % 15 == 0:
                    pct = int(10 + (frame_idx / target_frames_count) * 60)
                    pct = min(75, pct)
                    self.progress.emit(pct)
                    self.status_msg.emit(f"Rendering: {frame_idx}/{target_frames_count} frames completed...")

            cap.release()
            writer.release()

            # --- 3. Extract Audio Track with FFmpeg ---
            self.status_msg.emit("Extracting video clip audio...")
            self.progress.emit(80)
            
            ffmpeg_audio_cmd = [
                "ffmpeg", "-y",
                "-ss", str(start_time),
                "-to", str(end_time),
                "-i", input_path,
                "-vn",
                "-acodec", "copy",
                temp_audio
            ]
            
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
            subprocess.run(ffmpeg_audio_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)

            # --- 4. Merge Video and Audio ---
            self.status_msg.emit("Muxing final video and audio tracks...")
            self.progress.emit(90)

            # Check if NVENC is available for encoding
            ffmpeg_merge_cmd = [
                "ffmpeg", "-y",
                "-i", temp_visual,
                "-i", temp_audio,
                "-c:v", "libx264",  # Standard CPU h264 encoding
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-map", "0:v:0",
                "-map", "1:a:0",
                output_path
            ]
            
            subprocess.run(ffmpeg_merge_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
            
            # Cleanup temporary files
            try:
                if os.path.exists(temp_visual):
                    os.remove(temp_visual)
                if os.path.exists(temp_audio):
                    os.remove(temp_audio)
            except Exception as e:
                logger.warning(f"Failed to delete temp files: {e}")

            # Update clip status in DB
            self.db_manager.update_clip_status(self.clip_id, "rendered", output_path)

            self.progress.emit(100)
            self.status_msg.emit("Clip successfully rendered!")
            self.finished.emit(output_path)

        except Exception as e:
            logger.error(f"Video editing failed: {e}")
            self.error.emit(str(e))


class EditingAgent:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def render_clip(self, clip_id):
        """Returns an EditingWorker QThread ready to run."""
        return EditingWorker(self.db_manager, clip_id)
