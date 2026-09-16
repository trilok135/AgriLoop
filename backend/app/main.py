from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import get_settings
from app.database import Base, engine
from app.routers import bale, weigh, custody, documents, auth
import os

settings = get_settings()

# Create tables
Base.metadata.create_all(bind=engine)

# Create static directories
os.makedirs(settings.static_files_path, exist_ok=True)
os.makedirs(settings.qr_codes_path, exist_ok=True)
os.makedirs(settings.documents_path, exist_ok=True)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AgriLoop Backend API - Digital Agricultural Residue Platform"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
app.mount("/static", StaticFiles(directory=settings.static_files_path), name="static")
app.mount("/ui", StaticFiles(directory="../frontend", html=True), name="ui")

# Routers
app.include_router(bale.router)
app.include_router(weigh.router)
app.include_router(custody.router)
app.include_router(documents.router)
app.include_router(auth.router)


@app.get("/")
def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "demo_mode": settings.demo_mode,
        "docs": "/docs",
        "health": "ok"
    }


@app.get("/health")
def health():
    return {"status": "healthy", "demo_mode": settings.demo_mode}
