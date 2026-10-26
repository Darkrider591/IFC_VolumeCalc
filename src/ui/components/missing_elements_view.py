"""
View for inspecting elements that lack the selected attribute (BIM defects).
Shows GlobalId, IFC Class, Name, Storey, and allows copying GUIDs for BIM authoring tools.
"""
from typing import Dict, List, Optional
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QApplication,
    QMessageBox,
)
from PySide6.QtCore import Qt


class MissingElementsView(QWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self._all_elements: List[Dict[str, str]] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Top toolbar
        toolbar = QHBoxLayout()
        self.title_label = QLabel("Элементы без атрибута: 0")
        self.title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #F87171;")
        toolbar.addWidget(self.title_label)

        toolbar.addStretch()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Поиск по GUID, имени, классу...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setFixedWidth(260)
        self.search_input.textChanged.connect(self._filter_table)
        toolbar.addWidget(self.search_input)

        self.copy_btn = QPushButton("📋 Копировать выбранные GUID")
        self.copy_btn.setObjectName("secondaryBtn")
        self.copy_btn.clicked.connect(self._copy_selected_guids)
        toolbar.addWidget(self.copy_btn)

        layout.addLayout(toolbar)

        # Table
        self.table = QTableWidget()
        headers = ["№", "GlobalId (GUID)", "Класс IFC", "Имя элемента", "Марка / Tag", "Этаж / Уровень", "Тип элемента"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

    def set_missing_elements(self, elements: List[Dict[str, str]], attr_name: str = ""):
        self._all_elements = elements
        count = len(elements)
        self.title_label.setText(f"Элементы без атрибута '{attr_name}': {count:,} шт.")
        self._populate_table(elements)

    def _populate_table(self, elements: List[Dict[str, str]]):
        self.table.setRowCount(len(elements))
        for idx, elem in enumerate(elements):
            item_num = QTableWidgetItem(str(idx + 1))
            item_num.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(idx, 0, item_num)

            item_guid = QTableWidgetItem(elem.get("global_id", ""))
            self.table.setItem(idx, 1, item_guid)

            item_class = QTableWidgetItem(elem.get("ifc_class", ""))
            self.table.setItem(idx, 2, item_class)

            item_name = QTableWidgetItem(elem.get("name", ""))
            self.table.setItem(idx, 3, item_name)

            item_tag = QTableWidgetItem(elem.get("tag", ""))
            self.table.setItem(idx, 4, item_tag)

            item_storey = QTableWidgetItem(elem.get("storey", ""))
            self.table.setItem(idx, 5, item_storey)

            item_type = QTableWidgetItem(elem.get("element_type", ""))
            self.table.setItem(idx, 6, item_type)

        self.table.resizeColumnsToContents()
        self.table.setColumnWidth(1, 190)

    def _filter_table(self):
        query = self.search_input.text().strip().lower()
        if not query:
            filtered = self._all_elements
        else:
            filtered = [
                e for e in self._all_elements
                if any(query in str(v).lower() for v in e.values())
            ]
        self._populate_table(filtered)

    def _copy_selected_guids(self):
        selected_rows = sorted(set(idx.row() for idx in self.table.selectedIndexes()))
        if not selected_rows:
            QMessageBox.information(self, "Копирование", "Пожалуйста, выделите строки для копирования GUID.")
            return

        guids = []
        for r in selected_rows:
            guid_item = self.table.item(r, 1)
            if guid_item and guid_item.text():
                guids.append(guid_item.text())

        text_to_copy = "\n".join(guids)
        QApplication.clipboard().setText(text_to_copy)
        QMessageBox.information(
            self,
            "Успешно скопировано",
            f"Скопировано {len(guids)} GlobalId в буфер обмена.\nИх можно вставить в поле поиска/фильтрации BIM-программы."
        )
