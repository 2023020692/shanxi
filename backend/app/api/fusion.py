import uuid
from datetime import datetime, timezone
from typing import Literal, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import app.storage as storage

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
async def create_fusion_job(req: FusionJobRequest):
    """Create a new multi-source data fusion job."""
    job_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    job = {
        "id": job_id,
        "type": "fusion",
        "status": "PENDING",
        "result": {
            "name": req.name,
            "raster_ids": req.raster_ids,
            "method": req.method,
        },
        "created_at": now,
        "updated_at": now,
    }
    storage.save_job(job)

    from app.tasks.fusion_tasks import task_run_fusion_job
    task_run_fusion_job.delay(job_id)

    return FusionJobOut(
        id=job["id"],
        type=job["type"],
        status=job["status"],
        result=job["result"],
        created_at=now,
    )


@router.get("/fusion/jobs", response_model=List[FusionJobOut])
async def list_fusion_jobs():
    """List all fusion jobs ordered by creation time (newest first)."""
    jobs = storage.list_jobs(job_type="fusion")
    return [
        FusionJobOut(
            id=j["id"],
            type=j["type"],
            status=j["status"],
            result=j.get("result"),
            created_at=j["created_at"],
        )
        for j in jobs
    ]


@router.get("/fusion/jobs/{job_id}", response_model=FusionJobOut)
async def get_fusion_job(job_id: str):
    """Get details of a specific fusion job."""
    job = storage.load_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Fusion job not found")
    return FusionJobOut(
        id=job["id"],
        type=job["type"],
        status=job["status"],
        result=job.get("result"),
        created_at=job["created_at"],
    )
