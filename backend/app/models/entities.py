from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from ..database.session import Base

def generate_uuid():
    return str(uuid.uuid4())

def get_utc_now():
    return datetime.now(timezone.utc)

class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(1024), nullable=False)
    file_size = Column(Integer, default=0)
    page_count = Column(Integer, default=0)
    doc_type = Column(String(50), default="unknown")  # native, scanned, mixed
    processing_status = Column(String(50), default="uploaded")  # uploaded, processing, completed, failed
    created_at = Column(DateTime, default=get_utc_now)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)

    sheets = relationship("Sheet", back_populates="document", cascade="all, delete-orphan")
    processing_runs = relationship("ProcessingRun", back_populates="document", cascade="all, delete-orphan")
    components = relationship("Component", back_populates="document", cascade="all, delete-orphan")
    validation_results = relationship("ValidationResult", back_populates="document", cascade="all, delete-orphan")


class Sheet(Base):
    __tablename__ = "sheets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    sheet_number = Column(Integer, nullable=False)
    page_index = Column(Integer, nullable=False)
    sheet_name = Column(String(255), default="")
    page_type = Column(String(50), default="unknown")  # native, scanned, mixed
    width = Column(Float, default=0.0)
    height = Column(Float, default=0.0)
    image_path = Column(String(1024), default="")
    preprocessed_path = Column(String(1024), default="")
    overlay_path = Column(String(1024), default="")
    processing_status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=get_utc_now)

    document = relationship("Document", back_populates="sheets")
    ocr_results = relationship("OCRResult", back_populates="sheet", cascade="all, delete-orphan")
    symbols = relationship("Symbol", back_populates="sheet", cascade="all, delete-orphan")
    components = relationship("Component", back_populates="sheet", cascade="all, delete-orphan")
    connections = relationship("Connection", back_populates="sheet", cascade="all, delete-orphan")
    connectors = relationship("CrossSheetConnector", back_populates="sheet", cascade="all, delete-orphan")


class OCRResult(Base):
    __tablename__ = "ocr_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    sheet_id = Column(String(36), ForeignKey("sheets.id", ondelete="CASCADE"), nullable=False)
    text = Column(String(500), nullable=False)
    normalized_text = Column(String(500), default="")
    is_tag_candidate = Column(Boolean, default=False)
    parsed_prefix = Column(String(50), default="")
    parsed_number = Column(String(50), default="")
    parsed_suffix = Column(String(50), default="")
    confidence = Column(Float, default=0.0)
    x1 = Column(Float, nullable=False)
    y1 = Column(Float, nullable=False)
    x2 = Column(Float, nullable=False)
    y2 = Column(Float, nullable=False)
    source_type = Column(String(50), default="vector")  # vector, raster_ocr
    created_at = Column(DateTime, default=get_utc_now)

    sheet = relationship("Sheet", back_populates="ocr_results")


class Symbol(Base):
    __tablename__ = "symbols"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    sheet_id = Column(String(36), ForeignKey("sheets.id", ondelete="CASCADE"), nullable=False)
    class_name = Column(String(100), nullable=False)
    category = Column(String(50), default="Instrument")  # Instrument, Valve, Equipment, Fitting, Connector
    confidence = Column(Float, default=0.0)
    detector_type = Column(String(50), default="cv_geometric")  # cv_geometric, yolo, template
    x1 = Column(Float, nullable=False)
    y1 = Column(Float, nullable=False)
    x2 = Column(Float, nullable=False)
    y2 = Column(Float, nullable=False)
    center_x = Column(Float, nullable=False)
    center_y = Column(Float, nullable=False)
    created_at = Column(DateTime, default=get_utc_now)

    sheet = relationship("Sheet", back_populates="symbols")


