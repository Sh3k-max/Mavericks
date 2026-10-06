import io
import json
import pandas as pd
from typing import Dict, Any, List
from ..utils.logger import logger

class Exporter:
    """
    Exports extracted P&ID engineering component data to Excel, CSV, and hierarchical JSON.
    """

    @staticmethod
    def export_excel(components: List[Dict[str, Any]], doc_info: Dict[str, Any] = None) -> bytes:
        logger.info(f"Generating Excel export for {len(components)} components")
        rows = []
        for c in components:
            rows.append({
                "Tag": c.get("tag", ""),
                "Component Name": c.get("component_name", ""),
                "Type": c.get("component_type", ""),
                "Sheet": c.get("sheet_number", 1),
                "X": round(c.get("center_x", 0.0), 1),
                "Y": round(c.get("center_y", 0.0), 1),
                "Confidence": f"{round(c.get('confidence', 0.0) * 100, 1)}%",
                "Validation Status": c.get("validation_status", "VALID"),
                "Validation Notes": c.get("validation_notes", "")
            })

        df = pd.DataFrame(rows)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Components")
        return output.getvalue()

    @staticmethod
    def export_csv(components: List[Dict[str, Any]]) -> str:
        logger.info(f"Generating CSV export for {len(components)} components")
        rows = []
        for c in components:
            rows.append({
                "Tag": c.get("tag", ""),
                "Component Name": c.get("component_name", ""),
                "Type": c.get("component_type", ""),
                "Sheet": c.get("sheet_number", 1),
                "X": round(c.get("center_x", 0.0), 1),
                "Y": round(c.get("center_y", 0.0), 1),
                "Confidence": f"{round(c.get('confidence', 0.0) * 100, 1)}%",
                "Validation Status": c.get("validation_status", "VALID"),
                "Validation Notes": c.get("validation_notes", "")
            })

        df = pd.DataFrame(rows)
        return df.to_csv(index=False)

    @staticmethod
    def export_json(document_data: Dict[str, Any]) -> str:
        logger.info(f"Generating hierarchical JSON export for document {document_data.get('id')}")
        return json.dumps(document_data, indent=2, default=str)
