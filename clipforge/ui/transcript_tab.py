from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QPushButton, QFrame, QProgressBar, 
                             QListWidget, QListWidgetItem, QMessageBox)
from PySide6.QtCore import Qt, Signal
from clipforge.agents.transcript_agent import TranscriptAgent
from clipforge.agents.clip_detection_agent import ClipDetectionAgent

class TranscriptTab(QWidget):
    transcription_completed = Signal(int)  # Emits video_id
    highlights_detected = Signal(int)      # Emits video_id

    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.transcript_agent = TranscriptAgent(db_manager)
        self.clip_agent = ClipDetectionAgent(db_manager)
        self.active_transcribe_worker = None
        self.active_clip_worker = None
        self.selected_video_id = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # 1. Header & Video Selection Row
        header_layout = QHBoxLayout()
        title_label = QLabel("Transcription Room")
        title_label.setObjectName("headerTitle")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        header_layout.addWidget(QLabel("Select Video: "))
        self.video_combo = QComboBox()
        self.video_combo.setMinimumWidth(250)
        self.video_combo.currentIndexChanged.connect(self.on_video_selected)
        header_layout.addWidget(self.video_combo)
        
        btn_refresh = QPushButton("🔄")
        btn_refresh.setFixedWidth(40)
        btn_refresh.clicked.connect(self.populate_video_list)
        header_layout.addWidget(btn_refresh)
        
        layout.addLayout(header_layout)

        # 2. Control Actions & Progress Row
        controls_card = QFrame()
        controls_card.setObjectName("glassCard")
        controls_layout = QHBoxLayout(controls_card)
        controls_layout.setContentsMargins(15, 15, 15, 15)

        self.btn_transcribe = QPushButton("Transcribe Video")
        self.btn_transcribe.setObjectName("primaryActionButton")
        self.btn_transcribe.clicked.connect(self.run_transcription)
        controls_layout.addWidget(self.btn_transcribe)

        self.btn_detect_clips = QPushButton("Detect Highlights (Gemini)")
        self.btn_detect_clips.clicked.connect(self.run_clip_detection)
        self.btn_detect_clips.setEnabled(False)
        controls_layout.addWidget(self.btn_detect_clips)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        controls_layout.addWidget(self.progress_bar)

        layout.addWidget(controls_card)

        # 3. Transcripts List Card
        list_card = QFrame()
        list_card.setObjectName("glassCard")
        list_layout = QVBoxLayout(list_card)
        list_layout.setContentsMargins(15, 15, 15, 15)

        list_title = QLabel("Transcript Timeline")
        list_title.setObjectName("sectionTitle")
        list_layout.addWidget(list_title)

        self.transcript_list = QListWidget()
        self.transcript_list.setObjectName("transcriptTimeline")
        list_layout.addWidget(self.transcript_list)

        layout.addWidget(list_card)
        
        self.populate_video_list()

    def populate_video_list(self):
        """Fetches videos from database and adds them to combo box selection."""
        self.video_combo.blockSignals(True)
        self.video_combo.clear()
        self.video_combo.addItem("--- Select Video ---", None)
        
        videos = self.db_manager.get_all_videos()
        for v in videos:
            self.video_combo.addItem(f"📹 {v['title']} ({v['status']})", v["id"])
            
        self.video_combo.blockSignals(False)

    def on_video_selected(self, index):
        video_id = self.video_combo.itemData(index)
        self.selected_video_id = video_id
        
        # Reset UI elements
        self.transcript_list.clear()
        self.progress_bar.setValue(0)
        
        if not video_id:
            self.btn_detect_clips.setEnabled(False)
            return
            
        video = self.db_manager.get_video(video_id)
        if video:
            if video["status"] == "transcribed":
                self.btn_detect_clips.setEnabled(True)
                self.load_transcript_timeline(video_id)
            else:
                self.btn_detect_clips.setEnabled(False)
                self.transcript_list.addItem(QListWidgetItem("Video is not transcribed yet. Click 'Transcribe Video' to start."))

    def load_transcript_timeline(self, video_id):
        self.transcript_list.clear()
        segments = self.db_manager.get_transcripts_for_video(video_id)
        for seg in segments:
            # Convert start/end seconds to MM:SS format
            s_min = int(seg['start_time'] // 60)
            s_sec = int(seg['start_time'] % 60)
            e_min = int(seg['end_time'] // 60)
            e_sec = int(seg['end_time'] % 60)
            
            timestamp = f"[{s_min:02d}:{s_sec:02d} - {e_min:02d}:{e_sec:02d}]"
            speaker = seg["speaker"]
            text = seg["text"]
            
            item = QListWidgetItem(f"{timestamp} {speaker}: {text}")
            self.transcript_list.addItem(item)
            
        if not segments:
            self.transcript_list.addItem("No transcript data found. Try transcribing again.")

    def run_transcription(self):
        if not self.selected_video_id:
            QMessageBox.warning(self, "Warning", "Please select a video project first.")
            return

        self.transcript_list.clear()
        self.progress_bar.setValue(0)
        self.btn_transcribe.setEnabled(False)

        # Setup agent connections
        self.transcript_agent.progress.connect(self.progress_bar.setValue)
        self.transcript_agent.status_msg.connect(self._on_status_msg)
        self.transcript_agent.segment_ready.connect(self._on_segment_ready)
        self.transcript_agent.finished.connect(self._on_transcription_finished)
        self.transcript_agent.error.connect(self._on_error)

        self.transcript_agent.transcribe_video(self.selected_video_id)

    def _on_status_msg(self, msg):
        item = QListWidgetItem(f"⚙️ System: {msg}")
        item.setForeground(Qt.yellow)
        self.transcript_list.addItem(item)
        self.transcript_list.scrollToBottom()

    def _on_segment_ready(self, segment):
        s_min = int(segment['start'] // 60)
        s_sec = int(segment['start'] % 60)
        e_min = int(segment['end'] // 60)
        e_sec = int(segment['end'] % 60)
        timestamp = f"[{s_min:02d}:{s_sec:02d} - {e_min:02d}:{e_sec:02d}]"
        
        self.transcript_list.addItem(f"{timestamp} {segment.get('speaker', 'Speaker 1')}: {segment['text']}")
        self.transcript_list.scrollToBottom()

    def _on_transcription_finished(self, segments):
        self.btn_transcribe.setEnabled(True)
        self.btn_detect_clips.setEnabled(True)
        
        # Re-populate status in combo
        curr_idx = self.video_combo.currentIndex()
        self.populate_video_list()
        self.video_combo.setCurrentIndex(curr_idx)
        
        self.transcription_completed.emit(self.selected_video_id)
        QMessageBox.information(self, "Success", "Video transcription completed successfully!")

    def _on_error(self, err_msg):
        self.btn_transcribe.setEnabled(True)
        QMessageBox.critical(self, "Error", f"Transcription failed: {err_msg}")

    def run_clip_detection(self):
        if not self.selected_video_id:
            return

        self.btn_detect_clips.setEnabled(False)
        self.progress_bar.setValue(0)
        
        # Instantiate worker from agent
        self.active_clip_worker = self.clip_agent.detect_clips(self.selected_video_id)
        self.active_clip_worker.progress.connect(self.progress_bar.setValue)
        self.active_clip_worker.status_msg.connect(self._on_status_msg)
        self.active_clip_worker.finished.connect(self._on_clips_detected_finished)
        self.active_clip_worker.error.connect(self._on_clip_error)
        
        self.active_clip_worker.start()

    def _on_clips_detected_finished(self, clips):
        self.btn_detect_clips.setEnabled(True)
        self.progress_bar.setValue(100)
        
        self.highlights_detected.emit(self.selected_video_id)
        QMessageBox.information(
            self, "Clips Detected", 
            f"Successfully identified {len(clips)} social highlights! Redirection to Clip Editor to modify/render."
        )

    def _on_clip_error(self, error):
        self.btn_detect_clips.setEnabled(True)
        QMessageBox.critical(self, "Error", f"Failed to analyze highlights: {error}")
