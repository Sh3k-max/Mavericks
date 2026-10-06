from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from ..utils.logger import logger
from ..utils.geometry import (
    euclidean_distance,
    calculate_center,
    bbox_iou,
    bbox_contains,
    is_point_inside_bbox,
    alignment_score,
    min_distance_between_bboxes
)

class SpatialAssociationEngine:
    """
    Associates OCR tags with detected symbols using a multi-factor scoring model:
    - Euclidean Distance Score
    - Bounding Box Topological Relation (Containment, Overlap, Proximity)
    - Geometric Alignment Score (Vertical / Horizontal collinearity)
    - Semantic Class Compatibility (e.g., Transmitter tags map to Instrument bubbles)
    """

    def __init__(
        self,
        max_search_radius: float = 220.0,
        weight_distance: float = 0.35,
        weight_bbox_relation: float = 0.25,
        weight_alignment: float = 0.15,
        weight_compatibility: float = 0.25
    ):
        self.max_search_radius = max_search_radius
        self.w_dist = weight_distance
        self.w_bbox = weight_bbox_relation
        self.w_align = weight_alignment
        self.w_comp = weight_compatibility

    def associate(
        self,
        tag_candidates: List[Dict[str, Any]],
        symbols: List[Dict[str, Any]],
        sheet_id: str
    ) -> List[Dict[str, Any]]:
        logger.info(
            f"Associating {len(tag_candidates)} tags with {len(symbols)} symbols on sheet {sheet_id}"
        )

        associations = []
        assigned_symbols = set()

        # Build candidate pairs with scores
        candidate_pairs = []

        for tag in tag_candidates:
            t_box = (tag["x1"], tag["y1"], tag["x2"], tag["y2"])
            t_cx, t_cy = calculate_center(*t_box)
            t_prefix = tag.get("parsed_prefix", "")

            for sym in symbols:
                s_box = (sym["x1"], sym["y1"], sym["x2"], sym["y2"])
                s_cx, s_cy = sym["center_x"], sym["center_y"]
                s_cat = sym.get("category", "")
                s_cls = sym.get("class_name", "")

                dist = euclidean_distance((t_cx, t_cy), (s_cx, s_cy))
                if dist > self.max_search_radius:
                    continue

                # 1. Distance score (higher for closer)
                dist_score = max(0.0, 1.0 - (dist / self.max_search_radius))

                # 2. Bounding Box Topological Relationship
                # Check containment: tag inside symbol bubble
                if bbox_contains(s_box, t_box, tolerance=10.0) or is_point_inside_bbox(t_cx, t_cy, s_box, tolerance=10.0):
                    bbox_score = 1.0
                    rel_type = "CONTAINED_INSIDE"
                elif bbox_iou(s_box, t_box) > 0.1:
                    bbox_score = 0.85
                    rel_type = "OVERLAPPING"
                else:
                    edge_dist = min_distance_between_bboxes(s_box, t_box)
                    bbox_score = max(0.2, 1.0 - (edge_dist / 120.0))
                    rel_type = "ADJACENT_PROXIMITY"

                # 3. Alignment Score (horizontal or vertical stacking)
                align_score = alignment_score((t_cx, t_cy), (s_cx, s_cy))

                # 4. Class & Category Compatibility
                comp_score = self._compute_class_compatibility(t_prefix, s_cat, s_cls)

                # Weighted Composite Score
                total_score = (
                    self.w_dist * dist_score +
                    self.w_bbox * bbox_score +
                    self.w_align * align_score +
                    self.w_comp * comp_score
                )

                candidate_pairs.append({
                    "tag": tag,
                    "symbol": sym,
                    "distance": round(dist, 2),
                    "association_score": round(float(total_score), 4),
                    "relationship_type": rel_type,
                    "sub_scores": {
                        "distance_score": round(dist_score, 4),
                        "bbox_score": round(bbox_score, 4),
                        "align_score": round(align_score, 4),
                        "comp_score": round(comp_score, 4)
                    }
                })

        # Sort candidate pairs descending by association score
        candidate_pairs.sort(key=lambda p: p["association_score"], reverse=True)

        assigned_tags = set()

        for pair in candidate_pairs:
            tag_id = pair["tag"].get("id", pair["tag"]["text"])
            sym_id = pair["symbol"].get("id", f"{pair['symbol']['x1']}_{pair['symbol']['y1']}")

            if tag_id in assigned_tags:
                continue

            # We allow multiple tags to associate if equipment is large (e.g. pump with motor),
            # but for instruments, each symbol typically has 1 tag
            if sym_id in assigned_symbols and pair["symbol"]["category"] == "Instrument":
                continue

            # Minimum acceptance threshold
            if pair["association_score"] >= 0.35:
                assigned_tags.add(tag_id)
                assigned_symbols.add(sym_id)
                associations.append(pair)

        # Handle unassociated tags: Create a synthetic/virtual symbol bbox around the tag
        for tag in tag_candidates:
            tag_id = tag.get("id", tag["text"])
            if tag_id not in assigned_tags:
                t_box = (tag["x1"], tag["y1"], tag["x2"], tag["y2"])
                t_cx, t_cy = calculate_center(*t_box)
                associations.append({
                    "tag": tag,
                    "symbol": None,
                    "distance": 0.0,
                    "association_score": 0.50,
                    "relationship_type": "TAG_ONLY_VIRTUAL",
                    "sub_scores": {}
                })

        logger.info(f"Spatial association produced {len(associations)} matches")
        return associations

    def _compute_class_compatibility(self, tag_prefix: str, symbol_category: str, symbol_class: str) -> float:
        prefix = tag_prefix.upper()
        
        # Instrument tags
        if any(prefix.startswith(p) for p in ["PT", "TT", "FT", "LT", "PI", "TI", "FI", "LI"]):
            if symbol_category == "Instrument" or symbol_class in ["Instrument", "PT", "TT", "FT"]:
                return 1.0
            if symbol_category == "Valve":
                return 0.30
            return 0.40

        # Valve tags
        if any(prefix.startswith(v) for v in ["FCV", "PCV", "TCV", "LCV", "PSV", "XV", "HV", "MOV", "LV"]):
            if symbol_category == "Valve" or symbol_class in ["Valve", "FCV", "PSV"]:
                return 1.0
            if symbol_category == "Instrument":
                return 0.50
            return 0.30

        # Equipment tags
        if prefix in ["P", "PU", "PUMP", "TK", "T", "V", "E", "C", "CMP", "M"]:
            if symbol_category == "Equipment" or symbol_class in ["Pump", "Vessel", "Tank", "Compressor"]:
                return 1.0
            return 0.30

        # Connector tags
        if prefix in ["CONN", "OPC"] or "CONN" in prefix:
            if symbol_category == "Connector" or symbol_class == "Connector":
                return 1.0
            return 0.50

        return 0.60
