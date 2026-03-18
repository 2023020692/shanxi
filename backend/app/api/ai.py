import uuid

from fastapi import APIRouter, UploadFile, File

router = APIRouter(tags=["ai"])


@router.post("/ai/detect")
async def ai_detect(file: UploadFile = File(None)):
    """
    SAM2-based intelligent feature detection endpoint.
    Accepts an image file and returns detection results.
    Note: SAM2 model integration is pending; currently returns a structured placeholder response.
    """
    if file and file.filename:
        # Use reported size if available to avoid loading the whole file just for metadata
        file_size: int = file.size if file.size is not None else len(await file.read())
        return {
            "status": "completed",
            "detection_id": str(uuid.uuid4()),
            "filename": file.filename,
            "file_size_bytes": file_size,
            "detections": [],
            "model": "SAM2",
            "message": "SAM2模型待集成，当前返回空检测结果。请部署ai-service后使用完整功能。",
        }

    return {
        "status": "ready",
        "model": "SAM2",
        "message": "SAM2智能识别模块待实现，请上传图像文件进行检测。",
        "supported_formats": [".png", ".jpg", ".jpeg", ".tif"],
        "endpoint": "POST /api/ai/detect  (multipart/form-data, field: file)",
    }
