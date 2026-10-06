import cv2
import numpy as np
from typing import List, Dict, Any, Tuple
from ..utils.logger import logger
from ..utils.geometry import euclidean_distance

class LineDetector:
    """
    Detects pipeline lines in P&ID drawings:
    - Combines OpenCV morphological line filtering & Probabilistic Hough Transform
    - Ingests vector lines extracted from native PDF drawings
    - Merges collinear, overlapping, or nearly touching line segments
    - Traces path coordinates for each pipeline line.
    """

    def __init__(self, min_line_length: int = 25, max_line_gap: int = 15):
        self.min_line_length = min_line_length
        self.max_line_gap = max_line_gap

    def detect_lines(
        self,
        image_path: str,
        sheet_id: str,
        vector_lines: List[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        logger.info(f"Detecting pipeline lines on sheet {sheet_id}")

        detected_lines = []

        # 1. Include vector lines if available from native PDF extraction
        if vector_lines:
            for vl in vector_lines:
                if vl.get("type") == "line":
                    p1 = vl["start"]
                    p2 = vl["end"]
                    length = euclidean_distance((p1[0], p1[1]), (p2[0], p2[1]))
                    if length >= self.min_line_length:
                        detected_lines.append({
                            "start": [float(p1[0]), float(p1[1])],
                            "end": [float(p2[0]), float(p2[1])],
                            "length": float(length),
                            "source": "vector_drawing",
                            "confidence": 0.99
                        })

        # 2. In addition, run OpenCV line extraction from the raster image
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is not None:
            cv_lines = self._detect_raster_lines(img)
            detected_lines.extend(cv_lines)

        # 3. Merge collinear and adjacent segments
        merged_lines = self._merge_lines(detected_lines)
        logger.info(f"Line detection found {len(merged_lines)} pipeline lines on sheet {sheet_id}")
        return merged_lines

    def _detect_raster_lines(self, gray: np.ndarray) -> List[Dict[str, Any]]:
        lines_out = []
        # Invert: white lines on black background
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 3
        )

        # Morphological kernels to emphasize horizontal and vertical pipeline segments
        h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
        v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25))

        h_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, h_kernel)
        v_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, v_kernel)
        pipe_mask = cv2.bitwise_or(h_lines, v_lines)

        # Probabilistic Hough Transform
        lines = cv2.HoughLinesP(
            pipe_mask,
            rho=1,
            theta=np.pi / 180,
            threshold=40,
            minLineLength=self.min_line_length,
            maxLineGap=self.max_line_gap
        )

        if lines is not None:
            for l in lines:
                flat = np.array(l).flatten()
                if len(flat) >= 4:
                    x1, y1, x2, y2 = float(flat[0]), float(flat[1]), float(flat[2]), float(flat[3])
                    length = np.hypot(x2 - x1, y2 - y1)
                    lines_out.append({
                        "start": [x1, y1],
                        "end": [x2, y2],
                        "length": float(length),
                        "source": "raster_cv",
                        "confidence": 0.88
                    })

        return lines_out

    def _merge_lines(self, lines: List[Dict[str, Any]], distance_thresh: float = 12.0) -> List[Dict[str, Any]]:
        """
        Merges collinear and nearly-connected segments.
        Uses vectorized numpy endpoint distance matrix instead of O(n²) Python loop
        for a ~10-50x speedup on drawings with hundreds of detected segments.
        """
        if not lines:
            return []

        # Cap lines to prevent runaway processing on very dense drawings
        MAX_LINES = 2000
        if len(lines) > MAX_LINES:
            logger.warning(f"Line count {len(lines)} exceeds cap {MAX_LINES}, truncating.")
            lines = lines[:MAX_LINES]

        # Build numpy arrays for vectorized distance checks
        starts = np.array([[l["start"][0], l["start"][1]] for l in lines], dtype=np.float32)
        ends   = np.array([[l["end"][0],   l["end"][1]]   for l in lines], dtype=np.float32)

        # Precompute direction unit vectors
        dirs = ends - starts
        lengths = np.linalg.norm(dirs, axis=1, keepdims=True)
        valid_mask = lengths[:, 0] > 0
        lengths = np.where(lengths > 0, lengths, 1.0)
        dirs_norm = dirs / lengths  # (N, 2)

        used = np.zeros(len(lines), dtype=bool)
        merged = []

        for i in range(len(lines)):
            if used[i] or not valid_mask[i]:
                continue

            curr_s = starts[i].copy()
            curr_e = ends[i].copy()
            d1 = dirs_norm[i]

            # Vectorized dot product with all remaining lines
            dots = np.abs(dirs_norm @ d1)  # (N,) cosine similarity

            # Vectorized endpoint distance: check min of 4 endpoint pair distances
            d_s1_sj = np.linalg.norm(starts - curr_s, axis=1)
            d_e1_sj = np.linalg.norm(starts - curr_e, axis=1)
            d_s1_ej = np.linalg.norm(ends   - curr_s, axis=1)
            d_e1_ej = np.linalg.norm(ends   - curr_e, axis=1)
            min_dists = np.minimum(np.minimum(d_s1_sj, d_e1_sj), np.minimum(d_s1_ej, d_e1_ej))

            # Candidates: collinear (dot>0.96) and close (dist < thresh) and not yet used
            candidates = np.where(
                (~used) & valid_mask & (dots > 0.96) & (min_dists <= distance_thresh) & (np.arange(len(lines)) != i)
            )[0]

            for j in candidates:
                # Merge by extending extreme endpoints along the current direction
                points = np.stack([curr_s, curr_e, starts[j], ends[j]])
                projections = (points - curr_s) @ d1
                curr_s = points[np.argmin(projections)]
                curr_e = points[np.argmax(projections)]
                used[j] = True

            merged.append({
                "start": [float(curr_s[0]), float(curr_s[1])],
                "end":   [float(curr_e[0]), float(curr_e[1])],
                "length": float(np.linalg.norm(curr_e - curr_s)),
                "confidence": lines[i]["confidence"],
                "source": lines[i]["source"]
            })
            used[i] = True

        return merged
