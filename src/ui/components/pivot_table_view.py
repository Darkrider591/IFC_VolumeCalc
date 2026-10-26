"""
Virtualized QTableView and custom QAbstractTableModel for the summary pivot table.
Supports instant rendering, sorting, number formatting, and visual presence indicators.
"""
from typing import Any, List, Optional
from PySide6.QtWidgets import QTableView, QHeaderView, QWidget
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, Signal
from PySide6.QtGui import QColor, QBrush
from src.core.models import AggregationSummary, GroupSummaryRow


class PivotTableModel(QAbstractTableModel):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._summary: Optional[AggregationSummary] = None
        self._rows: List[GroupSummaryRow] = []
        self._is_numeric: bool = False
        self._group_col_title: str = "Категория / Группа"
        self._sort_col: int = 1
        self._sort_order: Qt.SortOrder = Qt.DescendingOrder

    def set_data(self, summary: AggregationSummary, group_col_title: str = "Категория / Группа"):
        self.beginResetModel()
        self._summary = summary
        self._rows = list(summary.rows)
        self._is_numeric = summary.total_sum is not None
        self._group_col_title = group_col_title
        self._apply_sort()
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 10 if self._is_numeric else 6

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            headers = [
                self._group_col_title,
                "Всего эл-тов",
                "С атрибутом",
                "С атрибутом %",
                "БЕЗ атрибута",
                "БЕЗ атрибута %",
                "Сумма",
                "Среднее",
                "Минимум",
                "Максимум",
            ]
            if section < len(headers):
                return headers[section]
        return None

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid() or index.row() >= len(self._rows):
            return None

        row = self._rows[index.row()]
        col = index.column()

        if role == Qt.DisplayRole:
            if col == 0:
                return row.group_name
            elif col == 1:
                return f"{row.total_elements:,}"
            elif col == 2:
                return f"{row.present_count:,}"
            elif col == 3:
                return f"{row.present_percent:.1f}%"
            elif col == 4:
                return f"{row.missing_count:,}"
            elif col == 5:
                return f"{row.missing_percent:.1f}%"
            elif col == 6:
                return f"{row.total_sum:,.2f}" if row.total_sum is not None else "—"
            elif col == 7:
                return f"{row.average:,.2f}" if row.average is not None else "—"
            elif col == 8:
                return f"{row.min_value:,.2f}" if row.min_value is not None else "—"
            elif col == 9:
                return f"{row.max_value:,.2f}" if row.max_value is not None else "—"

        elif role == Qt.TextAlignmentRole:
            if col == 0:
                return int(Qt.AlignLeft | Qt.AlignVCenter)
            elif col in [3, 5]:
                return int(Qt.AlignCenter | Qt.AlignVCenter)
            else:
                return int(Qt.AlignRight | Qt.AlignVCenter)

        elif role == Qt.ForegroundRole:
            if col == 3 and row.present_percent == 100.0:
                return QBrush(QColor("#10B981"))  # Emerald green
            elif col == 5 and row.missing_count > 0:
                return QBrush(QColor("#EF4444"))  # Red for missing

        return None

    def sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder):
        self._sort_col = column
        self._sort_order = order
        self.beginResetModel()
        self._apply_sort()
        self.endResetModel()

    def _apply_sort(self):
        reverse = (self._sort_order == Qt.DescendingOrder)

        def get_key(row: GroupSummaryRow):
            if self._sort_col == 0:
                return row.group_name.lower()
            elif self._sort_col == 1:
                return row.total_elements
            elif self._sort_col == 2:
                return row.present_count
            elif self._sort_col == 3:
                return row.present_percent
            elif self._sort_col == 4:
                return row.missing_count
            elif self._sort_col == 5:
                return row.missing_percent
            elif self._sort_col == 6:
                return row.total_sum if row.total_sum is not None else -1e12
            elif self._sort_col == 7:
                return row.average if row.average is not None else -1e12
            elif self._sort_col == 8:
                return row.min_value if row.min_value is not None else -1e12
            elif self._sort_col == 9:
                return row.max_value if row.max_value is not None else -1e12
            return 0

        self._rows.sort(key=get_key, reverse=reverse)

    def get_row(self, index: int) -> Optional[GroupSummaryRow]:
        if 0 <= index < len(self._rows):
            return self._rows[index]
        return None


class PivotTableView(QTableView):
    row_double_clicked = Signal(object)  # Emits GroupSummaryRow

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.model_instance = PivotTableModel(self)
        self.setModel(self.model_instance)

        self.setSortingEnabled(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setSelectionMode(QTableView.SingleSelection)
        self.setShowGrid(True)
        self.setAlternatingRowColors(True)

        self.doubleClicked.connect(self._on_double_clicked)

    def update_summary(self, summary: AggregationSummary, group_col_title: str = "Категория / Группа"):
        self.model_instance.set_data(summary, group_col_title)
        self.resizeColumnsToContents()
        # Ensure category column has good width
        if self.horizontalHeader().length() > 0:
            self.setColumnWidth(0, max(220, self.columnWidth(0)))

    def _on_double_clicked(self, index: QModelIndex):
        row = self.model_instance.get_row(index.row())
        if row:
            self.row_double_clicked.emit(row)
