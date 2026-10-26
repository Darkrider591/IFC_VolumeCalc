"""
Application entrypoint for IFC BIM Attribute Parser & Aggregator.
"""
import sys
import os

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from src.ui.main_window import MainWindow


def main():
    # Setup High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("IFC_VolumeCalc")
    app.setApplicationDisplayName("IFC_VolumeCalc")
    app.setOrganizationName("Antigravity BIM")

    # Set default clean UI font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()

    # If file passed via CLI or "Open with...", open it immediately
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]) and sys.argv[1].lower().endswith(".ifc"):
        window._start_parsing(sys.argv[1])

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
