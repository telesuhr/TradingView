"""Main entry point for LME Copper Trading System."""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.ui import TradingSystemMainWindow

logger = logging.getLogger(__name__)


def main():
    """Main application entry point."""
    # Create QApplication
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("LME Copper Trading System")
    app.setOrganizationName("Trading Analytics")
    
    # Enable high DPI support
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # Create and show main window
    window = TradingSystemMainWindow()
    window.show()
    
    logger.info("LME Copper Trading System started")
    
    # Run application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()