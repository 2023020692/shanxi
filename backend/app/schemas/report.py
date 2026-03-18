from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ReportOut(BaseModel):
    id: UUID
    title: str
    raster_id: Optional[UUID] = None
    file_path: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
