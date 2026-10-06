import os
import shutil
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

from ..database.session import get_db
from ..models.entities import (
    Document, Sheet, Component, Connection,
    CrossSheetConnector, ProcessingRun, ValidationResult, OCRResult, Symbol
)
from ..schemas.schemas import (
    DocumentSchema, SheetSchema, ComponentSchema,
    ConnectionSchema, CrossSheetConnectorSchema, ValidationResultSchema,
    ProcessingRunSchema
)
from ..services.pipeline import DocumentPipeline
from ..services.exporters import Exporter
from ..services.synthetic_generator import SyntheticPIDGenerator
from ..utils.logger import logger

router = APIRouter(prefix="/api/documents", tags=["Documents"])

UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def run_pipeline_task(doc_id: str):
    from ..database.session import SessionLocal
    db = SessionLocal()
    try:
        pipeline = DocumentPipeline(db)
        pipeline.process_document(doc_id)
    except Exception as e:
        logger.error(f"Async pipeline processing error: {e}", exc_info=True)
    finally:
        db.close()

@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    auto_process: bool = True,
    db: Session = Depends(get_db)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    doc_id = str(uuid.uuid4())
    file_ext = os.path.splitext(file.filename)[1]
    saved_filename = f"{doc_id}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, saved_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = os.path.getsize(file_path)

    doc = Document(
        id=doc_id,
        filename=file.filename,
        file_path=file_path,
        file_size=file_size,
        processing_status="uploaded"
    )
    db.add(doc)

    run = ProcessingRun(document_id=doc_id, current_stage="uploaded", progress_percentage=0.0)
    db.add(run)
    db.commit()
    db.refresh(doc)

    if auto_process:
        doc.processing_status = "processing"
        db.commit()
        background_tasks.add_task(run_pipeline_task, doc.id)

    return {
        "id": doc.id,
        "filename": doc.filename,
        "file_size": doc.file_size,
        "processing_status": doc.processing_status
    }

