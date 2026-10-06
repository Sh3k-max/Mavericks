import pytest
from backend.app.services.legend_mapper import LegendMapper
from backend.app.services.spatial_association import SpatialAssociationEngine
from backend.app.utils.geometry import euclidean_distance, bbox_contains, alignment_score

def test_legend_mapper():
    mapper = LegendMapper()

    pt = mapper.identify_component("PT")
    assert pt["component_name"] == "Pressure Transmitter"
    assert pt["component_type"] == "Instrument"

    fcv = mapper.identify_component("FCV")
    assert fcv["component_name"] == "Flow Control Valve"
    assert fcv["component_type"] == "Valve"

    p = mapper.identify_component("P")
    assert p["component_name"] == "Centrifugal Pump"
    assert p["component_type"] == "Equipment"

    psv = mapper.identify_component("PSV")
    assert psv["component_name"] == "Pressure Safety Valve"
    assert psv["component_type"] == "Valve"

def test_geometry_helpers():
    assert euclidean_distance((0, 0), (3, 4)) == 5.0

    outer = (10, 10, 100, 100)
    inner = (20, 20, 50, 50)
    assert bbox_contains(outer, inner)

    # Horizontally aligned centers
    assert alignment_score((100, 50), (300, 50)) == 1.0
    # Vertically aligned centers
    assert alignment_score((50, 100), (50, 400)) == 1.0

def test_spatial_association():
    engine = SpatialAssociationEngine()

    tags = [{
        "id": "t1",
        "text": "PT-101",
        "parsed_prefix": "PT",
        "canonical_tag": "PT-101",
        "confidence": 0.95,
        "x1": 95,
        "y1": 95,
        "x2": 145,
        "y2": 115
    }]

    symbols = [{
        "id": "s1",
        "class_name": "Instrument",
        "category": "Instrument",
        "confidence": 0.90,
        "x1": 80,
        "y1": 80,
        "x2": 160,
        "y2": 160,
        "center_x": 120,
        "center_y": 120
    }]

    associations = engine.associate(tags, symbols, "sheet_test")
    assert len(associations) == 1
    assoc = associations[0]
    assert assoc["symbol"]["id"] == "s1"
    assert assoc["association_score"] > 0.80
    assert assoc["relationship_type"] == "CONTAINED_INSIDE"
