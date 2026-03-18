from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.tasks.celery_app import celery_app
from app.config import settings


def get_sync_session() -> Session:
    # Convert asyncpg URL to psycopg2 URL for sync access in Celery workers
    sync_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    engine = create_engine(sync_url)
    SessionSync = sessionmaker(bind=engine)
    return SessionSync()


@celery_app.task(bind=True, name="tasks.preprocess_raster")
def task_preprocess_raster(self, raster_id: str):
    import rasterio
    from app.models.raster import RasterAsset, RasterStatus
    from app.services.cog_service import convert_to_cog

    db = get_sync_session()
    try:
        raster = db.query(RasterAsset).filter(RasterAsset.id == raster_id).first()
        if not raster:
            return {"error": "Raster not found"}

        raster.status = RasterStatus.processing
        db.commit()

        with rasterio.open(raster.original_path) as src:
            bounds = src.bounds
            crs = str(src.crs)
            band_count = src.count
            transform = src.transform
            resolution = abs(transform.a)
            bbox = {
                "west": bounds.left,
                "south": bounds.bottom,
                "east": bounds.right,
                "north": bounds.top,
            }

        output_path = Path(settings.processed_dir) / f"{raster_id}.cog.tif"
        convert_to_cog(raster.original_path, str(output_path))

        raster.cog_path = str(output_path)
        raster.crs = crs
        raster.bbox = bbox
        raster.band_count = band_count
        raster.resolution = resolution
        raster.status = RasterStatus.ready
        db.commit()

        return {
            "raster_id": raster_id,
            "cog_path": str(output_path),
            "status": "ready",
        }

    except Exception as exc:
        db.rollback()
        try:
            raster = db.query(RasterAsset).filter(RasterAsset.id == raster_id).first()
            if raster:
                raster.status = RasterStatus.failed
                db.commit()
        except Exception:
            pass
        raise self.retry(exc=exc, max_retries=0)
    finally:
        db.close()
