"""
Scene Manager for 3D Viewport.
Handles adding meshes to PyVista Plotter, actor-to-GUID mapping,
element selection, camera framing, visibility toggling, and coloring modes.
"""
from typing import Any, Dict, List, Optional, Set, Tuple
import pyvista as pv
from .geometry_loader import LoadedGeometry, ElementMesh, get_default_color_for_class

# Selection highlight color (Bright Cyan)
SELECTION_COLOR = (0.0, 0.90, 1.0)
DEFECT_COLOR = (0.95, 0.20, 0.20)  # Bright Red for missing attributes
OK_COLOR = (0.20, 0.80, 0.40)      # Soft Green for present attributes


class SceneManager:
    def __init__(self, plotter: pv.Plotter):
        self.plotter = plotter
        self.geometry: Optional[LoadedGeometry] = None
        self.actors: Dict[str, Any] = {}          # guid -> vtkActor
        self.actor_to_guid: Dict[Any, str] = {}    # actor -> guid
        self.selected_guid: Optional[str] = None
        self.original_actor_props: Dict[str, Dict[str, Any]] = {}
        self.selection_actor: Optional[Any] = None
        self.show_edges: bool = True
        self.is_xray: bool = False
        self.current_color_mode: str = "materials"  # 'materials', 'classes', 'defects'

    def clear(self):
        """Clear all meshes from scene and reset internal mappings."""
        self.plotter.clear()
        self.actors.clear()
        self.actor_to_guid.clear()
        self.original_actor_props.clear()
        self.selected_guid = None
        self.selection_actor = None
        self.geometry = None

    def load_geometry(self, geometry: LoadedGeometry):
        """Populate the 3D scene with the loaded geometry meshes."""
        self.clear()
        self.geometry = geometry

        # Disable rendering updates during bulk additions for speed
        render_window = self.plotter.render_window
        render_window.SetOffScreenRendering(False)

        for guid, elem in geometry.elements.items():
            # Skip spatial elements or helper objects from default solid view if needed
            if elem.ifc_class in ["IfcOpeningElement", "IfcSpace"]:
                continue

            color = elem.color
            opacity = elem.opacity

            actor = self.plotter.add_mesh(
                elem.mesh,
                color=color,
                opacity=opacity,
                show_edges=self.show_edges,
                edge_color=(0.2, 0.2, 0.2),
                line_width=0.8,
                smooth_shading=True,
                pickable=True,
                name=guid,
            )

            self.actors[guid] = actor
            self.actor_to_guid[actor] = guid
            self.original_actor_props[guid] = {
                "color": color,
                "opacity": opacity,
            }

        self.plotter.reset_camera()

    def get_guid_from_actor(self, actor: Any) -> Optional[str]:
        """Lookup element GUID by its VTK actor."""
        return self.actor_to_guid.get(actor)

    def select_element(self, guid: str, focus_camera: bool = False):
        """
        Highlight the selected element in vibrant cyan and optionally frame camera on it.
        """
        # Restore previously selected actor
        if self.selected_guid and self.selected_guid in self.actors:
            prev_actor = self.actors[self.selected_guid]
            prev_props = self.original_actor_props.get(self.selected_guid, {})
            if prev_actor and prev_props:
                prop = prev_actor.GetProperty()
                c = prev_props["color"]
                prop.SetColor(c[0], c[1], c[2])
                prop.SetOpacity(prev_props["opacity"])
                prop.SetAmbient(0.0)

        # Remove dedicated selection outline if exists
        if self.selection_actor:
            self.plotter.remove_actor(self.selection_actor)
            self.selection_actor = None

        self.selected_guid = guid

        if not guid or guid not in self.actors or not self.geometry:
            return

        actor = self.actors[guid]
        prop = actor.GetProperty()
        # Highlight in glowing cyan
        prop.SetColor(SELECTION_COLOR[0], SELECTION_COLOR[1], SELECTION_COLOR[2])
        prop.SetAmbient(0.35)
        prop.SetOpacity(1.0)

        # Add wireframe highlight outline over the mesh
        elem = self.geometry.elements.get(guid)
        if elem:
            self.selection_actor = self.plotter.add_mesh(
                elem.mesh,
                style="wireframe",
                color=(1.0, 1.0, 0.0),  # Yellow outline
                line_width=2.5,
                render_lines_as_tubes=False,
                name="selection_halo",
                pickable=False,
            )

            if focus_camera:
                self.focus_on_bounds(elem.bounds)

        self.plotter.render()

    def clear_selection(self):
        """Deselect currently highlighted element."""
        if self.selected_guid and self.selected_guid in self.actors:
            prev_actor = self.actors[self.selected_guid]
            prev_props = self.original_actor_props.get(self.selected_guid, {})
            if prev_actor and prev_props:
                prop = prev_actor.GetProperty()
                c = prev_props["color"]
                prop.SetColor(c[0], c[1], c[2])
                prop.SetOpacity(prev_props["opacity"])
                prop.SetAmbient(0.0)

        if self.selection_actor:
            self.plotter.remove_actor(self.selection_actor)
            self.selection_actor = None

        self.selected_guid = None
        self.plotter.render()

    def focus_on_bounds(self, bounds: Tuple[float, float, float, float, float, float]):
        """Smoothly fit camera to the specified bounding box."""
        bx = (bounds[0] + bounds[1]) * 0.5
        by = (bounds[2] + bounds[3]) * 0.5
        bz = (bounds[4] + bounds[5]) * 0.5
        diag = max(
            abs(bounds[1] - bounds[0]),
            abs(bounds[3] - bounds[2]),
            abs(bounds[5] - bounds[4]),
        )
        dist = max(diag * 2.5, 5.0)

        cam = self.plotter.camera
        cam.SetFocalPoint(bx, by, bz)
        cam.SetPosition(bx + dist * 0.7, by - dist * 0.7, bz + dist * 0.5)
        self.plotter.reset_camera_clipping_range()
        self.plotter.render()

    def isolate_elements(self, guids: Set[str]):
        """Make only the specified elements visible; hide the rest."""
        for guid, actor in self.actors.items():
            actor.SetVisibility(guid in guids)
        self.plotter.render()

    def reset_visibility(self):
        """Show all model elements."""
        for actor in self.actors.values():
            actor.SetVisibility(True)
        self.plotter.render()

    def set_edges_visible(self, visible: bool):
        """Toggle polygon wireframe/edges on all elements."""
        self.show_edges = visible
        for actor in self.actors.values():
            actor.GetProperty().SetEdgeVisibility(visible)
        self.plotter.render()

    def set_transparency_mode(self, enabled: bool):
        """Toggle semi-transparent X-Ray mode."""
        self.is_xray = enabled
        for guid, actor in self.actors.items():
            orig_op = self.original_actor_props.get(guid, {}).get("opacity", 1.0)
            target_op = min(orig_op, 0.25) if enabled else orig_op
            actor.GetProperty().SetOpacity(target_op)
        self.plotter.render()

    def highlight_defects(self, missing_guids: Set[str], present_guids: Set[str]):
        """
        Color elements in 3D:
        - Missing attribute: Bright Red (Defect).
        - Present: Soft Muted / Transparent Green.
        """
        for guid, actor in self.actors.items():
            prop = actor.GetProperty()
            if guid in missing_guids:
                prop.SetColor(DEFECT_COLOR[0], DEFECT_COLOR[1], DEFECT_COLOR[2])
                prop.SetOpacity(1.0)
                prop.SetAmbient(0.2)
            elif guid in present_guids:
                prop.SetColor(0.7, 0.7, 0.75)
                prop.SetOpacity(0.25)
                prop.SetAmbient(0.0)
            else:
                orig = self.original_actor_props.get(guid, {})
                c = orig.get("color", (0.7, 0.7, 0.7))
                prop.SetColor(c[0], c[1], c[2])
                prop.SetOpacity(orig.get("opacity", 1.0))
        self.plotter.render()

    def reset_colors(self):
        """Restore CAD/BIM material colors."""
        for guid, actor in self.actors.items():
            orig = self.original_actor_props.get(guid, {})
            c = orig.get("color", (0.7, 0.7, 0.7))
            prop = actor.GetProperty()
            prop.SetColor(c[0], c[1], c[2])
            prop.SetOpacity(orig.get("opacity", 1.0))
            prop.SetAmbient(0.0)
        self.plotter.render()