@router.post("/demo")
async def create_and_run_demo(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Demo/Test Mode: Generates a realistic synthetic multi-sheet P&ID PDF
    and runs the complete intelligence extraction pipeline immediately.
    """
    doc_id = str(uuid.uuid4())
    filename = f"demo_pid_multisheet_{doc_id[:8]}.pdf"
    file_path = os.path.join(UPLOAD_DIR, filename)

    SyntheticPIDGenerator.generate_demo_pdf(file_path)
    file_size = os.path.getsize(file_path)

    doc = Document(
        id=doc_id,
        filename="Demo_Refinery_PID_MultiSheet.pdf",
        file_path=file_path,
        file_size=file_size,
        processing_status="processing"
    )
    db.add(doc)

    run = ProcessingRun(document_id=doc_id, current_stage="queued", progress_percentage=0.0)
    db.add(run)
    db.commit()

    background_tasks.add_task(run_pipeline_task, doc.id)

    return {
        "message": "Synthetic P&ID generated and pipeline started.",
        "id": doc.id,
        "filename": doc.filename,
        "processing_status": doc.processing_status
    }

@router.get("", response_model=List[DocumentSchema])
def list_documents(db: Session = Depends(get_db)):
    docs = db.query(Document).order_by(Document.created_at.desc()).all()
    return docs

@router.get("/{id}")
def get_document(id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    sheets_data = []
    for s in doc.sheets:
        comps_count = db.query(Component).filter(Component.sheet_id == s.id).count()
        syms_count = db.query(Symbol).filter(Symbol.sheet_id == s.id).count()
        ocr_count = db.query(OCRResult).filter(OCRResult.sheet_id == s.id).count()
        conn_count = db.query(Connection).filter(Connection.sheet_id == s.id).count()
        sheets_data.append({
            "id": s.id,
            "document_id": s.document_id,
            "sheet_number": s.sheet_number,
            "page_index": s.page_index,
            "sheet_name": s.sheet_name,
            "page_type": s.page_type,
            "width": s.width,
            "height": s.height,
            "image_path": s.image_path,
            "preprocessed_path": s.preprocessed_path,
            "overlay_path": s.overlay_path,
            "processing_status": s.processing_status,
            "components_count": comps_count,
            "symbols_count": syms_count,
            "ocr_count": ocr_count,
            "connections_count": conn_count
        })

    runs = [ProcessingRunSchema.from_orm(r) for r in doc.processing_runs]

    return {
        "id": doc.id,
        "filename": doc.filename,
        "file_path": doc.file_path,
        "file_size": doc.file_size,
        "page_count": doc.page_count,
        "doc_type": doc.doc_type,
        "processing_status": doc.processing_status,
        "created_at": doc.created_at,
        "updated_at": doc.updated_at,
        "sheets": sheets_data,
        "processing_runs": runs
    }

@router.get("/{id}/status")
def get_document_status(id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    run = db.query(ProcessingRun).filter(ProcessingRun.document_id == id).order_by(ProcessingRun.started_at.desc()).first()
    if not run:
        return {
            "document_id": doc.id,
            "status": doc.processing_status,
            "progress_percentage": 0.0,
            "current_stage": "none",
            "stage_statuses": {},
            "backtrack_count": 0
        }

    return {
        "document_id": doc.id,
        "status": doc.processing_status,
        "progress_percentage": run.progress_percentage,
        "current_stage": run.current_stage,
        "stage_statuses": run.stage_statuses,
        "backtrack_count": run.backtrack_count,
        "backtrack_history": run.backtrack_history,
        "error_message": run.error_message
    }

@router.post("/{id}/process")
def trigger_process_document(id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.processing_status = "processing"
    db.commit()
    background_tasks.add_task(run_pipeline_task, doc.id)
    return {"message": "Processing started", "id": doc.id}

@router.get("/{id}/sheets")
def get_document_sheets(id: str, db: Session = Depends(get_db)):
    sheets = db.query(Sheet).filter(Sheet.document_id == id).order_by(Sheet.sheet_number.asc()).all()
    results = []
    for s in sheets:
        comps_count = db.query(Component).filter(Component.sheet_id == s.id).count()
        results.append({
            "id": s.id,
            "document_id": s.document_id,
            "sheet_number": s.sheet_number,
            "sheet_name": s.sheet_name,
            "page_type": s.page_type,
            "width": s.width,
            "height": s.height,
            "image_url": f"/api/documents/image/{s.id}",
            "overlay_url": f"/api/documents/{id}/overlay/{s.id}" if s.overlay_path else None,
            "components_count": comps_count,
            "processing_status": s.processing_status
        })
    return results

@router.get("/image/{sheet_id}")
def get_sheet_image(sheet_id: str, db: Session = Depends(get_db)):
    sheet = db.query(Sheet).filter(Sheet.id == sheet_id).first()
    if not sheet or not sheet.image_path or not os.path.exists(sheet.image_path):
        raise HTTPException(status_code=404, detail="Sheet image not found")
    return FileResponse(sheet.image_path, media_type="image/png")

@router.get("/{id}/overlay/{sheet_id}")
def get_sheet_overlay(id: str, sheet_id: str, db: Session = Depends(get_db)):
    sheet = db.query(Sheet).filter(Sheet.id == id, Sheet.id == sheet_id).first()
    if not sheet:
        sheet = db.query(Sheet).filter(Sheet.id == sheet_id).first()
    if not sheet or not sheet.overlay_path or not os.path.exists(sheet.overlay_path):
        raise HTTPException(status_code=404, detail="Overlay image not found")
    return FileResponse(sheet.overlay_path, media_type="image/png")

@router.get("/{id}/components")
def get_document_components(
    id: str,
    sheet_id: Optional[str] = None,
    component_type: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Component).filter(Component.document_id == id)
    if sheet_id:
        query = query.filter(Component.sheet_id == sheet_id)
    if component_type:
        query = query.filter(Component.component_type == component_type)
    if status:
        query = query.filter(Component.validation_status == status)
    if search:
        query = query.filter(Component.tag.ilike(f"%{search}%") | Component.component_name.ilike(f"%{search}%"))

    comps = query.order_by(Component.tag.asc()).all()
    return comps

@router.get("/{id}/connections")
def get_document_connections(id: str, sheet_id: Optional[str] = None, db: Session = Depends(get_db)):
    if sheet_id:
        conns = db.query(Connection).filter(Connection.sheet_id == sheet_id).all()
    else:
        conns = (
            db.query(Connection)
            .join(Sheet, Connection.sheet_id == Sheet.id)
            .filter(Sheet.document_id == id)
            .all()
        )
    
    # Enrich with tag labels for graph visualization
    enriched = []
    for c in conns:
        s_comp = db.query(Component).filter(Component.id == c.source_component_id).first() if c.source_component_id else None
        t_comp = db.query(Component).filter(Component.id == c.target_component_id).first() if c.target_component_id else None
        enriched.append({
            "id": c.id,
            "sheet_id": c.sheet_id,
            "source_component_id": c.source_component_id,
            "target_component_id": c.target_component_id,
            "source_tag": s_comp.tag if s_comp else "Pipe",
            "target_tag": t_comp.tag if t_comp else "Pipe",
            "source_type": s_comp.component_type if s_comp else "Node",
            "target_type": t_comp.component_type if t_comp else "Node",
            "line_label": c.line_label,
            "line_type": c.line_type,
            "start_x": c.start_x,
            "start_y": c.start_y,
            "end_x": c.end_x,
            "end_y": c.end_y,
            "path_points": c.path_points or [],
            "confidence": c.confidence
        })
    return enriched

@router.get("/{id}/cross-sheet")
def get_cross_sheet_connectors(id: str, db: Session = Depends(get_db)):
    conns = db.query(CrossSheetConnector).filter(CrossSheetConnector.document_id == id).all()
    results = []
    for c in conns:
        s_comp = db.query(Component).filter(Component.id == c.connected_component_id).first() if c.connected_component_id else None
        results.append({
            "id": c.id,
            "sheet_id": c.sheet_id,
            "connector_label": c.connector_label,
            "target_sheet_number": c.target_sheet_number,
            "target_sheet_id": c.target_sheet_id,
            "connected_component_id": c.connected_component_id,
            "connected_tag": s_comp.tag if s_comp else None,
            "direction": c.direction,
            "confidence": c.confidence,
            "matched": c.matched,
            "x1": c.x1,
            "y1": c.y1,
            "x2": c.x2,
            "y2": c.y2
        })
    return results

@router.get("/{id}/validation")
def get_document_validation(id: str, db: Session = Depends(get_db)):
    val_items = db.query(ValidationResult).filter(ValidationResult.document_id == id).all()
    comps = db.query(Component).filter(Component.document_id == id).all()

    valid_count = sum(1 for c in comps if c.validation_status == "VALID")
    warning_count = sum(1 for c in comps if c.validation_status == "WARNING")
    error_count = sum(1 for c in comps if c.validation_status == "ERROR")

    return {
        "valid_count": valid_count,
        "warning_count": warning_count,
        "error_count": error_count,
        "total_components": len(comps),
        "issues": [
            {
                "id": v.id,
                "sheet_id": v.sheet_id,
                "component_id": v.component_id,
                "component_tag": v.component_tag,
                "rule_name": v.rule_name,
                "severity": v.severity,
                "message": v.message,
                "details": v.details,
                "backtrack_suggested": v.backtrack_suggested,
                "resolved": v.resolved,
                "created_at": v.created_at
            }
            for v in val_items
        ]
    }

@router.get("/{id}/export/excel")
def export_document_excel(id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    comps = db.query(Component).filter(Component.document_id == id).all()
    comp_list = []
    for c in comps:
        s = db.query(Sheet).filter(Sheet.id == c.sheet_id).first()
        c_dict = c.__dict__.copy()
        c_dict["sheet_number"] = s.sheet_number if s else 1
        comp_list.append(c_dict)

    excel_bytes = Exporter.export_excel(comp_list, {"filename": doc.filename})
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={os.path.splitext(doc.filename)[0]}_components.xlsx"}
    )

@router.get("/{id}/export/csv")
def export_document_csv(id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    comps = db.query(Component).filter(Component.document_id == id).all()
    comp_list = []
    for c in comps:
        s = db.query(Sheet).filter(Sheet.id == c.sheet_id).first()
        c_dict = c.__dict__.copy()
        c_dict["sheet_number"] = s.sheet_number if s else 1
        comp_list.append(c_dict)

    csv_data = Exporter.export_csv(comp_list)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={os.path.splitext(doc.filename)[0]}_components.csv"}
    )

@router.get("/{id}/export/json")
def export_document_json(id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    sheets = db.query(Sheet).filter(Sheet.document_id == id).all()
    comps = db.query(Component).filter(Component.document_id == id).all()
    conns = (
        db.query(Connection)
        .join(Sheet, Connection.sheet_id == Sheet.id)
        .filter(Sheet.document_id == id)
        .all()
    )
    cross = db.query(CrossSheetConnector).filter(CrossSheetConnector.document_id == id).all()
    vals = db.query(ValidationResult).filter(ValidationResult.document_id == id).all()

    payload = {
        "document": {
            "id": doc.id,
            "filename": doc.filename,
            "file_size": doc.file_size,
            "page_count": doc.page_count,
            "doc_type": doc.doc_type,
            "processing_status": doc.processing_status,
        },
        "sheets": [
            {
                "id": s.id,
                "sheet_number": s.sheet_number,
                "page_type": s.page_type,
                "width": s.width,
                "height": s.height
            }
            for s in sheets
        ],
        "components": [
            {
                "id": c.id,
                "sheet_id": c.sheet_id,
                "tag": c.tag,
                "component_name": c.component_name,
                "component_type": c.component_type,
                "symbol_class": c.symbol_class,
                "x1": c.x1,
                "y1": c.y1,
                "x2": c.x2,
                "y2": c.y2,
                "confidence": c.confidence,
                "validation_status": c.validation_status
            }
            for c in comps
        ],
        "connections": [
            {
                "id": cn.id,
                "sheet_id": cn.sheet_id,
                "source_component_id": cn.source_component_id,
                "target_component_id": cn.target_component_id,
                "line_label": cn.line_label,
                "line_type": cn.line_type,
                "confidence": cn.confidence
            }
            for cn in conns
        ],
        "cross_sheet_connections": [
            {
                "id": cs.id,
                "connector_label": cs.connector_label,
                "sheet_id": cs.sheet_id,
                "target_sheet_id": cs.target_sheet_id,
                "matched": cs.matched
            }
            for cs in cross
        ],
        "validation_issues": [
            {
                "rule": v.rule_name,
                "severity": v.severity,
                "message": v.message,
                "component_tag": v.component_tag
            }
            for v in vals
        ]
    }

    json_str = Exporter.export_json(payload)
    return Response(
        content=json_str,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={os.path.splitext(doc.filename)[0]}_pid_intel.json"}
    )
