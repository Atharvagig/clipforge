from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QComboBox, QFrame, 
                             QMessageBox, QScrollArea)
from PySide6.QtCore import Qt

class SettingsTab(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.init_ui()

    def init_ui(self):
        # We wrap in a scroll area just in case window size is small
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(20, 20, 20, 20)
        scroll_layout.setSpacing(20)

        # 1. Header
        title_label = QLabel("Global System Settings")
        title_label.setObjectName("headerTitle")
        scroll_layout.addWidget(title_label)

        # 2. Hardware / VRAM Optimization Card
        hw_card = QFrame()
        hw_card.setObjectName("glassCard")
        hw_layout = QVBoxLayout(hw_card)
        hw_layout.setContentsMargins(15, 15, 15, 15)
        hw_layout.setSpacing(10)

        hw_title = QLabel("Hardware & Model Optimization")
        hw_title.setObjectName("sectionTitle")
        hw_layout.addWidget(hw_title)

        # CUDA Check Label
        self.cuda_status_lbl = QLabel("CUDA GPU Status: Checking...")
        self.cuda_status_lbl.setStyleSheet("font-weight: bold; color: #a855f7;")
        hw_layout.addWidget(self.cuda_status_lbl)

        # Model select
        row_model = QHBoxLayout()
        row_model.addWidget(QLabel("Whisper Model Size:"))
        self.combo_model = QComboBox()
        self.combo_model.addItems(["tiny", "base", "small"])
        row_model.addWidget(self.combo_model)
        hw_layout.addLayout(row_model)

        # Device select
        row_dev = QHBoxLayout()
        row_dev.addWidget(QLabel("Computation Device:"))
        self.combo_device = QComboBox()
        self.combo_device.addItems(["cuda", "cpu"])
        row_dev.addWidget(self.combo_device)
        hw_layout.addLayout(row_dev)

        # Compute type
        row_comp = QHBoxLayout()
        row_comp.addWidget(QLabel("Quantized Compute Type:"))
        self.combo_compute = QComboBox()
        self.combo_compute.addItems(["float16", "int8"])
        row_comp.addWidget(self.combo_compute)
        hw_layout.addLayout(row_comp)

        # VRAM limit
        row_vram = QHBoxLayout()
        row_vram.addWidget(QLabel("Max VRAM allocation boundary (GB):"))
        self.edit_vram = QLineEdit()
        self.edit_vram.setPlaceholderText("e.g. 5.0")
        row_vram.addWidget(self.edit_vram)
        hw_layout.addLayout(row_vram)

        scroll_layout.addWidget(hw_card)

        # 3. Gemini API Credentials Card
        api_card = QFrame()
        api_card.setObjectName("glassCard")
        api_layout = QVBoxLayout(api_card)
        api_layout.setContentsMargins(15, 15, 15, 15)
        api_layout.setSpacing(10)

        api_title = QLabel("Google Gemini API Credentials")
        api_title.setObjectName("sectionTitle")
        api_layout.addWidget(api_title)

        row_api = QHBoxLayout()
        row_api.addWidget(QLabel("Gemini API Key:"))
        self.edit_api_key = QLineEdit()
        self.edit_api_key.setEchoMode(QLineEdit.Password)
        self.edit_api_key.setPlaceholderText("Paste your AI Studio API key here...")
        row_api.addWidget(self.edit_api_key)
        api_layout.addLayout(row_api)

        scroll_layout.addWidget(api_card)

        # 4. Social OAuth Client Credentials Card
        social_card = QFrame()
        social_card.setObjectName("glassCard")
        social_layout = QVBoxLayout(social_card)
        social_layout.setContentsMargins(15, 15, 15, 15)
        social_layout.setSpacing(10)

        social_title = QLabel("Platform Integrations (OAuth2)")
        social_title.setObjectName("sectionTitle")
        social_layout.addWidget(social_title)

        row_cid = QHBoxLayout()
        row_cid.addWidget(QLabel("YouTube Client ID:"))
        self.edit_client_id = QLineEdit()
        self.edit_client_id.setPlaceholderText("Enter YouTube API Client ID...")
        row_cid.addWidget(self.edit_client_id)
        social_layout.addLayout(row_cid)

        row_sec = QHBoxLayout()
        row_sec.addWidget(QLabel("YouTube Client Secret:"))
        self.edit_client_secret = QLineEdit()
        self.edit_client_secret.setEchoMode(QLineEdit.Password)
        self.edit_client_secret.setPlaceholderText("Enter YouTube API Client Secret...")
        row_sec.addWidget(self.edit_client_secret)
        social_layout.addLayout(row_sec)

        scroll_layout.addWidget(social_card)

        # 5. Save Button
        self.btn_save = QPushButton("Save Configurations")
        self.btn_save.setObjectName("primaryActionButton")
        self.btn_save.clicked.connect(self.save_settings)
        scroll_layout.addWidget(self.btn_save)
        
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

        self.load_settings()
        self.check_cuda_status()

    def check_cuda_status(self):
        """Dynamic check of PyTorch CUDA availability."""
        try:
            import torch
            available = torch.cuda.is_available()
            if available:
                device_name = torch.cuda.get_device_name(0)
                self.cuda_status_lbl.setText(f"CUDA GPU Status: AVAILABLE - {device_name}")
                self.cuda_status_lbl.setStyleSheet("color: #00ff66; font-weight: bold;")
            else:
                self.cuda_status_lbl.setText("CUDA GPU Status: UNAVAILABLE (Running CPU models)")
                self.cuda_status_lbl.setStyleSheet("color: #ffaa00; font-weight: bold;")
        except ImportError:
            self.cuda_status_lbl.setText("CUDA GPU Status: PyTorch library is not installed.")
            self.cuda_status_lbl.setStyleSheet("color: #ff0055; font-weight: bold;")

    def load_settings(self):
        # Retrieve settings values from DB
        api_key = self.db_manager.get_setting("gemini_api_key", "")
        whisper_model = self.db_manager.get_setting("whisper_model", "base")
        whisper_device = self.db_manager.get_setting("whisper_device", "cuda")
        whisper_compute = self.db_manager.get_setting("whisper_compute_type", "float16")
        max_vram = self.db_manager.get_setting("max_vram_gb", "5.0")
        client_id = self.db_manager.get_setting("youtube_client_id", "")
        client_secret = self.db_manager.get_setting("youtube_client_secret", "")

        self.edit_api_key.setText(api_key)
        self.edit_vram.setText(max_vram)
        self.edit_client_id.setText(client_id)
        self.edit_client_secret.setText(client_secret)

        # Set combos
        self.combo_model.setCurrentText(whisper_model)
        self.combo_device.setCurrentText(whisper_device)
        self.combo_compute.setCurrentText(whisper_compute)

    def save_settings(self):
        # Save inputs to database
        self.db_manager.set_setting("gemini_api_key", self.edit_api_key.text().strip())
        self.db_manager.set_setting("whisper_model", self.combo_model.currentText())
        self.db_manager.set_setting("whisper_device", self.combo_device.currentText())
        self.db_manager.set_setting("whisper_compute_type", self.combo_compute.currentText())
        self.db_manager.set_setting("max_vram_gb", self.edit_vram.text().strip())
        self.db_manager.set_setting("youtube_client_id", self.edit_client_id.text().strip())
        self.db_manager.set_setting("youtube_client_secret", self.edit_client_secret.text().strip())

        QMessageBox.information(self, "Success", "Application configuration saved successfully!")
