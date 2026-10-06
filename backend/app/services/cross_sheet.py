import re
from typing import List, Dict, Any, Tuple, Optional
from ..utils.logger import logger
from ..utils.geometry import euclidean_distance

class CrossSheetProcessor:
    """
    Detects and associates off-page connectors across multiple P&ID sheets:
    - Identifies continuation arrow labels (e.g. 'CONN-A', 'TO SHEET 2', 'FROM SHEET 1')
    - Matches connectors between sheets having matching labels or complementary references
    - Links cross-sheet pipelines into a global multi-sheet graph.
    """

    OFF_PAGE_PATTERNS = [
        re.compile(r"(?:TO|FROM)\s+SH(?:EE)?T\s*[:#\-]?\s*(?P<target_sheet>\d+)", re.IGNORECASE),
        re.compile(r"(?:TO|FROM)\s+DWG\s*[:#\-]?\s*(?P<target_sheet>\d+)", re.IGNORECASE),
        re.compile(r"CONN[\-_]?(?P<conn_id>[A-Z0-9]+)", re.IGNORECASE),
        re.compile(r"OPC[\-_]?(?P<conn_id>[A-Z0-9]+)", re.IGNORECASE),
    ]

    def find_connectors_on_sheet(
        self,
        sheet_id: str,
        sheet_number: int,
        ocr_results: List[Dict[str, Any]],
        symbols: List[Dict[str, Any]],
        components: List[Dict[str, Any]],
        sheet_width: float,
        sheet_height: float
    ) -> List[Dict[str, Any]]:
        logger.info(f"Scanning sheet {sheet_number} ({sheet_id}) for off-page connectors")

        connectors = []

        # Connector symbols are typically near sheet edges (margins < 20% from border)
        edge_margin_x = sheet_width * 0.22
        edge_margin_y = sheet_height * 0.22

        # 1. Check OCR text tokens for off-page references
        for ocr in ocr_results:
            text = ocr["text"].strip()
            cx = (ocr["x1"] + ocr["x2"]) / 2.0
            cy = (ocr["y1"] + ocr["y2"]) / 2.0

            is_near_edge = (
                cx < edge_margin_x or cx > (sheet_width - edge_margin_x) or
                cy < edge_margin_y or cy > (sheet_height - edge_margin_y)
            )

            matched_label = None
            target_sheet_num = None
            direction = "out"

            for pat in self.OFF_PAGE_PATTERNS:
                m = pat.search(text)
                if m:
                    if "target_sheet" in m.groupdict() and m.group("target_sheet"):
                        target_sheet_num = int(m.group("target_sheet"))
                    if "conn_id" in m.groupdict() and m.group("conn_id"):
                        matched_label = f"CONN-{m.group('conn_id').upper()}"
                    else:
                        matched_label = text.upper()
                    
                    if "FROM" in text.upper():
                        direction = "in"
                    break

            # If it explicitly matches connector patterns, or is tagged near edge
            if matched_label or (is_near_edge and any(k in text.upper() for k in ["CONN", "OPC", "SHT", "SHEET"])):
                label = matched_label or text.upper()

                # Find nearest connected component on this sheet
                nearest_comp_id = None
                min_dist = float("inf")
                for comp in components:
                    d = euclidean_distance((cx, cy), (comp["center_x"], comp["center_y"]))
                    if d < min_dist and d < 350.0:
                        min_dist = d
                        nearest_comp_id = comp["id"]

                connectors.append({
                    "sheet_id": sheet_id,
                    "sheet_number": sheet_number,
                    "connector_label": label,
                    "target_sheet_number": target_sheet_num,
                    "direction": direction,
                    "connected_component_id": nearest_comp_id,
                    "x1": ocr["x1"],
                    "y1": ocr["y1"],
                    "x2": ocr["x2"],
                    "y2": ocr["y2"],
                    "confidence": ocr.get("confidence", 0.85),
                    "matched": False
                })

        # Also check detected symbols of class 'Connector'
        for sym in symbols:
            if sym.get("class_name") == "Connector" or sym.get("category") == "Connector":
                cx, cy = sym["center_x"], sym["center_y"]
                # Avoid duplicate with OCR token
                already_captured = any(
                    abs(c["x1"] - sym["x1"]) < 40 and abs(c["y1"] - sym["y1"]) < 40
                    for c in connectors
                )
                if not already_captured:
                    connectors.append({
                        "sheet_id": sheet_id,
                        "sheet_number": sheet_number,
                        "connector_label": f"OPC-SH{sheet_number}",
                        "target_sheet_number": None,
                        "direction": "out" if cx > sheet_width / 2 else "in",
                        "connected_component_id": None,
                        "x1": sym["x1"],
                        "y1": sym["y1"],
                        "x2": sym["x2"],
                        "y2": sym["y2"],
                        "confidence": sym.get("confidence", 0.80),
                        "matched": False
                    })

        return connectors

    def match_cross_sheet_connectors(
        self,
        all_sheet_connectors: Dict[str, List[Dict[str, Any]]],
        sheet_id_to_num: Dict[str, int]
    ) -> List[Dict[str, Any]]:
        """
        Pairs connectors between different sheets based on:
        1. Exact label match (e.g. CONN-A on Sheet 1 <-> CONN-A on Sheet 2)
        2. Explicit sheet pointers (e.g. 'TO SHEET 2' on Sheet 1 <-> 'FROM SHEET 1' on Sheet 2)
        """
        logger.info("Matching cross-sheet connectors across all sheets")
        matches = []
        all_connectors = []
        for sheet_id, conns in all_sheet_connectors.items():
            for c in conns:
                all_connectors.append(c)

        used_pairs = set()

        for i, c1 in enumerate(all_connectors):
            if i in used_pairs:
                continue

            for j, c2 in enumerate(all_connectors):
                if j <= i or j in used_pairs:
                    continue

                # Must be on different sheets!
                if c1["sheet_id"] == c2["sheet_id"]:
                    continue

                matched = False
                match_confidence = 0.0

                label1 = c1["connector_label"].strip().upper()
                label2 = c2["connector_label"].strip().upper()

                # Clean labels for matching: strip 'TO ' or 'FROM ' prefixes
                clean_l1 = re.sub(r"^(TO|FROM)\s+", "", label1)
                clean_l2 = re.sub(r"^(TO|FROM)\s+", "", label2)

                # Match Criteria 1: Exact cleaned identifier match
                if clean_l1 == clean_l2 and len(clean_l1) >= 2:
                    matched = True
                    match_confidence = 0.98

                # Match Criteria 2: Explicit sheet cross-reference
                s1_num = c1["sheet_number"]
                s2_num = c2["sheet_number"]
                if (c1.get("target_sheet_number") == s2_num and c2.get("target_sheet_number") == s1_num):
                    matched = True
                    match_confidence = 0.95
                elif (c1.get("target_sheet_number") == s2_num or c2.get("target_sheet_number") == s1_num) and clean_l1 == clean_l2:
                    matched = True
                    match_confidence = 0.96

                if matched:
                    c1["matched"] = True
                    c2["matched"] = True
                    c1["matched_connector_id"] = c2.get("id")
                    c2["matched_connector_id"] = c1.get("id")
                    c1["target_sheet_id"] = c2["sheet_id"]
                    c2["target_sheet_id"] = c1["sheet_id"]
                    used_pairs.add(i)
                    used_pairs.add(j)

                    matches.append({
                        "source_sheet_id": c1["sheet_id"],
                        "source_sheet_number": c1["sheet_number"],
                        "source_connector": c1["connector_label"],
                        "source_component_id": c1["connected_component_id"],
                        "target_sheet_id": c2["sheet_id"],
                        "target_sheet_number": c2["sheet_number"],
                        "target_connector": c2["connector_label"],
                        "target_component_id": c2["connected_component_id"],
                        "confidence": match_confidence
                    })

        logger.info(f"Cross-sheet processor identified {len(matches)} valid inter-sheet connections")
        return matches
