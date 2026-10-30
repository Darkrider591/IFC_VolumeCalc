"""
High-performance 3D geometry loader for IFC models.
Extracts triangulated meshes using ifcopenshell.geom with C++ multi-threading,
assigning materials, colors, and binding to element GlobalIds.
"""
from dataclasses import dataclass
import os
import sys
from typing import Callable, Dict, List, Optional, Set, Tuple, Any
import numpy as np
import pyvista as pv
import ifcopenshell
import ifcopenshell.geom

from src.core.ifc_parser import CancellationToken, CancelledException


# Default intuitive BIM category colors (R, G, B, Opacity)
DEFAULT_CATEGORY_COLORS = {
    "IfcWall": (0.80, 0.80, 0.82, 1.0),
    "IfcWallStandardCase": (0.80, 0.80, 0.82, 1.0),
    "IfcSlab": (0.72, 0.70, 0.68, 1.0),
    "IfcRoof": (0.60, 0.38, 0.32, 1.0),
    "IfcBeam": (0.32, 0.52, 0.70, 1.0),
    "IfcColumn": (0.28, 0.48, 0.65, 1.0),
    "IfcMember": (0.40, 0.50, 0.60, 1.0),
    "IfcPlate": (0.50, 0.55, 0.60, 1.0),
    "IfcWindow": (0.65, 0.82, 0.95, 0.45),
    "IfcDoor": (0.62, 0.42, 0.28, 1.0),
    "IfcStair": (0.55, 0.55, 0.58, 1.0),
    "IfcRailing": (0.45, 0.45, 0.48, 1.0),
    "IfcCovering": (0.85, 0.85, 0.82, 1.0),
    "IfcCurtainWall": (0.70, 0.85, 0.95, 0.50),
    "IfcPipeSegment": (0.30, 0.70, 0.75, 1.0),
    "IfcFlowFitting": (0.25, 0.65, 0.70, 1.0),
    "IfcDuctSegment": (0.72, 0.75, 0.78, 1.0),
    "IfcBuildingElementProxy": (0.65, 0.68, 0.72, 1.0),
    "IfcSpace": (0.85, 0.92, 1.0, 0.20),
}


@dataclass
class ElementMesh:
    guid: str
    step_id: int
    ifc_class: str
    name: str
    mesh: pv.PolyData
    color: Tuple[float, float, float]
    opacity: float
    bounds: Tuple[float, float, float, float, float, float]
    center: Tuple[float, float, float]


class LoadedGeometry:
    def __init__(self):
        self.elements: Dict[str, ElementMesh] = {}  # guid -> ElementMesh
        self.classes: Set[str] = set()
        self.total_triangles: int = 0
        self.overall_bounds: Tuple[float, float, float, float, float, float] = (0, 0, 0, 0, 0, 0)

    @property
    def total_count(self) -> int:
        return len(self.elements)


def get_default_color_for_class(ifc_class: str) -> Tuple[Tuple[float, float, float], float]:
    """Get fallback RGB and opacity for an IFC class."""
    entry = DEFAULT_CATEGORY_COLORS.get(ifc_class)
    if entry:
        return (entry[0], entry[1], entry[2]), entry[3]
    return (0.68, 0.70, 0.73), 1.0


