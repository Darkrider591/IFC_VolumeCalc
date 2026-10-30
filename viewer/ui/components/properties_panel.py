"""
Properties Inspector Panel.
Displays detailed attributes, Property Sets (Pset), and Quantity Sets (Qto)
for the selected BIM element with one-click GUID copying and search.
"""
from typing import Any, Dict, Optional
from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QApplication,
    QMessageBox,
    QWidget,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QBrush, QFont
from src.core.models import ElementRecord


class PropertiesPanel(QFrame):
    isolate_requested = Signal(str)  # GlobalId
    focus_requested = Signal(str)    # GlobalId

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setMinimumWidth(320)

        self.current_record: Optional[ElementRecord] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Свойства элемента")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #F8FAFC;")
        header_layout.addWidget(title_label)

        self.class_badge = QLabel("Не выбран")
        self.class_badge.setObjectName("kpiBadgeNeutral")
        header_layout.addWidget(self.class_badge)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Empty state prompt
        self.empty_label = QLabel("Кликните по любому элементу в 3D сцене для просмотра его свойств")
        self.empty_label.setStyleSheet("color: #94A3B8; font-style: italic; padding: 20px 0;")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setWordWrap(True)
        layout.addWidget(self.empty_label)

        # Details container
        self.details_widget = QWidget()
        details_layout = QVBoxLayout(self.details_widget)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(8)

        # Basic Info Card
        info_card = QFrame()
        info_card.setObjectName("card")
        info_card.setStyleSheet("background-color: #0F172A; border-radius: 6px; padding: 6px;")
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(8, 8, 8, 8)
        info_layout.setSpacing(4)

        # Name row
        self.name_label = QLabel("—")
        self.name_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #38BDF8;")
        self.name_label.setWordWrap(True)
        info_layout.addWidget(self.name_label)

        # GUID row + copy button
        guid_layout = QHBoxLayout()
        guid_lbl = QLabel("GUID:")
        guid_lbl.setStyleSheet("color: #94A3B8; font-size: 11px;")
        guid_layout.addWidget(guid_lbl)

        self.guid_label = QLabel("—")
        self.guid_label.setStyleSheet("color: #F8FAFC; font-size: 11px; font-family: monospace;")
        self.guid_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        guid_layout.addWidget(self.guid_label)
        guid_layout.addStretch()

        self.copy_guid_btn = QPushButton("📋")
        self.copy_guid_btn.setToolTip("Скопировать GlobalId (GUID)")
        self.copy_guid_btn.setFixedSize(26, 24)
        self.copy_guid_btn.setObjectName("secondaryBtn")
        self.copy_guid_btn.clicked.connect(self._copy_guid)
        guid_layout.addWidget(self.copy_guid_btn)
        info_layout.addLayout(guid_layout)

        # Storey and Type rows
        self.storey_label = QLabel("Этаж: —")
        self.storey_label.setStyleSheet("color: #CBD5E1; font-size: 11px;")
        info_layout.addWidget(self.storey_label)

        self.type_label = QLabel("Тип: —")
        self.type_label.setStyleSheet("color: #CBD5E1; font-size: 11px;")
        self.type_label.setWordWrap(True)
        info_layout.addWidget(self.type_label)

        details_layout.addWidget(info_card)

        # Action buttons for selected element
        elem_actions = QHBoxLayout()
        self.focus_btn = QPushButton("🎯 Приблизить")
        self.focus_btn.setObjectName("secondaryBtn")
        self.focus_btn.clicked.connect(self._on_focus_clicked)
        elem_actions.addWidget(self.focus_btn)

        self.isolate_btn = QPushButton("🔍 Изолировать")
        self.isolate_btn.setObjectName("secondaryBtn")
        self.isolate_btn.clicked.connect(self._on_isolate_clicked)
        elem_actions.addWidget(self.isolate_btn)
        details_layout.addLayout(elem_actions)

        # Search inside properties
        self.prop_search = QLineEdit()
        self.prop_search.setPlaceholderText("🔍 Поиск свойства или значения...")
        self.prop_search.setClearButtonEnabled(True)
        self.prop_search.textChanged.connect(self._filter_properties)
        details_layout.addWidget(self.prop_search)

        # Properties Tree Widget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Параметр / Набор", "Значение"])
        self.tree.setColumnWidth(0, 160)
        self.tree.setAlternatingRowColors(True)
        details_layout.addWidget(self.tree)

        layout.addWidget(self.details_widget)
        self.details_widget.setVisible(False)

    def set_element(self, record: Optional[ElementRecord]):
        """Populate inspector with the attributes of the selected element."""
        self.current_record = record

        if not record:
            self.empty_label.setVisible(True)
            self.details_widget.setVisible(False)
            self.class_badge.setText("Не выбран")
            return

        self.empty_label.setVisible(False)
        self.details_widget.setVisible(True)

        self.class_badge.setText(record.ifc_class)
        self.name_label.setText(record.name or f"[{record.ifc_class}]")
        self.guid_label.setText(record.global_id)
        self.storey_label.setText(f"Этаж: {record.storey}")
        self.type_label.setText(f"Тип: {record.element_type}")

        self._populate_tree(record.properties)

    def _populate_tree(self, properties: Dict[str, Any]):
        self.tree.clear()
        query = self.prop_search.text().strip().lower()

        # Group properties by PropertySet / Category
        grouped: Dict[str, Dict[str, Any]] = {}
        for full_path, val in properties.items():
            if "." in full_path:
                pset, prop_name = full_path.split(".", 1)
            else:
                pset = "Общие"
                prop_name = full_path

            if pset not in grouped:
                grouped[pset] = {}
            grouped[pset][prop_name] = val

        # Populate top-level pset nodes and child properties
        bold_font = QFont()
        bold_font.setBold(True)
        cyan_brush = QBrush(QColor("#38BDF8"))

        for pset_name in sorted(grouped.keys()):
            props = grouped[pset_name]
            pset_item = QTreeWidgetItem([pset_name, f"({len(props)} св-в)"])
            pset_item.setFont(0, bold_font)
            pset_item.setForeground(0, cyan_brush)

            has_matching_child = False
            for p_name in sorted(props.keys()):
                val = props[p_name]
                val_str = str(val) if val is not None else "—"

                if query:
                    if query not in p_name.lower() and query not in val_str.lower() and query not in pset_name.lower():
                        continue

                has_matching_child = True
                child = QTreeWidgetItem([p_name, val_str])
                pset_item.addChild(child)

            if not query or has_matching_child:
                self.tree.addTopLevelItem(pset_item)
                pset_item.setExpanded(True)

    def _filter_properties(self):
        if self.current_record:
            self._populate_tree(self.current_record.properties)

    def _copy_guid(self):
        if self.current_record:
            QApplication.clipboard().setText(self.current_record.global_id)
            QMessageBox.information(
                self,
                "Скопировано",
                f"GUID скопирован в буфер обмена:\n{self.current_record.global_id}"
            )

    def _on_focus_clicked(self):
        if self.current_record:
            self.focus_requested.emit(self.current_record.global_id)

    def _on_isolate_clicked(self):
        if self.current_record:
            self.isolate_requested.emit(self.current_record.global_id)
