from datetime import datetime
from typing import Optional, Any, Dict
from uuid import UUID

from pydantic import BaseModel


class WellOut(BaseModel):
    id: UUID
    name: str
    props: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True
