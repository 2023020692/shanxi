import uuid
from typing import Literal, Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.task import Job

router = APIRouter(tags=["fusion"])


class FusionJobRequest(BaseModel):
    name: str
    raster_ids: List[str]
    method: Literal["overlay", "weighted_sum", "mean"] = "overlay"


class FusionJobOut(BaseModel):
    id: str
    type: str
    status: str
    result: Optional[dict] = None
    created_at: str


@router.post("/fusion/jobs", response_model=FusionJobOut)
async def create_fusion_job(req: FusionJobRequest, db: AsyncSession = Depends(get_db)):
    """Create a new multi-source data fusion job."""
    job_id = str(uuid.uuid4())
    job = Job(
        id=job_id,
        type="fusion",
        status="PENDING",
        result={
            "name": req.name,
            "raster_ids": req.raster_ids,
            "method": req.method,
        },
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return FusionJobOut(
        id=job.id,
        type=job.type,
        status=job.status,
        result=job.result,
        created_at=str(job.created_at),
    )


@router.get("/fusion/jobs", response_model=List[FusionJobOut])
async def list_fusion_jobs(db: AsyncSession = Depends(get_db)):
    """List all fusion jobs ordered by creation time (newest first)."""
    result = await db.execute(
        select(Job).where(Job.type == "fusion").order_by(Job.created_at.desc())
    )
    jobs = result.scalars().all()
    return [
        FusionJobOut(
            id=j.id,
            type=j.type,
            status=j.status,
            result=j.result,
            created_at=str(j.created_at),
        )
        for j in jobs
    ]


@router.get("/fusion/jobs/{job_id}", response_model=FusionJobOut)
async def get_fusion_job(job_id: str, db: AsyncSession = Depends(get_db)):
    """Get details of a specific fusion job."""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Fusion job not found")
    return FusionJobOut(
        id=job.id,
        type=job.type,
        status=job.status,
        result=job.result,
        created_at=str(job.created_at),
    )
