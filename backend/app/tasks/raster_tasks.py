from pathlib import Path

from app.tasks.celery_app import celery_app
from app.config import settings


@celery_app.task(bind=True, name="tasks.preprocess_raster")
def task_preprocess_raster(self, raster_id: str):
    """Preprocess a raw TIF: extract metadata and convert to COG."""
    import rasterio
    from app.services.cog_service import convert_to_cog
    import app.storage as storage

    try:
        meta = storage.load_raster_meta(raster_id)
        if not meta:
            return {"error": "Raster not found"}

        storage.update_raster_meta(raster_id, {"status": "processing"})

        with rasterio.open(meta["original_path"]) as src:
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
        convert_to_cog(meta["original_path"], str(output_path))

        storage.update_raster_meta(raster_id, {
            "cog_path": str(output_path),
            "crs": crs,
            "bbox": bbox,
            "band_count": band_count,
            "resolution": resolution,
            "status": "ready",
        })

        return {"raster_id": raster_id, "cog_path": str(output_path), "status": "ready"}

    except Exception as exc:
        try:
            import app.storage as st
            st.update_raster_meta(raster_id, {"status": "failed"})
        except Exception:
            pass
        raise self.retry(exc=exc, max_retries=0)
