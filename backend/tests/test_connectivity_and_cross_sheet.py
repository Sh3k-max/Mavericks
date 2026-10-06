import pytest
from backend.app.services.connectivity import ConnectivityEngine
from backend.app.services.cross_sheet import CrossSheetProcessor

def test_connectivity_engine():
    engine = ConnectivityEngine(connection_tolerance=50.0)

    components = [
        {"id": "comp-pump", "tag": "P-101", "component_type": "Equipment", "center_x": 100, "center_y": 200},
        {"id": "comp-valve", "tag": "FCV-101", "component_type": "Valve", "center_x": 300, "center_y": 200},
        {"id": "comp-pt", "tag": "PT-101", "component_type": "Instrument", "center_x": 500, "center_y": 200},
    ]

    # Pipeline line connecting pump to valve, and valve to PT
    lines = [
        {"start": [100, 200], "end": [300, 200], "length": 200, "confidence": 0.95, "source": "test"},
        {"start": [300, 200], "end": [500, 200], "length": 200, "confidence": 0.95, "source": "test"}
    ]

    res = engine.build_graph(components, lines, "sheet_test")
    assert res["node_count"] == 3
    assert len(res["connections"]) >= 1

    # Verify pump connects to valve
    tags_connected = {(c["source_tag"], c["target_tag"]) for c in res["connections"]}
    assert ("P-101", "FCV-101") in tags_connected or ("FCV-101", "P-101") in tags_connected

def test_cross_sheet_processor():
    processor = CrossSheetProcessor()

    all_connectors = {
        "sheet_1": [
            {
                "id": "c1",
                "sheet_id": "sheet_1",
                "sheet_number": 1,
                "connector_label": "CONN-A",
                "target_sheet_number": 2,
                "connected_component_id": "comp-pt",
                "confidence": 0.95
            }
        ],
        "sheet_2": [
            {
                "id": "c2",
                "sheet_id": "sheet_2",
                "sheet_number": 2,
                "connector_label": "CONN-A",
                "target_sheet_number": 1,
                "connected_component_id": "comp-vessel",
                "confidence": 0.95
            }
        ]
    }

    matches = processor.match_cross_sheet_connectors(all_connectors, {"sheet_1": 1, "sheet_2": 2})
    assert len(matches) == 1
    m = matches[0]
    assert m["source_sheet_number"] == 1
    assert m["target_sheet_number"] == 2
    assert m["source_connector"] == "CONN-A"
    assert m["target_connector"] == "CONN-A"
