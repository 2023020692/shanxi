import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    raster_id = Column(UUID(as_uuid=True), ForeignKey("raster_assets.id", ondelete="SET NULL"), nullable=True)
    file_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
