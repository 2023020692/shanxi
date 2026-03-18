from fastapi import APIRouter

router = APIRouter(tags=["fusion"])


@router.post("/fusion/jobs")
async def create_fusion_job():
    return {"message": "融合模块待实现", "status": "placeholder"}
