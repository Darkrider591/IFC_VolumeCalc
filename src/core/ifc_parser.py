"""
High-performance IFC parser for extracting elements, spatial structure, and properties.
Optimized for large files by skipping 3D geometry and utilizing bulk relation lookups.
"""
import os
import re
from typing import Callable, Dict, List, Optional, Set, Tuple, Any
import ifcopenshell
import ifcopenshell.util.element
import pandas as pd

from .models import (
    AttributeMetadata,
    DataType,
    ElementRecord,
    PropertySource,
)


class CancelledException(Exception):
    """Raised when parsing is cancelled by user."""
    pass


class CancellationToken:
    def __init__(self):
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    @property
    def is_cancelled(self) -> bool:
        return self._is_cancelled


class ParseResult:
    def __init__(
        self,
        file_path: str,
        schema: str,
        elements: List[ElementRecord],
        attributes: Dict[str, AttributeMetadata],
        df: pd.DataFrame,
        storeys: List[str],
        ifc_classes: List[str],
        file_size_mb: float,
    ):
        self.file_path = file_path
        self.file_name = os.path.basename(file_path)
        self.file_size_mb = file_size_mb
        self.schema = schema
        self.elements = elements
        self.attributes = attributes
        self.df = df
        self.storeys = sorted(storeys)
        self.ifc_classes = sorted(ifc_classes)
        self.total_elements = len(elements)


def _detect_data_type(values: List[Any]) -> Tuple[DataType, str]:
    """
    Detect DataType (NUMERIC, TEXT, BOOLEAN) and possible unit from a sample of values.
    """
    non_null = [v for v in values if v is not None and v != ""]
    if not non_null:
        return DataType.TEXT, ""

    # Check boolean
    bool_count = sum(1 for v in non_null if isinstance(v, bool) or str(v).lower() in ["true", "false", ".t.", ".f."])
    if bool_count / len(non_null) > 0.8:
        return DataType.BOOLEAN, ""

    # Check numeric
    num_count = 0
    for v in non_null:
        if isinstance(v, (int, float)):
            num_count += 1
        elif isinstance(v, str):
            # Strip common units or spaces
            cleaned = v.strip().replace(" ", "").replace(",", ".")
            try:
                float(cleaned)
                num_count += 1
            except ValueError:
                pass

    if num_count / len(non_null) > 0.7:
        return DataType.NUMERIC, ""

    return DataType.TEXT, ""


