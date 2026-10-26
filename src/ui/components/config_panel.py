"""
Configuration toolbar for configuring the summary/pivot table.
Includes grouping mode selector, search, filters, and export buttons.
"""
from typing import Optional
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QLineEdit,
    QPushButton,
    QWidget,
)
from PySide6.QtCore import Signal
from src.core.models import GroupingMode


class ConfigPanel(QFrame):
    grouping_changed = Signal(object)      # GroupingMode
    search_changed = Signal(str)           # search text
    filter_presence_changed = Signal(str)  # 'all', 'only_present', 'only_missing'
    export_excel_requested = Signal()
    export_csv_requested = Signal()
    show_missing_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("card")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)

        # 1. Grouping selector
        lbl_group = QLabel("Группировка:")
        lbl_group.setStyleSheet("font-weight: 600; color: #94A3B8;")
        layout.addWidget(lbl_group)

        self.grouping_combo = QComboBox()
        self.grouping_combo.addItem(GroupingMode.BY_CLASS.value, GroupingMode.BY_CLASS)
        self.grouping_combo.addItem(GroupingMode.BY_STOREY.value, GroupingMode.BY_STOREY)
        self.grouping_combo.addItem(GroupingMode.BY_TYPE.value, GroupingMode.BY_TYPE)
        self.grouping_combo.addItem(GroupingMode.NO_GROUPING.value, GroupingMode.NO_GROUPING)
        self.grouping_combo.currentIndexChanged.connect(self._on_grouping_changed)
        layout.addWidget(self.grouping_combo)

        # 2. Presence filter
        lbl_filter = QLabel("Фильтр:")
        lbl_filter.setStyleSheet("font-weight: 600; color: #94A3B8;")
        layout.addWidget(lbl_filter)

        self.filter_combo = QComboBox()
        self.filter_combo.addItem("Все элементы", "all")
        self.filter_combo.addItem("Только с атрибутом", "only_present")
        self.filter_combo.addItem("Только БЕЗ атрибута", "only_missing")
        self.filter_combo.currentIndexChanged.connect(self._on_filter_changed)
        layout.addWidget(self.filter_combo)

        # 3. Search in table
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Поиск в таблице...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setMinimumWidth(180)
        self.search_input.textChanged.connect(self.search_changed.emit)
        layout.addWidget(self.search_input)

        layout.addStretch()

        # 4. Action buttons
        self.missing_btn = QPushButton("⚠️ Без атрибута")
        self.missing_btn.setObjectName("secondaryBtn")
        self.missing_btn.setToolTip("Посмотреть список элементов с отсутствующим свойством")
        self.missing_btn.clicked.connect(self.show_missing_requested.emit)
        layout.addWidget(self.missing_btn)

        self.export_excel_btn = QPushButton("📊 Экспорт в Excel")
        self.export_excel_btn.setObjectName("successBtn")
        self.export_excel_btn.setToolTip("Выгрузить сводную таблицу и дефекты в .xlsx файл")
        self.export_excel_btn.clicked.connect(self.export_excel_requested.emit)
        layout.addWidget(self.export_excel_btn)

        self.export_csv_btn = QPushButton("📄 CSV")
        self.export_csv_btn.setObjectName("secondaryBtn")
        self.export_csv_btn.setToolTip("Выгрузить в CSV формат")
        self.export_csv_btn.clicked.connect(self.export_csv_requested.emit)
        layout.addWidget(self.export_csv_btn)

    def _on_grouping_changed(self):
        mode = self.grouping_combo.currentData()
        self.grouping_changed.emit(mode)

    def _on_filter_changed(self):
        f_val = self.filter_combo.currentData()
        self.filter_presence_changed.emit(f_val)
