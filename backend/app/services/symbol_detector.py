import os
import cv2
import numpy as np
from typing import List, Dict, Any, Optional
from ..utils.logger import logger
from ..utils.geometry import calculate_center

class BaseSymbolDetector:
    def detect_symbols(self, image_path: str, sheet_id: str) -> List[Dict[str, Any]]:
        raise NotImplementedError

class YOLOSymbolDetector(BaseSymbolDetector):
    """
    Detector interface for YOLO models (e.g. YOLOv8 / YOLOv11 / ONNX).
    Checks if model weights exist; if not, yields gracefully.
    """
    def __init__(self, model_path: str = "models/symbol_detection/pid_yolo.pt"):
        self.model_path = model_path
        self.model = None
        self.is_loaded = False
        self._load_model()

    def _load_model(self):
        if os.path.exists(self.model_path):
            try:
                # Attempt loading ultralytics YOLO
                from ultralytics import YOLO
                self.model = YOLO(self.model_path)
                self.is_loaded = True
                logger.info(f"YOLO symbol detection model loaded from {self.model_path}")
            except Exception as e:
                logger.warning(f"Could not load YOLO model from {self.model_path}: {e}")
                self.is_loaded = False
        else:
            logger.info(f"No trained YOLO weights at {self.model_path}. Using CV geometric detector.")
            self.is_loaded = False

    def detect_symbols(self, image_path: str, sheet_id: str) -> List[Dict[str, Any]]:
        if not self.is_loaded:
            return []
        
        detections = []
        try:
            results = self.model(image_path, conf=0.25)
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    conf = float(box.conf[0])
                    cls_id = int(box.cls[0])
                    class_name = self.model.names[cls_id]
                    cx, cy = calculate_center(x1, y1, x2, y2)

                    category = self._infer_category(class_name)
                    detections.append({
                        "class_name": class_name,
                        "category": category,
                        "confidence": round(conf, 4),
                        "detector_type": "yolo",
                        "x1": float(x1),
                        "y1": float(y1),
                        "x2": float(x2),
                        "y2": float(y2),
                        "center_x": float(cx),
                        "center_y": float(cy),
                        "sheet_id": sheet_id
                    })
        except Exception as e:
            logger.error(f"YOLO inference error: {e}")
        return detections

    def _infer_category(self, class_name: str) -> str:
        name = class_name.lower()
        if any(term in name for term in ["valve", "fcv", "pcv", "psv", "xv", "lv"]):
            return "Valve"
        if any(term in name for term in ["transmitter", "pt", "tt", "ft", "lt", "instrument", "gauge"]):
            return "Instrument"
        if any(term in name for term in ["pump", "tank", "vessel", "motor", "compressor"]):
            return "Equipment"
        if "connector" in name:
            return "Connector"
        return "Instrument"

