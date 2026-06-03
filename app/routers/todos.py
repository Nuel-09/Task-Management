from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_db
from app.models.todo import TODOS_COLLECTION, TodoStatus, build_todo_document, serialize_todo
from app.routers.auth import get_current_user
from app.schemas.todo import (
    TodoCreateRequest,
    TodoResponse,
    TodoStatusUpdateRequest,
    TodoUpdateRequest,
)

router = APIRouter(prefix="/api/todos", tags=["todos"])


def _to_object_id(todo_id: str) -> ObjectId:
    if not ObjectId.is_valid(todo_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return ObjectId(todo_id)


@router.get("", response_model=list[TodoResponse])
async def list_todos(
    status_filter: TodoStatus | None = Query(default=None, alias="status"),
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    query: dict = {"user_id": current_user["_id"]}
    if status_filter is not None:
        query["status"] = status_filter

    cursor = db[TODOS_COLLECTION].find(query).sort("created_at", -1)
    documents = await cursor.to_list(length=500)
    return [serialize_todo(document) for document in documents]


@router.post("", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
async def create_todo(
    payload: TodoCreateRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    document = build_todo_document(
        user_id=current_user["_id"],
        title=payload.title,
        description=payload.description,
        due_date=payload.due_date,
    )
    result = await db[TODOS_COLLECTION].insert_one(document)
    created = await db[TODOS_COLLECTION].find_one({"_id": result.inserted_id})
    return serialize_todo(created)


@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(
    todo_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    document = await db[TODOS_COLLECTION].find_one(
        {"_id": _to_object_id(todo_id), "user_id": current_user["_id"]}
    )
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return serialize_todo(document)


@router.put("/{todo_id}", response_model=TodoResponse)
async def update_todo(
    todo_id: str,
    payload: TodoUpdateRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    update_data = payload.model_dump(exclude_unset=True)
    if "title" in update_data and update_data["title"] is not None:
        update_data["title"] = update_data["title"].strip()
    if "description" in update_data and update_data["description"] is not None:
        update_data["description"] = update_data["description"].strip()

    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc)
        result = await db[TODOS_COLLECTION].update_one(
            {"_id": _to_object_id(todo_id), "user_id": current_user["_id"]},
            {"$set": update_data},
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

    updated = await db[TODOS_COLLECTION].find_one(
        {"_id": _to_object_id(todo_id), "user_id": current_user["_id"]}
    )
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return serialize_todo(updated)


@router.patch("/{todo_id}/status", response_model=TodoResponse)
async def update_todo_status(
    todo_id: str,
    payload: TodoStatusUpdateRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    result = await db[TODOS_COLLECTION].update_one(
        {"_id": _to_object_id(todo_id), "user_id": current_user["_id"]},
        {"$set": {"status": payload.status, "updated_at": datetime.now(timezone.utc)}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

    updated = await db[TODOS_COLLECTION].find_one(
        {"_id": _to_object_id(todo_id), "user_id": current_user["_id"]}
    )
    return serialize_todo(updated)


@router.delete("/{todo_id}")
async def delete_todo(
    todo_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    result = await db[TODOS_COLLECTION].delete_one(
        {"_id": _to_object_id(todo_id), "user_id": current_user["_id"]}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

    return {"message": "Todo deleted"}
