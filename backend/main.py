"""
main.py — FastAPI application entry point.

- Serves FastAPI backend + static frontend from same origin
- On startup: creates DB tables + builds in-memory RAG index
- CORS: controlled via ALLOWED_ORIGINS env var
"""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """App startup: create DB tables + rebuild in-memory RAG index."""
    logger.info("Starting Career AI backend...")

    # Create database tables
    from .database import engine, Base
    from . import models  # noqa: F401 — registers models with Base
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ready.")

    # Build RAG pipeline (in-memory, fast, ~3–8s on first boot)
    try:
        from .services.rag_pipeline import initialize_rag
        initialize_rag()
        logger.info("RAG pipeline ready.")
    except Exception as e:
        logger.error(f"RAG initialization failed: {e}. Chat will work without retrieval.")

    yield

    logger.info("Career AI backend shutting down.")


app = FastAPI(
    title="AI Career Guidance & Resume Analyzer",
    description="AI-powered resume analysis, ATS scoring, career matching, and career coaching.",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
_origins_env = os.environ.get("ALLOWED_ORIGINS", "*")
allowed_origins = [o.strip() for o in _origins_env.split(",")] if _origins_env != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API Routers ────────────────────────────────────────────────────────────────
from .routers import auth, analysis  # noqa: E402

app.include_router(auth.router)
app.include_router(analysis.router)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {"status": "ok", "version": "2.0.0"}


# ── Serve Frontend (SPA) ──────────────────────────────────────────────────────
if FRONTEND_DIR.exists():
    # Mount static assets (css, js, images)
    app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
    app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")

    # SPA catch-all: serve each HTML page by filename, fallback to index.html
    @app.get("/{page_name}.html")
    def serve_page(page_name: str):
        page_file = FRONTEND_DIR / f"{page_name}.html"
        if page_file.exists():
            return FileResponse(str(page_file))
        return FileResponse(str(FRONTEND_DIR / "index.html"))

    @app.get("/")
    def serve_root():
        return FileResponse(str(FRONTEND_DIR / "index.html"))

    # Serve any other static file (favicon, etc.)
    @app.get("/{filename}")
    def serve_static(filename: str):
        file_path = FRONTEND_DIR / filename
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(FRONTEND_DIR / "index.html"))
else:
    logger.warning(f"Frontend directory not found at {FRONTEND_DIR}. Static serving disabled.")
