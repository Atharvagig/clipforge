from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                             QPushButton, QStackedWidget, QLabel, QFrame, 
                             QStatusBar)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon

from clipforge.ui.styles import GLASS_STYLE
from clipforge.ui.dashboard_tab import DashboardTab
from clipforge.ui.import_tab import ImportTab
from clipforge.ui.transcript_tab import TranscriptTab
from clipforge.ui.clip_editor_tab import ClipEditorTab
from clipforge.ui.queue_tab import QueueTab
from clipforge.ui.analytics_tab import AnalyticsTab
from clipforge.ui.settings_tab import SettingsTab

class MainWindow(QMainWindow):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.setWindowTitle("ClipForgeAI - Local AI Multi-Agent Video Clipper")
        self.resize(1280, 800)
        self.setMinimumSize(1024, 700)
        
        # Apply premium global dark mode glass styling
        self.setStyleSheet(GLASS_STYLE)
        
        self.init_ui()

    def init_ui(self):
        # Main central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Left Sidebar Navigation Panel
        sidebar = QFrame()
        sidebar.setObjectName("glassSidebar")
        sidebar.setFixedWidth(230)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(15, 25, 15, 25)
        sidebar_layout.setSpacing(8)

        # App Logo & Branding
        logo_label = QLabel("🔥 ClipForgeAI")
        logo_label.setStyleSheet("font-size: 22px; font-weight: 900; color: #ffffff; margin-bottom: 25px;")
        logo_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(logo_label)

        # Navigation Buttons definitions
        self.nav_buttons = []
        nav_info = [
            ("📊 Dashboard", 0),
            ("📥 Import Videos", 1),
            ("📝 Transcription", 2),
            ("🎬 Clip Editor", 3),
            ("📅 Publish Queue", 4),
            ("📈 Performance Stats", 5),
            ("⚙️ Settings", 6),
        ]

        for text, index in nav_info:
            btn = QPushButton(text)
            btn.setStyleSheet(
                "QPushButton { text-align: left; padding: 12px 15px; font-size: 13px; border: none; border-radius: 8px; }"
                "QPushButton:hover { background-color: rgba(255, 255, 255, 0.08); }"
            )
            btn.clicked.connect(lambda checked=False, idx=index: self.switch_tab(idx))
            sidebar_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        sidebar_layout.addStretch()
        
        # Version Badge
        v_label = QLabel("v1.0.0 (Local GPU)")
        v_label.setStyleSheet("color: rgba(255, 255, 255, 0.3); font-size: 11px;")
        v_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(v_label)

        main_layout.addWidget(sidebar)

        # 2. Right Stacked Widget Workspace
        self.workspace = QStackedWidget()
        
        # Instantiate Tabs
        self.tab_dashboard = DashboardTab(self.db_manager)
        self.tab_import = ImportTab(self.db_manager)
        self.tab_transcript = TranscriptTab(self.db_manager)
        self.tab_editor = ClipEditorTab(self.db_manager)
        self.tab_queue = QueueTab(self.db_manager)
        self.tab_analytics = AnalyticsTab(self.db_manager)
        self.tab_settings = SettingsTab(self.db_manager)

        # Add to stack
        self.workspace.addWidget(self.tab_dashboard)
        self.workspace.addWidget(self.tab_import)
        self.workspace.addWidget(self.tab_transcript)
        self.workspace.addWidget(self.tab_editor)
        self.workspace.addWidget(self.tab_queue)
        self.workspace.addWidget(self.tab_analytics)
        self.workspace.addWidget(self.tab_settings)

        main_layout.addWidget(self.workspace)

        # 3. Inter-Tab Event Connections (Orchestrating workflow)
        # Import Tab success triggers reload on Transcript Selection list
        self.tab_import.video_ingested.connect(self._on_video_ingested)
        
        # Transcription complete triggers switch/update on Clip Editor & Dashboard lists
        self.tab_transcript.transcription_completed.connect(self._on_transcription_done)
        self.tab_transcript.highlights_detected.connect(self._on_highlights_detected)
        
        # Clip render complete triggers reload of lists
        self.tab_editor.clip_rendered.connect(self._on_clip_rendered)
        self.tab_editor.clip_queued.connect(self._on_clip_queued)
        
        # Dashboard quick links navigation mapping
        self.tab_dashboard.navigate_to_tab.connect(self.switch_tab)

        # Set default tab highlight (Dashboard)
        self.switch_tab(0)

        # Status Bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("ClipForgeAI ready. Select a video project or configure API key in Settings.")

    def switch_tab(self, index):
        """Changes the current workspace stacked widget tab index and highlights sidebar item."""
        self.workspace.setCurrentIndex(index)
        
        # Highlight active button, reset others
        for idx, btn in enumerate(self.nav_buttons):
            if idx == index:
                btn.setStyleSheet(
                    "QPushButton { text-align: left; padding: 12px 15px; font-size: 13px; border: none; border-radius: 8px; "
                    "background-color: rgba(168, 85, 247, 0.25); border-left: 3px solid #00f0ff; color: #ffffff; font-weight: bold; }"
                )
            else:
                btn.setStyleSheet(
                    "QPushButton { text-align: left; padding: 12px 15px; font-size: 13px; border: none; border-radius: 8px; color: #94a3b8; }"
                    "QPushButton:hover { background-color: rgba(255, 255, 255, 0.08); color: #ffffff; }"
                )

        # Conditional refreshes on navigation
        if index == 0:
            self.tab_dashboard.refresh_data()
        elif index == 2:
            self.tab_transcript.populate_video_list()
        elif index == 3:
            self.tab_editor.populate_clips_list()
        elif index == 4:
            self.tab_queue.populate_queue()
        elif index == 5:
            self.tab_analytics.calculate_analytics()

    def _on_video_ingested(self, video_id):
        self.statusBar.showMessage(f"Video {video_id} successfully ingested! Redirecting to transcription room...")
        self.switch_tab(2)
        # Select the newly ingested video in combo
        self.tab_transcript.populate_video_list()
        # Find index of item with data == video_id
        combo = self.tab_transcript.video_combo
        for i in range(combo.count()):
            if combo.itemData(i) == video_id:
                combo.setCurrentIndex(i)
                break

    def _on_transcription_done(self, video_id):
        self.statusBar.showMessage(f"Transcription complete for video ID {video_id}.")
        self.tab_dashboard.refresh_data()

    def _on_highlights_detected(self, video_id):
        self.statusBar.showMessage(f"Highlight clips generated for video ID {video_id}. Redirecting to Clip Editor...")
        self.switch_tab(3)
        self.tab_editor.populate_clips_list()

    def _on_clip_rendered(self, clip_id):
        self.statusBar.showMessage(f"Clip ID {clip_id} successfully rendered!")
        self.tab_dashboard.refresh_data()

    def _on_clip_queued(self, clip_id):
        self.statusBar.showMessage(f"Clip ID {clip_id} successfully scheduled and queued for upload.")
        self.tab_dashboard.refresh_data()

    def closeEvent(self, event):
        # Propagate close event to tabs to ensure scheduler threads exit cleanly
        self.tab_queue.closeEvent(event)
        super().closeEvent(event)
