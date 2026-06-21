from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTableWidget, QTableWidgetItem, QPushButton, 
                             QFrame, QMessageBox, QHeaderView, QListWidget)
from PySide6.QtCore import Qt, Signal
from clipforge.agents.scheduler_agent import SchedulerAgent

class QueueTab(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.scheduler_agent = SchedulerAgent(db_manager)
        
        self.scheduler_worker = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # 1. Header & Scheduler Controls
        header_layout = QHBoxLayout()
        title_label = QLabel("Upload Scheduling Queue")
        title_label.setObjectName("headerTitle")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        self.scheduler_status = QLabel("Scheduler: INACTIVE")
        self.scheduler_status.setStyleSheet("color: #ff0055; font-weight: bold; font-size: 14px;")
        header_layout.addWidget(self.scheduler_status)

        self.btn_toggle_scheduler = QPushButton("Start Scheduler")
        self.btn_toggle_scheduler.setObjectName("primaryActionButton")
        self.btn_toggle_scheduler.clicked.connect(self.toggle_scheduler)
        header_layout.addWidget(self.btn_toggle_scheduler)

        layout.addLayout(header_layout)

        # 2. Main Queue Table Card
        table_card = QFrame()
        table_card.setObjectName("glassCard")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(15, 15, 15, 15)

        table_title = QLabel("Scheduled Posts")
        table_title.setObjectName("sectionTitle")
        table_layout.addWidget(table_title)

        self.queue_table = QTableWidget()
        self.queue_table.setColumnCount(6)
        self.queue_table.setHorizontalHeaderLabels([
            "ID", "Clip Title", "Platform", "Scheduled Date", "Status", "Retries/Errors"
        ])
        
        # Configure columns stretch
        header = self.queue_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.Stretch)

        table_layout.addWidget(self.queue_table)

        btn_row = QHBoxLayout()
        self.btn_delete_post = QPushButton("Delete Selected Job")
        self.btn_delete_post.clicked.connect(self.delete_selected_post)
        btn_row.addWidget(self.btn_delete_post)

        btn_refresh = QPushButton("Refresh Table")
        btn_refresh.clicked.connect(self.populate_queue)
        btn_row.addWidget(btn_refresh)
        table_layout.addLayout(btn_row)

        layout.addWidget(table_card, 2)

        # 3. Live Logs Card
        logs_card = QFrame()
        logs_card.setObjectName("glassCard")
        logs_layout = QVBoxLayout(logs_card)
        logs_layout.setContentsMargins(15, 15, 15, 15)

        logs_title = QLabel("Live Scheduler Logs")
        logs_title.setObjectName("sectionTitle")
        logs_layout.addWidget(logs_title)

        self.logs_list = QListWidget()
        self.logs_list.setObjectName("schedulerLogs")
        logs_layout.addWidget(self.logs_list)

        layout.addWidget(logs_card, 1)

        self.populate_queue()

    def populate_queue(self):
        """Queries queue items from database and populates table rows."""
        self.queue_table.setRowCount(0)
        posts = self.db_manager.get_queued_posts()
        
        for i, post in enumerate(posts):
            self.queue_table.insertRow(i)
            
            # Format row cells
            item_id = QTableWidgetItem(str(post["id"]))
            item_title = QTableWidgetItem(post["clip_title"])
            
            platform_clean = post["platform"].upper().replace("_", " ")
            item_platform = QTableWidgetItem(platform_clean)
            
            item_date = QTableWidgetItem(post["scheduled_time"])
            item_status = QTableWidgetItem(post["status"].upper())
            
            # Set background status colors
            if post["status"] == "posted":
                item_status.setForeground(Qt.green)
            elif post["status"] == "failed":
                item_status.setForeground(Qt.red)
            elif post["status"] == "posting":
                item_status.setForeground(Qt.yellow)
                
            error_details = post["error_message"] if post["error_message"] else f"Retries: {post['retry_count']}"
            item_error = QTableWidgetItem(error_details)
            
            # Set items
            self.queue_table.setItem(i, 0, item_id)
            self.queue_table.setItem(i, 1, item_title)
            self.queue_table.setItem(i, 2, item_platform)
            self.queue_table.setItem(i, 3, item_date)
            self.queue_table.setItem(i, 4, item_status)
            self.queue_table.setItem(i, 5, item_error)

    def toggle_scheduler(self):
        if self.scheduler_worker and self.scheduler_worker.isRunning():
            # Stop
            self.scheduler_worker.stop()
            self.scheduler_worker.wait()
            self.scheduler_worker = None
            
            self.scheduler_status.setText("Scheduler: INACTIVE")
            self.scheduler_status.setStyleSheet("color: #ff0055; font-weight: bold; font-size: 14px;")
            self.btn_toggle_scheduler.setText("Start Scheduler")
            self.log_message("Posting Scheduler stopped.")
        else:
            # Start
            self.scheduler_worker = self.scheduler_agent.start_scheduler()
            
            # Connect signals
            self.scheduler_worker.post_started.connect(self._on_post_started)
            self.scheduler_worker.post_progress.connect(self._on_post_progress)
            self.scheduler_worker.post_completed.connect(self._on_post_completed)
            self.scheduler_worker.status_msg.connect(self.log_message)
            
            self.scheduler_worker.start()
            
            self.scheduler_status.setText("Scheduler: ACTIVE")
            self.scheduler_status.setStyleSheet("color: #00ff66; font-weight: bold; font-size: 14px;")
            self.btn_toggle_scheduler.setText("Stop Scheduler")
            self.log_message("Posting Scheduler started in background.")

    def delete_selected_post(self):
        row = self.queue_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Warning", "Please select a scheduled post row from the table.")
            return

        post_id = int(self.queue_table.item(row, 0).text())
        confirm = QMessageBox.question(
            self, "Confirm Delete", 
            f"Are you sure you want to remove scheduled post ID {post_id} from queue?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            self.db_manager.delete_queued_post(post_id)
            self.populate_queue()
            self.log_message(f"Deleted queue post ID: {post_id}.")

    def _on_post_started(self, post):
        self.log_message(f"Starting upload for post ID {post['id']}: '{post['clip_title']}' to {post['platform'].upper()}...")
        self.populate_queue()

    def _on_post_progress(self, post_id, message):
        self.log_message(f"Post {post_id} Progress: {message}")

    def _on_post_completed(self, post_id, status_message):
        self.log_message(f"Post {post_id} Complete: {status_message}")
        self.populate_queue()

    def log_message(self, text):
        self.logs_list.addItem(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {text}")
        self.logs_list.scrollToBottom()

    def closeEvent(self, event):
        # Gracefully stop threads on tab closure
        if self.scheduler_worker and self.scheduler_worker.isRunning():
            self.scheduler_worker.stop()
            self.scheduler_worker.wait()
        event.accept()
