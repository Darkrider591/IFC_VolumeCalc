"""
Main 3D BIM Viewer Window.
Coordinates 3D rendering, interactive picking, property inspector,
and analytical attribute calculations (KPI cards, pivot tables, Excel/CSV export).
"""
import os
from typing import Dict, Optional, Set
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
)
from PySide6.QtCore import Qt

from src.core.models import (
    AggregationSummary,
    ElementRecord,
    GroupingMode,
)
from src.core.ifc_parser import ParseResult
from src.core.aggregator import calculate_aggregation
from src.core.exporter import export_to_excel, export_to_csv
from src.ui.components.file_drop_widget import FileDropWidget
from src.ui.components.kpi_card import KpiCard
from src.ui.components.attribute_selector import AttributeSelector
from src.ui.components.config_panel import ConfigPanel
from src.ui.components.pivot_table_view import PivotTableView
from src.ui.components.missing_elements_view import MissingElementsView
from src.ui.workers.parse_worker import ParseWorker
from src.ui.styles.themes import DARK_THEME, LIGHT_THEME

from viewer.core.geometry_loader import LoadedGeometry
from viewer.ui.workers.geom_worker import GeometryWorker
from viewer.ui.components.viewport_3d import Viewport3D
from viewer.ui.components.scene_toolbar import SceneToolbar
from viewer.ui.components.properties_panel import PropertiesPanel


class ViewerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IFC_VolumeCalc 3D Viewer — Интерактивный анализ и 3D визуализация")
        self.resize(1500, 950)
        self.setMinimumSize(1100, 750)

        # State
        self.is_dark_theme = True
        self.parse_result: Optional[ParseResult] = None
        self.elements_by_guid: Dict[str, ElementRecord] = {}
        self.loaded_geometry: Optional[LoadedGeometry] = None
        self.current_summary: Optional[AggregationSummary] = None
        self.current_attribute_path: Optional[str] = None
        self.current_grouping_mode: GroupingMode = GroupingMode.BY_CLASS
        self.current_presence_filter: str = "all"
        self.current_table_search: str = ""
        self.highlight_defects_enabled: bool = False

        self.parse_worker: Optional[ParseWorker] = None
        self.geom_worker: Optional[GeometryWorker] = None

        self._setup_ui()
        self._apply_theme()

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(10)

        # 1. Header Bar
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        app_title = QLabel("IFC_VolumeCalc 3D Viewer")
        app_title.setObjectName("headerTitle")
        title_box.addWidget(app_title)

        subtitle = QLabel("Интерактивная 3D визуализация BIM, подсчет объемов и инспектор свойств (Offline)")
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
        self.file_drop_widget.file_selected.connect(self._start_loading)
        main_layout.addWidget(self.file_drop_widget)

        # Progress bar
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
        kpi_layout.setSpacing(10)

        self.kpi_total = KpiCard("Всего элементов", "0 шт.", "100%", "neutral")
        kpi_layout.addWidget(self.kpi_total)

        self.kpi_present = KpiCard("С атрибутом", "0 шт.", "0.0%", "positive")
        kpi_layout.addWidget(self.kpi_present)

        self.kpi_missing = KpiCard("БЕЗ атрибута (пропущено)", "0 шт.", "0.0%", "negative")
        kpi_layout.addWidget(self.kpi_missing)

        self.kpi_sum = KpiCard("Сумма значений", "—", "Агрегация", "neutral")
        kpi_layout.addWidget(self.kpi_sum)

        main_layout.addLayout(kpi_layout)

        # 4. Main 3-Way Splitter: Left (Analytics) | Center (3D Viewport) | Right (Properties)
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.setChildrenCollapsible(False)

        # --- LEFT PANEL: Attribute Selector + Pivot Table / Defects ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        # Attribute Selector
        self.attr_selector = AttributeSelector(self)
        self.attr_selector.attribute_selected.connect(self._on_attribute_selected)
        left_layout.addWidget(self.attr_selector, 1)

        # Config Panel
        self.config_panel = ConfigPanel(self)
        self.config_panel.grouping_changed.connect(self._on_grouping_changed)
        self.config_panel.search_changed.connect(self._on_table_search_changed)
        self.config_panel.filter_presence_changed.connect(self._on_presence_filter_changed)
        self.config_panel.export_excel_requested.connect(self._export_excel)
        self.config_panel.export_csv_requested.connect(self._export_csv)
        self.config_panel.show_missing_requested.connect(self._switch_to_missing_tab)
        left_layout.addWidget(self.config_panel)

        # Analytical Tabs: Pivot Table & Missing Elements
        self.tabs = QTabWidget()
        self.pivot_table = PivotTableView(self)
        self.pivot_table.row_double_clicked.connect(self._on_group_row_double_clicked)
        self.tabs.addTab(self.pivot_table, "📊 Сводная таблица")

        self.missing_view = MissingElementsView(self)
        self.missing_view.table.itemSelectionChanged.connect(self._on_missing_element_selected)
        self.tabs.addTab(self.missing_view, "⚠️ Элементы без атрибута")
        left_layout.addWidget(self.tabs, 2)

        self.main_splitter.addWidget(left_panel)

        # --- CENTER PANEL: 3D Scene Toolbar + Viewport3D ---
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(4)

        # 3D Toolbar
        self.scene_toolbar = SceneToolbar(self)
        self.scene_toolbar.view_iso_clicked.connect(self._on_view_iso)
        self.scene_toolbar.view_top_clicked.connect(self._on_view_top)
        self.scene_toolbar.view_front_clicked.connect(self._on_view_front)
        self.scene_toolbar.reset_view_clicked.connect(self._on_reset_view)
        self.scene_toolbar.toggle_edges_toggled.connect(self._on_toggle_edges)
        self.scene_toolbar.toggle_xray_toggled.connect(self._on_toggle_xray)
        self.scene_toolbar.toggle_defects_toggled.connect(self._on_toggle_defects)
        self.scene_toolbar.isolate_clicked.connect(self._on_isolate_selected)
        self.scene_toolbar.show_all_clicked.connect(self._on_show_all)
        center_layout.addWidget(self.scene_toolbar)

        # 3D Viewport
        self.viewport_3d = Viewport3D(self)
        self.viewport_3d.element_selected.connect(self._on_3d_element_selected)
        self.viewport_3d.element_deselected.connect(self._on_3d_element_deselected)
        center_layout.addWidget(self.viewport_3d, 1)

        self.main_splitter.addWidget(center_panel)

        # --- RIGHT PANEL: Properties Inspector ---
        self.properties_panel = PropertiesPanel(self)
        self.properties_panel.focus_requested.connect(self._focus_element_in_3d)
        self.properties_panel.isolate_requested.connect(self._isolate_element_in_3d)
        self.main_splitter.addWidget(self.properties_panel)

        # Splitter sizing: 30% Left | 45% Center (3D) | 25% Right (Properties)
        self.main_splitter.setStretchFactor(0, 3)
        self.main_splitter.setStretchFactor(1, 5)
        self.main_splitter.setStretchFactor(2, 2)
        main_layout.addWidget(self.main_splitter, 1)

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

    def _start_loading(self, file_path: str):
        if not os.path.exists(file_path):
            QMessageBox.critical(self, "Ошибка", f"Файл не найден: {file_path}")
            return

        self.progress_container.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_badge.setText("Анализ атрибутов...")
        self.status_bar.showMessage(f"Чтение модели: {file_path}")

        # Cancel previous workers if active
        if self.parse_worker and self.parse_worker.isRunning():
            self.parse_worker.cancel()
            self.parse_worker.wait()
        if self.geom_worker and self.geom_worker.isRunning():
            self.geom_worker.cancel()
            self.geom_worker.wait()

        # Step 1: Fast metadata & attribute extraction
        self.parse_worker = ParseWorker(file_path, self)
        self.parse_worker.progress.connect(self._on_parse_progress)
        self.parse_worker.finished.connect(lambda res: self._on_parse_finished(res, file_path))
        self.parse_worker.error.connect(self._on_loading_error)
        self.parse_worker.start()

    def _on_parse_progress(self, percent: int, message: str):
        self.progress_bar.setValue(int(percent * 0.4))
        self.progress_status_label.setText(f"[1/2] {message}")
        self.status_bar.showMessage(message)

    def _on_parse_finished(self, result: ParseResult, file_path: str):
        self.parse_result = result
        self.elements_by_guid = {e.global_id: e for e in result.elements}

        self.file_drop_widget.set_file_loaded(
            file_name=result.file_name,
            size_mb=result.file_size_mb,
            schema=result.schema,
            total_elements=result.total_elements,
        )

        self.attr_selector.set_attributes(result.attributes)

        # Step 2: Background 3D solid tessellation
        self.status_badge.setText("Триангуляция 3D...")
        self.geom_worker = GeometryWorker(file_path, self, num_threads=4)
        self.geom_worker.progress.connect(self._on_geom_progress)
        self.geom_worker.finished.connect(self._on_geom_finished)
        self.geom_worker.error.connect(self._on_geom_error)
        self.geom_worker.start()

    def _on_geom_progress(self, percent: int, message: str):
        self.progress_bar.setValue(40 + int(percent * 0.6))
        self.progress_status_label.setText(f"[2/2] {message}")
        self.status_bar.showMessage(message)

    def _on_geom_finished(self, geometry: LoadedGeometry):
        self.loaded_geometry = geometry
        self.viewport_3d.load_geometry(geometry)
        self.progress_container.setVisible(False)
        self.status_badge.setText("Модель готова")
        self.status_bar.showMessage(
            f"3D модель визуализирована: {geometry.total_count:,} элементов ({geometry.total_triangles:,} полигонов)"
        )

    def _on_loading_error(self, err_msg: str):
        self.progress_container.setVisible(False)
        self.status_badge.setText("Ошибка")
        QMessageBox.critical(self, "Ошибка чтения IFC", f"Не удалось разобрать файл:\n{err_msg}")

    def _on_geom_error(self, err_msg: str):
        self.progress_container.setVisible(False)
        self.status_badge.setText("Ошибка 3D")
        QMessageBox.warning(self, "Ошибка 3D визуализации", f"Не удалось построить 3D геометрию:\n{err_msg}")

    # 3D Interaction
    def _on_3d_element_selected(self, guid: str):
        record = self.elements_by_guid.get(guid)
        self.properties_panel.set_element(record)
        if record:
            self.status_bar.showMessage(
                f"Выбран элемент: {record.ifc_class} | {record.name or 'Без имени'} | GUID: {guid}"
            )

    def _on_3d_element_deselected(self):
        self.properties_panel.set_element(None)
        self.status_bar.showMessage("Элемент снят с выделения")

    def _focus_element_in_3d(self, guid: str):
        self.viewport_3d.select_element_by_guid(guid, focus_camera=True)

    def _isolate_element_in_3d(self, guid: str):
        self.viewport_3d.scene_manager.isolate_elements({guid})

    def _on_view_iso(self):
        self.viewport_3d.view_isometric()

    def _on_view_top(self):
        self.viewport_3d.view_top()

    def _on_view_front(self):
        self.viewport_3d.view_front()

    def _on_reset_view(self):
        self.viewport_3d.reset_camera()

    def _on_toggle_edges(self, checked: bool):
        self.viewport_3d.toggle_edges(checked)

    def _on_toggle_xray(self, checked: bool):
        self.viewport_3d.toggle_xray(checked)

    def _on_toggle_defects(self, checked: bool):
        self.highlight_defects_enabled = checked
        self._update_3d_defects_highlight()

    def _on_isolate_selected(self):
        if self.viewport_3d.scene_manager.selected_guid:
            self.viewport_3d.scene_manager.isolate_elements({self.viewport_3d.scene_manager.selected_guid})

    def _on_show_all(self):
        self.viewport_3d.scene_manager.reset_visibility()

    def _update_3d_defects_highlight(self):
        if not self.current_summary or not self.loaded_geometry:
            return

        if self.highlight_defects_enabled:
            missing_guids = set(m.get("global_id") for m in self.current_summary.missing_elements)
            all_guids = set(self.elements_by_guid.keys())
            present_guids = all_guids - missing_guids
            self.viewport_3d.highlight_defects(missing_guids, present_guids)
        else:
            self.viewport_3d.reset_colors()

    # Analytical Calculations
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

        # 4. Refresh defect highlight in 3D if active
        if self.highlight_defects_enabled:
            self._update_3d_defects_highlight()

    def _switch_to_missing_tab(self):
        self.tabs.setCurrentIndex(1)

    def _on_missing_element_selected(self):
        selected_indexes = self.missing_view.table.selectedIndexes()
        if not selected_indexes:
            return
        row = selected_indexes[0].row()
        guid_item = self.missing_view.table.item(row, 1)
        if guid_item:
            guid = guid_item.text().strip()
            if guid:
                self.viewport_3d.select_element_by_guid(guid, focus_camera=True)
                record = self.elements_by_guid.get(guid)
                self.properties_panel.set_element(record)

    def _on_group_row_double_clicked(self, row):
        if row.missing_elements:
            self.tabs.setCurrentIndex(1)
            self.missing_view.set_missing_elements(
                row.missing_elements,
                f"{self.current_summary.attribute.display_name} ({row.group_name})"
            )
            # Isolate this group in 3D
            group_guids = set(m.get("global_id") for m in row.missing_elements)
            self.viewport_3d.scene_manager.isolate_elements(group_guids)

    def _export_excel(self):
        if not self.current_summary or not self.parse_result:
            QMessageBox.warning(self, "Экспорт", "Нет данных для экспорта.")
            return

        default_name = f"Report_{self.current_summary.attribute.display_name}_{self.parse_result.file_name}.xlsx"
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить отчет в Excel", default_name, "Excel Files (*.xlsx)")
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
                    self, "Экспорт завершен", f"Отчет сохранен:\n{file_path}\n\nОткрыть файл сейчас?",
                    QMessageBox.Yes | QMessageBox.No
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
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить сводку в CSV", default_name, "CSV Files (*.csv)")
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

    def closeEvent(self, event):
        """Cleanly close VTK interactor and threads before application exit."""
        if self.parse_worker and self.parse_worker.isRunning():
            self.parse_worker.cancel()
            self.parse_worker.wait()
        if self.geom_worker and self.geom_worker.isRunning():
            self.geom_worker.cancel()
            self.geom_worker.wait()
        self.viewport_3d.close()
        event.accept()
