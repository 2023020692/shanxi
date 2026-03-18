"""SAM2 (Segment Anything Model 2) analysis module API.

Accepts a satellite image annotated with mine well points and returns
simulated target-detection results together with heatmap grid data that
the frontend can render as a TIF-style overlay.
"""
import random
import uuid

from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional

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


@router.post("/ai/detect", response_model=SAM2Result)
async def ai_detect(file: Optional[UploadFile] = File(None)):
    """
    Run SAM2 target detection on a satellite image annotated with mine well points.

    Returns detected bounding boxes and a heatmap grid suitable for TIF rendering.
    """
    if file and file.filename:
        file_size: int = file.size if file.size is not None else len(await file.read())
        detection_count = random.randint(3, 18)
        return SAM2Result(
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
        )

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
