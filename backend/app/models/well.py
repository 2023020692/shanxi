import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geometry

from app.database import Base


class MineWell(Base):
    __tablename__ = "mine_wells"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    geom = Column(Geometry("POINT", srid=4326), nullable=False)
    props = Column(JSON, default={})
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
