from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

# Use non-relative imports for stability
from .database import Base, engine, get_db, User, ResumeResult
from .routers import auth, analysis
# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Career Guidance System")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Include API Routers
app.include_router(auth.router)
app.include_router(analysis.router)

# 2. Serve Frontend Files
FRONTEND_PATH = os.path.join(os.path.dirname(__file__), '..', 'frontend')

# Serve CSS files
# We map both /assets and /css to the css folder to ensure it works
app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_PATH, "css")), name="css_assets")
app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_PATH, "css")), name="css_dir")

# Serve JS files
app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND_PATH, "js")), name="js")

@app.get("/")
async def root():
    return FileResponse(os.path.join(FRONTEND_PATH, 'index.html'))

@app.get("/dashboard.html")
async def dashboard():
    return FileResponse(os.path.join(FRONTEND_PATH, 'dashboard.html'))