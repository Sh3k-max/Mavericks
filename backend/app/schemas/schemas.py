from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class OCRResultSchema(BaseModel):
    id: str
    sheet_id: str
    text: str
    normalized_text: str
    is_tag_candidate: bool
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float
    source_type: str

    class Config:
        from_attributes = True

class SymbolSchema(BaseModel):
    id: str
    sheet_id: str
    class_name: str
    category: str
    confidence: float
    detector_type: str
    x1: float
    y1: float
    x2: float
    y2: float
    center_x: float
    center_y: float

    class Config:
        from_attributes = True

class ComponentSchema(BaseModel):
    id: str
    document_id: str
    sheet_id: str
    symbol_id: Optional[str] = None
    ocr_result_id: Optional[str] = None
    tag: str
    component_name: str
    component_type: str
    symbol_class: str
    x1: float
    y1: float
    x2: float
    y2: float
    center_x: float
    center_y: float
    confidence: float
    association_score: float
    distance_to_tag: float
    source: str
    validation_status: str
    validation_notes: Optional[str] = ""
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ConnectionSchema(BaseModel):
    id: str
    sheet_id: str
    source_component_id: Optional[str] = None
    target_component_id: Optional[str] = None
    source_tag: Optional[str] = None
    target_tag: Optional[str] = None
    line_label: str
    line_type: str
    start_x: float
    start_y: float
    end_x: float
    end_y: float
    path_points: List[List[float]] = []
    confidence: float

    class Config:
        from_attributes = True

class CrossSheetConnectorSchema(BaseModel):
    id: str
    document_id: str
    sheet_id: str
    connector_label: str
    target_sheet_number: Optional[int] = None
    target_sheet_id: Optional[str] = None
    connected_component_id: Optional[str] = None
    connected_tag: Optional[str] = None
    x1: float
    y1: float
    x2: float
    y2: float
    direction: str
    confidence: float
    matched: bool
    matched_connector_id: Optional[str] = None

    class Config:
        from_attributes = True

class ValidationResultSchema(BaseModel):
    id: str
    document_id: str
    sheet_id: Optional[str] = None
    component_id: Optional[str] = None
    component_tag: Optional[str] = None
    rule_name: str
    severity: str
    message: str
    details: Dict[str, Any] = {}
    backtrack_suggested: str
    resolved: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class SheetSchema(BaseModel):
    id: str
    document_id: str
    sheet_number: int
    page_index: int
    sheet_name: str
    page_type: str
    width: float
    height: float
    image_path: str
    preprocessed_path: Optional[str] = ""
    overlay_path: Optional[str] = ""
    processing_status: str
    components_count: Optional[int] = 0
    symbols_count: Optional[int] = 0
    ocr_count: Optional[int] = 0
    connections_count: Optional[int] = 0

    class Config:
        from_attributes = True

class ProcessingRunSchema(BaseModel):
    id: str
    document_id: str
    current_stage: str
    progress_percentage: float
    stage_statuses: Dict[str, Any] = {}
    backtrack_count: int
    backtrack_history: List[Dict[str, Any]] = []
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class DocumentSchema(BaseModel):
    id: str
    filename: str
    file_path: str
    file_size: int
    page_count: int
    doc_type: str
    processing_status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    sheets: List[SheetSchema] = []
    processing_runs: List[ProcessingRunSchema] = []

    class Config:
        from_attributes = True
