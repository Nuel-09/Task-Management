import pytest


@pytest.mark.asyncio
async def test_ui_pages_return_html(async_client):
    pages = ["/", "/register", "/dashboard"]
    for path in pages:
        response = await async_client.get(path)
        assert response.status_code == 200, f"{path} should return 200"
        assert "text/html" in response.headers.get("content-type", "")
