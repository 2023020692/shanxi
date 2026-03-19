# Model removed – replaced by file-system storage (app/storage.py).
import enum


class RasterStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    ready = "ready"
    failed = "failed"
