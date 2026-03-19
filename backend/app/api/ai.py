"""SAM2 (Segment Anything Model 2) analysis module API.

Accepts a satellite image annotated with mine well points and returns
simulated target-detection results together with heatmap grid data that
the frontend can render as a TIF-style overlay.

All detection results are persisted to disk so they can be listed and
replayed later.
"""
import asyncio
import random
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

import app.storage as storage
from app.config import settings

router = APIRouter(tags=["sam2"])


class DetectionBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float
    label: str


class SAM2Result(BaseModel):
    detection_id: str
    filename: str
    file_size_bytes: int
    model: str
    status: str
    detection_count: int
    detections: List[DetectionBox]
    heatmap_grid: List[dict]
    message: str
    created_at: Optional[str] = None


class SatelliteImageOut(BaseModel):
    image_id: str
    filename: str
    file_size_bytes: int
    image_url: str
    status: str
    message: str
    created_at: str


class SAM2RasterOut(BaseModel):
    raster_id: str
    filename: str
    file_size_bytes: int
    heatmap_grid: List[dict]
    status: str
    message: str
    created_at: str


def _simulate_detections(n: int) -> List[DetectionBox]:
    """Generate n simulated bounding-box detections."""
    detections = []
    for _ in range(n):
        x1 = round(random.uniform(0.05, 0.75), 4)
        y1 = round(random.uniform(0.05, 0.75), 4)
        detections.append(
            DetectionBox(
                x1=x1,
                y1=y1,
                x2=round(x1 + random.uniform(0.04, 0.15), 4),
                y2=round(y1 + random.uniform(0.04, 0.15), 4),
                confidence=round(random.uniform(0.72, 0.98), 4),
                label="coal_mine_well",
            )
        )
    return detections


def _simulate_heatmap_grid() -> List[dict]:
    """Generate a simulated heatmap grid (lon/lat/intensity) for map overlay."""
    grid = []
    base_lon, base_lat = 111.5, 37.5
    for i in range(10):
        for j in range(10):
            intensity = max(0.0, min(1.0, round(random.gauss(0.50, 0.25), 3)))
            grid.append(
                {
                    "lon": round(base_lon + (i - 5) * 0.25, 4),
                    "lat": round(base_lat + (j - 5) * 0.20, 4),
                    "intensity": intensity,
                }
            )
    return grid


@router.get("/ai/info")
async def ai_info():
    """Return information about the SAM2 analysis module."""
    return {
        "model": "SAM2",
        "version": "2.1",
        "description": "基于SAM2模型的煤矿井点卫星图像目标识别模块",
        "supported_formats": [".png", ".jpg", ".jpeg", ".tif", ".tiff"],
        "output": "热力图TIF数据（heatmap grid）及目标检测边界框",
        "status": "ready",
    }


@router.get("/ai/results", response_model=List[SAM2Result])
async def list_detections():
    """List all saved SAM2 detection results (newest first)."""
    return storage.list_detections()


@router.get("/ai/results/{detection_id}", response_model=SAM2Result)
async def get_detection(detection_id: str):
    """Get a specific saved SAM2 detection result."""
    data = storage.load_detection(detection_id)
    if not data:
        raise HTTPException(status_code=404, detail="Detection not found")
    return data


@router.post("/ai/detect", response_model=SAM2Result)
async def ai_detect(file: Optional[UploadFile] = File(None)):
    """
    Run SAM2 target detection on a satellite image annotated with mine well points.

    NOTE: The SAM2 model integration code is present for future use. Currently this
    endpoint is kept for backward compatibility but the primary workflow uses
    /api/ai/analyze-image for PNG/JPG and /api/ai/analyze-tif for TIF files.

    Returns detected bounding boxes and a heatmap grid suitable for TIF rendering.
    The result is persisted to disk and available via GET /api/ai/results.
    """
    if file and file.filename:
        file_size: int = file.size if file.size is not None else len(await file.read())
        detection_count = random.randint(3, 18)
        now = datetime.now(timezone.utc).isoformat()
        result = SAM2Result(
            detection_id=str(uuid.uuid4()),
            filename=file.filename,
            file_size_bytes=file_size,
            model="SAM2",
            status="completed",
            detection_count=detection_count,
            detections=_simulate_detections(detection_count),
            heatmap_grid=_simulate_heatmap_grid(),
            message=(
                f"SAM2目标识别完成，共识别到 {detection_count} 处煤矿井点目标，"
                "热力图数据已生成，可在地图上渲染。"
            ),
            created_at=now,
        )
        storage.save_detection(result.model_dump())
        return result

    return SAM2Result(
        detection_id="",
        filename="",
        file_size_bytes=0,
        model="SAM2",
        status="ready",
        detection_count=0,
        detections=[],
        heatmap_grid=[],
        message="请上传带有煤矿井点标注的卫星图像以启动SAM2目标识别分析。",
    )


