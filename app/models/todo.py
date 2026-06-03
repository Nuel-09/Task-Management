from datetime import datetime, timezone
from typing import Any, Literal, TypedDict

from bson import ObjectId

TODOS_COLLECTION = "todos"
TodoStatus = Literal["pending", "completed"]


class TodoDocument(TypedDict):
    _id: ObjectId
    user_id: ObjectId
    title: str
    description: str | None
    status: TodoStatus
    due_date: datetime | None
    created_at: datetime
    updated_at: datetime


def build_todo_document(
    user_id: ObjectId,
    title: str,
    description: str | None = None,
    due_date: datetime | None = None,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    return {
        "user_id": user_id,
        "title": title.strip(),
        "description": description.strip() if description else None,
        "status": "pending",
        "due_date": due_date,
        "created_at": now,
        "updated_at": now,
    }


def serialize_todo(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(document["_id"]),
        "user_id": str(document["user_id"]),
        "title": document["title"],
        "description": document.get("description"),
        "status": document["status"],
        "due_date": document.get("due_date"),
        "created_at": document["created_at"],
        "updated_at": document["updated_at"],
    }
