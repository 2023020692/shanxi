import datetime
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    os.makedirs(settings.raw_dir, exist_ok=True)
    os.makedirs(settings.processed_dir, exist_ok=True)
    os.makedirs(settings.reports_dir, exist_ok=True)
    yield


app = FastAPI(
    title="山西省 WebGIS 平台 API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:5173", "http://localhost:80"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(str(settings.reports_dir), exist_ok=True)
app.mount("/files/reports", StaticFiles(directory=str(settings.reports_dir)), name="reports")

from app.api import rasters, wells, tasks, reports, analytics, fusion, ai  # noqa: E402

app.include_router(rasters.router, prefix="/api")
app.include_router(wells.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(fusion.router, prefix="/api")
app.include_router(ai.router, prefix="/api")


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()}