@router.post("/ai/analyze-image", response_model=SatelliteImageOut)
async def analyze_image(file: UploadFile = File(...)):
    """
    Analyze a satellite image (PNG/JPG).

    Copies the image to the analysis folder and simulates a 3-6 second
    processing delay. The SAM2 model call code is intentionally not invoked here;
    results are stored for display in the satellite image list.
    """
    allowed_exts = {".png", ".jpg", ".jpeg"}
    filename_lower = (file.filename or "").lower()
    if not any(filename_lower.endswith(ext) for ext in allowed_exts):
        raise HTTPException(status_code=400, detail="只支持 PNG / JPG / JPEG 格式")

    image_id = str(uuid.uuid4())
    analysis_dir = Path(settings.analysis_dir)
    analysis_dir.mkdir(parents=True, exist_ok=True)

    # Sanitize filename to prevent path traversal
    safe_name = Path(file.filename or "image").name.replace("..", "").lstrip("/\\")
    if not safe_name:
        safe_name = "image.png"

    # Copy image to analysis directory
    dest_filename = f"{image_id}_{safe_name}"
    dest_path = analysis_dir / dest_filename
    with open(dest_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    file_size = dest_path.stat().st_size

    # Simulate SAM2 analysis processing time (3-6 seconds)
    sleep_seconds = random.uniform(3.0, 6.0)
    await asyncio.sleep(sleep_seconds)

    now = datetime.now(timezone.utc).isoformat()
    record = {
        "image_id": image_id,
        "filename": safe_name,
        "dest_filename": dest_filename,
        "file_size_bytes": file_size,
        "image_url": f"/files/analysis/{dest_filename}",
        "status": "completed",
        "message": "分析成功，卫星图像已添加到分析列表",
        "created_at": now,
    }
    storage.save_satellite_image(record)

    return SatelliteImageOut(
        image_id=image_id,
        filename=safe_name,
        file_size_bytes=file_size,
        image_url=f"/files/analysis/{dest_filename}",
        status="completed",
        message="分析成功，卫星图像已添加到分析列表",
        created_at=now,
    )


@router.get("/ai/satellite-images", response_model=List[SatelliteImageOut])
async def list_satellite_images():
    """List all satellite images uploaded through the SAM2 analysis module."""
    items = storage.list_satellite_images()
    return [
        SatelliteImageOut(
            image_id=item["image_id"],
            filename=item.get("filename", ""),
            file_size_bytes=item.get("file_size_bytes", 0),
            image_url=item.get("image_url", ""),
            status=item.get("status", "completed"),
            message=item.get("message", ""),
            created_at=item.get("created_at", ""),
        )
        for item in items
    ]


@router.post("/ai/analyze-tif", response_model=SAM2RasterOut)
async def analyze_tif(file: UploadFile = File(...)):
    """
    Analyze a TIF image via SAM2, rendering it as a heatmap.

    Accepts a TIF/TIFF raster file, simulates a 10+ second SAM2 processing delay,
    and returns heatmap grid data for direct map rendering. The result is stored
    and available in the SAM2 raster list for comprehensive analysis.
    """
    allowed_exts = {".tif", ".tiff"}
    filename_lower = (file.filename or "").lower()
    if not any(filename_lower.endswith(ext) for ext in allowed_exts):
        raise HTTPException(status_code=400, detail="只支持 TIF / TIFF 格式")

    raster_id = str(uuid.uuid4())
    raw_dir = Path(settings.raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Sanitize filename to prevent path traversal
    safe_tif_name = Path(file.filename or "upload.tif").name.replace("..", "").lstrip("/\\")
    if not safe_tif_name:
        safe_tif_name = "upload.tif"

    # Save TIF to raw directory
    dest_path = raw_dir / f"{raster_id}_{safe_tif_name}"
    with open(dest_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    file_size = dest_path.stat().st_size

    # Simulate SAM2 TIF analysis processing time (10-14 seconds)
    sleep_seconds = random.uniform(10.0, 14.0)
    await asyncio.sleep(sleep_seconds)

    now = datetime.now(timezone.utc).isoformat()
    heatmap_grid = _simulate_heatmap_grid()

    record = {
        "raster_id": raster_id,
        "filename": safe_tif_name,
        "file_size_bytes": file_size,
        "original_path": str(dest_path),
        "heatmap_grid": heatmap_grid,
        "status": "completed",
        "message": "TIF图像SAM2分析完成，热力图数据已生成",
        "created_at": now,
    }
    storage.save_sam2_raster(record)

    return SAM2RasterOut(
        raster_id=raster_id,
        filename=safe_tif_name,
        file_size_bytes=file_size,
        heatmap_grid=heatmap_grid,
        status="completed",
        message="TIF图像SAM2分析完成，热力图数据已生成",
        created_at=now,
    )


@router.get("/ai/sam2-rasters", response_model=List[SAM2RasterOut])
async def list_sam2_rasters():
    """List all TIF raster files analyzed through the SAM2 module."""
    items = storage.list_sam2_rasters()
    return [
        SAM2RasterOut(
            raster_id=item["raster_id"],
            filename=item.get("filename", ""),
            file_size_bytes=item.get("file_size_bytes", 0),
            heatmap_grid=item.get("heatmap_grid", []),
            status=item.get("status", "completed"),
            message=item.get("message", ""),
            created_at=item.get("created_at", ""),
        )
        for item in items
    ]

