from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QListWidget, QListWidgetItem, QPushButton, QGridLayout
from PySide6.QtCore import Qt, Signal
import datetime

class DashboardTab(QWidget):
    navigate_to_tab = Signal(int)  # Emits tab index to redirect user

    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # 1. Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Dashboard")
        title_label.setObjectName("headerTitle")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # 2. KPI Cards Grid Layout
        self.cards_layout = QGridLayout()
        self.cards_layout.setSpacing(15)
        layout.addLayout(self.cards_layout)
        
        # 3. Bottom Panels: Recent Videos + Quick Actions
        panels_layout = QHBoxLayout()
        panels_layout.setSpacing(20)

        # Left Panel: Recent Videos
        recent_panel = QFrame()
        recent_panel.setObjectName("glassCard")
        recent_layout = QVBoxLayout(recent_panel)
        recent_layout.setContentsMargins(15, 15, 15, 15)
        
        recent_title = QLabel("Recent Video Projects")
        recent_title.setObjectName("sectionTitle")
        recent_layout.addWidget(recent_title)

        self.videos_list = QListWidget()
        self.videos_list.setObjectName("videosList")
        recent_layout.addWidget(self.videos_list)

        panels_layout.addWidget(recent_panel, 2)

        # Right Panel: Quick Operations
        actions_panel = QFrame()
        actions_panel.setObjectName("glassCard")
        actions_layout = QVBoxLayout(actions_panel)
        actions_layout.setContentsMargins(15, 15, 15, 15)
        actions_layout.setSpacing(15)

        actions_title = QLabel("Quick Actions")
        actions_title.setObjectName("sectionTitle")
        actions_layout.addWidget(actions_title)

        btn_import = QPushButton("Import New Video")
        btn_import.setObjectName("primaryActionButton")
        btn_import.clicked.connect(lambda: self.navigate_to_tab.emit(1)) # Redirect to Import tab
        actions_layout.addWidget(btn_import)

        btn_scheduler = QPushButton("View Scheduled Queue")
        btn_scheduler.clicked.connect(lambda: self.navigate_to_tab.emit(4)) # Redirect to Queue tab
        actions_layout.addWidget(btn_scheduler)

        btn_analytics = QPushButton("View Creator Insights")
        btn_analytics.clicked.connect(lambda: self.navigate_to_tab.emit(5)) # Redirect to Analytics tab
        actions_layout.addWidget(btn_analytics)
        
        actions_layout.addStretch()
        panels_layout.addWidget(actions_panel, 1)

        layout.addLayout(panels_layout)
        
        self.refresh_data()

    def create_stat_card(self, title, value, unit="", row=0, col=0):
        """Creates a gorgeous glassmorphic stat card."""
        card = QFrame()
        card.setObjectName("glassCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(15, 15, 15, 15)
        
        val_label = QLabel(f"{value}{unit}")
        val_label.setStyleSheet("font-size: 28px; font-weight: 800; color: #00f0ff; background: transparent;")
        val_label.setAlignment(Qt.AlignCenter)
        
        lbl_label = QLabel(title)
        lbl_label.setObjectName("bodyText")
        lbl_label.setAlignment(Qt.AlignCenter)
        
        card_layout.addWidget(val_label)
        card_layout.addWidget(lbl_label)
        
        self.cards_layout.addWidget(card, row, col)

    def refresh_data(self):
        """Fetches current stats from the database and updates visual cards and lists."""
        # Clean current cards layout
        for i in reversed(range(self.cards_layout.count())): 
            self.cards_layout.itemAt(i).widget().setParent(None)

        # 1. Fetch DB metrics
        videos = self.db_manager.get_all_videos()
        clips = self.db_manager.get_all_clips()
        queue = self.db_manager.get_queued_posts()
        
        total_videos = len(videos)
        total_clips = len(clips)
        active_queue = len([q for q in queue if q["status"] == 'queued'])
        
        # views aggregation
        aggregates = self.db_manager.get_aggregated_analytics()
        total_views = sum(a["total_views"] for a in aggregates)

        # 2. Draw Cards
        self.create_stat_card("Total Videos Ingested", total_videos, row=0, col=0)
        self.create_stat_card("Highlights Generated", total_clips, row=0, col=1)
        self.create_stat_card("Scheduled Queue", active_queue, row=0, col=2)
        self.create_stat_card("Total Audience Views", total_views, row=0, col=3)

        # 3. Populate Recent Videos list
        self.videos_list.clear()
        for video in videos[:6]:
            item = QListWidgetItem()
            status_text = video["status"].upper()
            
            # Formulate title
            title = video["title"]
            duration_min = int(video["duration"] // 60)
            duration_sec = int(video["duration"] % 60)
            
            item.setText(f"📹 {title} ({duration_min}m {duration_sec}s) - [{status_text}]")
            self.videos_list.addItem(item)
            
        if not videos:
            self.videos_list.addItem("No video projects found. Import one to start!")
