import datetime
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure all data directories exist on startup
    for d in [
        settings.raw_dir,
        settings.processed_dir,
        settings.reports_dir,
        settings.wells_dir,
        settings.jobs_dir,
        settings.detections_dir,
        settings.analysis_dir,
    ]:
        os.makedirs(d, exist_ok=True)
    yield


app = FastAPI(
    title="煤矿资源分析系统 API",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:5173", "http://localhost:80"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    os.makedirs(str(settings.reports_dir), exist_ok=True)
    app.mount("/files/reports", StaticFiles(directory=str(settings.reports_dir)), name="reports")
except Exception:
    pass  # Directory will be created on first startup inside Docker

try:
    os.makedirs(str(settings.analysis_dir), exist_ok=True)
    app.mount("/files/analysis", StaticFiles(directory=str(settings.analysis_dir)), name="analysis")
except Exception:
    pass  # Directory will be created on first startup inside Docker

from app.api import rasters, wells, tasks, reports, analytics, fusion, ai, cross_validation, enrichment  # noqa: E402

app.include_router(rasters.router, prefix="/api")
app.include_router(wells.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(fusion.router, prefix="/api")
app.include_router(ai.router, prefix="/api")
app.include_router(cross_validation.router, prefix="/api")
app.include_router(enrichment.router, prefix="/api")


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()}
