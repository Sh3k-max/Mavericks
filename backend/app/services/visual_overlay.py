import os
import cv2
import numpy as np
from typing import List, Dict, Any
from ..utils.logger import logger

class VisualOverlayGenerator:
    """
    Renders high-resolution visual overlays on P&ID sheets:
    - Color-coded component bounding boxes (Instrument=Emerald, Valve=Orange, Equipment=Purple, Connector=Blue)
    - OCR token boxes and confidence badges
    - Traced pipeline routes
    - Cross-sheet continuation arrows
    """

    COLOR_PALETTE = {
        "Instrument": (0, 180, 50),     # Emerald green (BGR: 50, 180, 0)
        "Valve": (0, 140, 255),          # Amber / Orange
        "Equipment": (180, 50, 180),     # Purple
        "Connector": (255, 100, 0),      # Blue
        "Pipeline": (0, 0, 220),         # Crimson Red
        "OCR": (200, 200, 50),           # Cyan / Yellow-Blue
    }

    def generate_overlay(
        self,
        base_image_path: str,
        components: List[Dict[str, Any]],
        symbols: List[Dict[str, Any]],
        ocr_results: List[Dict[str, Any]],
        connections: List[Dict[str, Any]],
        connectors: List[Dict[str, Any]],
        output_path: str
    ) -> str:
        logger.info(f"Generating visual overlay on {base_image_path} -> {output_path}")

        img = cv2.imread(base_image_path)
        if img is None:
            raise FileNotFoundError(f"Cannot load image {base_image_path}")

        overlay = img.copy()

        # 1. Draw Pipeline Connections
        for conn in connections:
            path = conn.get("path_points", [])
            if len(path) >= 2:
                pts = np.array(path, np.int32).reshape((-1, 1, 2))
                cv2.polylines(overlay, [pts], isClosed=False, color=(0, 0, 230), thickness=3, lineType=cv2.LINE_AA)
            else:
                sx, sy = int(conn["start_x"]), int(conn["start_y"])
                ex, ey = int(conn["end_x"]), int(conn["end_y"])
                cv2.line(overlay, (sx, sy), (ex, ey), (0, 0, 230), thickness=3, lineType=cv2.LINE_AA)

        # 2. Draw OCR bounding boxes (subtle)
        for ocr in ocr_results:
            x1, y1 = int(ocr["x1"]), int(ocr["y1"])
            x2, y2 = int(ocr["x2"]), int(ocr["y2"])
            cv2.rectangle(overlay, (x1, y1), (x2, y2), (200, 180, 50), 1, cv2.LINE_AA)

        # 3. Draw Detected Symbols
        for sym in symbols:
            x1, y1 = int(sym["x1"]), int(sym["y1"])
            x2, y2 = int(sym["x2"]), int(sym["y2"])
            cat = sym.get("category", "Instrument")
            color = self.COLOR_PALETTE.get(cat, (0, 180, 50))
            cv2.rectangle(overlay, (x1, y1), (x2, y2), color, 2, cv2.LINE_AA)

        # 4. Draw Components with Tags & Confidence
        for comp in components:
            x1, y1 = int(comp["x1"]), int(comp["y1"])
            x2, y2 = int(comp["x2"]), int(comp["y2"])
            ctype = comp.get("component_type", "Instrument")
            color = self.COLOR_PALETTE.get(ctype, (0, 180, 50))

            # Bold component boundary
            cv2.rectangle(overlay, (x1 - 3, y1 - 3), (x2 + 3, y2 + 3), color, 2, cv2.LINE_AA)

            tag = comp.get("tag", "UNTAGGED")
            conf = int(comp.get("confidence", 0.9) * 100)
            badge_text = f"{tag} [{conf}%]"

            # Tag label background banner
            (t_w, t_h), _ = cv2.getTextSize(badge_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            b_y1 = max(0, y1 - t_h - 8)
            cv2.rectangle(overlay, (x1, b_y1), (x1 + t_w + 6, b_y1 + t_h + 6), color, -1)
            cv2.putText(
                overlay,
                badge_text,
                (x1 + 3, b_y1 + t_h + 2),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (255, 255, 255),
                1,
                cv2.LINE_AA
            )

        # 5. Draw Cross-Sheet Connectors
        for conn in connectors:
            x1, y1 = int(conn["x1"]), int(conn["y1"])
            x2, y2 = int(conn["x2"]), int(conn["y2"])
            cv2.rectangle(overlay, (x1, y1), (x2, y2), (255, 120, 0), 2, cv2.LINE_AA)
            label = conn.get("connector_label", "CONN")
            cv2.putText(
                overlay,
                f"OFF-PAGE: {label}",
                (x1, max(15, y1 - 5)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (255, 120, 0),
                1,
                cv2.LINE_AA
            )

        # Blend overlay with original for clean anti-aliased look
        alpha = 0.85
        blended = cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        cv2.imwrite(output_path, blended)
        logger.info(f"Visual overlay successfully written to {output_path}")
        return output_path
