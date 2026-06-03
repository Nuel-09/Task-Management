import pytest


@pytest.mark.asyncio
async def test_register_login_and_profile(async_client):
    register_response = await async_client.post(
        "/api/auth/register",
        json={
            "email": "user@example.com",
            "full_name": "Example User",
            "password": "password123",
        },
    )
    assert register_response.status_code == 201
    registered = register_response.json()
    assert registered["email"] == "user@example.com"
    assert registered["full_name"] == "Example User"

    login_response = await async_client.post(
        "/api/auth/login",
        json={"email": "user@example.com", "password": "password123"},
    )
    assert login_response.status_code == 200
    login_body = login_response.json()
    assert "access_token" in login_body
    assert login_body["token_type"] == "bearer"

    me_response = await async_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {login_body['access_token']}"},
    )
    assert me_response.status_code == 200
    profile = me_response.json()
    assert profile["email"] == "user@example.com"


@pytest.mark.asyncio
async def test_profile_requires_valid_token(async_client):
    response = await async_client.get("/api/auth/me")
    assert response.status_code == 401
