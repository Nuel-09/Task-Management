from datetime import datetime, timezone
from typing import Any, TypedDict

from bson import ObjectId

USERS_COLLECTION = "users"


class UserDocument(TypedDict):
    _id: ObjectId
    email: str
    full_name: str
    hashed_password: str
    created_at: datetime


def build_user_document(email: str, full_name: str, hashed_password: str) -> dict[str, Any]:
    return {
        "email": email.lower(),
        "full_name": full_name.strip(),
        "hashed_password": hashed_password,
        "created_at": datetime.now(timezone.utc),
    }


def serialize_user(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(document["_id"]),
        "email": document["email"],
        "full_name": document["full_name"],
        "created_at": document["created_at"],
    }
