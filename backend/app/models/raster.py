import uuid
from datetime import datetime, timezone
import enum

from sqlalchemy import Column, String, Integer, Float, DateTime, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class RasterStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    ready = "ready"
    failed = "failed"


class RasterAsset(Base):
    __tablename__ = "raster_assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String, nullable=False)
    original_path = Column(String, nullable=False)
    cog_path = Column(String, nullable=True)
    crs = Column(String, nullable=True)
    bbox = Column(JSON, nullable=True)
    band_count = Column(Integer, nullable=True)
    resolution = Column(Float, nullable=True)
    status = Column(Enum(RasterStatus), default=RasterStatus.pending, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
