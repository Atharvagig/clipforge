from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QTextEdit, QProgressBar, QMessageBox)
from PySide6.QtCore import Qt, QRect, QPoint, QSize
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QFont
from clipforge.agents.analytics_agent import AnalyticsAgent

class CustomBarChart(QWidget):
    """Draws a premium glassmorphic bar chart using QPainter."""
    def __init__(self, data=None):
        super().__init__()
        self.data = data or {"YT Shorts": 1500, "TikTok": 2400, "IG Reels": 1900}
        self.setMinimumHeight(180)

    def set_data(self, data):
        self.data = data
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        margin = 35

        # Draw grid lines
        painter.setPen(QPen(QColor(255, 255, 255, 15), 1))
        for i in range(4):
            grid_y = margin + i * (h - margin * 2) // 3
            painter.drawLine(margin, grid_y, w - margin, grid_y)

        # Compute max scale
        max_val = max(self.data.values()) if self.data and max(self.data.values()) > 0 else 100
        bar_count = len(self.data)
        if bar_count == 0:
            return

        bar_width = min(60, (w - margin * 2) // (bar_count * 2))
        spacing = (w - margin * 2 - (bar_width * bar_count)) // (bar_count + 1)

        # Draw bars
        font = QFont("Segoe UI", 9)
        painter.setFont(font)

        for idx, (platform, val) in enumerate(self.data.items()):
            bar_h = int((val / max_val) * (h - margin * 2))
            
            x = margin + spacing + idx * (bar_width + spacing)
            y = h - margin - bar_h

            # Draw bar with gradient look (neon cyan to purple)
            rect = QRect(x, y, bar_width, bar_h)
            brush = QBrush(QColor(0, 240, 255, 120))
            if idx % 2 == 1:
                brush = QBrush(QColor(168, 85, 247, 120))
                
            painter.setPen(QPen(QColor(255, 255, 255, 30), 1))
            painter.setBrush(brush)
            painter.drawRoundedRect(rect, 4, 4)

            # Draw values above bar
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(QRect(x - 10, y - 20, bar_width + 20, 20), Qt.AlignCenter, f"{val}")

            # Draw Labels below bar
            painter.setPen(QColor(148, 163, 184))
            painter.drawText(QRect(x - 20, h - margin + 5, bar_width + 40, 20), Qt.AlignCenter, platform)


class CustomLineChart(QWidget):
    """Draws a retention decay curve using QPainter."""
    def __init__(self, data=None):
        super().__init__()
        # Default retention decay (x: seconds, y: percent retention)
        self.data = data or [(0, 100), (3, 85), (8, 75), (15, 68), (30, 60), (45, 52), (60, 48)]
        self.setMinimumHeight(180)

    def set_data(self, data):
        self.data = data
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        margin = 35

        # Draw grid axes lines
        painter.setPen(QPen(QColor(255, 255, 255, 15), 1))
        for i in range(5):
            pct_label = 100 - i * 20
            grid_y = margin + i * (h - margin * 2) // 4
            painter.drawLine(margin, grid_y, w - margin, grid_y)
            # Label
            painter.setPen(QColor(148, 163, 184))
            painter.drawText(5, grid_y + 5, f"{pct_label}%")
            painter.setPen(QPen(QColor(255, 255, 255, 15), 1))

        if not self.data:
            return

        # Map data coordinates to screen points
        points = []
        max_x = max(d[0] for d in self.data) if self.data else 60
        
        for sec, pct in self.data:
            x = int(margin + (sec / max_x) * (w - margin * 2 - 10))
            y = int(margin + ((100 - pct) / 100) * (h - margin * 2))
            points.append(QPoint(x, y))

        # Draw smooth line
        pen = QPen(QColor(0, 240, 255), 2.5)
        painter.setPen(pen)
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i+1])

        # Draw dots at key nodes
        painter.setBrush(QBrush(QColor(168, 85, 247)))
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        for p in points:
            painter.drawEllipse(p, 4, 4)

        # Draw timeline axis text
        painter.setPen(QColor(148, 163, 184))
        painter.drawText(margin, h - 10, "0s")
        painter.drawText(w - margin - 20, h - 10, f"{max_x}s")
        painter.drawText(w // 2 - 20, h - 10, "Timeline")


class AnalyticsTab(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.analytics_agent = AnalyticsAgent(db_manager)
        
        self.active_worker = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # 1. Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Creator Performance Analytics")
        title_label.setObjectName("headerTitle")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        btn_recalc = QPushButton("Update Advisor Data")
        btn_recalc.setObjectName("primaryActionButton")
        btn_recalc.clicked.connect(self.calculate_analytics)
        header_layout.addWidget(btn_recalc)

        layout.addLayout(header_layout)

        # 2. Charts Row
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(20)

        # Left Chart Panel
        bar_card = QFrame()
        bar_card.setObjectName("glassCard")
        bar_layout = QVBoxLayout(bar_card)
        bar_layout.setContentsMargins(15, 15, 15, 15)
        bar_layout.addWidget(QLabel("Views count per platform"))
        
        self.bar_chart = CustomBarChart()
        bar_layout.addWidget(self.bar_chart)
        charts_layout.addWidget(bar_card, 1)

        # Right Chart Panel
        line_card = QFrame()
        line_card.setObjectName("glassCard")
        line_layout = QVBoxLayout(line_card)
        line_layout.setContentsMargins(15, 15, 15, 15)
        line_layout.addWidget(QLabel("Avg audience retention decay (%)"))
        
        self.line_chart = CustomLineChart()
        line_layout.addWidget(self.line_chart)
        charts_layout.addWidget(line_card, 1)

        layout.addLayout(charts_layout)

        # 3. AI Insights Advisor Panel
        insights_card = QFrame()
        insights_card.setObjectName("glassCard")
        insights_layout = QVBoxLayout(insights_card)
        insights_layout.setContentsMargins(15, 15, 15, 15)

        insights_title = QLabel("Gemini AI Analytics Advisor")
        insights_title.setObjectName("sectionTitle")
        insights_layout.addWidget(insights_title)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        insights_layout.addWidget(self.progress_bar)

        self.insights_viewer = QTextEdit()
        self.insights_viewer.setReadOnly(True)
        self.insights_viewer.setPlaceholderText("Click 'Update Advisor Data' to retrieve performance summaries.")
        insights_layout.addWidget(self.insights_viewer)

        layout.addWidget(insights_card)
        
        self.calculate_analytics()

    def calculate_analytics(self):
        if self.active_worker and self.active_worker.isRunning():
            return
            
        self.progress_bar.setValue(0)
        
        # Instantiate worker thread
        self.active_worker = self.analytics_agent.fetch_insights()
        self.active_worker.progress.connect(self.progress_bar.setValue)
        self.active_worker.finished.connect(self._on_analytics_finished)
        self.active_worker.error.connect(self._on_error)
        
        self.active_worker.start()

    def _on_analytics_finished(self, result):
        self.progress_bar.setValue(100)
        
        # 1. Update charts values
        aggregates = self.db_manager.get_aggregated_analytics()
        platform_views = {}
        for a in aggregates:
            # Map labels
            p_name = a["platform"].replace("_", " ").title()
            platform_views[p_name] = a["total_views"]
            
        if platform_views:
            self.bar_chart.set_data(platform_views)

        # 2. Update insights summary viewer
        self.insights_viewer.setMarkdown(result["summary"])

    def _on_error(self, err):
        QMessageBox.critical(self, "Error", f"Could not retrieve creator insights: {err}")
