import os
import tempfile

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_db
from app.models.well import MineWell
from app.services.well_service import parse_wells_excel

router = APIRouter(tags=["wells"])


@router.post("/wells/import")
async def import_wells(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    if not file.filename or not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files accepted")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        wells_data = parse_wells_excel(tmp_path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        os.unlink(tmp_path)

    count = 0
    for well in wells_data:
        wkt = f"SRID=4326;POINT({well['lon']} {well['lat']})"
        db_well = MineWell(
            name=well["name"],
            geom=wkt,
            props={k: v for k, v in well.items() if k not in ("lon", "lat", "name")},
        )
        db.add(db_well)
        count += 1

    await db.commit()
    return {"imported": count}


@router.get("/wells")
async def get_wells(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text("SELECT id, name, props, ST_X(geom) as lon, ST_Y(geom) as lat FROM mine_wells")
    )
    rows = result.fetchall()
    features = []
    for row in rows:
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [row.lon, row.lat]},
            "properties": {"id": str(row.id), "name": row.name, **(row.props or {})},
        })
    return {"type": "FeatureCollection", "features": features}
