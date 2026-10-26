"""
Background worker thread for non-blocking IFC parsing.
Emits progress and completion signals to keep the UI responsive.
"""
from PySide6.QtCore import QThread, Signal
from src.core.ifc_parser import parse_ifc_file, CancellationToken, CancelledException


class ParseWorker(QThread):
    progress = Signal(int, str)       # (percentage, status_text)
    finished = Signal(object)         # (ParseResult)
    error = Signal(str)               # (error_message)
    cancelled = Signal()

    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.cancel_token = CancellationToken()

    def cancel(self):
        self.cancel_token.cancel()

    def run(self):
        try:
            def on_progress(pct: int, msg: str):
                self.progress.emit(pct, msg)

            result = parse_ifc_file(
                self.file_path,
                progress_callback=on_progress,
                cancel_token=self.cancel_token,
            )
            self.finished.emit(result)
        except CancelledException:
            self.cancelled.emit()
        except Exception as e:
            self.error.emit(str(e))
