from datetime import datetime
from typing import Optional, Any, Dict
from uuid import UUID

from pydantic import BaseModel


class RasterOut(BaseModel):
    id: UUID
    filename: str
    original_path: str
    cog_path: Optional[str] = None
    crs: Optional[str] = None
    bbox: Optional[Dict[str, Any]] = None
    band_count: Optional[int] = None
    resolution: Optional[float] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
