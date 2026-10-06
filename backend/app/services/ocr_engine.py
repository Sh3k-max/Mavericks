import os
import re
from typing import List, Dict, Any, Optional
import pymupdf
import cv2
import numpy as np
from ..utils.logger import logger

class BaseOCREngine:
    def extract_text(self, image_path: str, scale_factor: float = 1.0) -> List[Dict[str, Any]]:
        raise NotImplementedError

class PyMuPDFVectorExtractor(BaseOCREngine):
    """
    Extracts high-precision text and bounding boxes directly from vector PDF pages.
    """
    def extract_from_pdf_page(self, pdf_path: str, page_index: int, scale_factor: float = 2.0) -> List[Dict[str, Any]]:
        results = []
        try:
            doc = pymupdf.open(pdf_path)
            if page_index >= len(doc):
                return results
            page = doc[page_index]

            # Use words extraction: (x0, y0, x1, y1, "word", block_no, line_no, word_no)
            words = page.get_text("words")
            
            # Group close words that belong to the same line/tag (e.g. "PT", "101" -> "PT 101" or "PT-101")
            for w in words:
                x0, y0, x1, y1, text, block_no, line_no, word_no = w
                cleaned = text.strip()
                if not cleaned:
                    continue
                results.append({
                    "text": cleaned,
                    "confidence": 0.98,  # Vector text extraction has high intrinsic confidence
                    "x1": float(x0 * scale_factor),
                    "y1": float(y0 * scale_factor),
                    "x2": float(x1 * scale_factor),
                    "y2": float(y1 * scale_factor),
                    "source_type": "vector_native"
                })

            doc.close()
        except Exception as e:
            logger.error(f"PyMuPDF vector extraction error: {e}")
        return results

class TesseractRasterOCREngine(BaseOCREngine):
    """
    Raster OCR using pytesseract when Tesseract binary is available.
    """
    def __init__(self):
        self.available = False
        try:
            import pytesseract
            # Test if tesseract is callable
            pytesseract.get_tesseract_version()
            self.pytesseract = pytesseract
            self.available = True
        except Exception:
            self.available = False

    def extract_text(self, image_path: str, scale_factor: float = 1.0) -> List[Dict[str, Any]]:
        if not self.available:
            return []
        results = []
        try:
            import pytesseract
            from PIL import Image
            img = Image.open(image_path)
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            n_boxes = len(data["text"])
            for i in range(n_boxes):
                text = data["text"][i].strip()
                conf = float(data["conf"][i])
                if conf < 10 or not text:
                    continue
                x = float(data["left"][i])
                y = float(data["top"][i])
                w = float(data["width"][i])
                h = float(data["height"][i])
                results.append({
                    "text": text,
                    "confidence": conf / 100.0,
                    "x1": x,
                    "y1": y,
                    "x2": x + w,
                    "y2": y + h,
                    "source_type": "tesseract_ocr"
                })
        except Exception as e:
            logger.warning(f"Tesseract OCR failed: {e}")
        return results

class CVGlyphHeuristicOCREngine(BaseOCREngine):
    """
    Clean fallback CV engine when native vector text is absent and no external OCR binary is found.
    Extracts text-like contour clusters, aspect ratios, and character patterns.
    """
    def extract_text(self, image_path: str, scale_factor: float = 1.0) -> List[Dict[str, Any]]:
        results = []
        try:
            img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                return results

            # Adaptive threshold
            binary = cv2.adaptiveThreshold(
                img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 4
            )
            # Find contours
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            h_img, w_img = img.shape

            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                # Text character/tag bounding boxes typically have:
                # height between 8 and 60 px, width between 5 and 150 px
                if 8 <= h <= 60 and 5 <= w <= 180 and w * h < 8000:
                    results.append({
                        "text": "[OCR_TOKEN]",
                        "confidence": 0.70,
                        "x1": float(x),
                        "y1": float(y),
                        "x2": float(x + w),
                        "y2": float(y + h),
                        "source_type": "cv_glyph_fallback"
                    })
        except Exception as e:
            logger.warning(f"CV Glyph fallback error: {e}")
        return results