class Component(Base):
    __tablename__ = "components"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    sheet_id = Column(String(36), ForeignKey("sheets.id", ondelete="CASCADE"), nullable=False)
    symbol_id = Column(String(36), ForeignKey("symbols.id", ondelete="SET NULL"), nullable=True)
    ocr_result_id = Column(String(36), ForeignKey("ocr_results.id", ondelete="SET NULL"), nullable=True)
    
    tag = Column(String(100), nullable=False)
    component_name = Column(String(255), nullable=False)  # e.g., Pressure Transmitter
    component_type = Column(String(100), nullable=False)  # Instrument, Valve, Equipment, etc.
    symbol_class = Column(String(100), default="")
    
    x1 = Column(Float, nullable=False)
    y1 = Column(Float, nullable=False)
    x2 = Column(Float, nullable=False)
    y2 = Column(Float, nullable=False)
    center_x = Column(Float, nullable=False)
    center_y = Column(Float, nullable=False)
    
    confidence = Column(Float, default=0.0)
    association_score = Column(Float, default=0.0)
    distance_to_tag = Column(Float, default=0.0)
    source = Column(String(50), default="auto_pipeline")
    validation_status = Column(String(50), default="VALID")  # VALID, WARNING, ERROR
    validation_notes = Column(Text, default="")
    created_at = Column(DateTime, default=get_utc_now)

    document = relationship("Document", back_populates="components")
    sheet = relationship("Sheet", back_populates="components")


class Connection(Base):
    __tablename__ = "connections"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    sheet_id = Column(String(36), ForeignKey("sheets.id", ondelete="CASCADE"), nullable=False)
    source_component_id = Column(String(36), ForeignKey("components.id", ondelete="CASCADE"), nullable=True)
    target_component_id = Column(String(36), ForeignKey("components.id", ondelete="CASCADE"), nullable=True)
    line_label = Column(String(100), default="")
    line_type = Column(String(50), default="primary_pipeline")  # primary_pipeline, signal_line, electrical
    start_x = Column(Float, default=0.0)
    start_y = Column(Float, default=0.0)
    end_x = Column(Float, default=0.0)
    end_y = Column(Float, default=0.0)
    path_points = Column(JSON, default=list)  # list of [x, y] coordinates
    confidence = Column(Float, default=0.0)
    created_at = Column(DateTime, default=get_utc_now)

    sheet = relationship("Sheet", back_populates="connections")


class CrossSheetConnector(Base):
    __tablename__ = "cross_sheet_connectors"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    sheet_id = Column(String(36), ForeignKey("sheets.id", ondelete="CASCADE"), nullable=False)
    connector_label = Column(String(100), nullable=False)  # e.g., "CONN-A" or "TO SHEET 2"
    target_sheet_number = Column(Integer, nullable=True)
    target_sheet_id = Column(String(36), nullable=True)
    connected_component_id = Column(String(36), ForeignKey("components.id", ondelete="SET NULL"), nullable=True)
    x1 = Column(Float, nullable=False)
    y1 = Column(Float, nullable=False)
    x2 = Column(Float, nullable=False)
    y2 = Column(Float, nullable=False)
    direction = Column(String(20), default="out")  # in, out, bidirectional
    confidence = Column(Float, default=0.0)
    matched = Column(Boolean, default=False)
    matched_connector_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=get_utc_now)

    sheet = relationship("Sheet", back_populates="connectors")


class ProcessingRun(Base):
    __tablename__ = "processing_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    current_stage = Column(String(100), default="init")
    progress_percentage = Column(Float, default=0.0)
    stage_statuses = Column(JSON, default=dict)  # {stage_name: {status: "done"|"running"|"failed"|"backtracking", details: ""}}
    backtrack_count = Column(Integer, default=0)
    backtrack_history = Column(JSON, default=list)  # [{from_stage, to_stage, reason, timestamp}]
    error_message = Column(Text, default="")
    started_at = Column(DateTime, default=get_utc_now)
    completed_at = Column(DateTime, nullable=True)

    document = relationship("Document", back_populates="processing_runs")


class ValidationResult(Base):
    __tablename__ = "validation_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    sheet_id = Column(String(36), nullable=True)
    component_id = Column(String(36), nullable=True)
    rule_name = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False)  # ERROR, WARNING, VALID
    message = Column(Text, nullable=False)
    details = Column(JSON, default=dict)
    backtrack_suggested = Column(String(100), default="")  # e.g., "spatial_association", "ocr", "line_detection"
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=get_utc_now)

    document = relationship("Document", back_populates="validation_results")
