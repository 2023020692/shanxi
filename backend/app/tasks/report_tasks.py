from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.tasks.celery_app import celery_app
from app.config import settings


def get_sync_session():
    sync_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    engine = create_engine(sync_url)
    SessionSync = sessionmaker(bind=engine)
    return SessionSync()


@celery_app.task(bind=True, name="tasks.generate_report")
def task_generate_report(self, report_id: str, title: str, raster_id: str = None):
    from app.models.report import Report
    from app.models.raster import RasterAsset
    from app.services.pdf_service import generate_pdf_report

    db = get_sync_session()
    try:
        stats = {}
        if raster_id:
            raster = db.query(RasterAsset).filter(RasterAsset.id == raster_id).first()
            if raster:
                stats = {
                    "文件名": raster.filename,
                    "状态": raster.status.value if raster.status else "N/A",
                    "波段数": raster.band_count or "N/A",
                    "分辨率": raster.resolution or "N/A",
                    "坐标系": raster.crs or "N/A",
                }

        output_path = Path(settings.reports_dir) / f"{report_id}.pdf"
        generate_pdf_report(str(output_path), title, stats)

        report = db.query(Report).filter(Report.id == report_id).first()
        if report:
            report.file_path = str(output_path)
            db.commit()

        return {"report_id": report_id, "file_path": str(output_path)}
    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc, max_retries=0)
    finally:
        db.close()
