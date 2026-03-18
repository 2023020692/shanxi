from fastapi import APIRouter

router = APIRouter(tags=["ai"])


@router.post("/ai/detect")
async def ai_detect():
    return {"message": "SAM2识别模块待实现", "status": "placeholder"}
