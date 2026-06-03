from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

TodoStatus = Literal["pending", "completed"]


class TodoCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    due_date: datetime | None = None


class TodoUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    due_date: datetime | None = None
    status: TodoStatus | None = None


class TodoStatusUpdateRequest(BaseModel):
    status: TodoStatus


class TodoResponse(BaseModel):
    id: str
    user_id: str
    title: str
    description: str | None = None
    status: TodoStatus
    due_date: datetime | None = None
    created_at: datetime
    updated_at: datetime
