import math
from collections import defaultdict

from fastapi import APIRouter, Query

import app.storage as storage

router = APIRouter(tags=["analytics"])


@router.get("/analytics/heatgrid")
async def heatgrid(
    resolution: float = Query(default=0.5, ge=0.01, le=5.0, description="Grid cell size in degrees"),
):
    """Return well density grid as GeoJSON FeatureCollection."""
    geojson = storage.load_wells()
    coords = [
        (f["geometry"]["coordinates"][0], f["geometry"]["coordinates"][1])
        for f in geojson.get("features", [])
    ]

    if not coords:
        return {"type": "FeatureCollection", "features": [], "total_wells": 0}

    grid: dict[tuple[int, int], int] = defaultdict(int)
    for lon, lat in coords:
        gi = math.floor(lon / resolution)
        gj = math.floor(lat / resolution)
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
        "total_wells": len(coords),
        "grid_cells": len(features),
    }


@router.get("/analytics/summary")
async def summary():
    """Return basic statistics about the platform data."""
    geojson = storage.load_wells()
    well_count = len(geojson.get("features", []))

    rasters = storage.list_rasters()
    raster_stats: dict[str, int] = defaultdict(int)
    for r in rasters:
        raster_stats[r.get("status", "unknown")] += 1

    report_count = len(storage.list_reports())

    return {
        "well_count": well_count,
        "raster_stats": dict(raster_stats),
        "report_count": report_count,
    }
