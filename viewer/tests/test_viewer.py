"""
Unit tests for 3D Viewer core and UI components.
"""
import os
import sys
import pytest
from PySide6.QtWidgets import QApplication

# Ensure QApplication exists for UI tests
app = QApplication.instance() or QApplication(sys.argv)

from viewer.core.geometry_loader import extract_geometry, LoadedGeometry
from viewer.core.scene_manager import SceneManager
from viewer.ui.viewer_window import ViewerWindow
from src.core.ifc_parser import parse_ifc_file
import pyvista as pv

SAMPLE_HOUSE = r"d:\IT\Dev\IFC\ifc viktor platform\ifc-viewer-1.0.1\AC20-FZK-Haus (Sample IFC).ifc"


def test_extract_geometry():
    assert os.path.exists(SAMPLE_HOUSE), "Sample IFC must exist"
    geom = extract_geometry(SAMPLE_HOUSE, num_threads=2)
    assert geom.total_count > 0
    assert geom.total_triangles > 0
    assert len(geom.classes) > 0

    guid = next(iter(geom.elements.keys()))
    elem = geom.elements[guid]
    assert elem.guid == guid
    assert elem.mesh.n_points > 0
    assert elem.mesh.n_cells > 0
    assert len(elem.color) == 3
    assert 0.0 <= elem.opacity <= 1.0


def test_scene_manager_selection():
    geom = extract_geometry(SAMPLE_HOUSE, num_threads=2)
    plotter = pv.Plotter(off_screen=True)
    sm = SceneManager(plotter)

    sm.load_geometry(geom)
    assert len(sm.actors) > 0

    guid = next(iter(sm.actors.keys()))
    actor = sm.actors[guid]
    assert sm.get_guid_from_actor(actor) == guid

    # Test selection
    sm.select_element(guid)
    assert sm.selected_guid == guid
    assert sm.selection_actor is not None

    # Test clear selection
    sm.clear_selection()
    assert sm.selected_guid is None
    assert sm.selection_actor is None

    # Test isolation
    sm.isolate_elements({guid})
    assert sm.actors[guid].GetVisibility() == 1

    sm.reset_visibility()
    assert all(a.GetVisibility() == 1 for a in sm.actors.values())

    plotter.close()


def test_viewer_window_init():
    window = ViewerWindow()
    assert window.windowTitle().startswith("IFC_VolumeCalc 3D Viewer")
    assert window.properties_panel.class_badge.text() == "Не выбран"

    # Simulate loading
    parse_res = parse_ifc_file(SAMPLE_HOUSE)
    window._on_parse_finished(parse_res, SAMPLE_HOUSE)
    assert window.parse_result is not None

    geom = extract_geometry(SAMPLE_HOUSE, num_threads=2)
    window._on_geom_finished(geom)
    assert window.loaded_geometry is not None

    # Select an element
    sample_guid = next(iter(window.elements_by_guid.keys()))
    window._on_3d_element_selected(sample_guid)
    assert window.properties_panel.guid_label.text() == sample_guid
    assert window.properties_panel.class_badge.text() != "Не выбран"

    window.close()
