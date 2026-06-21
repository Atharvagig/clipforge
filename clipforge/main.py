import os
import sys
import logging
from PySide6.QtWidgets import QApplication
from clipforge.database.db_manager import DatabaseManager
from clipforge.ui.main_window import MainWindow

# Set up logging formatting
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("ClipForgeMain")

def main():
    logger.info("Initializing ClipForgeAI...")
    
    # 1. Initialize SQLite Database Schema
    try:
        db_manager = DatabaseManager()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.critical(f"Failed to initialize database: {e}")
        sys.exit(1)

    # 2. Launch PySide6 GUI App
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Fusion matches custom stylesheet dark look best
    
    # Instantiate Main Window
    window = MainWindow(db_manager)
    window.show()
    
    logger.info("Main Window displayed. Starting event loop...")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
