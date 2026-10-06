import math
from typing import Tuple, List, Dict, Any, Optional

def euclidean_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

def calculate_center(x1: float, y1: float, x2: float, y2: float) -> Tuple[float, float]:
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)

def bbox_iou(box1: Tuple[float, float, float, float], box2: Tuple[float, float, float, float]) -> float:
    # box format: (x1, y1, x2, y2)
    b1_x1, b1_y1, b1_x2, b1_y2 = box1
    b2_x1, b2_y1, b2_x2, b2_y2 = box2

    inter_x1 = max(b1_x1, b2_x1)
    inter_y1 = max(b1_y1, b2_y1)
    inter_x2 = min(b1_x2, b2_x2)
    inter_y2 = min(b1_y2, b2_y2)

    inter_w = max(0.0, inter_x2 - inter_x1)
    inter_h = max(0.0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h

    area1 = max(0.0, b1_x2 - b1_x1) * max(0.0, b1_y2 - b1_y1)
    area2 = max(0.0, b2_x2 - b2_x1) * max(0.0, b2_y2 - b2_y1)

    union_area = area1 + area2 - inter_area
    if union_area <= 0:
        return 0.0
    return inter_area / union_area

def is_point_inside_bbox(px: float, py: float, box: Tuple[float, float, float, float], tolerance: float = 0.0) -> bool:
    x1, y1, x2, y2 = box
    return (x1 - tolerance <= px <= x2 + tolerance) and (y1 - tolerance <= py <= y2 + tolerance)

def bbox_contains(outer: Tuple[float, float, float, float], inner: Tuple[float, float, float, float], tolerance: float = 5.0) -> bool:
    ox1, oy1, ox2, oy2 = outer
    ix1, iy1, ix2, iy2 = inner
    return (
        (ox1 - tolerance <= ix1) and
        (oy1 - tolerance <= iy1) and
        (ox2 + tolerance >= ix2) and
        (oy2 + tolerance >= iy2)
    )

def alignment_score(c1: Tuple[float, float], c2: Tuple[float, float]) -> float:
    """Returns 1.0 if perfectly horizontally or vertically aligned, falling off smoothly."""
    dx = abs(c1[0] - c2[0])
    dy = abs(c1[1] - c2[1])
    
    # Near horizontal alignment
    h_align = max(0.0, 1.0 - (dy / 50.0))
    # Near vertical alignment
    v_align = max(0.0, 1.0 - (dx / 50.0))
    
    return max(h_align, v_align)

def min_distance_between_bboxes(box1: Tuple[float, float, float, float], box2: Tuple[float, float, float, float]) -> float:
    b1_x1, b1_y1, b1_x2, b1_y2 = box1
    b2_x1, b2_y1, b2_x2, b2_y2 = box2

    # Check for overlap
    x_overlap = max(0.0, min(b1_x2, b2_x2) - max(b1_x1, b2_x1))
    y_overlap = max(0.0, min(b1_y2, b2_y2) - max(b1_y1, b2_y1))
    if x_overlap > 0 and y_overlap > 0:
        return 0.0

    # Distance along x
    dx = 0.0
    if b1_x2 < b2_x1:
        dx = b2_x1 - b1_x2
    elif b2_x2 < b1_x1:
        dx = b1_x1 - b2_x2

    # Distance along y
    dy = 0.0
    if b1_y2 < b2_y1:
        dy = b2_y1 - b1_y2
    elif b2_y2 < b1_y1:
        dy = b1_y1 - b2_y2

    return math.sqrt(dx * dx + dy * dy)
