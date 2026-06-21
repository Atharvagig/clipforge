from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QListWidget, QListWidgetItem, QFrame, QLineEdit, 
                             QTextEdit, QCheckBox, QPushButton, QProgressBar, 
                             QComboBox, QDateTimeEdit, QMessageBox, QSplitter)
from PySide6.QtCore import Qt, Signal, QDateTime
from clipforge.agents.editing_agent import EditingAgent
from clipforge.agents.caption_agent import CaptionAgent
import os

class ClipEditorTab(QWidget):
    clip_rendered = Signal(int)       # Emits clip_id once rendered
    clip_queued = Signal(int)         # Emits clip_id once added to queue

    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.editing_agent = EditingAgent(db_manager)
        self.caption_agent = CaptionAgent(db_manager)
        
        self.active_render_worker = None
        self.active_caption_worker = None
        self.selected_clip_id = None
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Splitter to allow resizing panels
        splitter = QSplitter(Qt.Horizontal)
        
        # Left Panel: Clips List
        left_panel = QFrame()
        left_panel.setObjectName("glassCard")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(15, 15, 15, 15)

        list_title = QLabel("Available Highlights")
        list_title.setObjectName("sectionTitle")
        left_layout.addWidget(list_title)

        self.clips_list = QListWidget()
        self.clips_list.currentRowChanged.connect(self.on_clip_selected)
        left_layout.addWidget(self.clips_list)
        
        btn_refresh = QPushButton("Refresh List")
        btn_refresh.clicked.connect(self.populate_clips_list)
        left_layout.addWidget(btn_refresh)

        splitter.addWidget(left_panel)

        # Right Panel: Workspace Form (Scrollable content)
        right_panel = QFrame()
        right_panel.setObjectName("glassCard")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(15, 15, 15, 15)
        right_layout.setSpacing(15)

        # Workspace Title
        ws_title = QLabel("Clip workspace")
        ws_title.setObjectName("sectionTitle")
        right_layout.addWidget(ws_title)

        # Card 1: Copywriting Metadata Editors
        self.edit_title = QLineEdit()
        self.edit_title.setPlaceholderText("Clip Title")
        right_layout.addWidget(QLabel("Title:"))
        right_layout.addWidget(self.edit_title)

        self.edit_hook = QLineEdit()
        self.edit_hook.setPlaceholderText("Active overlay text overlay hook...")
        right_layout.addWidget(QLabel("Hooks Overlay:"))
        right_layout.addWidget(self.edit_hook)

        self.edit_desc = QTextEdit()
        self.edit_desc.setPlaceholderText("Write search-optimized description...")
        self.edit_desc.setMaximumHeight(80)
        right_layout.addWidget(QLabel("Social Copy / Description:"))
        right_layout.addWidget(self.edit_desc)

        self.edit_tags = QLineEdit()
        self.edit_tags.setPlaceholderText("comma-separated hashtags (e.g. #shorts, #creator)")
        right_layout.addWidget(QLabel("Hashtags:"))
        right_layout.addWidget(self.edit_tags)

        # Actions for Metadata
        meta_buttons = QHBoxLayout()
        self.btn_save_meta = QPushButton("Save Details")
        self.btn_save_meta.clicked.connect(self.save_clip_metadata)
        meta_buttons.addWidget(self.btn_save_meta)

        self.btn_gen_assets = QPushButton("Generate Assets (Gemini)")
        self.btn_gen_assets.clicked.connect(self.generate_assets_via_gemini)
        meta_buttons.addWidget(self.btn_gen_assets)
        right_layout.addLayout(meta_buttons)

        # Card 2: Render configuration & Processing
        render_settings_layout = QHBoxLayout()
        self.chk_face_track = QCheckBox("Auto Crop face-tracking (9:16)")
        self.chk_face_track.setChecked(True)
        self.chk_face_track.stateChanged.connect(self.on_render_setting_changed)
        render_settings_layout.addWidget(self.chk_face_track)
        
        self.chk_silence = QCheckBox("Compress Silences")
        self.chk_silence.setChecked(True)
        self.chk_silence.stateChanged.connect(self.on_render_setting_changed)
        render_settings_layout.addWidget(self.chk_silence)
        
        right_layout.addLayout(render_settings_layout)

        # Card 3: Scheduler Input
        sched_frame = QFrame()
        sched_frame.setStyleSheet("background-color: rgba(0,0,0,0.15); border-radius: 8px; border: 1px solid rgba(255,255,255,0.05);")
        sched_layout = QVBoxLayout(sched_frame)
        sched_layout.setContentsMargins(10, 10, 10, 10)
        
        sched_title = QLabel("Posting Scheduler")
        sched_title.setStyleSheet("font-weight: 700; color: #a855f7;")
        sched_layout.addWidget(sched_title)
        
        sched_inputs = QHBoxLayout()
        self.platform_combo = QComboBox()
        self.platform_combo.addItems(["YouTube Shorts", "TikTok", "Instagram Reels"])
        sched_inputs.addWidget(self.platform_combo)
        
        self.datetime_edit = QDateTimeEdit(QDateTime.currentDateTime())
        self.datetime_edit.setCalendarPopup(True)
        sched_inputs.addWidget(self.datetime_edit)
        
        self.btn_queue = QPushButton("Queue Video")
        self.btn_queue.clicked.connect(self.add_to_upload_queue)
        sched_inputs.addWidget(self.btn_queue)
        sched_layout.addLayout(sched_inputs)
        right_layout.addWidget(sched_frame)

        # Card 4: Action Button & progress Bar
        self.btn_render = QPushButton("Render Clip 9:16 Video")
        self.btn_render.setObjectName("primaryActionButton")
        self.btn_render.clicked.connect(self.render_clip_video)
        right_layout.addWidget(self.btn_render)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        right_layout.addWidget(self.progress_bar)

        self.console_msg = QLabel("Ready.")
        self.console_msg.setStyleSheet("font-size: 11px; color: #94a3b8;")
        right_layout.addWidget(self.console_msg)

        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        main_layout.addWidget(splitter)

        self.populate_clips_list()

    def populate_clips_list(self):
        self.clips_list.clear()
        clips = self.db_manager.get_all_clips()
        for c in clips:
            item = QListWidgetItem()
            # Format times
            s_min = int(c['start_time'] // 60)
            s_sec = int(c['start_time'] % 60)
            e_min = int(c['end_time'] // 60)
            e_sec = int(c['end_time'] % 60)
            
            status = c["status"].upper()
            item.setText(f"🎬 {c['title']} ({s_min:02d}:{s_sec:02d}-{e_min:02d}:{e_sec:02d}) [{status}]")
            item.setData(Qt.UserRole, c["id"])
            self.clips_list.addItem(item)
            
        if not clips:
            self.clips_list.addItem("No clips generated. Run highlight detection first!")

    def on_clip_selected(self, row):
        if row < 0:
            self.selected_clip_id = None
            return
            
        item = self.clips_list.item(row)
        clip_id = item.data(Qt.UserRole)
        self.selected_clip_id = clip_id
        
        # Load clip details
        clip = self.db_manager.get_clip(clip_id)
        if clip:
            self.edit_title.setText(clip["title"])
            self.edit_hook.setText(clip.get("hook", ""))
            self.edit_desc.setPlainText(clip.get("description", ""))
            self.edit_tags.setText(clip.get("tags", ""))
            self.console_msg.setText(f"Selected clip ID: {clip_id}. Status: {clip['status']}.")
            self.progress_bar.setValue(100 if clip["status"] == "rendered" else 0)

    def on_render_setting_changed(self):
        # Update setting config to SQLite
        self.db_manager.set_setting("face_tracking_enabled", str(self.chk_face_track.isChecked()))
        self.db_manager.set_setting("silence_removal_enabled", str(self.chk_silence.isChecked()))

    def save_clip_metadata(self):
        if not self.selected_clip_id:
            QMessageBox.warning(self, "Warning", "Please select a clip project.")
            return
            
        self.db_manager.update_clip_metadata(
            clip_id=self.selected_clip_id,
            title=self.edit_title.text().strip(),
            hook=self.edit_hook.text().strip(),
            caption=self.edit_hook.text().strip(),
            description=self.edit_desc.toPlainText().strip(),
            tags=self.edit_tags.text().strip()
        )
        
        QMessageBox.information(self, "Success", "Clip details updated successfully!")
        self.populate_clips_list()

    def generate_assets_via_gemini(self):
        if not self.selected_clip_id:
            QMessageBox.warning(self, "Warning", "Please select a clip project.")
            return

        self.btn_gen_assets.setEnabled(False)
        self.console_msg.setText("AI generating copy hook, titles and tags...")
        self.progress_bar.setValue(30)
        
        # Set up Caption agent worker
        self.active_caption_worker = self.caption_agent.generate_copy(self.selected_clip_id)
        self.active_caption_worker.progress.connect(self.progress_bar.setValue)
        self.active_caption_worker.status_msg.connect(self.console_msg.setText)
        self.active_caption_worker.finished.connect(self._on_copy_assets_finished)
        self.active_caption_worker.error.connect(self._on_copy_error)
        
        self.active_caption_worker.start()

    def _on_copy_assets_finished(self, copy_assets):
        self.btn_gen_assets.setEnabled(True)
        self.edit_title.setText(copy_assets["title"])
        self.edit_hook.setText(copy_assets["hook"])
        self.edit_desc.setPlainText(copy_assets["description"])
        self.edit_tags.setText(copy_assets["hashtags"])
        
        # Reload clips titles
        self.populate_clips_list()
        QMessageBox.information(self, "Copy Assets Done", "AI generated social copywriting assets populated!")

    def _on_copy_error(self, err):
        self.btn_gen_assets.setEnabled(True)
        QMessageBox.critical(self, "Error", f"AI copy asset generation failed: {err}")

    def render_clip_video(self):
        if not self.selected_clip_id:
            QMessageBox.warning(self, "Warning", "Please select a clip project first.")
            return

        self.btn_render.setEnabled(False)
        self.progress_bar.setValue(0)
        
        # Setup Editing Agent connection
        self.active_render_worker = self.editing_agent.render_clip(self.selected_clip_id)
        self.active_render_worker.progress.connect(self.progress_bar.setValue)
        self.active_render_worker.status_msg.connect(self.console_msg.setText)
        self.active_render_worker.finished.connect(self._on_render_finished)
        self.active_render_worker.error.connect(self._on_render_error)
        
        self.active_render_worker.start()

    def _on_render_finished(self, output_path):
        self.btn_render.setEnabled(True)
        self.progress_bar.setValue(100)
        self.clip_rendered.emit(self.selected_clip_id)
        
        # Update clips lists
        self.populate_clips_list()
        QMessageBox.information(
            self, "Render Complete", 
            f"Successfully rendered 9:16 video! Saved to:\n{output_path}"
        )

    def _on_render_error(self, error):
        self.btn_render.setEnabled(True)
        QMessageBox.critical(self, "Error", f"Video rendering failed: {error}")

    def add_to_upload_queue(self):
        if not self.selected_clip_id:
            QMessageBox.warning(self, "Warning", "Please select a clip project.")
            return
            
        clip = self.db_manager.get_clip(self.selected_clip_id)
        if not clip or clip["status"] != "rendered":
            QMessageBox.warning(self, "Warning", "Please render the clip 9:16 video first before adding to the queue.")
            return

        platform_map = {
            "YouTube Shorts": "youtube_shorts",
            "TikTok": "tiktok",
            "Instagram Reels": "instagram_reels"
        }
        platform = platform_map[self.platform_combo.currentText()]
        scheduled_time = self.datetime_edit.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        
        # Save upload queue row
        self.db_manager.enqueue_post(
            clip_id=self.selected_clip_id,
            platform=platform,
            scheduled_time=scheduled_time
        )
        
        self.clip_queued.emit(self.selected_clip_id)
        QMessageBox.information(
            self, "Queued", 
            f"Clip queued for scheduling on {self.platform_combo.currentText()} at {scheduled_time}!"
        )
