"""
Data aggregator for IFC elements and attributes.
Performs grouping, summation, presence analysis, and statistical calculations.
"""
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import numpy as np

from .models import (
    AggregationSummary,
    AttributeMetadata,
    DataType,
    GroupingMode,
    GroupSummaryRow,
)
from .ifc_parser import ParseResult


def _parse_numeric(val: Any) -> Optional[float]:
    """Safely parse a value into float."""
    if val is None or val == "" or pd.isna(val):
        return None
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, bool):
        return None
    try:
        cleaned = str(val).strip().replace(" ", "").replace(",", ".")
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def calculate_aggregation(
    parse_result: ParseResult,
    attribute_path: str,
    grouping_mode: GroupingMode = GroupingMode.BY_CLASS,
    search_filter: str = "",
    only_present: bool = False,
    only_missing: bool = False,
    selected_classes: Optional[List[str]] = None,
    selected_storeys: Optional[List[str]] = None,
) -> AggregationSummary:
    """
    Compute overall summary and grouped pivot breakdown for a given attribute.
    """
    attr_meta = parse_result.attributes.get(attribute_path)
    if not attr_meta:
        # Fallback if attribute was not pre-registered
        attr_meta = AttributeMetadata(
            full_path=attribute_path,
            display_name=attribute_path.split(".")[-1],
            source="Свойство",
            pset_name=attribute_path.split(".")[0] if "." in attribute_path else None,
            data_type=DataType.TEXT,
        )

    df = parse_result.df

    # Apply class and storey filters if specified
    if selected_classes is not None and len(selected_classes) > 0:
        df = df[df["ifc_class"].isin(selected_classes)]
    if selected_storeys is not None and len(selected_storeys) > 0:
        df = df[df["storey"].isin(selected_storeys)]

    # If column not in df, create empty column
    if attribute_path not in df.columns:
        df[attribute_path] = None

    # Determine presence for each element
    # Value is present if it's not None, not empty string, and not NaN
    is_present_series = df[attribute_path].apply(
        lambda x: x is not None and x != "" and not pd.isna(x)
    )

    if only_present:
        df = df[is_present_series]
        is_present_series = df[attribute_path].apply(lambda x: True)
    elif only_missing:
        df = df[~is_present_series]
        is_present_series = df[attribute_path].apply(lambda x: False)

    total_elements = len(df)
    present_count = int(is_present_series.sum())
    missing_count = total_elements - present_count

    present_percent = round((present_count / total_elements * 100), 1) if total_elements > 0 else 0.0
    missing_percent = round((missing_count / total_elements * 100), 1) if total_elements > 0 else 0.0

    # Numeric series
    numeric_series = df[attribute_path].apply(_parse_numeric).dropna()
    is_numeric = attr_meta.data_type == DataType.NUMERIC or len(numeric_series) > 0.5 * max(1, present_count)

    total_sum: Optional[float] = None
    average: Optional[float] = None
    min_val: Optional[float] = None
    max_val: Optional[float] = None

    if is_numeric and len(numeric_series) > 0:
        total_sum = round(float(numeric_series.sum()), 4)
        average = round(float(numeric_series.mean()), 4)
        min_val = round(float(numeric_series.min()), 4)
        max_val = round(float(numeric_series.max()), 4)

    # Collect missing elements summary (for QA/QC report)
    missing_elements: List[Dict[str, str]] = []
    missing_subset = df[~is_present_series]
    for _, row in missing_subset.iterrows():
        missing_elements.append({
            "global_id": str(row.get("global_id", "")),
            "ifc_class": str(row.get("ifc_class", "")),
            "name": str(row.get("name", "")),
            "tag": str(row.get("tag", "")),
            "storey": str(row.get("storey", "")),
            "element_type": str(row.get("element_type", "")),
        })

    # Grouping breakdown
    group_col_map = {
        GroupingMode.BY_CLASS: "ifc_class",
        GroupingMode.BY_STOREY: "storey",
        GroupingMode.BY_TYPE: "element_type",
    }

    rows: List[GroupSummaryRow] = []

    if grouping_mode == GroupingMode.NO_GROUPING:
        # Detailed row for each element
        for _, row in df.iterrows():
            elem_val = row.get(attribute_path)
            has_val = elem_val is not None and elem_val != "" and not pd.isna(elem_val)
            num_v = _parse_numeric(elem_val)

            g_name = f"{row.get('ifc_class', '')}: {row.get('name', '') or row.get('global_id', '')}"
            rows.append(
                GroupSummaryRow(
                    group_name=g_name,
                    total_elements=1,
                    present_count=1 if has_val else 0,
                    present_percent=100.0 if has_val else 0.0,
                    missing_count=0 if has_val else 1,
                    missing_percent=0.0 if has_val else 100.0,
                    total_sum=num_v,
                    average=num_v,
                    min_value=num_v,
                    max_value=num_v,
                    unit=attr_meta.unit,
                    missing_elements=[] if has_val else [{
                        "global_id": str(row.get("global_id", "")),
                        "ifc_class": str(row.get("ifc_class", "")),
                        "name": str(row.get("name", "")),
                        "tag": str(row.get("tag", "")),
                        "storey": str(row.get("storey", "")),
                        "element_type": str(row.get("element_type", "")),
                    }]
                )
            )
    else:
        group_col = group_col_map.get(grouping_mode, "ifc_class")
        # Perform group-by
        groups = df.groupby(group_col, dropna=False)

        for g_name, group_df in groups:
            g_name_str = str(g_name) if g_name is not None and not pd.isna(g_name) and g_name != "" else "Не определено"
            
            # Apply search filter to group name if provided
            if search_filter and search_filter.lower() not in g_name_str.lower():
                continue

            g_total = len(group_df)
            g_present_s = group_df[attribute_path].apply(
                lambda x: x is not None and x != "" and not pd.isna(x)
            )
            g_present = int(g_present_s.sum())
            g_missing = g_total - g_present
            g_pres_pct = round((g_present / g_total * 100), 1) if g_total > 0 else 0.0
            g_miss_pct = round((g_missing / g_total * 100), 1) if g_total > 0 else 0.0

            g_nums = group_df[attribute_path].apply(_parse_numeric).dropna()
            g_sum = round(float(g_nums.sum()), 4) if len(g_nums) > 0 else None
            g_avg = round(float(g_nums.mean()), 4) if len(g_nums) > 0 else None
            g_min = round(float(g_nums.min()), 4) if len(g_nums) > 0 else None
            g_max = round(float(g_nums.max()), 4) if len(g_nums) > 0 else None

            # Collect missing elements for this group
            g_missing_elems: List[Dict[str, str]] = []
            for _, r in group_df[~g_present_s].iterrows():
                g_missing_elems.append({
                    "global_id": str(r.get("global_id", "")),
                    "ifc_class": str(r.get("ifc_class", "")),
                    "name": str(r.get("name", "")),
                    "tag": str(r.get("tag", "")),
                    "storey": str(r.get("storey", "")),
                    "element_type": str(r.get("element_type", "")),
                })

            rows.append(
                GroupSummaryRow(
                    group_name=g_name_str,
                    total_elements=g_total,
                    present_count=g_present,
                    present_percent=g_pres_pct,
                    missing_count=g_missing,
                    missing_percent=g_miss_pct,
                    total_sum=g_sum,
                    average=g_avg,
                    min_value=g_min,
                    max_value=g_max,
                    unit=attr_meta.unit,
                    missing_elements=g_missing_elems,
                )
            )

        # Sort rows by total elements descending
        rows.sort(key=lambda r: r.total_elements, reverse=True)

    return AggregationSummary(
        attribute=attr_meta,
        total_elements=total_elements,
        present_count=present_count,
        present_percent=present_percent,
        missing_count=missing_count,
        missing_percent=missing_percent,
        total_sum=total_sum,
        average=average,
        min_value=min_val,
        max_value=max_val,
        rows=rows,
        missing_elements=missing_elements,
    )
