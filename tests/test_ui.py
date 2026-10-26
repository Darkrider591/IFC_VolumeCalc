"""
UI tests for MainWindow and components using PySide6.
"""
import os
import sys
import pytest
from PySide6.QtWidgets import QApplication

# Ensure QApplication exists for widget testing
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

from src.ui.main_window import MainWindow
from src.core.ifc_parser import parse_ifc_file
from src.core.models import GroupingMode

SAMPLE_HOUSE = r"d:\IT\Dev\IFC\ifc viktor platform\ifc-viewer-1.0.1\AC20-FZK-Haus (Sample IFC).ifc"


def test_main_window_init():
    window = MainWindow()
    assert window.windowTitle().startswith("IFC_VolumeCalc")
    assert window.kpi_total.value_label.text() == "0 шт."
    assert window.is_dark_theme is True

    # Test theme toggle
    window._toggle_theme()
    assert window.is_dark_theme is False
    window._toggle_theme()
    assert window.is_dark_theme is True


def test_main_window_load_and_aggregate():
    window = MainWindow()
    res = parse_ifc_file(SAMPLE_HOUSE)
    window._on_parse_finished(res)

    assert window.parse_result is not None
    assert window.parse_result.total_elements > 0
    assert window.attr_selector.tree.topLevelItemCount() > 0

    # Select an attribute
    window._on_attribute_selected("Entity.Name")
    assert window.current_summary is not None
    assert window.kpi_present.value_label.text() != "0 шт."

    # Test changing grouping
    window._on_grouping_changed(GroupingMode.BY_STOREY)
    assert window.current_grouping_mode == GroupingMode.BY_STOREY
    assert len(window.current_summary.rows) > 0

    # Test presence filter
    window._on_presence_filter_changed("only_present")
    assert window.current_presence_filter == "only_present"
