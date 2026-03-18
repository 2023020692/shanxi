import os
import tempfile
import uuid

from fastapi import APIRouter, UploadFile, File, HTTPException

import app.storage as storage
from app.services.well_service import parse_wells_excel

router = APIRouter(tags=["wells"])


@router.post("/wells/import")
async def import_wells(file: UploadFile = File(...)):
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

    new_features = []
    for well in wells_data:
        new_features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [well["lon"], well["lat"]]},
            "properties": {
                "id": str(uuid.uuid4()),
                "name": well["name"],
                **{k: v for k, v in well.items() if k not in ("lon", "lat", "name")},
            },
        })

    count = storage.append_wells(new_features)
    return {"imported": count}


@router.get("/wells")
async def get_wells():
    return storage.load_wells()
