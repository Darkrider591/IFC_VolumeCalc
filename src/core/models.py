"""
Data models for IFC Parser and Aggregator.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class PropertySource(str, Enum):
    DIRECT = "Прямой атрибут"
    PROPERTY_SET = "Набор свойств (Pset)"
    QUANTITY_SET = "Количества (Qto)"
    TYPE_PROPERTY = "Свойство типа"


class DataType(str, Enum):
    NUMERIC = "Число"
    TEXT = "Текст"
    BOOLEAN = "Да/Нет"


class GroupingMode(str, Enum):
    BY_CLASS = "По классам IFC"
    BY_STOREY = "По этажам / уровням"
    BY_TYPE = "По типам элементов"
    NO_GROUPING = "Детальный реестр (без группировки)"


@dataclass
class AttributeMetadata:
    full_path: str                 # e.g. "BaseQuantities.NetVolume" or "Pset_WallCommon.LoadBearing" or "Entity.Name"
    display_name: str              # e.g. "NetVolume"
    source: PropertySource
    pset_name: Optional[str] = None
    data_type: DataType = DataType.TEXT
    unit: str = ""
    present_count: int = 0
    missing_count: int = 0

    @property
    def key(self) -> str:
        return self.full_path


@dataclass
class ElementRecord:
    global_id: str
    ifc_class: str
    name: str = ""
    tag: str = ""
    storey: str = "Не назначен"
    element_type: str = "Не указан"
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GroupSummaryRow:
    group_name: str
    total_elements: int
    present_count: int
    present_percent: float
    missing_count: int
    missing_percent: float
    total_sum: Optional[float] = None
    average: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    unit: str = ""
    missing_elements: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class AggregationSummary:
    attribute: AttributeMetadata
    total_elements: int
    present_count: int
    present_percent: float
    missing_count: int
    missing_percent: float
    total_sum: Optional[float] = None
    average: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    rows: List[GroupSummaryRow] = field(default_factory=list)
    missing_elements: List[Dict[str, str]] = field(default_factory=list)
