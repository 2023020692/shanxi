import random
import uuid
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

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
        "cog_path": str(save_path),
        "crs": None,
        "bbox": None,
        "band_count": None,
        "resolution": None,
        "status": "ready",
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


@router.get("/rasters/{raster_id}/heatmap-grid")
async def get_raster_heatmap_grid(raster_id: str):
    """Return a simulated heatmap grid (lon/lat/value points) for the raster.

    This endpoint generates grid data suitable for point-based map rendering,
    similar to how ArcGIS Pro renders raster cells as coloured point features.
    """
    meta = storage.load_raster_meta(raster_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Raster not found")

    # Grid parameters chosen to cover the Shanxi province study area (approximately
    # 110°–114°E, 35°–40°N).  16×14 cells at 0.22°×0.18° spacing provide a
    # ~3.5°×2.5° coverage centred on (111.5°E, 37.5°N).  These values are used
    # for simulation purposes until real raster data processing is implemented.
    grid: List[Dict[str, Any]] = []
    base_lon, base_lat = 111.5, 37.5
    cols, rows = 16, 14
    lon_step = 0.22
    lat_step = 0.18
    for i in range(cols):
        for j in range(rows):
            # Simulate a normalised raster value in [0,1] using a Gaussian distribution
    # (mean=0.55, stddev=0.22) to generate realistic-looking continuous data with
    # a slight positive bias, matching typical coal-density raster statistics.
    value = max(0.0, min(1.0, round(random.gauss(0.55, 0.22), 3)))
            grid.append(
                {
                    "lon": round(base_lon + (i - cols / 2) * lon_step, 4),
                    "lat": round(base_lat + (j - rows / 2) * lat_step, 4),
                    "value": value,
                }
            )
    return {"raster_id": raster_id, "filename": meta.get("filename", ""), "grid": grid}
