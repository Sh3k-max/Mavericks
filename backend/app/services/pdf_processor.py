import os
import pymupdf  # PyMuPDF
from PIL import Image
import numpy as np
from typing import Dict, Any, List, Tuple
from ..utils.logger import logger

class PDFProcessor:
    """
    Handles PDF ingestion, classification (native/scanned/mixed),
    page extraction, rendering high-resolution images, and extracting vector paths.
    """

    def __init__(self, output_dir: str = "data/processed"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def inspect_and_extract(self, file_path: str, doc_id: str) -> Dict[str, Any]:
        """
        Opens PDF, determines overall and per-page types,
        renders pages to PNG for CV/OCR, and extracts vector elements if native.
        """
        logger.info(f"Inspecting PDF document: {file_path} (doc_id: {doc_id})")
        doc_dir = os.path.join(self.output_dir, doc_id)
        os.makedirs(doc_dir, exist_ok=True)

        try:
            doc = pymupdf.open(file_path)
        except Exception as e:
            logger.error(f"Failed to open PDF {file_path}: {e}")
            raise ValueError(f"Corrupted or invalid PDF file: {e}")

        page_count = len(doc)
        if page_count == 0:
            doc.close()
            raise ValueError("PDF document has 0 pages.")

        pages_info = []
        native_count = 0
        scanned_count = 0

        for page_idx in range(page_count):
            page = doc[page_idx]
            sheet_num = page_idx + 1
            rect = page.rect
            width, height = rect.width, rect.height

            # Analyze text and vector drawings
            text_instances = page.get_text("words")
            drawings = page.get_drawings()
            image_list = page.get_images()

            has_native_text = len(text_instances) > 5
            has_vector_drawings = len(drawings) > 10

            if has_native_text or has_vector_drawings:
                page_type = "native"
                native_count += 1
            elif len(image_list) > 0 and len(text_instances) == 0:
                page_type = "scanned"
                scanned_count += 1
            else:
                page_type = "mixed"
                native_count += 1

            # Render high-resolution page image (300 DPI scale ~ 4.16x, or 2x for balance of speed and clarity)
            # 2.0 zoom factor gives crisp 150-200 DPI suitable for engineering drawings
            zoom = 2.0
            mat = pymupdf.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            image_filename = f"sheet_{sheet_num}_render.png"
            image_path = os.path.join(doc_dir, image_filename)
            pix.save(image_path)

            # Extract vector lines/rectangles from drawings
            vector_lines = []
            for draw in drawings:
                items = draw.get("items", [])
                for item in items:
                    item_type = item[0]
                    if item_type == "l":  # line: ('l', p1, p2)
                        p1, p2 = item[1], item[2]
                        raw_w = draw.get("width")
                        line_w = float(raw_w) if raw_w is not None else 1.0
                        vector_lines.append({
                            "type": "line",
                            "start": [float(p1.x * zoom), float(p1.y * zoom)],
                            "end": [float(p2.x * zoom), float(p2.y * zoom)],
                            "width": float(line_w * zoom)
                        })
                    elif item_type == "re":  # rect: ('re', rect)
                        r = item[1]
                        vector_lines.append({
                            "type": "rect",
                            "bbox": [float(r.x0 * zoom), float(r.y0 * zoom), float(r.x1 * zoom), float(r.y1 * zoom)]
                        })

            pages_info.append({
                "page_index": page_idx,
                "sheet_number": sheet_num,
                "page_type": page_type,
                "width": float(pix.width),
                "height": float(pix.height),
                "raw_width": float(width),
                "raw_height": float(height),
                "scale_factor": zoom,
                "image_path": image_path,
                "vector_lines_count": len(vector_lines),
                "vector_lines": vector_lines,
                "native_words_count": len(text_instances),
                "page_rect": [float(rect.x0), float(rect.y0), float(rect.x1), float(rect.y1)]
            })

        doc.close()

        # Determine document overall type
        if scanned_count == page_count:
            overall_type = "scanned"
        elif native_count == page_count:
            overall_type = "native"
        else:
            overall_type = "mixed"

        return {
            "doc_id": doc_id,
            "filename": os.path.basename(file_path),
            "file_path": file_path,
            "page_count": page_count,
            "overall_type": overall_type,
            "pages": pages_info
        }
