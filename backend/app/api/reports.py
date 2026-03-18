import uuid
import os
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

import app.storage as storage

router = APIRouter(tags=["reports"])


class ReportRequest(BaseModel):
    title: Optional[str] = "煤矿资源分析系统数据分析报告"
    raster_id: Optional[str] = None
    enrichment_result_ids: Optional[List[str]] = None
    sam2_detection_id: Optional[str] = None
    ai_analysis_text: Optional[str] = None


class ReportOut(BaseModel):
    id: str
    title: str
    raster_id: Optional[str] = None
    file_path: Optional[str] = None
    created_at: str


@router.get("/reports", response_model=list[ReportOut])
async def list_reports():
    return [ReportOut(**r) for r in storage.list_reports()]


@router.post("/reports/generate", response_model=ReportOut)
async def generate_report(req: ReportRequest):
    report_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    report_meta = {
        "id": report_id,
        "title": req.title or "煤矿资源分析系统数据分析报告",
        "raster_id": req.raster_id,
        "file_path": None,
        "created_at": now,
    }
    storage.save_report_meta(report_meta)

    extra_context = {
        "enrichment_result_ids": req.enrichment_result_ids or [],
        "sam2_detection_id": req.sam2_detection_id,
        "ai_analysis_text": req.ai_analysis_text,
    }
    from app.tasks.report_tasks import task_generate_report
    task_generate_report.delay(
        report_id,
        req.title or "煤矿资源分析系统数据分析报告",
        req.raster_id,
        extra_context,
    )
    return ReportOut(**report_meta)


@router.get("/reports/{report_id}/download")
async def download_report(report_id: str):
    report = storage.load_report_meta(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if not report.get("file_path"):
        raise HTTPException(status_code=202, detail="Report not yet generated")
    if not os.path.exists(report["file_path"]):
        raise HTTPException(status_code=404, detail="Report file not found on disk")
    return FileResponse(
        report["file_path"],
        media_type="application/pdf",
        filename=f"report_{report_id}.pdf",
    )
