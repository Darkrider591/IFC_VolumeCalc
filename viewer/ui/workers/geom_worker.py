"""
Background worker thread for 3D geometry tessellation.
Keeps UI completely responsive during heavy CAD solid meshing.
"""
from PySide6.QtCore import QThread, Signal
from src.core.ifc_parser import CancellationToken, CancelledException
from viewer.core.geometry_loader import extract_geometry, LoadedGeometry


class GeometryWorker(QThread):
    progress = Signal(int, str)
    finished = Signal(object)  # LoadedGeometry
    error = Signal(str)
    cancelled = Signal()

    def __init__(self, file_path: str, parent=None, num_threads: int = 4):
        super().__init__(parent)
        self.file_path = file_path
        self.num_threads = num_threads
        self.cancel_token = CancellationToken()

    def cancel(self):
        self.cancel_token.cancel()

    def run(self):
        try:
            def on_progress(pct: int, msg: str):
                self.progress.emit(pct, msg)

            geometry = extract_geometry(
                self.file_path,
                progress_callback=on_progress,
                cancel_token=self.cancel_token,
                num_threads=self.num_threads,
            )
            self.finished.emit(geometry)
        except CancelledException:
            self.cancelled.emit()
        except Exception as e:
            self.error.emit(str(e))
