from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.tasks.celery_app import celery_app
from app.config import settings


def get_sync_session():
    sync_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    engine = create_engine(sync_url)
    SessionSync = sessionmaker(bind=engine)
    return SessionSync()


@celery_app.task(bind=True, name="tasks.run_fusion_job")
def task_run_fusion_job(self, job_id: str):
    """Process a fusion job: merge raster metadata and mark job complete."""
    import copy
    from app.models.task import Job
    from app.models.raster import RasterAsset

    db = get_sync_session()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return {"error": "Job not found"}

        job.status = "STARTED"
        db.commit()

        result_data = job.result or {}
        raster_ids = result_data.get("raster_ids", [])
        method = result_data.get("method", "overlay")

        merged_bbox = None
        raster_details = []
        for rid in raster_ids:
            raster = db.query(RasterAsset).filter(RasterAsset.id == rid).first()
            if raster and raster.bbox:
                raster_details.append(
                    {
                        "id": str(raster.id),
                        "filename": raster.filename,
                        "crs": raster.crs,
                        "band_count": raster.band_count,
                        "resolution": raster.resolution,
                        "bbox": raster.bbox,
                    }
                )
                bbox = raster.bbox
                if merged_bbox is None:
                    merged_bbox = copy.deepcopy(bbox)
                else:
                    merged_bbox["west"] = min(merged_bbox["west"], bbox["west"])
                    merged_bbox["south"] = min(merged_bbox["south"], bbox["south"])
                    merged_bbox["east"] = max(merged_bbox["east"], bbox["east"])
                    merged_bbox["north"] = max(merged_bbox["north"], bbox["north"])

        job.result = {
            **result_data,
            "raster_details": raster_details,
            "merged_bbox": merged_bbox,
            "output_message": (
                f"融合完成: 方法={method}, 栅格数量={len(raster_details)}"
            ),
        }
        job.status = "SUCCESS"
        db.commit()

        return {"job_id": job_id, "status": "SUCCESS"}

    except Exception as exc:
        db.rollback()
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                job.status = "FAILURE"
                db.commit()
        except Exception:
            pass
        raise self.retry(exc=exc, max_retries=0)
    finally:
        db.close()
