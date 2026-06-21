from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFileDialog, QFrame, 
                             QProgressBar, QTextEdit)
from PySide6.QtCore import Qt, Signal
from clipforge.agents.ingestion_agent import IngestionAgent

class ImportTab(QWidget):
    video_ingested = Signal(int)  # Emits video_id once ingested successfully

    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.ingestion_agent = IngestionAgent(db_manager)
        self.active_worker = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # 1. Header
        title_label = QLabel("Import Video Sources")
        title_label.setObjectName("headerTitle")
        layout.addWidget(title_label)

        # 2. Local Ingest Card
        local_card = QFrame()
        local_card.setObjectName("glassCard")
        local_layout = QVBoxLayout(local_card)
        local_layout.setContentsMargins(15, 15, 15, 15)

        local_title = QLabel("Import Local File")
        local_title.setObjectName("sectionTitle")
        local_layout.addWidget(local_title)

        local_row = QHBoxLayout()
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("Select video file (*.mp4, *.mkv)...")
        local_row.addWidget(self.file_path_input)

        btn_browse = QPushButton("Browse")
        btn_browse.clicked.connect(self.browse_local_file)
        local_row.addWidget(btn_browse)

        btn_import_local = QPushButton("Import File")
        btn_import_local.clicked.connect(self.import_local_file)
        local_row.addWidget(btn_import_local)
        local_layout.addLayout(local_row)

        layout.addWidget(local_card)

        # 3. YouTube Ingest Card
        yt_card = QFrame()
        yt_card.setObjectName("glassCard")
        yt_layout = QVBoxLayout(yt_card)
        yt_layout.setContentsMargins(15, 15, 15, 15)

        yt_title = QLabel("Import YouTube Video")
        yt_title.setObjectName("sectionTitle")
        yt_layout.addWidget(yt_title)

        yt_row = QHBoxLayout()
        self.yt_url_input = QLineEdit()
        self.yt_url_input.setPlaceholderText("Paste YouTube Video URL (e.g., https://www.youtube.com/watch?v=...)")
        yt_row.addWidget(self.yt_url_input)

        btn_download = QPushButton("Download & Ingest")
        btn_download.clicked.connect(self.import_youtube_video)
        yt_row.addWidget(btn_download)
        yt_layout.addLayout(yt_row)

        layout.addWidget(yt_card)

        # 4. Progress and Logger Card
        status_card = QFrame()
        status_card.setObjectName("glassCard")
        status_layout = QVBoxLayout(status_card)
        status_layout.setContentsMargins(15, 15, 15, 15)

        status_title = QLabel("Ingestion Task Monitor")
        status_title.setObjectName("sectionTitle")
        status_layout.addWidget(status_title)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("QProgressBar { text-align: center; font-weight: bold; }")
        status_layout.addWidget(self.progress_bar)

        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setObjectName("logConsole")
        self.log_console.setPlaceholderText("System messages will appear here...")
        status_layout.addWidget(self.log_console)

        layout.addWidget(status_card)

    def browse_local_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Video File", "", "Video Files (*.mp4 *.mkv *.avi *.mov)"
        )
        if file_path:
            self.file_path_input.setText(file_path)

    def import_local_file(self):
        file_path = self.file_path_input.text().strip()
        if not file_path:
            self.log_message("Please select a video file first.")
            return

        self.start_ingestion_thread(file_path, is_youtube=False)

    def import_youtube_video(self):
        url = self.yt_url_input.text().strip()
        if not url:
            self.log_message("Please paste a valid YouTube URL first.")
            return

        self.start_ingestion_thread(url, is_youtube=True)

    def start_ingestion_thread(self, source, is_youtube=False):
        if self.active_worker and self.active_worker.isRunning():
            self.log_message("An ingestion process is already running. Please wait for it to complete.")
            return

        self.log_console.clear()
        self.progress_bar.setValue(0)
        
        # Get active worker thread from agent
        self.active_worker = self.ingestion_agent.start_ingestion(source, is_youtube)
        
        # Connect signals
        self.active_worker.progress.connect(self.progress_bar.setValue)
        self.active_worker.status_msg.connect(self.log_message)
        self.active_worker.finished.connect(self.on_ingestion_success)
        self.active_worker.error.connect(self.on_ingestion_failed)
        
        # Start execution
        self.active_worker.start()

    def on_ingestion_success(self, video_data):
        self.log_message(f"Successfully processed video details! Ingested ID: {video_data['id']}. Duration: {video_data['duration']:.1f}s.")
        self.video_ingested.emit(video_data["id"])
        
        # Clean text fields
        self.file_path_input.clear()
        self.yt_url_input.clear()

    def on_ingestion_failed(self, error_msg):
        self.log_message(f"ERROR: Ingestion failed - {error_msg}")
        self.progress_bar.setValue(0)

    def log_message(self, message):
        self.log_console.append(message)
        # Scroll console to bottom
        scrollbar = self.log_console.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
