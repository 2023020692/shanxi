import math
from collections import defaultdict

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_db

router = APIRouter(tags=["analytics"])


@router.get("/analytics/heatgrid")
async def heatgrid(
    db: AsyncSession = Depends(get_db),
    resolution: float = Query(default=0.5, ge=0.01, le=5.0, description="Grid cell size in degrees"),
):
    """Return well density grid as GeoJSON FeatureCollection."""
    result = await db.execute(
        text("SELECT ST_X(geom) as lon, ST_Y(geom) as lat FROM mine_wells")
    )
    rows = result.fetchall()

    if not rows:
        return {"type": "FeatureCollection", "features": [], "total_wells": 0}

    grid: dict[tuple[int, int], int] = defaultdict(int)
    for row in rows:
        gi = math.floor(row.lon / resolution)
        gj = math.floor(row.lat / resolution)
        grid[(gi, gj)] += 1

    features = []
    for (gi, gj), count in grid.items():
        cx = round((gi + 0.5) * resolution, 6)
        cy = round((gj + 0.5) * resolution, 6)
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [cx, cy]},
                "properties": {"count": count, "lon": cx, "lat": cy},
            }
        )

    features.sort(key=lambda f: f["properties"]["count"], reverse=True)
    return {
        "type": "FeatureCollection",
        "features": features,
        "total_wells": len(rows),
        "grid_cells": len(features),
    }


@router.get("/analytics/summary")
async def summary(db: AsyncSession = Depends(get_db)):
    """Return basic statistics about the platform data."""
    wells_result = await db.execute(text("SELECT COUNT(*) as cnt FROM mine_wells"))
    well_count = wells_result.scalar() or 0

    raster_result = await db.execute(
        text("SELECT status, COUNT(*) as cnt FROM raster_assets GROUP BY status")
    )
    raster_stats = {row.status: row.cnt for row in raster_result.fetchall()}

    report_result = await db.execute(text("SELECT COUNT(*) as cnt FROM reports"))
    report_count = report_result.scalar() or 0

    return {
        "well_count": well_count,
        "raster_stats": raster_stats,
        "report_count": report_count,
    }
