import uuid
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

import app.storage as storage
from app.config import settings

router = APIRouter(tags=["rasters"])


class RasterOut(BaseModel):
    id: str
    filename: str
    original_path: str
    cog_path: Optional[str] = None
    crs: Optional[str] = None
    bbox: Optional[Dict[str, Any]] = None
    band_count: Optional[int] = None
    resolution: Optional[float] = None
    status: str
    created_at: str
    updated_at: Optional[str] = None


@router.get("/rasters", response_model=list[RasterOut])
async def list_rasters():
    return storage.list_rasters()


@router.get("/rasters/{raster_id}", response_model=RasterOut)
async def get_raster(raster_id: str):
    meta = storage.load_raster_meta(raster_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Raster not found")
    return meta


@router.post("/rasters/upload", response_model=RasterOut)
async def upload_raster(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith((".tif", ".tiff")):
        raise HTTPException(status_code=400, detail="Only .tif files are accepted")

    raster_id = str(uuid.uuid4())
    save_path = Path(settings.raw_dir) / f"{raster_id}_{file.filename}"
    save_path.parent.mkdir(parents=True, exist_ok=True)

    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    now = datetime.now(timezone.utc).isoformat()
    meta: Dict[str, Any] = {
        "id": raster_id,
        "filename": file.filename,
        "original_path": str(save_path),
        "cog_path": None,
        "crs": None,
        "bbox": None,
        "band_count": None,
        "resolution": None,
        "status": "pending",
        "created_at": now,
        "updated_at": now,
    }
    storage.save_raster_meta(meta)
    return meta


@router.post("/rasters/{raster_id}/preprocess")
async def preprocess_raster(raster_id: str):
    meta = storage.load_raster_meta(raster_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Raster not found")

    from app.tasks.raster_tasks import task_preprocess_raster
    task = task_preprocess_raster.delay(raster_id)
    return {"task_id": task.id, "raster_id": raster_id}
