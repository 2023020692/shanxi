import uuid
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.raster import RasterAsset, RasterStatus
from app.schemas.raster import RasterOut
from app.config import settings

router = APIRouter(tags=["rasters"])


@router.get("/rasters", response_model=list[RasterOut])
async def list_rasters(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RasterAsset).order_by(RasterAsset.created_at.desc()))
    return result.scalars().all()


@router.get("/rasters/{raster_id}", response_model=RasterOut)
async def get_raster(raster_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RasterAsset).where(RasterAsset.id == raster_id))
    raster = result.scalar_one_or_none()
    if not raster:
        raise HTTPException(status_code=404, detail="Raster not found")
    return raster


@router.post("/rasters/upload", response_model=RasterOut)
async def upload_raster(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    if not file.filename or not file.filename.endswith(".tif"):
        raise HTTPException(status_code=400, detail="Only .tif files are accepted")

    raster_id = uuid.uuid4()
    save_path = Path(settings.raw_dir) / f"{raster_id}_{file.filename}"
    save_path.parent.mkdir(parents=True, exist_ok=True)

    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    raster = RasterAsset(
        id=raster_id,
        filename=file.filename,
        original_path=str(save_path),
        status=RasterStatus.pending,
    )
    db.add(raster)
    await db.commit()
    await db.refresh(raster)
    return raster


@router.post("/rasters/{raster_id}/preprocess")
async def preprocess_raster(raster_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RasterAsset).where(RasterAsset.id == raster_id))
    raster = result.scalar_one_or_none()
    if not raster:
        raise HTTPException(status_code=404, detail="Raster not found")

    from app.tasks.raster_tasks import task_preprocess_raster
    task = task_preprocess_raster.delay(str(raster_id))
    return {"task_id": task.id, "raster_id": str(raster_id)}
