"""FastAPI application entry point."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config_loader import load_config
from database import init_db

# Import routers
from api.upload import router as upload_router
from api.dashboard import router as dashboard_router
from api.drilldown import router as drilldown_router
from api.checklist import router as checklist_router

app = FastAPI(title="Process Evaluation Agent", version="0.1.0")

# CORS — allow Vite dev server on port 5173
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routers
app.include_router(upload_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(drilldown_router, prefix="/api")
app.include_router(checklist_router, prefix="/api")

# Serve built React app (Phase 3+; skip if not built yet)
_FRONTEND_BUILD = Path(__file__).parent.parent / "frontend" / "dist"
if _FRONTEND_BUILD.exists():
    app.mount("/", StaticFiles(directory=_FRONTEND_BUILD, html=True), name="static")


@app.on_event("startup")
def on_startup() -> None:
    load_config()
    init_db()
