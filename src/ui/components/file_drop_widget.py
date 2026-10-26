"""
Drag & Drop file selection widget for IFC files.
Supports dragging files from Explorer or picking via native file dialog.
"""
import os
from typing import Optional
from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QWidget,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent


class FileDropWidget(QFrame):
    file_selected = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("dropZone")
        self.setAcceptDrops(True)
        self.setMinimumHeight(110)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 16, 20, 16)
        self.main_layout.setAlignment(Qt.AlignCenter)

        # Empty state layout
        self.empty_widget = QWidget()
        empty_layout = QVBoxLayout(self.empty_widget)
        empty_layout.setAlignment(Qt.AlignCenter)
        empty_layout.setSpacing(8)

        self.prompt_label = QLabel("Перетащите IFC-файл сюда или выберите на диске")
        self.prompt_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #94A3B8;")
        self.prompt_label.setAlignment(Qt.AlignCenter)
        empty_layout.addWidget(self.prompt_label)

        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignCenter)
        self.browse_btn = QPushButton("📁  Выбрать IFC файл...")
        self.browse_btn.setFixedWidth(200)
        self.browse_btn.clicked.connect(self._open_file_dialog)
        btn_layout.addWidget(self.browse_btn)
        empty_layout.addLayout(btn_layout)

        self.main_layout.addWidget(self.empty_widget)

        # Loaded state widget
        self.loaded_widget = QWidget()
        loaded_layout = QHBoxLayout(self.loaded_widget)
        loaded_layout.setContentsMargins(10, 5, 10, 5)

        file_icon_label = QLabel("🏗️")
        file_icon_label.setStyleSheet("font-size: 28px;")
        loaded_layout.addWidget(file_icon_label)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(3)
        self.file_name_label = QLabel("model.ifc")
        self.file_name_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #38BDF8;")
        info_layout.addWidget(self.file_name_label)

        self.file_details_label = QLabel("Схема: IFC4 | Размер: 12.4 МБ | Элементов: 1,420")
        self.file_details_label.setStyleSheet("font-size: 12px; color: #94A3B8;")
        info_layout.addWidget(self.file_details_label)
        loaded_layout.addLayout(info_layout)

        loaded_layout.addStretch()

        self.change_file_btn = QPushButton("Загрузить другой файл")
        self.change_file_btn.setObjectName("secondaryBtn")
        self.change_file_btn.clicked.connect(self._open_file_dialog)
        loaded_layout.addWidget(self.change_file_btn)

        self.main_layout.addWidget(self.loaded_widget)
        self.loaded_widget.setVisible(False)

    def _open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите IFC файл 3D модели",
            "",
            "BIM IFC Files (*.ifc);;All Files (*.*)",
        )
        if file_path:
            self.file_selected.emit(file_path)

    def set_file_loaded(self, file_name: str, size_mb: float, schema: str, total_elements: int):
        self.empty_widget.setVisible(False)
        self.loaded_widget.setVisible(True)
        self.file_name_label.setText(file_name)
        self.file_details_label.setText(
            f"Схема: {schema}  •  Размер: {size_mb} МБ  •  Всего элементов: {total_elements:,}"
        )

    def reset(self):
        self.empty_widget.setVisible(True)
        self.loaded_widget.setVisible(False)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if any(u.toLocalFile().lower().endswith(".ifc") for u in urls):
                event.acceptProposedAction()
                self.setStyleSheet("border-color: #3B82F6; background-color: rgba(59, 130, 246, 0.08);")

    def dragLeaveEvent(self, event):
        self.setStyleSheet("")
        event.accept()

    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet("")
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith(".ifc") and os.path.exists(file_path):
                self.file_selected.emit(file_path)
                event.acceptProposedAction()
                break