def parse_ifc_file(
    file_path: str,
    progress_callback: Optional[Callable[[int, str], None]] = None,
    cancel_token: Optional[CancellationToken] = None,
) -> ParseResult:
    """
    Parse an IFC file without loading geometry. Extracts all physical elements,
    their spatial storeys, types, and all properties/quantities.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    file_size_mb = round(os.path.getsize(file_path) / (1024 * 1024), 2)

    if progress_callback:
        progress_callback(5, f"Открытие файла IFC ({file_size_mb} МБ)...")

    if cancel_token and cancel_token.is_cancelled:
        raise CancelledException()

    # Open IFC model without geometry
    model = ifcopenshell.open(file_path)
    schema = getattr(model, "schema", "IFC")

    if progress_callback:
        progress_callback(15, "Анализ пространственной структуры и типов...")

    if cancel_token and cancel_token.is_cancelled:
        raise CancelledException()

    # 1. Bulk mapping: element.id -> Storey Name
    element_to_storey: Dict[int, str] = {}
    try:
        for rel in model.by_type("IfcRelContainedInSpatialStructure"):
            structure = rel.RelatingStructure
            structure_name = getattr(structure, "Name", None) or getattr(structure, "LongName", None) or structure.is_a()
            for elem in getattr(rel, "RelatedElements", []):
                element_to_storey[elem.id()] = str(structure_name)
    except Exception:
        pass

    # 2. Bulk mapping: element.id -> Type Name
    element_to_type: Dict[int, str] = {}
    try:
        for rel in model.by_type("IfcRelDefinesByType"):
            rel_type = rel.RelatingType
            type_name = getattr(rel_type, "Name", None) or rel_type.is_a()
            for elem in getattr(rel, "RelatedObjects", []):
                element_to_type[elem.id()] = str(type_name)
    except Exception:
        pass

    if progress_callback:
        progress_callback(25, "Сбор физических элементов модели...")

    if cancel_token and cancel_token.is_cancelled:
        raise CancelledException()

    # 3. Retrieve all physical products (and spaces), excluding spatial containers
    spatial_container_types = {
        "IfcProject", "IfcSite", "IfcBuilding", "IfcBuildingStorey",
        "IfcSpaceType", "IfcDistributionSystem"
    }

    all_products = model.by_type("IfcProduct")
    elements_to_parse = [
        e for e in all_products
        if e.is_a() not in spatial_container_types and not (e.is_a("IfcSpatialStructureElement") and not e.is_a("IfcSpace"))
    ]

    total_count = len(elements_to_parse)
    if total_count == 0:
        # Fallback if model has unusual structure
        elements_to_parse = all_products
        total_count = len(elements_to_parse)

    if progress_callback:
        progress_callback(30, f"Найдено {total_count} элементов. Извлечение атрибутов...")

    # 4. Extract element records and properties
    records: List[ElementRecord] = []
    storeys_set: Set[str] = set()
    classes_set: Set[str] = set()

    # Track all observed properties: full_path -> list of values for type detection
    all_props_values: Dict[str, List[Any]] = {}
    prop_metadata_dict: Dict[str, AttributeMetadata] = {}

    # Standard direct entity attributes
    direct_attrs = ["Name", "Tag", "ObjectType", "Description", "PredefinedType"]
    for attr in direct_attrs:
        key = f"Entity.{attr}"
        all_props_values[key] = []
        prop_metadata_dict[key] = AttributeMetadata(
            full_path=key,
            display_name=attr,
            source=PropertySource.DIRECT,
            pset_name=None,
            data_type=DataType.TEXT,
        )

    # Pre-add GlobalId as direct attribute
    key_gid = "Entity.GlobalId"
    all_props_values[key_gid] = []
    prop_metadata_dict[key_gid] = AttributeMetadata(
        full_path=key_gid,
        display_name="GlobalId",
        source=PropertySource.DIRECT,
        pset_name=None,
        data_type=DataType.TEXT,
    )

    batch_size = max(1, total_count // 20)  # update progress ~20 times

    for idx, elem in enumerate(elements_to_parse):
        if cancel_token and cancel_token.is_cancelled:
            raise CancelledException()

        if idx > 0 and idx % batch_size == 0 and progress_callback:
            pct = 30 + int(50 * (idx / total_count))
            progress_callback(pct, f"Обработка свойств: {idx}/{total_count}...")

        elem_id = elem.id()
        elem_class = elem.is_a()
        classes_set.add(elem_class)

        global_id = getattr(elem, "GlobalId", str(elem_id))
        name = getattr(elem, "Name", "") or ""
        tag = getattr(elem, "Tag", "") or ""
        storey = element_to_storey.get(elem_id, "Без уровня")
        storeys_set.add(storey)
        elem_type = element_to_type.get(elem_id, "Не указан")

        props_map: Dict[str, Any] = {
            "Entity.GlobalId": global_id,
            "Entity.Name": name,
            "Entity.Tag": tag,
            "Entity.ObjectType": getattr(elem, "ObjectType", "") or "",
            "Entity.Description": getattr(elem, "Description", "") or "",
            "Entity.PredefinedType": getattr(elem, "PredefinedType", "") or "",
        }

        for k, v in props_map.items():
            all_props_values[k].append(v if v else None)

        # Extract Psets and Quantities using ifcopenshell utility
        try:
            psets = ifcopenshell.util.element.get_psets(elem, psets_only=False, qtos_only=False)
        except Exception:
            psets = {}

        for pset_name, pset_props in psets.items():
            if not isinstance(pset_props, dict):
                continue
            is_qto = pset_name.startswith("Qto_") or "Quantity" in pset_name or pset_name == "BaseQuantities"
            source = PropertySource.QUANTITY_SET if is_qto else PropertySource.PROPERTY_SET

            for prop_name, prop_val in pset_props.items():
                if prop_name == "id":
                    continue
                full_path = f"{pset_name}.{prop_name}"
                props_map[full_path] = prop_val

                if full_path not in all_props_values:
                    all_props_values[full_path] = []
                    prop_metadata_dict[full_path] = AttributeMetadata(
                        full_path=full_path,
                        display_name=prop_name,
                        source=source,
                        pset_name=pset_name,
                    )
                all_props_values[full_path].append(prop_val)

        records.append(
            ElementRecord(
                global_id=global_id,
                ifc_class=elem_class,
                name=name,
                tag=tag,
                storey=storey,
                element_type=elem_type,
                properties=props_map,
            )
        )

    if progress_callback:
        progress_callback(85, "Определение типов данных и подсчет статистики...")

    # Detect data types and count presence for each attribute
    for full_path, meta in prop_metadata_dict.items():
        vals = all_props_values.get(full_path, [])
        non_null_count = sum(1 for v in vals if v is not None and v != "")
        meta.present_count = non_null_count
        meta.missing_count = total_count - non_null_count

        dtype, unit = _detect_data_type(vals)
        meta.data_type = dtype
        meta.unit = unit

    if progress_callback:
        progress_callback(92, "Создание структуры данных для быстрого поиска...")

    # Build DataFrame for ultra-fast vectorized filtering and aggregation
    # We create flat rows with core columns + property dictionary access
    flat_data = []
    for r in records:
        row = {
            "global_id": r.global_id,
            "ifc_class": r.ifc_class,
            "name": r.name,
            "tag": r.tag,
            "storey": r.storey,
            "element_type": r.element_type,
        }
        row.update(r.properties)
        flat_data.append(row)

    df = pd.DataFrame(flat_data)

    if progress_callback:
        progress_callback(100, f"Готово! Обработано {total_count} элементов.")

    return ParseResult(
        file_path=file_path,
        schema=schema,
        elements=records,
        attributes=prop_metadata_dict,
        df=df,
        storeys=list(storeys_set),
        ifc_classes=list(classes_set),
        file_size_mb=file_size_mb,
    )
