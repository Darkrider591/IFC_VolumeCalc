"""
Main Application Window for IFC BIM Attribute Parser & Aggregator.
Coordinates all views, workers, state management, and export actions.
"""
import os
import subprocess
from typing import Optional
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QSplitter,
    QTabWidget,
    QFileDialog,
    QMessageBox,
    QStatusBar,
    QApplication,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon

from src.core.models import (
    AggregationSummary,
    DataType,
    GroupingMode,
)
from src.core.ifc_parser import ParseResult
from src.core.aggregator import calculate_aggregation
from src.core.exporter import export_to_excel, export_to_csv

from .components.file_drop_widget import FileDropWidget
from .components.kpi_card import KpiCard
from .components.attribute_selector import AttributeSelector
from .components.config_panel import ConfigPanel
from .components.pivot_table_view import PivotTableView
from .components.missing_elements_view import MissingElementsView
from .workers.parse_worker import ParseWorker
from .styles.themes import DARK_THEME, LIGHT_THEME


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IFC_VolumeCalc — Анализ и расчет объемов и атрибутов")
        self.resize(1300, 850)
        self.setMinimumSize(1000, 650)

        # State
        self.is_dark_theme = True
        self.parse_result: Optional[ParseResult] = None
        self.current_summary: Optional[AggregationSummary] = None
        self.current_attribute_path: Optional[str] = None
        self.current_grouping_mode: GroupingMode = GroupingMode.BY_CLASS
        self.current_presence_filter: str = "all"
        self.current_table_search: str = ""
        self.parse_worker: Optional[ParseWorker] = None

        self._setup_ui()
        self._apply_theme()

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(18, 14, 18, 14)
        main_layout.setSpacing(12)

        # 1. Header Bar
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        app_title = QLabel("IFC_VolumeCalc")
        app_title.setObjectName("headerTitle")
        title_box.addWidget(app_title)

        subtitle = QLabel("Локальный анализ, подсчет сумм и валидация атрибутов BIM-моделей (Offline)")
        subtitle.setObjectName("subtitle")
        title_box.addWidget(subtitle)
        header_layout.addLayout(title_box)

        header_layout.addStretch()

        self.status_badge = QLabel("Ожидание файла")
        self.status_badge.setObjectName("kpiBadgeNeutral")
        header_layout.addWidget(self.status_badge)

        self.theme_btn = QPushButton("🌙 Тёмная тема")
        self.theme_btn.setObjectName("themeToggleBtn")
        self.theme_btn.clicked.connect(self._toggle_theme)
        header_layout.addWidget(self.theme_btn)

        main_layout.addLayout(header_layout)

        # 2. File Drop Zone
        self.file_drop_widget = FileDropWidget(self)
        self.file_drop_widget.file_selected.connect(self._start_parsing)
        main_layout.addWidget(self.file_drop_widget)

        # Progress bar (hidden by default)
        self.progress_container = QWidget()
        prog_layout = QVBoxLayout(self.progress_container)
        prog_layout.setContentsMargins(0, 0, 0, 0)
        prog_layout.setSpacing(4)

        self.progress_status_label = QLabel("Чтение модели...")
        self.progress_status_label.setStyleSheet("color: #38BDF8; font-size: 12px;")
        prog_layout.addWidget(self.progress_status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        prog_layout.addWidget(self.progress_bar)

        self.progress_container.setVisible(False)
        main_layout.addWidget(self.progress_container)

        # 3. KPI Stat Cards
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(12)

        self.kpi_total = KpiCard("Всего элементов", "0 шт.", "100%", "neutral")
        kpi_layout.addWidget(self.kpi_total)

        self.kpi_present = KpiCard("С атрибутом", "0 шт.", "0.0%", "positive")
        kpi_layout.addWidget(self.kpi_present)

        self.kpi_missing = KpiCard("БЕЗ атрибута (пропущено)", "0 шт.", "0.0%", "negative")
        kpi_layout.addWidget(self.kpi_missing)

        self.kpi_sum = KpiCard("Сумма значений", "—", "Агрегация", "neutral")
        kpi_layout.addWidget(self.kpi_sum)

        main_layout.addLayout(kpi_layout)

        # 4. Main Splitter: Left Sidebar (Attribute Selector) + Right Panel (Tabs)
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Left: Attribute Selector
        self.attr_selector = AttributeSelector(self)
        self.attr_selector.attribute_selected.connect(self._on_attribute_selected)
        splitter.addWidget(self.attr_selector)

        # Right: Config panel + Tabs
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        # Config Panel
        self.config_panel = ConfigPanel(self)
        self.config_panel.grouping_changed.connect(self._on_grouping_changed)
        self.config_panel.search_changed.connect(self._on_table_search_changed)
        self.config_panel.filter_presence_changed.connect(self._on_presence_filter_changed)
        self.config_panel.export_excel_requested.connect(self._export_excel)
        self.config_panel.export_csv_requested.connect(self._export_csv)
        self.config_panel.show_missing_requested.connect(self._switch_to_missing_tab)
        right_layout.addWidget(self.config_panel)

        # Tabs: Pivot Table & Missing Elements
        self.tabs = QTabWidget()

        self.pivot_table = PivotTableView(self)
        self.pivot_table.row_double_clicked.connect(self._on_group_row_double_clicked)
        self.tabs.addTab(self.pivot_table, "📊 Сводная таблица")

        self.missing_view = MissingElementsView(self)
        self.tabs.addTab(self.missing_view, "⚠️ Элементы без атрибута (QA/QC)")

        right_layout.addWidget(self.tabs)
        splitter.addWidget(right_panel)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        main_layout.addWidget(splitter, 1)

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готов к работе. Перетащите IFC файл модели.")

    def _toggle_theme(self):
        self.is_dark_theme = not self.is_dark_theme
        self._apply_theme()

    def _apply_theme(self):
        if self.is_dark_theme:
            self.setStyleSheet(DARK_THEME)
            self.theme_btn.setText("☀️ Светлая тема")
        else:
            self.setStyleSheet(LIGHT_THEME)
            self.theme_btn.setText("🌙 Тёмная тема")

    def _start_parsing(self, file_path: str):
        if not os.path.exists(file_path):
            QMessageBox.critical(self, "Ошибка", f"Файл не найден: {file_path}")
            return

        self.progress_container.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_badge.setText("Парсинг модели...")
        self.status_bar.showMessage(f"Загрузка файла: {file_path}")

        # Cancel previous worker if running
        if self.parse_worker and self.parse_worker.isRunning():
            self.parse_worker.cancel()
            self.parse_worker.wait()

        self.parse_worker = ParseWorker(file_path, self)
        self.parse_worker.progress.connect(self._on_parse_progress)
        self.parse_worker.finished.connect(self._on_parse_finished)
        self.parse_worker.error.connect(self._on_parse_error)
        self.parse_worker.start()

    def _on_parse_progress(self, percent: int, message: str):
        self.progress_bar.setValue(percent)
        self.progress_status_label.setText(message)
        self.status_bar.showMessage(message)

    def _on_parse_finished(self, result: ParseResult):
        self.parse_result = result
        self.progress_container.setVisible(False)
        self.status_badge.setText("Модель активна")

        self.file_drop_widget.set_file_loaded(
            file_name=result.file_name,
            size_mb=result.file_size_mb,
            schema=result.schema,
            total_elements=result.total_elements,
        )

        self.status_bar.showMessage(
            f"Загружено {result.total_elements:,} элементов из {result.file_name} ({result.schema})"
        )

        # Update attributes list and auto-select a property
        self.attr_selector.set_attributes(result.attributes)

    def _on_parse_error(self, err_msg: str):
        self.progress_container.setVisible(False)
        self.status_badge.setText("Ошибка")
        QMessageBox.critical(self, "Ошибка чтения IFC", f"Не удалось проанализировать IFC-файл:\n{err_msg}")
        self.status_bar.showMessage("Ошибка чтения файла")

    def _on_attribute_selected(self, full_path: str):
        self.current_attribute_path = full_path
        self._recalculate()

    def _on_grouping_changed(self, mode: GroupingMode):
        self.current_grouping_mode = mode
        self._recalculate()

    def _on_presence_filter_changed(self, filter_val: str):
        self.current_presence_filter = filter_val
        self._recalculate()

    def _on_table_search_changed(self, search_txt: str):
        self.current_table_search = search_txt
        self._recalculate()

    def _recalculate(self):
        if not self.parse_result or not self.current_attribute_path:
            return

        only_present = (self.current_presence_filter == "only_present")
        only_missing = (self.current_presence_filter == "only_missing")

        summary = calculate_aggregation(
            parse_result=self.parse_result,
            attribute_path=self.current_attribute_path,
            grouping_mode=self.current_grouping_mode,
            search_filter=self.current_table_search,
            only_present=only_present,
            only_missing=only_missing,
        )
        self.current_summary = summary

        # 1. Update KPI Cards
        self.kpi_total.set_value(f"{summary.total_elements:,} шт.")

        pres_text = f"{summary.present_count:,} шт."
        self.kpi_present.set_value(pres_text)
        self.kpi_present.set_badge(f"{summary.present_percent:.1f}%", "positive")

        miss_text = f"{summary.missing_count:,} шт."
        self.kpi_missing.set_value(miss_text)
        b_type = "positive" if summary.missing_count == 0 else "negative"
        self.kpi_missing.set_badge(f"{summary.missing_percent:.1f}%", b_type)

        if summary.total_sum is not None:
            unit_str = f" {summary.attribute.unit}" if summary.attribute.unit else ""
            self.kpi_sum.title_label.setText("СУММА ЗНАЧЕНИЙ")
            self.kpi_sum.set_value(f"{summary.total_sum:,.2f}{unit_str}")
            avg_str = f"Ср: {summary.average:,.2f}" if summary.average is not None else "Сумма"
            self.kpi_sum.set_badge(avg_str, "neutral")
        else:
            self.kpi_sum.title_label.setText("ЗНАЧЕНИЯ")
            self.kpi_sum.set_value("Текстовые данные")
            self.kpi_sum.set_badge("Не числовое", "neutral")

        # 2. Update Table View
        group_title = (
            "Класс IFC" if self.current_grouping_mode == GroupingMode.BY_CLASS else
            "Этаж / Уровень" if self.current_grouping_mode == GroupingMode.BY_STOREY else
            "Тип элемента" if self.current_grouping_mode == GroupingMode.BY_TYPE else
            "Элемент"
        )
        self.pivot_table.update_summary(summary, group_col_title=group_title)

        # 3. Update Missing Elements View
        self.missing_view.set_missing_elements(summary.missing_elements, summary.attribute.display_name)

        self.status_bar.showMessage(
            f"Атрибут: {summary.attribute.full_path}  •  Строк в сводке: {len(summary.rows)}"
        )

    def _switch_to_missing_tab(self):
        self.tabs.setCurrentIndex(1)

    def _on_group_row_double_clicked(self, row):
        if row.missing_elements:
            self.tabs.setCurrentIndex(1)
            self.missing_view.set_missing_elements(
                row.missing_elements,
                f"{self.current_summary.attribute.display_name} ({row.group_name})"
            )

    def _export_excel(self):
        if not self.current_summary or not self.parse_result:
            QMessageBox.warning(self, "Экспорт", "Нет данных для экспорта. Сначала выберите файл и атрибут.")
            return

        default_name = f"Report_{self.current_summary.attribute.display_name}_{self.parse_result.file_name}.xlsx"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить отчет в Excel",
            default_name,
            "Excel Files (*.xlsx)",
        )
        if file_path:
            try:
                group_title = (
                    "Класс IFC" if self.current_grouping_mode == GroupingMode.BY_CLASS else
                    "Этаж / Уровень" if self.current_grouping_mode == GroupingMode.BY_STOREY else
                    "Тип элемента" if self.current_grouping_mode == GroupingMode.BY_TYPE else
                    "Элемент"
                )
                export_to_excel(self.current_summary, self.parse_result.file_name, file_path, group_title)
                
                reply = QMessageBox.question(
                    self,
                    "Экспорт завершен",
                    f"Отчет успешно сохранен:\n{file_path}\n\nОткрыть файл сейчас?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if reply == QMessageBox.Yes:
                    os.startfile(file_path)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка экспорта", f"Не удалось сохранить Excel:\n{e}")

    def _export_csv(self):
        if not self.current_summary or not self.parse_result:
            QMessageBox.warning(self, "Экспорт", "Нет данных для экспорта.")
            return

        default_name = f"Report_{self.current_summary.attribute.display_name}.csv"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить сводку в CSV",
            default_name,
            "CSV Files (*.csv)",
        )
        if file_path:
            try:
                group_title = (
                    "Класс IFC" if self.current_grouping_mode == GroupingMode.BY_CLASS else
                    "Этаж / Уровень" if self.current_grouping_mode == GroupingMode.BY_STOREY else
                    "Тип элемента" if self.current_grouping_mode == GroupingMode.BY_TYPE else
                    "Элемент"
                )
                export_to_csv(self.current_summary, file_path, group_title)
                QMessageBox.information(self, "Экспорт завершен", f"Файл сохранен:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка экспорта", f"Не удалось сохранить CSV:\n{e}")
