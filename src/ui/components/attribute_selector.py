"""
Searchable and categorized attribute selection widget.
Allows searching and selecting IFC properties, quantities, and direct entity attributes.
"""
from typing import Dict, List, Optional
from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
    QComboBox,
    QWidget,
)
from PySide6.QtCore import Qt, Signal
from src.core.models import AttributeMetadata, DataType, PropertySource


class AttributeSelector(QFrame):
    attribute_selected = Signal(str)  # Emits full_path of selected attribute

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setMinimumWidth(320)

        self._attributes: Dict[str, AttributeMetadata] = {}
        self._current_selected_key: Optional[str] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Header title
        header_layout = QHBoxLayout()
        title_label = QLabel("Атрибуты модели")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #F8FAFC;")
        header_layout.addWidget(title_label)

        self.count_badge = QLabel("0")
        self.count_badge.setObjectName("kpiBadgeNeutral")
        header_layout.addWidget(self.count_badge)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Search box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Поиск свойства или набора...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._apply_filter)
        layout.addWidget(self.search_input)

        # Filter row: Source + Data Type
        filters_layout = QHBoxLayout()
        filters_layout.setSpacing(6)

        self.source_combo = QComboBox()
        self.source_combo.addItems([
            "Все источники",
            "Количества (Qto)",
            "Наборы свойств (Pset)",
            "Прямые атрибуты",
        ])
        self.source_combo.currentIndexChanged.connect(self._apply_filter)
        filters_layout.addWidget(self.source_combo)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["Все типы", "Только числа", "Только текст", "Только Да/Нет"])
        self.type_combo.currentIndexChanged.connect(self._apply_filter)
        filters_layout.addWidget(self.type_combo)

        layout.addLayout(filters_layout)

        # Tree Widget for attributes
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Атрибут / Набор свойств", "Тип", "Найдено"])
        self.tree.setColumnWidth(0, 180)
        self.tree.setColumnWidth(1, 65)
        self.tree.setColumnWidth(2, 70)
        self.tree.setRootIsDecorated(False)
        self.tree.setAlternatingRowColors(True)
        self.tree.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.tree)

    def set_attributes(self, attributes: Dict[str, AttributeMetadata], default_key: Optional[str] = None):
        self._attributes = attributes
        self.count_badge.setText(str(len(attributes)))
        self._populate_tree()

        # Select default attribute (prefer a quantity or volume/area if available, else first)
        key_to_select = default_key
        if not key_to_select and attributes:
            # Look for volume or area first
            for k in attributes:
                if any(term in k.lower() for term in ["volume", "area", "length", "объем", "площадь"]):
                    key_to_select = k
                    break
            if not key_to_select:
                # Or pick first numeric
                for k, v in attributes.items():
                    if v.data_type == DataType.NUMERIC:
                        key_to_select = k
                        break
            if not key_to_select:
                key_to_select = next(iter(attributes.keys()))

        if key_to_select:
            self.select_attribute(key_to_select)

    def select_attribute(self, full_path: str):
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item.data(0, Qt.UserRole) == full_path:
                self.tree.setCurrentItem(item)
                break

    def _populate_tree(self):
        self.tree.clear()
        search_txt = self.search_input.text().strip().lower()
        source_idx = self.source_combo.currentIndex()
        type_idx = self.type_combo.currentIndex()

        # Sort attributes: Quantities first, then Psets, then Direct
        sorted_attrs = sorted(
            self._attributes.values(),
            key=lambda a: (
                0 if a.source == PropertySource.QUANTITY_SET else
                1 if a.source == PropertySource.PROPERTY_SET else 2,
                a.full_path.lower()
            )
        )

        for attr in sorted_attrs:
            # Check search filter
            if search_txt:
                match_name = search_txt in attr.display_name.lower()
                match_path = search_txt in attr.full_path.lower()
                if not (match_name or match_path):
                    continue

            # Check source filter
            if source_idx == 1 and attr.source != PropertySource.QUANTITY_SET:
                continue
            if source_idx == 2 and attr.source != PropertySource.PROPERTY_SET:
                continue
            if source_idx == 3 and attr.source != PropertySource.DIRECT:
                continue

            # Check type filter
            if type_idx == 1 and attr.data_type != DataType.NUMERIC:
                continue
            if type_idx == 2 and attr.data_type != DataType.TEXT:
                continue
            if type_idx == 3 and attr.data_type != DataType.BOOLEAN:
                continue

            item = QTreeWidgetItem()
            item.setData(0, Qt.UserRole, attr.full_path)

            # Display name & set
            if attr.pset_name:
                item.setText(0, f"{attr.display_name} ({attr.pset_name})")
            else:
                item.setText(0, attr.display_name)
            item.setToolTip(0, attr.full_path)

            # Type
            type_str = "Число" if attr.data_type == DataType.NUMERIC else "Да/Нет" if attr.data_type == DataType.BOOLEAN else "Текст"
            item.setText(1, type_str)

            # Presence
            item.setText(2, f"{attr.present_count}")
            item.setTextAlignment(2, Qt.AlignRight)

            self.tree.addTopLevelItem(item)

    def _apply_filter(self):
        self._populate_tree()

    def _on_selection_changed(self):
        items = self.tree.selectedItems()
        if items:
            key = items[0].data(0, Qt.UserRole)
            if key and key != self._current_selected_key:
                self._current_selected_key = key
                self.attribute_selected.emit(key)
