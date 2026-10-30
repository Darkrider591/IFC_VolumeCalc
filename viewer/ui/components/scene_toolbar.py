"""
Toolbar for 3D Viewport navigation and rendering modes.
"""
from typing import Optional
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QToolButton, QLabel
from PySide6.QtCore import Signal


class SceneToolbar(QWidget):
    view_iso_clicked = Signal()
    view_top_clicked = Signal()
    view_front_clicked = Signal()
    view_side_clicked = Signal()
    reset_view_clicked = Signal()
    toggle_edges_toggled = Signal(bool)
    toggle_xray_toggled = Signal(bool)
    toggle_defects_toggled = Signal(bool)
    isolate_clicked = Signal()
    show_all_clicked = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(6)

        # Camera view buttons
        lbl_views = QLabel("Виды:")
        lbl_views.setStyleSheet("color: #94A3B8; font-weight: 600; font-size: 11px;")
        layout.addWidget(lbl_views)

        self.btn_iso = QPushButton("Изометрия")
        self.btn_iso.setObjectName("secondaryBtn")
        self.btn_iso.setToolTip("Изометрический вид")
        self.btn_iso.clicked.connect(self.view_iso_clicked.emit)
        layout.addWidget(self.btn_iso)

        self.btn_top = QPushButton("Сверху")
        self.btn_top.setObjectName("secondaryBtn")
        self.btn_top.setToolTip("Вид сверху (план)")
        self.btn_top.clicked.connect(self.view_top_clicked.emit)
        layout.addWidget(self.btn_top)

        self.btn_front = QPushButton("Фасад")
        self.btn_front.setObjectName("secondaryBtn")
        self.btn_front.setToolTip("Вид спереди (фасад)")
        self.btn_front.clicked.connect(self.view_front_clicked.emit)
        layout.addWidget(self.btn_front)

        self.btn_reset = QPushButton("Сбросить вид")
        self.btn_reset.setObjectName("secondaryBtn")
        self.btn_reset.clicked.connect(self.reset_view_clicked.emit)
        layout.addWidget(self.btn_reset)

        layout.addSpacing(10)

        # Display mode toggles
        self.btn_edges = QPushButton("Рёбра")
        self.btn_edges.setCheckable(True)
        self.btn_edges.setChecked(True)
        self.btn_edges.setObjectName("secondaryBtn")
        self.btn_edges.setToolTip("Отображение граней и контуров")
        self.btn_edges.toggled.connect(self.toggle_edges_toggled.emit)
        layout.addWidget(self.btn_edges)

        self.btn_xray = QPushButton("Рентген (X-Ray)")
        self.btn_xray.setCheckable(True)
        self.btn_xray.setObjectName("secondaryBtn")
        self.btn_xray.setToolTip("Полупрозрачный режим для просмотра внутренних элементов")
        self.btn_xray.toggled.connect(self.toggle_xray_toggled.emit)
        layout.addWidget(self.btn_xray)

        self.btn_defects = QPushButton("⚠️ Выделить дефекты в 3D")
        self.btn_defects.setCheckable(True)
        self.btn_defects.setObjectName("secondaryBtn")
        self.btn_defects.setToolTip("Окрасить элементы без выбранного атрибута в красный цвет")
        self.btn_defects.toggled.connect(self.toggle_defects_toggled.emit)
        layout.addWidget(self.btn_defects)

        layout.addStretch()

        self.btn_isolate = QPushButton("Изолировать")
        self.btn_isolate.setObjectName("secondaryBtn")
        self.btn_isolate.setToolTip("Скрыть всё, кроме выбранного элемента")
        self.btn_isolate.clicked.connect(self.isolate_clicked.emit)
        layout.addWidget(self.btn_isolate)

        self.btn_show_all = QPushButton("Показать всё")
        self.btn_show_all.setObjectName("secondaryBtn")
        self.btn_show_all.clicked.connect(self.show_all_clicked.emit)
        layout.addWidget(self.btn_show_all)
