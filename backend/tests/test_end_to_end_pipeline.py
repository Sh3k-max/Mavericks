import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database.session import Base
from backend.app.models.entities import Document, Sheet, Component, Connection, CrossSheetConnector, ValidationResult
from backend.app.services.pipeline import DocumentPipeline
from backend.app.services.synthetic_generator import SyntheticPIDGenerator
from backend.app.services.exporters import Exporter

def test_complete_end_to_end_pipeline(tmp_path):
    # Setup test database
    db_file = tmp_path / "test_pid.db"
    test_engine = create_engine(f"sqlite:///{db_file}")
    Base.metadata.create_all(bind=test_engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestingSession()

    # Generate synthetic P&ID PDF
    pdf_path = str(tmp_path / "synthetic_pid_test.pdf")
    SyntheticPIDGenerator.generate_demo_pdf(pdf_path)
    assert os.path.exists(pdf_path)

    # Create document record
    doc_id = "test-doc-001"
    doc = Document(
        id=doc_id,
        filename="synthetic_pid_test.pdf",
        file_path=pdf_path,
        file_size=os.path.getsize(pdf_path),
        processing_status="uploaded"
    )
    db.add(doc)
    db.commit()

    # Run complete pipeline
    pipeline = DocumentPipeline(db)
    result = pipeline.process_document(doc_id)
    assert result["status"] == "success"

    # Verify database contents
    updated_doc = db.query(Document).filter(Document.id == doc_id).first()
    assert updated_doc.processing_status == "completed"
    assert updated_doc.page_count == 2
    assert updated_doc.doc_type in ["native", "mixed"]

    sheets = db.query(Sheet).filter(Sheet.document_id == doc_id).all()
    assert len(sheets) == 2
    assert os.path.exists(sheets[0].image_path)
    assert os.path.exists(sheets[0].overlay_path)

    components = db.query(Component).filter(Component.document_id == doc_id).all()
    assert len(components) >= 5
    tags_extracted = {c.tag for c in components}
    print("Extracted Tags:", tags_extracted)
    
    # Must have extracted real components like PT-101, FCV-101, P-101A, TT-101, FCV-201, PSV-201, etc.
    assert any("PT-101" in t for t in tags_extracted)
    assert any("FCV" in t for t in tags_extracted)
    assert any("P-101" in t for t in tags_extracted)

    connections = (
        db.query(Connection)
        .join(Sheet, Connection.sheet_id == Sheet.id)
        .filter(Sheet.document_id == doc_id)
        .all()
    )
    assert len(connections) >= 1

    cross_conns = db.query(CrossSheetConnector).filter(CrossSheetConnector.document_id == doc_id).all()
    assert len(cross_conns) >= 2
    matched_conns = [c for c in cross_conns if c.matched]
    assert len(matched_conns) >= 2

    # Verify exporters
    excel_bytes = Exporter.export_excel([c.__dict__ for c in components])
    assert len(excel_bytes) > 500

    csv_data = Exporter.export_csv([c.__dict__ for c in components])
    assert "Tag,Component Name,Type" in csv_data

    json_data = Exporter.export_json({"id": doc_id, "components": [c.tag for c in components]})
    assert doc_id in json_data

    db.close()
