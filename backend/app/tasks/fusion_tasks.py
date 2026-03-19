import copy

from app.tasks.celery_app import celery_app


@celery_app.task(bind=True, name="tasks.run_fusion_job")
def task_run_fusion_job(self, job_id: str):
    """Process a fusion job: merge raster metadata and mark job complete."""
    import app.storage as storage

    try:
        job = storage.load_job(job_id)
        if not job:
            return {"error": "Job not found"}

        storage.update_job(job_id, {"status": "STARTED"})

        result_data = job.get("result") or {}
        raster_ids = result_data.get("raster_ids", [])
        method = result_data.get("method", "overlay")

        merged_bbox = None
        raster_details = []
        for rid in raster_ids:
            raster = storage.load_raster_meta(rid)
            if raster and raster.get("bbox"):
                raster_details.append(
                    {
                        "id": raster["id"],
                        "filename": raster["filename"],
                        "crs": raster.get("crs"),
                        "band_count": raster.get("band_count"),
                        "resolution": raster.get("resolution"),
                        "bbox": raster.get("bbox"),
                    }
                )
                bbox = raster["bbox"]
                if merged_bbox is None:
                    merged_bbox = copy.deepcopy(bbox)
                else:
                    merged_bbox["west"] = min(merged_bbox["west"], bbox["west"])
                    merged_bbox["south"] = min(merged_bbox["south"], bbox["south"])
                    merged_bbox["east"] = max(merged_bbox["east"], bbox["east"])
                    merged_bbox["north"] = max(merged_bbox["north"], bbox["north"])

        storage.update_job(job_id, {
            "status": "SUCCESS",
            "result": {
                **result_data,
                "raster_details": raster_details,
                "merged_bbox": merged_bbox,
                "output_message": (
                    f"融合完成: 方法={method}, 栅格数量={len(raster_details)}"
                ),
            },
        })

        return {"job_id": job_id, "status": "SUCCESS"}

    except Exception as exc:
        try:
            import app.storage as st
            st.update_job(job_id, {"status": "FAILURE"})
        except Exception:
            pass
        raise self.retry(exc=exc, max_retries=0)