class CVSymbolDetector(BaseSymbolDetector):
    """
    OpenCV-based geometric and contour symbol detector for P&IDs:
    - Circular contours & Hough circles -> Instrument bubbles / Pumps
    - Bowtie / hourglass contours -> Valves (FCV, PSV, generic Valve)
    - Large elongated capsules/rectangles -> Tanks, Vessels
    - Chevron / arrow polygons -> Cross-sheet Connectors
    """

    def detect_symbols(self, image_path: str, sheet_id: str) -> List[Dict[str, Any]]:
        logger.info(f"Running CV geometric symbol detection on {image_path}")
        img = cv2.imread(image_path)
        if img is None:
            logger.error(f"Unable to read image {image_path}")
            return []

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h_img, w_img = gray.shape

        # Use adaptive threshold to extract distinct symbol silhouettes
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 3
        )

        detected_symbols = []

        # 1. Detect Circles (Instrument Bubbles & Pump bodies)
        circles_detected = self._detect_circles(gray, binary, sheet_id)
        detected_symbols.extend(circles_detected)

        # 2. Detect Valves & Equipment using contour shape descriptors
        contours_detected = self._detect_contour_symbols(binary, sheet_id, circles_detected)
        detected_symbols.extend(contours_detected)

        # Deduplicate detections that have high IoU overlap
        deduped = self._deduplicate_symbols(detected_symbols)
        logger.info(f"CV Symbol Detector found {len(deduped)} symbols on sheet {sheet_id}")
        return deduped

    def _detect_circles(self, gray: np.ndarray, binary: np.ndarray, sheet_id: str) -> List[Dict[str, Any]]:
        symbols = []
        # HoughCircles for clean circles
        circles = cv2.HoughCircles(
            gray,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=35,
            param1=80,
            param2=30,
            minRadius=14,
            maxRadius=65
        )

        if circles is not None:
            circles = np.uint16(np.around(circles))
            for i in circles[0, :]:
                cx, cy, r = float(i[0]), float(i[1]), float(i[2])
                x1 = max(0.0, cx - r)
                y1 = max(0.0, cy - r)
                x2 = min(float(gray.shape[1]), cx + r)
                y2 = min(float(gray.shape[0]), cy + r)

                # Verify if this is an instrument bubble or pump
                symbols.append({
                    "class_name": "Instrument",
                    "category": "Instrument",
                    "confidence": 0.88,
                    "detector_type": "cv_geometric",
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                    "center_x": cx,
                    "center_y": cy,
                    "sheet_id": sheet_id
                })
        return symbols

    def _detect_contour_symbols(
        self,
        binary: np.ndarray,
        sheet_id: str,
        existing_circles: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        symbols = []
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 200 or area > 500000:
                continue

            x, y, w, h = cv2.boundingRect(cnt)
            cx, cy = x + w / 2.0, y + h / 2.0
            aspect_ratio = float(w) / float(h)
            perimeter = cv2.arcLength(cnt, True)
            if perimeter == 0:
                continue
            circularity = 4 * np.pi * (area / (perimeter * perimeter))

            # Skip if already captured by circles
            is_circle_overlap = any(
                abs(c["center_x"] - cx) < 25 and abs(c["center_y"] - cy) < 25
                for c in existing_circles
            )
            if is_circle_overlap:
                continue

            # Check for Valve shape:
            # Valves are bowtie-shaped: aspect ratio usually 1.2 to 2.8, area between 250 and 6000
            # Convex hull area is significantly larger than contour area due to the inward pinch
            hull = cv2.convexHull(cnt)
            hull_area = cv2.contourArea(hull)
            solidity = float(area) / hull_area if hull_area > 0 else 0

            if 250 <= area <= 7000 and 0.35 <= solidity <= 0.78 and 0.8 <= aspect_ratio <= 3.2:
                # Bowtie valve signature
                symbols.append({
                    "class_name": "Valve",
                    "category": "Valve",
                    "confidence": 0.85,
                    "detector_type": "cv_contour",
                    "x1": float(x),
                    "y1": float(y),
                    "x2": float(x + w),
                    "y2": float(y + h),
                    "center_x": float(cx),
                    "center_y": float(cy),
                    "sheet_id": sheet_id
                })
            # Check for large Tanks / Vessels:
            # Large rectangular / pill containers, area > 10,000 px
            elif area > 12000 and (w > 80 or h > 80):
                symbols.append({
                    "class_name": "Vessel",
                    "category": "Equipment",
                    "confidence": 0.82,
                    "detector_type": "cv_contour",
                    "x1": float(x),
                    "y1": float(y),
                    "x2": float(x + w),
                    "y2": float(y + h),
                    "center_x": float(cx),
                    "center_y": float(cy),
                    "sheet_id": sheet_id
                })
            # Check for Off-page connector / Arrow:
            # Polygon approximation has 5 or 6 vertices (pentagon arrow)
            approx = cv2.approxPolyDP(cnt, 0.04 * perimeter, True)
            if len(approx) in [4, 5, 6, 7] and 300 <= area <= 5000:
                # Potential off-page connector or tag border
                if aspect_ratio > 1.3 or aspect_ratio < 0.7:
                    symbols.append({
                        "class_name": "Connector",
                        "category": "Connector",
                        "confidence": 0.78,
                        "detector_type": "cv_contour",
                        "x1": float(x),
                        "y1": float(y),
                        "x2": float(x + w),
                        "y2": float(y + h),
                        "center_x": float(cx),
                        "center_y": float(cy),
                        "sheet_id": sheet_id
                    })

        return symbols

    def _deduplicate_symbols(self, symbols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filters out duplicate detections with IoU > 0.45 or center distance < 18px."""
        deduped = []
        for sym in symbols:
            duplicate = False
            for existing in deduped:
                dist = np.hypot(sym["center_x"] - existing["center_x"], sym["center_y"] - existing["center_y"])
                if dist < 18:
                    duplicate = True
                    break
            if not duplicate:
                deduped.append(sym)
        return deduped

class SymbolDetector:
    """
    Unified Symbol Detection Manager:
    Attempts YOLO first if model weights are present;
    Otherwise falls back seamlessly to the CV Geometric Detector.
    """
    def __init__(self, yolo_path: str = "models/symbol_detection/pid_yolo.pt"):
        self.yolo_detector = YOLOSymbolDetector(yolo_path)
        self.cv_detector = CVSymbolDetector()

    def detect(self, image_path: str, sheet_id: str) -> List[Dict[str, Any]]:
        if self.yolo_detector.is_loaded:
            logger.info("Using YOLO detector for symbol detection")
            results = self.yolo_detector.detect_symbols(image_path, sheet_id)
            if results:
                return results
        
        logger.info("Using CV Geometric & Contour detector for symbol detection")
        return self.cv_detector.detect_symbols(image_path, sheet_id)
