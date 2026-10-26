"""
Unit tests for IFC Parser, Aggregator, and Exporter.
"""
import os
import tempfile
import pytest

from src.core.ifc_parser import parse_ifc_file
from src.core.aggregator import calculate_aggregation
from src.core.models import GroupingMode, DataType
from src.core.exporter import export_to_excel, export_to_csv

SAMPLE_HOUSE = r"d:\IT\Dev\IFC\ifc viktor platform\ifc-viewer-1.0.1\AC20-FZK-Haus (Sample IFC).ifc"
SAMPLE_PIPING = r"d:\IT\Dev\IFC\ifc_otvod_py\009_Piping (1).ifc"


def test_parse_sample_house():
    assert os.path.exists(SAMPLE_HOUSE), "Sample IFC file must exist"
    
    progress_updates = []
    def on_progress(pct, msg):
        progress_updates.append((pct, msg))

    res = parse_ifc_file(SAMPLE_HOUSE, progress_callback=on_progress)
    
    assert res.total_elements > 0
    assert len(res.elements) == res.total_elements
    assert any("Wall" in c for c in res.ifc_classes)
    assert len(res.attributes) > 0
    assert len(progress_updates) > 0
    assert progress_updates[-1][0] == 100

    # Direct attribute test
    assert "Entity.Name" in res.attributes
    assert "Entity.GlobalId" in res.attributes


def test_aggregation_direct_attribute():
    res = parse_ifc_file(SAMPLE_HOUSE)
    
    summary = calculate_aggregation(
        parse_result=res,
        attribute_path="Entity.Name",
        grouping_mode=GroupingMode.BY_CLASS
    )
    
    assert summary.total_elements == res.total_elements
    assert summary.present_count > 0
    assert summary.present_percent + summary.missing_percent == pytest.approx(100.0, 0.1)
    assert len(summary.rows) > 0


def test_aggregation_numeric_quantity():
    res = parse_ifc_file(SAMPLE_HOUSE)
    
    # Find any quantity attribute in the model
    quant_attr = None
    for k in res.attributes.keys():
        if "Volume" in k or "Area" in k or "Length" in k:
            quant_attr = k
            break
            
    if quant_attr:
        summary = calculate_aggregation(
            parse_result=res,
            attribute_path=quant_attr,
            grouping_mode=GroupingMode.BY_CLASS
        )
        assert summary.present_count > 0
        assert summary.total_sum is not None
        assert summary.total_sum > 0


def test_piping_missing_attribute():
    assert os.path.exists(SAMPLE_PIPING), "Piping IFC file must exist"
    res = parse_ifc_file(SAMPLE_PIPING)
    
    # Check Smart Plant 3D or Identifier Data properties
    target_attr = None
    for k in res.attributes.keys():
        if "Smart Plant" in k or "Identifier Data" in k:
            target_attr = k
            break
            
    if target_attr:
        summary = calculate_aggregation(
            parse_result=res,
            attribute_path=target_attr,
            grouping_mode=GroupingMode.BY_CLASS
        )
        # Should have both present and missing
        assert summary.present_count > 0
        assert summary.missing_count > 0
        assert len(summary.missing_elements) == summary.missing_count


def test_export_excel_and_csv():
    res = parse_ifc_file(SAMPLE_HOUSE)
    summary = calculate_aggregation(
        parse_result=res,
        attribute_path="Entity.Name",
        grouping_mode=GroupingMode.BY_CLASS
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        excel_path = os.path.join(tmp_dir, "test_summary.xlsx")
        csv_path = os.path.join(tmp_dir, "test_summary.csv")

        export_to_excel(summary, res.file_name, excel_path)
        export_to_csv(summary, csv_path)

        assert os.path.exists(excel_path)
        assert os.path.getsize(excel_path) > 1000
        assert os.path.exists(csv_path)
        assert os.path.getsize(csv_path) > 100
