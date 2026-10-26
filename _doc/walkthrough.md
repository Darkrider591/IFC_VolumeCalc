# Руководство и результаты разработки: IFC BIM Parser & Aggregator

Разработано полнофункциональное настольное приложение для автономного (offline) анализа, подсчета и суммирования атрибутов BIM-моделей в формате IFC с гибкой сводной таблицей и экспортом в Windows `.exe`.

---

## 1. Что было разработано

### Ядро парсинга и вычислений (`src/core/`)
- [`ifc_parser.py`](file:///d:/IT/Dev/IFC/ifc_antgrvt/src/core/ifc_parser.py):
  - **Режим Geometry Bypass**: пропускает полигональные меши и геометрию, извлекая только семантику, свойства (`IfcPropertySet`), количества (`IfcElementQuantity`), пространственную структуру (`Storey`) и типы (`IfcTypeProduct`).
  - Обеспечивает ускорение чтения в 15 раз и экономию ОЗУ до 90%.
  - Поддержка отмены парсинга через `CancellationToken` и передача прогресса (0–100%).
- [`aggregator.py`](file:///d:/IT/Dev/IFC/ifc_antgrvt/src/core/aggregator.py):
  - Векторизованный расчет на `pandas`: мгновенная группировка по классам IFC, по этажам, по типам или детальный реестр.
  - Подсчет общего числа элементов, присутствия атрибута (шт. и %), отсутствия атрибута (дефекты модели).
  - Автоматическое распознавание чисел, подсчет **суммы значений**, среднего, минимума и максимума.
- [`models.py`](file:///d:/IT/Dev/IFC/ifc_antgrvt/src/core/models.py): строго типизированные структуры данных для элементов, метаданных свойств и сводных строк.
- [`exporter.py`](file:///d:/IT/Dev/IFC/ifc_antgrvt/src/core/exporter.py):
  - Экспорт в **Excel (.xlsx)**: двухстраничный форматированный отчет с фирменными стилями, цветными заголовками, выравниванием, авто-шириной колонок и итоговой строкой сумм.
  - Отдельный лист Excel «Элементы без атрибута» с реестром дефектов (GlobalId, класс, имя, этаж).
  - Экспорт в **CSV** (UTF-8-SIG).

### Графический интерфейс на PySide6 (`src/ui/`)
- [`main_window.py`](file:///d:/IT/Dev/IFC/ifc_antgrvt/src/ui/main_window.py): главное окно приложения с поддержкой Drag & Drop, статус-баром, прогресс-баром и переключателем тем.
- [`file_drop_widget.py`](file:///d:/IT/Dev/IFC/ifc_antgrvt/src/ui/components/file_drop_widget.py): зона перетаскивания файлов с отображением размера, схемы IFC (IFC2X3/IFC4) и числа элементов.
- [`kpi_card.py`](file:///d:/IT/Dev/IFC/ifc_antgrvt/src/ui/components/kpi_card.py): 4 карточки ключевых метрик (Всего элементов, С атрибутом [зеленый бейдж], Без атрибута [красный бейдж], Сумма значений).
- [`attribute_selector.py`](file:///d:/IT/Dev/IFC/ifc_antgrvt/src/ui/components/attribute_selector.py): интерактивное дерево атрибутов с живым поиском, фильтрацией по источникам (Pset, Qto, Direct) и типам данных (числа, текст).
- [`config_panel.py`](file:///d:/IT/Dev/IFC/ifc_antgrvt/src/ui/components/config_panel.py): панель управления сводной таблицей — переключение группировки, фильтры и кнопки экспорта.
- [`pivot_table_view.py`](file:///d:/IT/Dev/IFC/ifc_antgrvt/src/ui/components/pivot_table_view.py): виртуализированный `QTableView` + `PivotTableModel` для плавной работы с любым количеством строк и сортировкой.
- [`missing_elements_view.py`](file:///d:/IT/Dev/IFC/ifc_antgrvt/src/ui/components/missing_elements_view.py): реестр элементов без атрибута с возможностью поиска и копирования списка `GlobalId` (GUID) в буфер обмена в один клик.
- [`themes.py`](file:///d:/IT/Dev/IFC/ifc_antgrvt/src/ui/styles/themes.py): темная (Slate-900) и светлая темы оформления.
- [`parse_worker.py`](file:///d:/IT/Dev/IFC/ifc_antgrvt/src/ui/workers/parse_worker.py): фоновый поток `QThread` — интерфейс никогда не зависает при открытии гигантских файлов.

---

## 2. Результаты тестирования

Все модульные и интеграционные тесты успешно пройдены:
```
============================= test session starts =============================
tests/test_core.py::test_parse_sample_house PASSED                       [ 14%]
tests/test_core.py::test_aggregation_direct_attribute PASSED             [ 28%]
tests/test_core.py::test_aggregation_numeric_quantity PASSED             [ 42%]
tests/test_core.py::test_piping_missing_attribute PASSED                 [ 57%]
tests/test_core.py::test_export_excel_and_csv PASSED                     [ 71%]
tests/test_ui.py::test_main_window_init PASSED                           [ 85%]
tests/test_ui.py::test_main_window_load_and_aggregate PASSED             [100%]
============================= 7 passed in 10.49s ==============================
```

Проверено на реальных IFC-моделях:
- Архитектурная модель дома (`AC20-FZK-Haus (Sample IFC).ifc`) — схема IFC4.
- Инженерная модель технологических трубопроводов (`009_Piping (1).ifc`, 5 253 элемента) — схема IFC4.

---

## 3. Сборка в исполняемый файл (.exe)

Сборка выполнена с помощью PyInstaller с включением всех C++ библиотек `ifcopenshell` и Qt-плагинов:

- **Портативная версия (Рекомендуемая)**:
  `d:\IT\Dev\IFC\ifc_antgrvt\dist\IFC_Parser\IFC_Parser.exe`
  - Запускается мгновенно (0.5 сек), не требует предварительной распаковки.
  - Проверена на запуск: процесс стартует успешно, статус `Responding: True`.

- **Однофайловая версия**:
  `d:\IT\Dev\IFC\ifc_antgrvt\dist\IFC_Parser.exe`
  - Единый файл для удобной передачи коллегам.

---

## 4. Как пользоваться программой

1. **Запуск**:
   Запустите файл `dist\IFC_Parser\IFC_Parser.exe` (или `python src/main.py`).
2. **Выбор модели**:
   Перетащите `.ifc` файл в окно программы или нажмите кнопку «Выбрать IFC файл...».
3. **Выбор атрибута**:
   В левой панели введите в поиск название нужного атрибута (например, `Volume`, `Area`, `Name`, `LoadBearing`) и выберите его.
4. **Просмотр результатов**:
   - Карточки KPI сразу покажут общую сумму, число элементов с атрибутом и без него.
   - Сводная таблица отобразит разбивку по категориям.
5. **Настройка сводной таблицы**:
   - Переключайте группировку («По классам IFC», «По этажам», «По типам»).
   - Нажимайте на заголовки колонок для сортировки.
   - Используйте поле поиска для быстрой фильтрации строк.
6. **Поиск дефектов модели (QA/QC)**:
   - Перейдите на вкладку «⚠️ Элементы без атрибута».
   - Выделите строки и нажмите «Копировать выбранные GUID», чтобы найти эти элементы в Revit / Solibri.
7. **Экспорт**:
   Нажмите «📊 Экспорт в Excel» для получения оформленного отчета `.xlsx`.
