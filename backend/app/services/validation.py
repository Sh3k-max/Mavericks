from typing import List, Dict, Any, Tuple, Optional
from ..utils.logger import logger

class ValidationEngine:
    """
    Validates extracted components, tags, connections, and cross-sheet connectors.
    Evaluates:
    - Duplicate tags
    - Tag with no symbol / symbol with no tag
    - Low OCR or symbol confidence
    - Broken or disconnected pipelines
    - Suspicious spatial association scores
    - Unmatched cross-sheet connectors

    Supports BACKTRACKING:
    Recommends specific upstream stage targets ('ocr', 'spatial_association', 'line_detection')
    when anomalies are detected, allowing the pipeline to re-run only that module with adapted hyperparameters.
    """

    def validate_sheet_results(
        self,
        document_id: str,
        sheet_id: str,
        components: List[Dict[str, Any]],
        symbols: List[Dict[str, Any]],
        ocr_results: List[Dict[str, Any]],
        connections: List[Dict[str, Any]],
        connectors: List[Dict[str, Any]],
        backtrack_count: int = 0
    ) -> Dict[str, Any]:
        logger.info(f"Validating extraction results for sheet {sheet_id}")

        validation_items = []
        backtrack_suggestions = []

        # 1. Check for Duplicate Tags
        seen_tags = {}
        for comp in components:
            tag = comp.get("tag", "").strip()
            if not tag:
                continue
            if tag in seen_tags:
                prev_id = seen_tags[tag]
                validation_items.append({
                    "document_id": document_id,
                    "sheet_id": sheet_id,
                    "component_id": comp["id"],
                    "component_tag": tag,
                    "rule_name": "DUPLICATE_TAG",
                    "severity": "WARNING",
                    "message": f"Duplicate tag '{tag}' detected on sheet. May indicate a dual sensor or OCR misread.",
                    "details": {"duplicate_with": prev_id, "tag": tag},
                    "backtrack_suggested": "spatial_association" if backtrack_count < 2 else "",
                    "resolved": False
                })
                comp["validation_status"] = "WARNING"
                comp["validation_notes"] = f"Duplicate tag '{tag}'"
            else:
                seen_tags[tag] = comp["id"]

        # 2. Check for Low Confidence or Suspicious Association
        for comp in components:
            score = comp.get("association_score", 1.0)
            conf = comp.get("confidence", 1.0)
            tag = comp.get("tag", "")

            # Tag without detected symbol
            if comp.get("symbol_id") is None:
                validation_items.append({
                    "document_id": document_id,
                    "sheet_id": sheet_id,
                    "component_id": comp["id"],
                    "component_tag": tag,
                    "rule_name": "TAG_WITHOUT_SYMBOL",
                    "severity": "WARNING",
                    "message": f"Tag '{tag}' found without an enclosing or adjacent geometric symbol.",
                    "details": {"tag": tag, "score": score},
                    "backtrack_suggested": "symbol_detector" if backtrack_count < 2 else "",
                    "resolved": False
                })
                comp["validation_status"] = "WARNING"
                comp["validation_notes"] = "No geometric symbol detected nearby"

            elif score < 0.40:
                validation_items.append({
                    "document_id": document_id,
                    "sheet_id": sheet_id,
                    "component_id": comp["id"],
                    "component_tag": tag,
                    "rule_name": "SUSPICIOUS_SPATIAL_ASSOCIATION",
                    "severity": "WARNING",
                    "message": f"Low spatial association score ({score:.2f}) between tag '{tag}' and symbol.",
                    "details": {"score": score, "tag": tag},
                    "backtrack_suggested": "spatial_association" if backtrack_count < 2 else "",
                    "resolved": False
                })
                comp["validation_status"] = "WARNING"
                comp["validation_notes"] = f"Low association confidence: {score:.2f}"

            elif conf < 0.60:
                validation_items.append({
                    "document_id": document_id,
                    "sheet_id": sheet_id,
                    "component_id": comp["id"],
                    "component_tag": tag,
                    "rule_name": "LOW_CONFIDENCE",
                    "severity": "WARNING",
                    "message": f"Low OCR/detection confidence ({conf:.2f}) for '{tag}'.",
                    "details": {"confidence": conf, "tag": tag},
                    "backtrack_suggested": "ocr" if backtrack_count < 2 else "",
                    "resolved": False
                })
                comp["validation_status"] = "WARNING"
                comp["validation_notes"] = f"Low OCR confidence: {conf:.2f}"
            else:
                if not comp.get("validation_status") or comp.get("validation_status") == "pending":
                    comp["validation_status"] = "VALID"
                    comp["validation_notes"] = "All validation rules passed."

        # 3. Check for Disconnected Pipeline Components
        connected_comp_ids = set()
        for conn in connections:
            if conn.get("source_component_id"):
                connected_comp_ids.add(conn["source_component_id"])
            if conn.get("target_component_id"):
                connected_comp_ids.add(conn["target_component_id"])

        for comp in components:
            c_type = comp.get("component_type", "")
            # Instruments or Valves are typically expected to connect to lines
            if c_type in ["Valve", "Equipment"] and comp["id"] not in connected_comp_ids:
                validation_items.append({
                    "document_id": document_id,
                    "sheet_id": sheet_id,
                    "component_id": comp["id"],
                    "component_tag": comp.get("tag", ""),
                    "rule_name": "DISCONNECTED_PIPELINE",
                    "severity": "WARNING",
                    "message": f"{c_type} '{comp.get('tag')}' does not have any detected pipeline line connected to it.",
                    "details": {"component_id": comp["id"], "type": c_type},
                    "backtrack_suggested": "line_detector" if backtrack_count < 2 else "",
                    "resolved": False
                })
                if comp.get("validation_status") == "VALID":
                    comp["validation_status"] = "WARNING"
                    comp["validation_notes"] = "Disconnected from pipeline network"

        # 4. Check for Unmatched Connectors
        for conn in connectors:
            if not conn.get("matched", False):
                validation_items.append({
                    "document_id": document_id,
                    "sheet_id": sheet_id,
                    "component_id": None,
                    "component_tag": conn.get("connector_label", ""),
                    "rule_name": "UNMATCHED_CONNECTOR",
                    "severity": "WARNING",
                    "message": f"Off-page connector '{conn.get('connector_label')}' has no matching continuation on other sheets.",
                    "details": {"connector": conn.get("connector_label")},
                    "backtrack_suggested": "",
                    "resolved": False
                })

        # Determine if backtracking should be triggered
        should_backtrack = False
        target_stage = None
        reason = ""

        # Only allow max 2 backtracks per sheet to prevent infinite loops
        if backtrack_count < 2:
            stage_priority = ["ocr", "spatial_association", "line_detector"]
            for s in stage_priority:
                matches = [item for item in validation_items if item["backtrack_suggested"] == s]
                if len(matches) >= 2:  # If 2 or more issues point to this stage
                    should_backtrack = True
                    target_stage = s
                    reason = f"Backtracking triggered by {len(matches)} validation issues in {s}"
                    break

        error_count = sum(1 for v in validation_items if v["severity"] == "ERROR")
        warning_count = sum(1 for v in validation_items if v["severity"] == "WARNING")
        valid_count = sum(1 for c in components if c.get("validation_status") == "VALID")

        logger.info(
            f"Validation complete for sheet {sheet_id}: {valid_count} VALID, {warning_count} WARNINGS, {error_count} ERRORS"
        )

        return {
            "validation_items": validation_items,
            "valid_count": valid_count,
            "warning_count": warning_count,
            "error_count": error_count,
            "should_backtrack": should_backtrack,
            "target_stage": target_stage,
            "backtrack_reason": reason
        }
