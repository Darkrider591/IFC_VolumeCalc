"""
Interactive 3D Viewport component using PyVistaQt and VTK.
Handles rendering, CAD camera controls, and raycast picking of BIM elements.
"""
from typing import Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QFrame
from PySide6.QtCore import Signal
import pyvistaqt as pvqt
import vtk
from viewer.core.scene_manager import SceneManager
from viewer.core.geometry_loader import LoadedGeometry


class Viewport3D(QFrame):
    element_selected = Signal(str)  # Emits GlobalId
    element_deselected = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setContentsMargins(0, 0, 0, 0)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # PyVista Qt Interactor
        self.plotter = pvqt.QtInteractor(self)
        self.plotter.set_background("#0F172A", top="#1E293B")  # Dark modern CAD gradient
        layout.addWidget(self.plotter.interactor)

        # Scene manager
        self.scene_manager = SceneManager(self.plotter)

        # Picker
        self.prop_picker = vtk.vtkPropPicker()

        # Orientation widget (View Cube / Axes)
        self.plotter.add_axes(interactive=False, line_width=2)

        # Setup mouse click event
        self.plotter.track_click_position(self._on_mouse_click, side="left")

    def _on_mouse_click(self, point):
        """Handle mouse click for hardware raycast element picking."""
        interactor = self.plotter.interactor
        if not interactor:
            return

        x, y = interactor.GetEventPosition()
        self.prop_picker.Pick(x, y, 0, self.plotter.renderer)
        actor = self.prop_picker.GetActor()

        if actor:
            guid = self.scene_manager.get_guid_from_actor(actor)
            if guid:
                self.scene_manager.select_element(guid, focus_camera=False)
                self.element_selected.emit(guid)
                return

        # Clicked background or non-pickable actor
        self.scene_manager.clear_selection()
        self.element_deselected.emit()

    def load_geometry(self, geometry: LoadedGeometry):
        """Load and display the 3D geometry in the scene."""
        self.scene_manager.load_geometry(geometry)

    def select_element_by_guid(self, guid: str, focus_camera: bool = True):
        """Programmatically select and focus element from UI/table."""
        self.scene_manager.select_element(guid, focus_camera=focus_camera)

    def clear_selection(self):
        """Clear current selection."""
        self.scene_manager.clear_selection()

    # Camera presets
    def reset_camera(self):
        self.plotter.reset_camera()
        self.plotter.render()

    def view_isometric(self):
        self.plotter.view_isometric()
        self.plotter.reset_camera()
        self.plotter.render()

    def view_top(self):
        self.plotter.view_xy()
        self.plotter.reset_camera()
        self.plotter.render()

    def view_front(self):
        self.plotter.view_xz()
        self.plotter.reset_camera()
        self.plotter.render()

    def view_left(self):
        self.plotter.view_yz()
        self.plotter.reset_camera()
        self.plotter.render()

    # Display toggles
    def toggle_edges(self, visible: bool):
        self.scene_manager.set_edges_visible(visible)

    def toggle_xray(self, enabled: bool):
        self.scene_manager.set_transparency_mode(enabled)

    def highlight_defects(self, missing_guids: set, present_guids: set):
        self.scene_manager.highlight_defects(missing_guids, present_guids)

    def reset_colors(self):
        self.scene_manager.reset_colors()

    def close(self):
        """Cleanly shutdown VTK interactor on window close."""
        try:
            self.plotter.close()
        except Exception:
            pass
        super().close()
