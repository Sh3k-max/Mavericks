import os
import uuid
import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from ..utils.logger import logger
from ..models.entities import (
    Document, Sheet, OCRResult, Symbol, Component,
    Connection, CrossSheetConnector, ProcessingRun, ValidationResult
)
from .pdf_processor import PDFProcessor
from .preprocessing import ImagePreprocessor
from .ocr_engine import OCREngine
from .tag_extractor import TagExtractor
from .tag_normalizer import TagNormalizer
from .symbol_detector import SymbolDetector
from .legend_mapper import LegendMapper
from .spatial_association import SpatialAssociationEngine
from .line_detector import LineDetector
from .connectivity import ConnectivityEngine
from .cross_sheet import CrossSheetProcessor
from .validation import ValidationEngine
from .visual_overlay import VisualOverlayGenerator

class DocumentPipeline:
    """
    End-to-End Orchestrator for P&ID Document Intelligence & Component Extraction.
    Implements all pipeline stages sequentially and executes backtracking on anomalies.
    """

    def __init__(self, db: Session):
        self.db = db
        self.pdf_processor = PDFProcessor()
        self.preprocessor = ImagePreprocessor()
        self.ocr_engine = OCREngine()
        self.tag_extractor = TagExtractor()
        self.tag_normalizer = TagNormalizer()
        self.symbol_detector = SymbolDetector()
        self.legend_mapper = LegendMapper()
        self.spatial_engine = SpatialAssociationEngine()
        self.line_detector = LineDetector()
        self.connectivity_engine = ConnectivityEngine()
        self.cross_sheet_processor = CrossSheetProcessor()
        self.validation_engine = ValidationEngine()
        self.overlay_generator = VisualOverlayGenerator()

    def process_document(self, document_id: str) -> Dict[str, Any]:
        doc = self.db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise ValueError(f"Document {document_id} not found")

        # Create or update ProcessingRun
        run = self.db.query(ProcessingRun).filter(ProcessingRun.document_id == document_id).first()
        if not run:
            run = ProcessingRun(document_id=document_id)
            self.db.add(run)

        run.current_stage = "pdf_detection"
        run.progress_percentage = 5.0
        run.error_message = None
        run.stage_statuses = {
            "pdf_detection": {"status": "running"},
            "page_extraction": {"status": "pending"},
            "preprocessing": {"status": "pending"},
            "ocr": {"status": "pending"},
            "symbol_detection": {"status": "pending"},
            "tag_normalization": {"status": "pending"},
            "spatial_association": {"status": "pending"},
            "connectivity": {"status": "pending"},
            "cross_sheet": {"status": "pending"},
            "validation": {"status": "pending"},
            "database": {"status": "pending"},
            "visual_overlay": {"status": "pending"}
        }
        self.db.commit()

        try:
            logger.info(f"=== Starting Pipeline Execution for Document: {doc.filename} ===")

            # -----------------------------------------------------------------
            # 1. PDF TYPE DETECTION & PAGE EXTRACTION
            # -----------------------------------------------------------------
            pdf_info = self.pdf_processor.inspect_and_extract(doc.file_path, doc.id)
            doc.doc_type = pdf_info["overall_type"]
            doc.page_count = pdf_info["page_count"]
            doc.file_size = os.path.getsize(doc.file_path)

            run.stage_statuses["pdf_detection"] = {"status": "done", "type": doc.doc_type}
            run.stage_statuses["page_extraction"] = {"status": "done", "pages": doc.page_count}
            run.progress_percentage = 15.0
            self.db.commit()

            # Clean up old child records if re-running
            self.db.query(Sheet).filter(Sheet.document_id == doc.id).delete()
            self.db.query(Component).filter(Component.document_id == doc.id).delete()
            self.db.query(ValidationResult).filter(ValidationResult.document_id == doc.id).delete()
            self.db.query(CrossSheetConnector).filter(CrossSheetConnector.document_id == doc.id).delete()
            self.db.commit()

            sheets_created = []
            for p_info in pdf_info["pages"]:
                sheet = Sheet(
                    document_id=doc.id,
                    sheet_number=p_info["sheet_number"],
                    page_index=p_info["page_index"],
                    sheet_name=f"Sheet {p_info['sheet_number']:02d}",
                    page_type=p_info["page_type"],
                    width=p_info["width"],
                    height=p_info["height"],
                    image_path=p_info["image_path"],
                    processing_status="processing"
                )
                self.db.add(sheet)
                sheets_created.append((sheet, p_info))
            self.db.commit()

            all_sheet_connectors = {}
            sheet_id_to_num = {}

            # Process each sheet
            total_sheets = len(sheets_created)
            for idx, (sheet, p_info) in enumerate(sheets_created):
                sheet_id_to_num[sheet.id] = sheet.sheet_number
                self._process_single_sheet(sheet, p_info, run)
                run.progress_percentage = 20.0 + (idx + 1) / total_sheets * 55.0
                self.db.commit()

            # -----------------------------------------------------------------
            # CROSS-SHEET CONNECTOR MATCHING
            # -----------------------------------------------------------------
            run.current_stage = "cross_sheet"
            run.stage_statuses["cross_sheet"] = {"status": "running"}
            self.db.commit()

            all_connectors = self.db.query(CrossSheetConnector).filter(CrossSheetConnector.document_id == doc.id).all()
            grouped_conns = {}
            for c in all_connectors:
                c_dict = {
                    "id": c.id,
                    "sheet_id": c.sheet_id,
                    "sheet_number": sheet_id_to_num.get(c.sheet_id, 1),
                    "connector_label": c.connector_label,
                    "target_sheet_number": c.target_sheet_number,
                    "connected_component_id": c.connected_component_id,
                    "matched": c.matched,
                    "confidence": c.confidence
                }
                grouped_conns.setdefault(c.sheet_id, []).append(c_dict)

            matches = self.cross_sheet_processor.match_cross_sheet_connectors(grouped_conns, sheet_id_to_num)

            # Update DB with matched connector states
            for m in matches:
                c1 = self.db.query(CrossSheetConnector).filter(
                    CrossSheetConnector.sheet_id == m["source_sheet_id"],
                    CrossSheetConnector.connector_label == m["source_connector"]
                ).first()
                if c1:
                    c1.matched = True
                    c1.target_sheet_id = m["target_sheet_id"]
                    c1.target_sheet_number = m["target_sheet_number"]
                    c1.confidence = m["confidence"]

            run.stage_statuses["cross_sheet"] = {"status": "done", "matches_found": len(matches)}
            run.progress_percentage = 85.0
            self.db.commit()

            # -----------------------------------------------------------------
            # GENERATE VISUAL OVERLAYS
            # -----------------------------------------------------------------
            run.current_stage = "visual_overlay"
            run.stage_statuses["visual_overlay"] = {"status": "running"}
            self.db.commit()

            for sheet, _ in sheets_created:
                comps = self.db.query(Component).filter(Component.sheet_id == sheet.id).all()
                syms = self.db.query(Symbol).filter(Symbol.sheet_id == sheet.id).all()
                ocrs = self.db.query(OCRResult).filter(OCRResult.sheet_id == sheet.id).all()
                conns = self.db.query(Connection).filter(Connection.sheet_id == sheet.id).all()
                sc_conns = self.db.query(CrossSheetConnector).filter(CrossSheetConnector.sheet_id == sheet.id).all()

                overlay_dir = os.path.join(os.path.dirname(sheet.image_path), "overlays")
                os.makedirs(overlay_dir, exist_ok=True)
                overlay_path = os.path.join(overlay_dir, f"sheet_{sheet.sheet_number}_overlay.png")

                comps_data = [
                    {
                        "x1": c.x1, "y1": c.y1, "x2": c.x2, "y2": c.y2,
                        "tag": c.tag, "confidence": c.confidence, "component_type": c.component_type
                    }
                    for c in comps
                ]
                syms_data = [
                    {
                        "x1": s.x1, "y1": s.y1, "x2": s.x2, "y2": s.y2,
                        "category": s.category, "class_name": s.class_name
                    }
                    for s in syms
                ]
                ocrs_data = [
                    {"x1": o.x1, "y1": o.y1, "x2": o.x2, "y2": o.y2}
                    for o in ocrs
                ]
                conns_data = [
                    {
                        "start_x": cn.start_x, "start_y": cn.start_y,
                        "end_x": cn.end_x, "end_y": cn.end_y,
                        "path_points": cn.path_points or []
                    }
                    for cn in conns
                ]
                sc_data = [
                    {"x1": sc.x1, "y1": sc.y1, "x2": sc.x2, "y2": sc.y2, "connector_label": sc.connector_label}
                    for sc in sc_conns
                ]

                self.overlay_generator.generate_overlay(
                    base_image_path=sheet.image_path,
                    components=comps_data,
                    symbols=syms_data,
                    ocr_results=ocrs_data,
                    connections=conns_data,
                    connectors=sc_data,
                    output_path=overlay_path
                )
                sheet.overlay_path = overlay_path
                sheet.processing_status = "completed"

            run.stage_statuses["visual_overlay"] = {"status": "done"}
            run.stage_statuses["database"] = {"status": "done"}
            run.current_stage = "completed"
            run.progress_percentage = 100.0
            run.error_message = None
            run.completed_at = datetime.datetime.now(datetime.timezone.utc)

            doc.processing_status = "completed"
            self.db.commit()

            logger.info(f"=== Pipeline Successfully Completed for Document: {doc.filename} ===")
            return {"status": "success", "document_id": doc.id}

        except Exception as e:
            logger.error(f"Pipeline failed for document {document_id}: {e}", exc_info=True)
            doc.processing_status = "failed"
            failed_stage = run.current_stage or "unknown"
            run.current_stage = "failed"
            run.error_message = str(e)
            if run.stage_statuses and failed_stage in run.stage_statuses:
                run.stage_statuses[failed_stage]["status"] = "failed"
                run.stage_statuses[failed_stage]["error"] = str(e)
            self.db.commit()
            raise

    def _process_single_sheet(self, sheet: Sheet, p_info: Dict[str, Any], run: ProcessingRun):
        sheet_id = sheet.id
        image_path = sheet.image_path
        scale_factor = p_info.get("scale_factor", 2.0)
        vector_lines = p_info.get("vector_lines", [])

        # -------------------------------------------------------------
        # 1. PREPROCESSING
        # -------------------------------------------------------------
        run.stage_statuses["preprocessing"] = {"status": "running", "sheet": sheet.sheet_number}
        self.db.commit()

        preproc_result = self.preprocessor.preprocess_sheet(image_path, sheet_id)
        sheet.preprocessed_path = preproc_result["preprocessed_image_path"]

        # -------------------------------------------------------------
        # 2. OCR / TEXT RECOGNITION
        # -------------------------------------------------------------
        run.stage_statuses["ocr"] = {"status": "running", "sheet": sheet.sheet_number}
        self.db.commit()

        ocr_tokens = self.ocr_engine.process_sheet_ocr(
            pdf_path=sheet.document.file_path,
            page_index=sheet.page_index,
            sheet_id=sheet_id,
            image_path=sheet.preprocessed_path,
            page_type=sheet.page_type,
            scale_factor=scale_factor
        )

        ocr_db_entities = []
        tag_candidates = []

        for t in ocr_tokens:
            is_tag = self.tag_extractor.is_likely_tag(t["text"])
            parsed = self.tag_extractor.parse_tag(t["text"]) if is_tag else None

            # Normalization
            normalized = self.tag_normalizer.normalize_tag(t["text"]) if is_tag else None
            normalized_text = normalized["canonical_tag"] if normalized else t["text"].strip()

            ocr_res = OCRResult(
                id=str(uuid.uuid4()),
                sheet_id=sheet_id,
                text=t["text"],
                normalized_text=normalized_text,
                is_tag_candidate=is_tag,
                parsed_prefix=parsed["prefix"] if parsed else "",
                parsed_number=parsed["number"] if parsed else "",
                parsed_suffix=parsed["suffix"] if parsed else "",
                confidence=t.get("confidence", 0.9),
                x1=t["x1"],
                y1=t["y1"],
                x2=t["x2"],
                y2=t["y2"],
                source_type=t.get("source_type", "vector")
            )
            self.db.add(ocr_res)
            ocr_db_entities.append(ocr_res)

            if is_tag:
                tag_candidates.append({
                    "id": ocr_res.id,
                    "text": t["text"],
                    "canonical_tag": normalized_text,
                    "parsed_prefix": ocr_res.parsed_prefix,
                    "parsed_number": ocr_res.parsed_number,
                    "parsed_suffix": ocr_res.parsed_suffix,
                    "confidence": ocr_res.confidence,
                    "x1": ocr_res.x1,
                    "y1": ocr_res.y1,
                    "x2": ocr_res.x2,
                    "y2": ocr_res.y2,
                })

        self.db.commit()

        # -------------------------------------------------------------
        # 3. SYMBOL DETECTION
        # -------------------------------------------------------------
        run.stage_statuses["symbol_detection"] = {"status": "running", "sheet": sheet.sheet_number}
        self.db.commit()

        detected_symbols = self.symbol_detector.detect(image_path, sheet_id)
        symbol_db_entities = []
        for s in detected_symbols:
            sym_obj = Symbol(
                id=str(uuid.uuid4()),
                sheet_id=sheet_id,
                class_name=s["class_name"],
                category=s["category"],
                confidence=s["confidence"],
                detector_type=s["detector_type"],
                x1=s["x1"],
                y1=s["y1"],
                x2=s["x2"],
                y2=s["y2"],
                center_x=s["center_x"],
                center_y=s["center_y"]
            )
            self.db.add(sym_obj)
            symbol_db_entities.append(sym_obj)
        self.db.commit()

        # Pass symbol dictionaries with assigned IDs to spatial association
        symbols_with_ids = []
        for idx, sym_obj in enumerate(symbol_db_entities):
            s_dict = dict(detected_symbols[idx])
            s_dict["id"] = sym_obj.id
            symbols_with_ids.append(s_dict)

        # -------------------------------------------------------------
        # 4. SPATIAL ASSOCIATION & LEGEND MAPPING
        # -------------------------------------------------------------
        run.stage_statuses["spatial_association"] = {"status": "running", "sheet": sheet.sheet_number}
        self.db.commit()

        associations = self.spatial_engine.associate(tag_candidates, symbols_with_ids, sheet_id)

        components_created = []
        for assoc in associations:
            tag_data = assoc["tag"]
            sym_data = assoc.get("symbol")
            tag_str = tag_data.get("canonical_tag", tag_data["text"])
            prefix = tag_data.get("parsed_prefix", "")

            # Identity from Legend Mapper
            identity = self.legend_mapper.identify_component(
                prefix=prefix,
                symbol_class=sym_data["class_name"] if sym_data else "",
                symbol_category=sym_data["category"] if sym_data else ""
            )

            # Determine component bounding box
            if sym_data:
                cx, cy = sym_data["center_x"], sym_data["center_y"]
                bx1, by1 = sym_data["x1"], sym_data["y1"]
                bx2, by2 = sym_data["x2"], sym_data["y2"]
                conf = round((tag_data["confidence"] + sym_data["confidence"]) / 2.0, 3)
            else:
                cx = (tag_data["x1"] + tag_data["x2"]) / 2.0
                cy = (tag_data["y1"] + tag_data["y2"]) / 2.0
                bx1, by1 = tag_data["x1"] - 10, tag_data["y1"] - 10
                bx2, by2 = tag_data["x2"] + 10, tag_data["y2"] + 10
                conf = tag_data["confidence"]

            comp = Component(
                id=str(uuid.uuid4()),
                document_id=sheet.document_id,
                sheet_id=sheet_id,
                symbol_id=sym_data["id"] if sym_data else None,
                ocr_result_id=tag_data.get("id"),
                tag=tag_str,
                component_name=identity["component_name"],
                component_type=identity["component_type"],
                symbol_class=identity["resolved_class"],
                x1=bx1,
                y1=by1,
                x2=bx2,
                y2=by2,
                center_x=cx,
                center_y=cy,
                confidence=conf,
                association_score=assoc.get("association_score", 0.8),
                distance_to_tag=assoc.get("distance", 0.0),
                source="auto_pipeline",
                validation_status="VALID"
            )
            self.db.add(comp)
            components_created.append(comp)

        self.db.commit()

        # -------------------------------------------------------------
        # 5. LINE DETECTION & CONNECTIVITY
        # -------------------------------------------------------------
        run.stage_statuses["connectivity"] = {"status": "running", "sheet": sheet.sheet_number}
        self.db.commit()

        detected_lines = self.line_detector.detect_lines(
            image_path=sheet.preprocessed_path,
            sheet_id=sheet_id,
            vector_lines=vector_lines
        )

        comp_dicts = [
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
                "center_x": c.center_x,
                "center_y": c.center_y,
                "confidence": c.confidence,
                "association_score": c.association_score,
                "symbol_id": c.symbol_id,
                "validation_status": c.validation_status,
                "validation_notes": c.validation_notes
            }
            for c in components_created
        ]
        conn_res = self.connectivity_engine.build_graph(comp_dicts, detected_lines, sheet_id)

        connections_created = []
        for c_data in conn_res["connections"]:
            connection = Connection(
                id=str(uuid.uuid4()),
                sheet_id=sheet_id,
                source_component_id=c_data["source_component_id"],
                target_component_id=c_data["target_component_id"],
                line_label=c_data["line_label"],
                line_type=c_data["line_type"],
                start_x=c_data["start_x"],
                start_y=c_data["start_y"],
                end_x=c_data["end_x"],
                end_y=c_data["end_y"],
                path_points=c_data["path_points"],
                confidence=c_data["confidence"]
            )
            self.db.add(connection)
            connections_created.append(connection)

        self.db.commit()

        # -------------------------------------------------------------
        # 6. OFF-PAGE CONNECTORS ON THIS SHEET
        # -------------------------------------------------------------
        sheet_conns = self.cross_sheet_processor.find_connectors_on_sheet(
            sheet_id=sheet_id,
            sheet_number=sheet.sheet_number,
            ocr_results=ocr_tokens,
            symbols=symbols_with_ids,
            components=comp_dicts,
            sheet_width=sheet.width,
            sheet_height=sheet.height
        )

        for sc in sheet_conns:
            cross_conn = CrossSheetConnector(
                id=str(uuid.uuid4()),
                document_id=sheet.document_id,
                sheet_id=sheet_id,
                connector_label=sc["connector_label"],
                target_sheet_number=sc.get("target_sheet_number"),
                connected_component_id=sc.get("connected_component_id"),
                x1=sc["x1"],
                y1=sc["y1"],
                x2=sc["x2"],
                y2=sc["y2"],
                direction=sc.get("direction", "out"),
                confidence=sc.get("confidence", 0.85),
                matched=False
            )
            self.db.add(cross_conn)
            sc["id"] = cross_conn.id

        self.db.commit()

        # -------------------------------------------------------------
        # 7. VALIDATION ENGINE & BACKTRACKING
        # -------------------------------------------------------------
        run.stage_statuses["validation"] = {"status": "running", "sheet": sheet.sheet_number}
        self.db.commit()

        conn_dicts = [
            {"source_component_id": cn.source_component_id, "target_component_id": cn.target_component_id}
            for cn in connections_created
        ]

        val_summary = self.validation_engine.validate_sheet_results(
            document_id=sheet.document_id,
            sheet_id=sheet_id,
            components=comp_dicts,
            symbols=symbols_with_ids,
            ocr_results=ocr_tokens,
            connections=conn_dicts,
            connectors=sheet_conns,
            backtrack_count=run.backtrack_count
        )

        for v_item in val_summary["validation_items"]:
            val_res = ValidationResult(
                id=str(uuid.uuid4()),
                document_id=sheet.document_id,
                sheet_id=sheet_id,
                component_id=v_item["component_id"],
                rule_name=v_item["rule_name"],
                severity=v_item["severity"],
                message=v_item["message"],
                details=v_item["details"],
                backtrack_suggested=v_item["backtrack_suggested"],
                resolved=v_item["resolved"]
            )
            self.db.add(val_res)

        # Update component validation statuses back to DB
        for c in components_created:
            db_c = self.db.query(Component).filter(Component.id == c.id).first()
            if db_c:
                db_c.validation_status = c.validation_status
                db_c.validation_notes = c.validation_notes

        self.db.commit()

        # Handle BACKTRACKING if suggested
        if val_summary["should_backtrack"] and run.backtrack_count < 2:
            target = val_summary["target_stage"]
            reason = val_summary["backtrack_reason"]
            logger.warning(f"Backtracking triggered for sheet {sheet_id} to stage '{target}': {reason}")

            run.backtrack_count += 1
            history = list(run.backtrack_history or [])
            history.append({
                "from_stage": "validation",
                "to_stage": target,
                "reason": reason,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
            })
            run.backtrack_history = history
            self.db.commit()

            # Execute targeted backtracking with adapted parameters
            if target == "spatial_association":
                # Relax radius and re-run association
                relaxed_engine = SpatialAssociationEngine(max_search_radius=300.0, weight_distance=0.25)
                re_associations = relaxed_engine.associate(tag_candidates, symbols_with_ids, sheet_id)
                # Re-associate any previously unassociated components
                for a in re_associations:
                    if a.get("symbol"):
                        for c in components_created:
                            if c.tag == a["tag"].get("canonical_tag") and c.symbol_id is None:
                                c.symbol_id = a["symbol"]["id"]
                                c.association_score = a["association_score"]
                                c.validation_status = "VALID"
                                c.validation_notes = "Resolved by backtracking re-association."
                self.db.commit()

            elif target == "line_detector":
                # Re-run line detection with more forgiving gap threshold
                relaxed_line_det = LineDetector(min_line_length=18, max_line_gap=25)
                extra_lines = relaxed_line_det.detect_lines(sheet.preprocessed_path, sheet_id, vector_lines)
                re_conn_res = self.connectivity_engine.build_graph(comp_dicts, extra_lines, sheet_id)
                for new_conn in re_conn_res["connections"]:
                    # check if not already present
                    exists = any(
                        cn.source_component_id == new_conn["source_component_id"] and
                        cn.target_component_id == new_conn["target_component_id"]
                        for cn in connections_created
                    )
                    if not exists:
                        db_new_conn = Connection(
                            id=str(uuid.uuid4()),
                            sheet_id=sheet_id,
                            source_component_id=new_conn["source_component_id"],
                            target_component_id=new_conn["target_component_id"],
                            line_label=new_conn["line_label"],
                            line_type=new_conn["line_type"],
                            start_x=new_conn["start_x"],
                            start_y=new_conn["start_y"],
                            end_x=new_conn["end_x"],
                            end_y=new_conn["end_y"],
                            path_points=new_conn["path_points"],
                            confidence=new_conn["confidence"]
                        )
                        self.db.add(db_new_conn)
                self.db.commit()
