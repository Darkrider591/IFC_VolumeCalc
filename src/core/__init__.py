"""Core modules for IFC parsing, data models, aggregation and export."""
from .models import (
    AttributeMetadata,
    DataType,
    GroupingMode,
    GroupSummaryRow,
    AggregationSummary,
    ElementRecord,
    PropertySource,
)
from .ifc_parser import parse_ifc_file, ParseResult, CancellationToken, CancelledException
from .aggregator import calculate_aggregation
from .exporter import export_to_excel, export_to_csv

__all__ = [
    "AttributeMetadata",
    "DataType",
    "GroupingMode",
    "GroupSummaryRow",
    "AggregationSummary",
    "ElementRecord",
    "PropertySource",
    "parse_ifc_file",
    "ParseResult",
    "CancellationToken",
    "CancelledException",
    "calculate_aggregation",
    "export_to_excel",
    "export_to_csv",
]
