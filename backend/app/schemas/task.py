from typing import Optional, Any

from pydantic import BaseModel


class TaskOut(BaseModel):
    task_id: str
    status: str
    result: Optional[Any] = None
