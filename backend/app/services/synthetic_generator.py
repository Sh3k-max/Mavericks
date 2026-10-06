import os
import pymupdf
from ..utils.logger import logger

class SyntheticPIDGenerator:
    """
    Generates a realistic multi-sheet synthetic P&ID PDF document for immediate testing
    and demo execution.
    Exercises:
    - Multi-sheet PDF ingestion
    - Real vector text + geometric symbols
    - Transmitters (PT-101, TT-101, FT-101, TT-201)
    - Control Valves (FCV-101, FCV-201, PSV-201)
    - Equipment (P-101A Pump, TK-101 Tank, V-201 Vessel)
    - Pipeline networks with line connectivity
    - Cross-sheet connectors (CONN-A between Sheet 1 and Sheet 2)
    """

    @staticmethod
    def generate_demo_pdf(output_path: str = "data/uploads/sample_pid_drawing.pdf") -> str:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        doc = pymupdf.open()

        # Page Dimensions: A3 Landscape (1190 x 842 pt) or standard 1000 x 700 pt
        width, height = 1000, 700

        # ========================================================
        # SHEET 1: Feed Pumping & Metering System (Sheet 01)
        # ========================================================
        p1 = doc.new_page(width=width, height=height)
        shape1 = p1.new_shape()

        # Border & Title Block
        shape1.draw_rect(pymupdf.Rect(30, 30, width - 30, height - 30))
        shape1.draw_rect(pymupdf.Rect(width - 280, height - 100, width - 30, height - 30))
        shape1.finish(color=(0, 0, 0), width=1.5)

        # Title Block Text
        p1.insert_text(pymupdf.Point(width - 270, height - 75), "PROJECT: HYDROCARBON REFINERY", fontsize=10, fontname="helv")
        p1.insert_text(pymupdf.Point(width - 270, height - 55), "DWG: FEED PUMPING & METERING", fontsize=10, fontname="helv")
        p1.insert_text(pymupdf.Point(width - 270, height - 38), "SHEET: 01 OF 02 | REV: 0", fontsize=9, fontname="helv")

        # 1. Storage Tank TK-101 (Rectangular / Capsule)
        shape1.draw_rect(pymupdf.Rect(70, 220, 170, 480))
        shape1.finish(color=(0, 0, 0), width=2.0)
        p1.insert_text(pymupdf.Point(95, 340), "TK-101", fontsize=12, fontname="helv")
        p1.insert_text(pymupdf.Point(82, 360), "FEED TANK", fontsize=9, fontname="helv")

        # 2. Pipeline from Tank to Pump
        shape1.draw_line(pymupdf.Point(170, 420), pymupdf.Point(260, 420))
        shape1.finish(color=(0, 0, 0), width=2.5)

        # 3. Pump P-101A (Circle + discharge nozzle)
        shape1.draw_circle(pymupdf.Point(290, 420), 28)
        shape1.draw_line(pymupdf.Point(290, 392), pymupdf.Point(290, 340))
        shape1.finish(color=(0, 0, 0), width=2.0)
        p1.insert_text(pymupdf.Point(270, 425), "P-101A", fontsize=9, fontname="helv")

        # 4. Discharge Pipeline continuing up and right
        shape1.draw_line(pymupdf.Point(290, 340), pymupdf.Point(400, 340))
        shape1.finish(color=(0, 0, 0), width=2.5)

        # 5. Flow Control Valve FCV-101 (Bowtie shape on pipe)
        # Left triangle (400, 325) to (420, 340) to (400, 355)
        shape1.draw_line(pymupdf.Point(400, 325), pymupdf.Point(420, 340))
        shape1.draw_line(pymupdf.Point(420, 340), pymupdf.Point(400, 355))
        shape1.draw_line(pymupdf.Point(400, 355), pymupdf.Point(400, 325))
        # Right triangle (440, 325) to (420, 340) to (440, 355)
        shape1.draw_line(pymupdf.Point(440, 325), pymupdf.Point(420, 340))
        shape1.draw_line(pymupdf.Point(420, 340), pymupdf.Point(440, 355))
        shape1.draw_line(pymupdf.Point(440, 355), pymupdf.Point(440, 325))
        # Actuator stem and diaphragm dome
        shape1.draw_line(pymupdf.Point(420, 340), pymupdf.Point(420, 305))
        shape1.draw_circle(pymupdf.Point(420, 295), 10)
        shape1.finish(color=(0, 0, 0), width=1.5)
        p1.insert_text(pymupdf.Point(400, 275), "FCV-101", fontsize=9, fontname="helv")

        # 6. Pipeline from FCV-101 through transmitters to connector
        shape1.draw_line(pymupdf.Point(440, 340), pymupdf.Point(820, 340))
        shape1.finish(color=(0, 0, 0), width=2.5)

        # 7. Flow Transmitter FT-101 (Bubble connected to pipe)
        shape1.draw_line(pymupdf.Point(520, 340), pymupdf.Point(520, 240))
        shape1.draw_circle(pymupdf.Point(520, 215), 24)
        shape1.finish(color=(0, 0, 0), width=1.5)
        p1.insert_text(pymupdf.Point(507, 219), "FT-101", fontsize=9, fontname="helv")

        # 8. Pressure Transmitter PT-101 (Bubble connected to pipe)
        shape1.draw_line(pymupdf.Point(630, 340), pymupdf.Point(630, 240))
        shape1.draw_circle(pymupdf.Point(630, 215), 24)
        shape1.finish(color=(0, 0, 0), width=1.5)
        p1.insert_text(pymupdf.Point(617, 219), "PT-101", fontsize=9, fontname="helv")

        # 9. Temperature Transmitter TT-101 (Bubble connected to pipe)
        shape1.draw_line(pymupdf.Point(740, 340), pymupdf.Point(740, 440))
        shape1.draw_circle(pymupdf.Point(740, 465), 24)
        shape1.finish(color=(0, 0, 0), width=1.5)
        p1.insert_text(pymupdf.Point(727, 469), "TT-101", fontsize=9, fontname="helv")

        # 10. Off-Page Connector Arrow CONN-A TO SHEET 2
        # Arrow pointing to the right margin
        shape1.draw_line(pymupdf.Point(820, 325), pymupdf.Point(870, 325))
        shape1.draw_line(pymupdf.Point(870, 325), pymupdf.Point(895, 340))
        shape1.draw_line(pymupdf.Point(895, 340), pymupdf.Point(870, 355))
        shape1.draw_line(pymupdf.Point(870, 355), pymupdf.Point(820, 355))
        shape1.draw_line(pymupdf.Point(820, 355), pymupdf.Point(820, 325))
        shape1.finish(color=(0, 0, 0), width=1.5)
        p1.insert_text(pymupdf.Point(825, 344), "CONN-A", fontsize=9, fontname="helv")
        p1.insert_text(pymupdf.Point(815, 375), "TO SHEET 2", fontsize=9, fontname="helv")

        shape1.commit()

        # ========================================================
        # SHEET 2: Fractionation & Separation System (Sheet 02)
        # ========================================================
        p2 = doc.new_page(width=width, height=height)
        shape2 = p2.new_shape()

        # Border & Title Block
        shape2.draw_rect(pymupdf.Rect(30, 30, width - 30, height - 30))
        shape2.draw_rect(pymupdf.Rect(width - 280, height - 100, width - 30, height - 30))
        shape2.finish(color=(0, 0, 0), width=1.5)

        # Title Block Text
        p2.insert_text(pymupdf.Point(width - 270, height - 75), "PROJECT: HYDROCARBON REFINERY", fontsize=10, fontname="helv")
        p2.insert_text(pymupdf.Point(width - 270, height - 55), "DWG: FRACTIONATION COLUMN", fontsize=10, fontname="helv")
        p2.insert_text(pymupdf.Point(width - 270, height - 38), "SHEET: 02 OF 02 | REV: 0", fontsize=9, fontname="helv")

        # 1. Matching Off-Page Connector Arrow CONN-A FROM SHEET 1
        shape2.draw_line(pymupdf.Point(80, 340), pymupdf.Point(105, 325))
        shape2.draw_line(pymupdf.Point(105, 325), pymupdf.Point(155, 325))
        shape2.draw_line(pymupdf.Point(155, 325), pymupdf.Point(155, 355))
        shape2.draw_line(pymupdf.Point(155, 355), pymupdf.Point(105, 355))
        shape2.draw_line(pymupdf.Point(105, 355), pymupdf.Point(80, 340))
        shape2.finish(color=(0, 0, 0), width=1.5)
        p2.insert_text(pymupdf.Point(92, 344), "CONN-A", fontsize=9, fontname="helv")
        p2.insert_text(pymupdf.Point(82, 375), "FROM SHEET 1", fontsize=9, fontname="helv")

        # 2. Pipeline leading into FCV-201
        shape2.draw_line(pymupdf.Point(155, 340), pymupdf.Point(260, 340))
        shape2.finish(color=(0, 0, 0), width=2.5)

        # 3. Flow Control Valve FCV-201
        shape2.draw_line(pymupdf.Point(260, 325), pymupdf.Point(280, 340))
        shape2.draw_line(pymupdf.Point(280, 340), pymupdf.Point(260, 355))
        shape2.draw_line(pymupdf.Point(260, 355), pymupdf.Point(260, 325))
        shape2.draw_line(pymupdf.Point(300, 325), pymupdf.Point(280, 340))
        shape2.draw_line(pymupdf.Point(280, 340), pymupdf.Point(300, 355))
        shape2.draw_line(pymupdf.Point(300, 355), pymupdf.Point(300, 325))
        shape2.draw_line(pymupdf.Point(280, 340), pymupdf.Point(280, 305))
        shape2.draw_circle(pymupdf.Point(280, 295), 10)
        shape2.finish(color=(0, 0, 0), width=1.5)
        p2.insert_text(pymupdf.Point(260, 275), "FCV-201", fontsize=9, fontname="helv")

        # 4. Pipeline into Column V-201
        shape2.draw_line(pymupdf.Point(300, 340), pymupdf.Point(480, 340))
        shape2.finish(color=(0, 0, 0), width=2.5)

        # 5. Fractionation Vessel V-201
        shape2.draw_rect(pymupdf.Rect(480, 160, 580, 520))
        shape2.finish(color=(0, 0, 0), width=2.5)
        p2.insert_text(pymupdf.Point(515, 335), "V-201", fontsize=12, fontname="helv")
        p2.insert_text(pymupdf.Point(495, 355), "COLUMN", fontsize=9, fontname="helv")

        # 6. Pressure Safety Valve PSV-201 on top vapor line of column
        shape2.draw_line(pymupdf.Point(530, 160), pymupdf.Point(530, 100))
        shape2.draw_line(pymupdf.Point(530, 100), pymupdf.Point(620, 100))
        # Valve bowtie at (620, 100)
        shape2.draw_line(pymupdf.Point(620, 90), pymupdf.Point(635, 100))
        shape2.draw_line(pymupdf.Point(635, 100), pymupdf.Point(620, 110))
        shape2.draw_line(pymupdf.Point(620, 110), pymupdf.Point(620, 90))
        shape2.draw_line(pymupdf.Point(650, 90), pymupdf.Point(635, 100))
        shape2.draw_line(pymupdf.Point(635, 100), pymupdf.Point(650, 110))
        shape2.draw_line(pymupdf.Point(650, 110), pymupdf.Point(650, 90))
        shape2.finish(color=(0, 0, 0), width=1.5)
        p2.insert_text(pymupdf.Point(620, 75), "PSV-201", fontsize=9, fontname="helv")

        # 7. Temperature Transmitter TT-201 on Column Body
        shape2.draw_line(pymupdf.Point(580, 240), pymupdf.Point(680, 240))
        shape2.draw_circle(pymupdf.Point(705, 240), 24)
        shape2.finish(color=(0, 0, 0), width=1.5)
        p2.insert_text(pymupdf.Point(692, 244), "TT-201", fontsize=9, fontname="helv")

        shape2.commit()

        doc.save(output_path)
        doc.close()
        logger.info(f"Synthetic demo P&ID PDF successfully generated at {output_path}")
        return output_path