class OCREngine:
    """
    Unified OCR abstraction layer:
    - Extracts native vector text if the document has vector layers.
    - Uses raster OCR (Tesseract / CV heuristic) for scanned drawings or missing text.
    - Merges and dedupes adjacent tokens (e.g. 'PT' and '101' -> 'PT-101').
    """

    def __init__(self):
        self.vector_extractor = PyMuPDFVectorExtractor()
        self.tesseract_engine = TesseractRasterOCREngine()
        self.fallback_engine = CVGlyphHeuristicOCREngine()

    def process_sheet_ocr(
        self,
        pdf_path: str,
        page_index: int,
        sheet_id: str,
        image_path: str,
        page_type: str = "native",
        scale_factor: float = 2.0
    ) -> List[Dict[str, Any]]:
        logger.info(f"Running OCR for sheet {sheet_id}, page_type: {page_type}")

        raw_tokens = []

        # 1. If native or mixed, extract vector words first
        if page_type in ["native", "mixed"]:
            vector_tokens = self.vector_extractor.extract_from_pdf_page(
                pdf_path, page_index, scale_factor=scale_factor
            )
            raw_tokens.extend(vector_tokens)

        # 2. If no vector text found, or scanned page, run raster OCR
        if len(raw_tokens) == 0 or page_type == "scanned":
            if self.tesseract_engine.available:
                raster_tokens = self.tesseract_engine.extract_text(image_path, scale_factor=1.0)
                raw_tokens.extend(raster_tokens)
            else:
                fallback_tokens = self.fallback_engine.extract_text(image_path, scale_factor=1.0)
                raw_tokens.extend(fallback_tokens)

        # 3. Post-process tokens: Merge vertically or horizontally adjacent tokens that form complete P&ID tags
        merged_tokens = self._merge_adjacent_tokens(raw_tokens)

        for item in merged_tokens:
            item["sheet_id"] = sheet_id

        logger.info(f"OCR extracted {len(merged_tokens)} text tokens for sheet {sheet_id}")
        return merged_tokens

    def _merge_adjacent_tokens(self, tokens: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merges horizontally or vertically split text tokens that form tags.
        e.g., Token 1: 'PT', Token 2: '101' separated by small gap -> 'PT-101'
        or 'P' above '101' in a bubble -> 'P-101'.
        """
        if not tokens:
            return []

        # Sort tokens by y1, then x1
        sorted_tokens = sorted(tokens, key=lambda t: (t["y1"], t["x1"]))
        merged = []
        used = set()

        tag_prefix_pattern = re.compile(r"^[A-Z]{1,4}$")
        tag_num_pattern = re.compile(r"^\d{2,5}[A-Z]?$")

        for i, t1 in enumerate(sorted_tokens):
            if i in used:
                continue

            text1 = t1["text"].strip()
            matched_pair = False

            # Check if t1 is a prefix like PT, TT, FT, FCV, P
            if tag_prefix_pattern.match(text1):
                for j, t2 in enumerate(sorted_tokens):
                    if j <= i or j in used:
                        continue
                    text2 = t2["text"].strip()

                    # Horizontal neighbor: similar y, x2 of t1 close to x1 of t2
                    y_diff = abs(t1["y1"] - t2["y1"])
                    x_gap = t2["x1"] - t1["x2"]

                    # Vertical neighbor: similar x, y2 of t1 close to y1 of t2 (stacked bubble text)
                    x_diff = abs(t1["x1"] - t2["x1"])
                    y_gap = t2["y1"] - t1["y2"]

                    is_horizontal = (y_diff < 15 and 0 <= x_gap < 40)
                    is_vertical = (x_diff < 25 and 0 <= y_gap < 30)

                    if (is_horizontal or is_vertical) and tag_num_pattern.match(text2):
                        combined_text = f"{text1}-{text2}"
                        merged.append({
                            "text": combined_text,
                            "confidence": min(t1["confidence"], t2["confidence"]),
                            "x1": min(t1["x1"], t2["x1"]),
                            "y1": min(t1["y1"], t2["y1"]),
                            "x2": max(t1["x2"], t2["x2"]),
                            "y2": max(t1["y2"], t2["y2"]),
                            "source_type": t1["source_type"]
                        })
                        used.add(i)
                        used.add(j)
                        matched_pair = True
                        break

            if not matched_pair:
                merged.append(t1)
                used.add(i)

        return merged
