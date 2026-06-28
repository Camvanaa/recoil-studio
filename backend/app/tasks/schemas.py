from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

TaskStatus = Literal["queued", "running", "succeeded", "failed", "cancelled"]


class TaskCreateRequest(BaseModel):
    type: str
    payload: dict[str, object] = Field(default_factory=dict)


class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: str
    status: TaskStatus = "queued"
    progress: float = 0
    message: str | None = None
    payload: dict[str, object] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