def extract_geometry(
    file_path: str,
    progress_callback: Optional[Callable[[int, str], None]] = None,
    cancel_token: Optional[CancellationToken] = None,
    num_threads: int = 4,
) -> LoadedGeometry:
    """
    Tessellates 3D solids from an IFC model using ifcopenshell.geom C++ kernel.
    Returns LoadedGeometry with a dictionary of ElementMesh objects keyed by GlobalId.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    if progress_callback:
        progress_callback(5, "Инициализация C++ геометрического ядра...")

    if cancel_token and cancel_token.is_cancelled:
        raise CancelledException()

    model = ifcopenshell.open(file_path)

    # Configure geometric kernel settings
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    settings.set(settings.WELD_VERTICES, True)
    settings.set(settings.CONVERT_BACK_UNITS, False)

    if progress_callback:
        progress_callback(15, "Подготовка 3D сцены и связей...")

    # Initialize iterator
    iterator = ifcopenshell.geom.iterator(settings, model, num_threads)
    if not iterator.initialize():
        # Model might have no geometric 3D shapes
        return LoadedGeometry()

    loaded = LoadedGeometry()
    all_bounds_min = np.array([float("inf"), float("inf"), float("inf")])
    all_bounds_max = np.array([float("-inf"), float("-inf"), float("-inf")])

    shape_index = 0
    while True:
        if cancel_token and cancel_token.is_cancelled:
            raise CancelledException()

        shape = iterator.get()
        shape_index += 1

        if shape_index % 50 == 0 and progress_callback:
            progress_callback(15 + min(75, shape_index // 20), f"Триангуляция 3D: элемент #{shape_index}...")

        geom = shape.geometry
        verts_raw = geom.verts
        faces_raw = geom.faces

        if len(verts_raw) >= 9 and len(faces_raw) >= 3:
            # Reshape into numpy arrays
            verts = np.array(verts_raw, dtype=np.float32).reshape((-1, 3))
            faces_arr = np.array(faces_raw, dtype=np.int32).reshape((-1, 3))

            # Build PyVista PolyData (prefix each triangle with '3')
            pad = np.full((len(faces_arr), 1), 3, dtype=np.int32)
            pv_faces = np.hstack([pad, faces_arr]).ravel()

            mesh = pv.PolyData(verts, pv_faces)
            mesh._obbTree = None  # prevent pyvista warning on cleanup

            # Compute element bounds and center
            b = mesh.bounds
            bounds = (b[0], b[1], b[2], b[3], b[4], b[5])
            center = (
                (b[0] + b[1]) * 0.5,
                (b[2] + b[3]) * 0.5,
                (b[4] + b[5]) * 0.5,
            )

            # Update overall scene bounds
            all_bounds_min = np.minimum(all_bounds_min, [b[0], b[2], b[4]])
            all_bounds_max = np.maximum(all_bounds_max, [b[1], b[3], b[5]])

            # Resolve element metadata
            step_id = shape.id
            guid = shape.guid

            elem = None
            try:
                elem = model.by_id(step_id)
            except Exception:
                pass

            elem_class = elem.is_a() if elem else shape.type or "IfcProduct"
            elem_name = getattr(elem, "Name", "") or getattr(shape, "name", "") or ""

            # Resolve color and opacity
            color, opacity = get_default_color_for_class(elem_class)
            if hasattr(geom, "materials") and geom.materials:
                mat = geom.materials[0]
                if hasattr(mat, "diffuse"):
                    diff = mat.diffuse
                    color = (float(diff.r()), float(diff.g()), float(diff.b()))
                if hasattr(mat, "transparency"):
                    opacity = max(0.0, min(1.0, 1.0 - float(mat.transparency)))

            loaded.elements[guid] = ElementMesh(
                guid=guid,
                step_id=step_id,
                ifc_class=elem_class,
                name=elem_name,
                mesh=mesh,
                color=color,
                opacity=opacity,
                bounds=bounds,
                center=center,
            )
            loaded.classes.add(elem_class)
            loaded.total_triangles += len(faces_arr)

        if not iterator.next():
            break

    if np.all(np.isfinite(all_bounds_min)) and np.all(np.isfinite(all_bounds_max)):
        loaded.overall_bounds = (
            float(all_bounds_min[0]), float(all_bounds_max[0]),
            float(all_bounds_min[1]), float(all_bounds_max[1]),
            float(all_bounds_min[2]), float(all_bounds_max[2]),
        )

    if progress_callback:
        progress_callback(100, f"Готово! Загружено {loaded.total_count} 3D элементов ({loaded.total_triangles:,} полигонов).")

    return loaded
