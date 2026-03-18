from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, JSON

from app.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True)
    type = Column(String, nullable=False)
    status = Column(String, nullable=False, default="PENDING")
    result = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
