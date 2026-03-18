import uuid
import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.report import Report
from app.models.raster import RasterAsset
from app.schemas.report import ReportOut

router = APIRouter(tags=["reports"])


class ReportRequest(BaseModel):
    title: Optional[str] = "山西省 WebGIS 数据分析报告"
    raster_id: Optional[uuid.UUID] = None


@router.post("/reports/generate", response_model=ReportOut)
async def generate_report(req: ReportRequest, db: AsyncSession = Depends(get_db)):
    if req.raster_id:
        r = await db.execute(select(RasterAsset).where(RasterAsset.id == req.raster_id))
        r.scalar_one_or_none()  # validate it exists (optional)

    from app.tasks.report_tasks import task_generate_report
    report_id = uuid.uuid4()
    report = Report(id=report_id, title=req.title, raster_id=req.raster_id)
    db.add(report)
    await db.commit()

    task_generate_report.delay(str(report_id), req.title, str(req.raster_id) if req.raster_id else None)
    await db.refresh(report)
    return report


@router.get("/reports/{report_id}/download")
async def download_report(report_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if not report.file_path:
        raise HTTPException(status_code=202, detail="Report not yet generated")
    if not os.path.exists(report.file_path):
        raise HTTPException(status_code=404, detail="Report file not found on disk")
    return FileResponse(report.file_path, media_type="application/pdf", filename=f"report_{report_id}.pdf")
