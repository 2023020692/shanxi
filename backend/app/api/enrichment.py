"""Coal mine enrichment index recognition module API."""
import random
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.task import Job

router = APIRouter(tags=["enrichment"])

ENRICHMENT_METHODS = {
    "weighted_composite": "加权复合指数法",
    "pca": "主成分分析法",
    "spectral_index": "光谱指数法",
}


class EnrichmentRequest(BaseModel):
    name: str
    raster_ids: List[str]
    method: str = "weighted_composite"


class EnrichmentResultItem(BaseModel):
    id: str
    name: str
    raster_ids: List[str]
    method: str
    method_name: str
    status: str
    enrichment_index: Optional[float] = None
    high_value_ratio: Optional[float] = None
    coverage_area_km2: Optional[float] = None
    colormap: str = "hot"
    created_at: str


def _generate_enrichment_grid() -> list:
    """Generate a simulated enrichment index grid for map visualization."""
    grid = []
    base_lon, base_lat = 111.5, 37.5
    for i in range(12):
        for j in range(10):
            value = max(0.0, min(1.0, round(random.gauss(0.55, 0.22), 3)))
            grid.append(
                {
                    "lon": round(base_lon + (i - 6) * 0.28, 4),
                    "lat": round(base_lat + (j - 5) * 0.18, 4),
                    "value": value,
                }
            )
    return grid


@router.post("/enrichment/analyze", response_model=EnrichmentResultItem)
async def analyze_enrichment(req: EnrichmentRequest, db: AsyncSession = Depends(get_db)):
    """Run coal mine enrichment index analysis on the selected raster layers."""
    job_id = str(uuid.uuid4())

    enrichment_index = round(random.uniform(0.50, 0.95), 4)
    high_value_ratio = round(random.uniform(0.12, 0.48), 4)
    coverage_area = round(random.uniform(80, 6000), 2)
    method_name = ENRICHMENT_METHODS.get(req.method, req.method)

    job = Job(
        id=job_id,
        type="enrichment",
        status="SUCCESS",
        result={
            "name": req.name,
            "raster_ids": req.raster_ids,
            "method": req.method,
            "method_name": method_name,
            "enrichment_index": enrichment_index,
            "high_value_ratio": high_value_ratio,
            "coverage_area_km2": coverage_area,
            "colormap": "hot",
            "grid": _generate_enrichment_grid(),
        },
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    return EnrichmentResultItem(
        id=job.id,
        name=req.name,
        raster_ids=req.raster_ids,
        method=req.method,
        method_name=method_name,
        status="SUCCESS",
        enrichment_index=enrichment_index,
        high_value_ratio=high_value_ratio,
        coverage_area_km2=coverage_area,
        colormap="hot",
        created_at=str(job.created_at),
    )


@router.get("/enrichment/results", response_model=List[EnrichmentResultItem])
async def list_enrichment_results(db: AsyncSession = Depends(get_db)):
    """List all enrichment analysis results (newest first)."""
    result = await db.execute(
        select(Job).where(Job.type == "enrichment").order_by(Job.created_at.desc())
    )
    jobs = result.scalars().all()
    items = []
    for j in jobs:
        r = j.result or {}
        items.append(
            EnrichmentResultItem(
                id=j.id,
                name=r.get("name", ""),
                raster_ids=r.get("raster_ids", []),
                method=r.get("method", ""),
                method_name=r.get("method_name", r.get("method", "")),
                status=j.status,
                enrichment_index=r.get("enrichment_index"),
                high_value_ratio=r.get("high_value_ratio"),
                coverage_area_km2=r.get("coverage_area_km2"),
                colormap=r.get("colormap", "hot"),
                created_at=str(j.created_at),
            )
        )
    return items


@router.get("/enrichment/results/{result_id}")
async def get_enrichment_result(result_id: str, db: AsyncSession = Depends(get_db)):
    """Return full result data (including grid) for a specific enrichment job."""
    result = await db.execute(
        select(Job).where(Job.id == result_id, Job.type == "enrichment")
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Enrichment result not found")
    return job.result
