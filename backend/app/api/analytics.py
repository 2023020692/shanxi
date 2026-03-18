from fastapi import APIRouter

router = APIRouter(tags=["analytics"])


@router.get("/analytics/heatgrid")
async def heatgrid():
    return {"type": "FeatureCollection", "features": []}
