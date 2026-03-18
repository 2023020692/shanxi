from pathlib import Path
from typing import Optional

from app.tasks.celery_app import celery_app
from app.config import settings


@celery_app.task(bind=True, name="tasks.generate_report")
def task_generate_report(
    self,
    report_id: str,
    title: str,
    raster_id: Optional[str] = None,
    extra_context: Optional[dict] = None,
):
    from app.services.pdf_service import generate_pdf_report
    import app.storage as storage

    try:
        stats = {}
        if raster_id:
            raster = storage.load_raster_meta(raster_id)
            if raster:
                stats = {
                    "文件名": raster["filename"],
                    "状态": raster.get("status", "N/A"),
                    "波段数": raster.get("band_count") or "N/A",
                    "分辨率": raster.get("resolution") or "N/A",
                    "坐标系": raster.get("crs") or "N/A",
                }

        if extra_context:
            if extra_context.get("enrichment_result_ids"):
                stats["富集指数结果"] = ", ".join(extra_context["enrichment_result_ids"])
            if extra_context.get("sam2_detection_id"):
                stats["SAM2检测ID"] = extra_context["sam2_detection_id"]
            if extra_context.get("ai_analysis_text"):
                stats["AI分析结论"] = extra_context["ai_analysis_text"]

        output_path = Path(settings.reports_dir) / f"{report_id}.pdf"
        generate_pdf_report(str(output_path), title, stats)

        storage.update_report_meta(report_id, {"file_path": str(output_path)})

        return {"report_id": report_id, "file_path": str(output_path)}
    except Exception as exc:
        raise self.retry(exc=exc, max_retries=0)
