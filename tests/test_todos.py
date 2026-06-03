import pytest


async def _auth_headers(async_client):
    await async_client.post(
        "/api/auth/register",
        json={
            "email": "todo-user@example.com",
            "full_name": "Todo User",
            "password": "password123",
        },
    )
    login_response = await async_client.post(
        "/api/auth/login",
        json={"email": "todo-user@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_todo_crud_flow(async_client):
    headers = await _auth_headers(async_client)

    create_response = await async_client.post(
        "/api/todos",
        headers=headers,
        json={"title": "Write assignment", "description": "Prepare screenshots for evidence"},
    )
    assert create_response.status_code == 201
    created = create_response.json()
    todo_id = created["id"]
    assert created["status"] == "pending"

    list_response = await async_client.get("/api/todos", headers=headers)
    assert list_response.status_code == 200
    todos = list_response.json()
    assert len(todos) == 1

    update_response = await async_client.put(
        f"/api/todos/{todo_id}",
        headers=headers,
        json={"title": "Write assignment report"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Write assignment report"

    status_response = await async_client.patch(
        f"/api/todos/{todo_id}/status",
        headers=headers,
        json={"status": "completed"},
    )
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "completed"

    filtered_response = await async_client.get("/api/todos?status=completed", headers=headers)
    assert filtered_response.status_code == 200
    assert len(filtered_response.json()) == 1

    delete_response = await async_client.delete(f"/api/todos/{todo_id}", headers=headers)
    assert delete_response.status_code == 200

    final_list_response = await async_client.get("/api/todos", headers=headers)
    assert final_list_response.status_code == 200
    assert final_list_response.json() == []
