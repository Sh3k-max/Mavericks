import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .database.session import engine, Base, SessionLocal
from .models.entities import Document
from .api.documents import router as documents_router
from .services.synthetic_generator import SyntheticPIDGenerator
from .utils.logger import logger

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="P&ID Document Intelligence & Component Extraction System",
    description="Automated P&ID component extraction, spatial association, line connectivity, and validation engine.",
    version="1.0.0"
)

# Enable CORS for frontend Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure data directories exist
os.makedirs("data/uploads", exist_ok=True)
os.makedirs("data/processed", exist_ok=True)
os.makedirs("data/overlays", exist_ok=True)

# Mount static directories
app.mount("/static/processed", StaticFiles(directory="data/processed"), name="processed")

# Include Routers
app.include_router(documents_router)

@app.get("/health")
def healthcheck():
    return {
        "status": "healthy",
        "service": "P&ID Document Intelligence Backend",
        "version": "1.0.0"
    }

@app.on_event("startup")
def startup_event():
    logger.info("Initializing P&ID Intelligence System Backend...")
    # Generate default demo file in data/uploads if none exists
    demo_file = "data/uploads/sample_pid_drawing.pdf"
    if not os.path.exists(demo_file):
        try:
            SyntheticPIDGenerator.generate_demo_pdf(demo_file)
            logger.info(f"Default synthetic demo P&ID created at {demo_file}")
        except Exception as e:
            logger.warning(f"Could not generate default demo PDF: {e}")
