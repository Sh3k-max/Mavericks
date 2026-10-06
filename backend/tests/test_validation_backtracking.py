import pytest
from backend.app.services.validation import ValidationEngine

def test_validation_engine_duplicate_detection():
    validator = ValidationEngine()

    components = [
        {"id": "c1", "tag": "PT-101", "component_type": "Instrument", "symbol_id": "s1", "confidence": 0.95, "association_score": 0.9},
        {"id": "c2", "tag": "PT-101", "component_type": "Instrument", "symbol_id": "s2", "confidence": 0.95, "association_score": 0.88},
    ]

    summary = validator.validate_sheet_results(
        document_id="doc1",
        sheet_id="sheet1",
        components=components,
        symbols=[{"id": "s1"}, {"id": "s2"}],
        ocr_results=[],
        connections=[{"source_component_id": "c1", "target_component_id": "c2"}],
        connectors=[]
    )

    duplicate_rules = [i for i in summary["validation_items"] if i["rule_name"] == "DUPLICATE_TAG"]
    assert len(duplicate_rules) >= 1
    assert duplicate_rules[0]["severity"] == "WARNING"

def test_validation_engine_backtracking_trigger():
    validator = ValidationEngine()

    # Create components with low spatial association scores to trigger backtracking
    components = [
        {"id": "c1", "tag": "PT-101", "component_type": "Instrument", "symbol_id": "s1", "confidence": 0.9, "association_score": 0.25},
        {"id": "c2", "tag": "TT-102", "component_type": "Instrument", "symbol_id": "s2", "confidence": 0.9, "association_score": 0.28},
    ]

    summary = validator.validate_sheet_results(
        document_id="doc1",
        sheet_id="sheet1",
        components=components,
        symbols=[{"id": "s1"}, {"id": "s2"}],
        ocr_results=[],
        connections=[],
        connectors=[],
        backtrack_count=0
    )

    assert summary["should_backtrack"] is True
    assert summary["target_stage"] == "spatial_association"
